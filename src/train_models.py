from __future__ import annotations
from pathlib import Path
import json, joblib, warnings
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_score, recall_score, f1_score,
                             accuracy_score, confusion_matrix, classification_report)

warnings.filterwarnings('ignore', category=FutureWarning)
SEED=20261030
NUMERIC = ["BilledAmount","LengthOfStay","Age","TierNumeric","CostPerDay","DiagnosisMedianBill",
           "BilledVsDiagnosisMedian","HospitalDiagnosisMedianBill","BilledVsHospitalDiagnosisMedian",
           "AdmissionMonth","AdmissionYear","AdmissionDayOfWeek","PriorPatientClaims",
           "DuplicateBusinessKeyCount","RepeatUse30dFlag","IsEmergency","HasComplications"]
CATEGORICAL = ["DiagnosisCode","ProcedureCategory","AdmissionType","Gender","PatientRegion","PatientState",
               "HospitalTier","HospitalRegion"]
FEATURES=NUMERIC+CATEGORICAL


def build_feature_frame(root: Path):
    claims=pd.read_csv(root/'data/raw/claims.csv', parse_dates=['AdmissionDate'])
    patients=pd.read_csv(root/'data/raw/patients.csv')
    hospitals=pd.read_csv(root/'data/raw/hospitals.csv')
    df=claims.merge(patients[['PatientID','Age','Gender','Region','State']],on='PatientID',how='left',validate='many_to_one')
    df=df.rename(columns={'Region':'PatientRegion','State':'PatientState'})
    df=df.merge(hospitals[['HospitalID','Tier','State','Region','HospitalCostIndex']],on='HospitalID',how='left',validate='many_to_one',suffixes=('','_Hospital'))
    df=df.rename(columns={'State':'HospitalState','Region':'HospitalRegion','Tier':'HospitalTier'})
    df['TierNumeric']=df['HospitalTier'].map({'Tier 1':1,'Tier 2':2,'Tier 3':3}).astype(float)
    df['CostPerDay']=df['BilledAmount']/df['LengthOfStay'].clip(lower=1)
    df['AdmissionMonth']=df['AdmissionDate'].dt.month.astype(int)
    df['AdmissionYear']=df['AdmissionDate'].dt.year.astype(int)
    df['AdmissionDayOfWeek']=df['AdmissionDate'].dt.dayofweek.astype(int)
    # Patient prior-utilization count is chronological, not simply the final lifetime count.
    prior=df.sort_values(['PatientID','AdmissionDate','ClaimID']).groupby('PatientID').cumcount()
    df['PriorPatientClaims']=prior.reindex(df.index).astype(int)
    key_cols=['PatientID','HospitalID','AdmissionDate','DiagnosisCode']
    df['DuplicateBusinessKeyCount']=df.groupby(key_cols)['ClaimID'].transform('size').astype(int)
    sorted_rows=df[['PatientID','DiagnosisCode','AdmissionDate']].sort_values(['PatientID','DiagnosisCode','AdmissionDate'])
    day_gap=sorted_rows.groupby(['PatientID','DiagnosisCode'])['AdmissionDate'].diff().dt.days
    df['RepeatUse30dFlag']=((day_gap>=0)&(day_gap<=30)).astype(int).reindex(df.index).fillna(0).astype(int)
    return df


def fit_and_score(root: Path):
    out=root/'outputs'; models=root/'models'; reports=root/'reports'
    out.mkdir(exist_ok=True,parents=True);models.mkdir(exist_ok=True);reports.mkdir(exist_ok=True)
    df=build_feature_frame(root)
    y=df['IsFraud'].astype(int)
    split=GroupShuffleSplit(n_splits=1,test_size=.20,random_state=SEED)
    train_idx,test_idx=next(split.split(df,y,groups=df['PatientID']))
    train_raw=df.iloc[train_idx].copy(); test_raw=df.iloc[test_idx].copy()
    # Diagnosis and hospital-diagnosis benchmarks are fit only on the training patients.
    diag_median=train_raw.groupby('DiagnosisCode')['BilledAmount'].median()
    hosp_diag_median=train_raw.groupby(['HospitalID','DiagnosisCode'])['BilledAmount'].median()
    global_med=float(train_raw['BilledAmount'].median())
    df['DiagnosisMedianBill']=df['DiagnosisCode'].map(diag_median).fillna(global_med)
    hd_index=pd.MultiIndex.from_frame(df[['HospitalID','DiagnosisCode']])
    df['HospitalDiagnosisMedianBill']=hosp_diag_median.reindex(hd_index).to_numpy()
    df['HospitalDiagnosisMedianBill']=df['HospitalDiagnosisMedianBill'].fillna(df['DiagnosisMedianBill'])
    df['BilledVsDiagnosisMedian']=(df['BilledAmount']/df['DiagnosisMedianBill'].clip(lower=1)).clip(0,30)
    df['BilledVsHospitalDiagnosisMedian']=(df['BilledAmount']/df['HospitalDiagnosisMedianBill'].clip(lower=1)).clip(0,30)
    # LightGBM uses native categorical features; align category levels across train/test/all rows.
    for col in CATEGORICAL:
        df[col]=df[col].astype('category')
    X_train=df.iloc[train_idx][FEATURES]
    X_test=df.iloc[test_idx][FEATURES]
    y_train=y.iloc[train_idx];y_test=y.iloc[test_idx]
    neg=max(1,int((y_train==0).sum()));pos=max(1,int((y_train==1).sum()))
    # A moderate positive-class weight addresses imbalance without forcing a 50/50 resampling.
    model=LGBMClassifier(n_estimators=420,learning_rate=.045,num_leaves=31,max_depth=-1,
        min_child_samples=90,subsample=.82,colsample_bytree=.84,reg_lambda=2.5,
        scale_pos_weight=min(10.0,max(1.0,(neg/pos)**.45)),random_state=SEED,n_jobs=4,
        verbosity=-1, max_bin=127)
    model.fit(X_train,y_train,categorical_feature=CATEGORICAL)
    test_prob=model.predict_proba(X_test)[:,1]
    test_pred=(test_prob>=.50).astype(int)
    cm=confusion_matrix(y_test,test_pred,labels=[0,1])
    high85=test_prob>=.85
    metrics={
      'dataset_claims':int(len(df)),'train_rows':int(len(train_idx)),'test_rows':int(len(test_idx)),
      'train_positive_rate':float(y_train.mean()),'test_positive_rate':float(y_test.mean()),
      'threshold_0_50':{'precision':float(precision_score(y_test,test_pred,zero_division=0)),
        'recall':float(recall_score(y_test,test_pred,zero_division=0)),
        'f1':float(f1_score(y_test,test_pred,zero_division=0)),
        'accuracy':float(accuracy_score(y_test,test_pred)),'confusion_matrix':cm.tolist()},
      'roc_auc':float(roc_auc_score(y_test,test_prob)),
      'average_precision_pr_auc':float(average_precision_score(y_test,test_prob)),
      'threshold_0_85':{'precision':float(precision_score(y_test,high85,zero_division=0)),
        'recall':float(recall_score(y_test,high85,zero_division=0)),
        'flagged_claims':int(high85.sum()),'billed_exposure_usd':float(test_raw.loc[high85,'BilledAmount'].sum())},
      'evaluation_design':'Single 80/20 GroupShuffleSplit by PatientID. Diagnosis and hospital-diagnosis median benchmarks are derived from training patients only.',
      'model':'LightGBM binary classifier; positive class given moderate scale_pos_weight to account for imbalance.',
      'target_caveat':'IsFraud is a generated scenario label, not a verified fraud outcome. Metrics measure recovery of generator-created patterns only.'
    }
    (reports/'model_metrics.json').write_text(json.dumps(metrics,indent=2))
    pd.DataFrame(classification_report(y_test,test_pred,output_dict=True,zero_division=0)).T.to_csv(out/'classification_report_threshold_050.csv')
    pd.DataFrame(cm,index=['Actual_0','Actual_1'],columns=['Predicted_0','Predicted_1']).to_csv(out/'confusion_matrix_threshold_050.csv')
    holdout=df.iloc[test_idx][['ClaimID','PatientID','HospitalID','AdmissionDate','DiagnosisCode','BilledAmount','IsFraud']].copy()
    holdout['RiskScore']=test_prob
    holdout['PredictedLabel_050']=test_pred
    holdout['PotentialBilledExposure_085']=np.where(high85,holdout['BilledAmount'],0.0)

    # Isolation Forest is fit without IsFraud or risk model probabilities.
    anomaly_cols=['BilledAmount','CostPerDay','LengthOfStay','BilledVsDiagnosisMedian','BilledVsHospitalDiagnosisMedian','PriorPatientClaims']
    numeric_anomaly=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler())])
    an_train=numeric_anomaly.fit_transform(df.iloc[train_idx][anomaly_cols])
    rng=np.random.default_rng(SEED)
    sample_ix=rng.choice(len(an_train),size=min(80_000,len(an_train)),replace=False)
    iso=IsolationForest(n_estimators=100,max_samples=1024,contamination='auto',n_jobs=4,random_state=SEED)
    iso.fit(an_train[sample_ix])
    an_all=numeric_anomaly.transform(df[anomaly_cols])
    raw_anomaly=-iso.score_samples(an_all)
    anomaly_score=pd.Series(raw_anomaly).rank(pct=True,method='average').to_numpy()

    # The full-population score file is for exploratory dashboard use. The held-out metrics
    # above are the unbiased project evaluation slice; scores on training rows are in-sample.
    all_prob=model.predict_proba(df[FEATURES])[:,1]
    scored=df[['ClaimID','PatientID','HospitalID','AdmissionDate','DischargeDate','DiagnosisCode','SecondaryDiagnosisCode',
               'ProcedureCategory','AdmissionType','IsEmergency','LengthOfStay','HasComplications','BilledAmount','IsFraud',
               'Age','Gender','PatientRegion','PatientState','HospitalTier','HospitalState','HospitalRegion',
               'CostPerDay','DiagnosisMedianBill','BilledVsDiagnosisMedian','HospitalDiagnosisMedianBill',
               'BilledVsHospitalDiagnosisMedian','PriorPatientClaims','DuplicateBusinessKeyCount','RepeatUse30dFlag']].copy()
    scored['RiskScore']=all_prob
    scored['AnomalyScore']=anomaly_score
    scored['RiskBand']=pd.cut(all_prob,bins=[-0.001,.20,.50,.85,1.001],labels=['Low','Moderate','Elevated','High']).astype(str)
    scored['AnomalyReviewFlag']=scored['AnomalyScore']>=.98
    scored['PotentialBilledExposure_085']=np.where(scored['RiskScore']>=.85,scored['BilledAmount'],0.0)
    train_mask=np.ones(len(df),dtype=bool);train_mask[test_idx]=False
    scored['ScoringPartition']=np.where(train_mask,'Training population score (in-sample)','Held-out test score')
    scored.to_csv(out/'claims_scored.csv',index=False)
    scored[['ClaimID','RiskScore','AnomalyScore','RiskBand','AnomalyReviewFlag','PotentialBilledExposure_085','ScoringPartition']].to_csv(out/'claim_scores.csv',index=False)
    # Enrich the independent holdout export with both scores for fair comparison / review examples.
    holdout['AnomalyScore']=anomaly_score[test_idx]
    holdout['AnomalyReviewFlag']=holdout['AnomalyScore']>=.98
    holdout['RiskBand']=pd.cut(holdout['RiskScore'],bins=[-0.001,.20,.50,.85,1.001],labels=['Low','Moderate','Elevated','High']).astype(str)
    holdout.to_csv(out/'holdout_scored.csv',index=False)
    holdout.nlargest(1000,'RiskScore').to_csv(out/'holdout_high_risk_review_queue_top_1000.csv',index=False)
    holdout.nlargest(1000,'AnomalyScore').to_csv(out/'holdout_anomaly_review_queue_top_1000.csv',index=False)
    joblib.dump({'model':model,'numeric_features':NUMERIC,'categorical_features':CATEGORICAL,'training_medians':{'diagnosis':diag_median.to_dict(),'hospital_diagnosis':{f'{k[0]}|{k[1]}':v for k,v in hosp_diag_median.items()},'global':global_med}},models/'lightgbm_claim_risk_pipeline.joblib',compress=3)
    joblib.dump({'preprocessor':numeric_anomaly,'isolation_forest':iso,'features':anomaly_cols},models/'isolation_forest_pipeline.joblib',compress=3)
    fi=pd.DataFrame({'Feature':model.feature_name_,'Importance':model.feature_importances_}).sort_values('Importance',ascending=False)
    fi.to_csv(out/'feature_importance.csv',index=False)
    scored.nlargest(5000,'RiskScore').to_csv(out/'top_5000_risk_claims.csv',index=False)
    print(json.dumps(metrics,indent=2))
    print('All-claims scored rows:',len(scored),'High risk >=.85:',int((scored.RiskScore>=.85).sum()),'Anomaly >=.98:',int((scored.AnomalyScore>=.98).sum()))
    return metrics

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();fit_and_score(a.root)
