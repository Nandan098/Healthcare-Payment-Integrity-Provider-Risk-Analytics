from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main(root:Path):
    raw=root/'data/raw';out=root/'outputs';rep=root/'reports';charts=rep/'charts'
    charts.mkdir(parents=True,exist_ok=True)
    patients=pd.read_csv(raw/'patients.csv')
    hospitals=pd.read_csv(raw/'hospitals.csv')
    claims=pd.read_csv(raw/'claims.csv',parse_dates=['AdmissionDate'])
    scores=pd.read_csv(out/'claims_scored.csv',parse_dates=['AdmissionDate'])
    scores[['ClaimID','RiskScore','AnomalyScore','RiskBand','AnomalyReviewFlag','PotentialBilledExposure_085','ScoringPartition']].to_csv(out/'claim_scores.csv',index=False)
    hold=pd.read_csv(out/'holdout_scored.csv')
    hold=hold.merge(patients[['PatientID','Age','Gender','Region']],on='PatientID',how='left')
    hold=hold.merge(hospitals[['HospitalID','Tier','Region']],on='HospitalID',how='left',suffixes=('_Patient','_Hospital'))
    hold['AgeBand']=pd.cut(hold.Age,[17,39,64,79,110],labels=['18-39','40-64','65-79','80+'])
    # KPI/Power BI-ready summaries.
    claims['ClaimMonth']=claims.AdmissionDate.dt.to_period('M').astype(str)
    monthly=claims.groupby('ClaimMonth',as_index=False).agg(Claims=('ClaimID','count'),BilledAmount_USD=('BilledAmount','sum'),AverageBill_USD=('BilledAmount','mean'),PositiveLabelRows=('IsFraud','sum'))
    monthly.to_csv(out/'monthly_claim_trends.csv',index=False)
    diagnosis=claims.groupby('DiagnosisCode',as_index=False).agg(Claims=('ClaimID','count'),TotalBilled_USD=('BilledAmount','sum'),AverageBilled_USD=('BilledAmount','mean'),MedianBilled_USD=('BilledAmount','median'),GeneratedPositiveRows=('IsFraud','sum'))
    diagnosis['SpendSharePct']=100*diagnosis.TotalBilled_USD/diagnosis.TotalBilled_USD.sum()
    diagnosis.sort_values('TotalBilled_USD',ascending=False).to_csv(out/'diagnosis_summary.csv',index=False)
    hosp=claims.merge(hospitals[['HospitalID','Hospital_Name','Tier','State','Region']],on='HospitalID',how='left')
    hsum=hosp.groupby(['HospitalID','Hospital_Name','Tier','State','Region'],as_index=False).agg(Claims=('ClaimID','count'),TotalBilled_USD=('BilledAmount','sum'),AverageBilled_USD=('BilledAmount','mean'),GeneratedPositiveRows=('IsFraud','sum'))
    hsum.sort_values('TotalBilled_USD',ascending=False).to_csv(out/'hospital_summary.csv',index=False)
    tier=hosp.groupby('Tier',as_index=False).agg(Claims=('ClaimID','count'),TotalBilled_USD=('BilledAmount','sum'),AverageBilled_USD=('BilledAmount','mean'),GeneratedPositiveRows=('IsFraud','sum'))
    tier.to_csv(out/'hospital_tier_summary.csv',index=False)
    region=hosp.groupby('Region',as_index=False).agg(Claims=('ClaimID','count'),TotalBilled_USD=('BilledAmount','sum'),AverageBilled_USD=('BilledAmount','mean'))
    region.to_csv(out/'region_summary.csv',index=False)
    rband=scores.groupby('RiskBand',observed=False,as_index=False).agg(Claims=('ClaimID','count'),AverageRiskScore=('RiskScore','mean'),BilledAmount_USD=('BilledAmount','sum'),PotentialBilledExposure_USD=('PotentialBilledExposure_085','sum'))
    rband.to_csv(out/'risk_band_summary.csv',index=False)
    # The top list is a workflow queue for further review, not an accusation or adjudication.
    scores.nlargest(1000,'RiskScore').to_csv(out/'high_risk_review_queue_top_1000.csv',index=False)
    scores.nlargest(1000,'AnomalyScore').to_csv(out/'anomaly_review_queue_top_1000.csv',index=False)

    # Group diagnostics on the held-out patient groups; this is a screening diagnostic, not a fairness certification.
    subgroup_rows=[]
    for col in ['Gender','AgeBand','Region_Patient','Tier']:
        for group,part in hold.groupby(col,dropna=False,observed=True):
            actual=part.IsFraud.to_numpy().astype(int)
            pred=(part.RiskScore.to_numpy()>=.5).astype(int)
            tp=int(((actual==1)&(pred==1)).sum()); fn=int(((actual==1)&(pred==0)).sum())
            fp=int(((actual==0)&(pred==1)).sum()); tn=int(((actual==0)&(pred==0)).sum())
            subgroup_rows.append({'GroupDimension':col,'GroupValue':str(group),'HoldoutClaims':len(part),
              'GeneratedPositiveRatePct':100*actual.mean(),'PredictedPositiveRatePct':100*pred.mean(),
              'Recall_TPR':tp/(tp+fn) if tp+fn else np.nan,'FalsePositiveRate':fp/(fp+tn) if fp+tn else np.nan,
              'Precision':tp/(tp+fp) if tp+fp else np.nan})
    pd.DataFrame(subgroup_rows).to_csv(out/'subgroup_model_diagnostics.csv',index=False)

    # EDA charts.
    plt.figure(figsize=(9,5));plt.hist(np.log10(claims.BilledAmount.clip(lower=1)),bins=45);plt.xlabel('log10(BilledAmount USD)');plt.ylabel('Claims');plt.title('Right-skewed claim billing distribution');plt.tight_layout();plt.savefig(charts/'01_log_billed_amount_distribution.png',dpi=150);plt.close()
    plt.figure(figsize=(10,5));plt.plot(monthly.ClaimMonth,monthly.Claims,marker='o',linewidth=1.2);plt.xticks(rotation=60,ha='right');plt.ylabel('Claims');plt.title('Monthly claim volume');plt.tight_layout();plt.savefig(charts/'02_monthly_claim_volume.png',dpi=150);plt.close()
    plt.figure(figsize=(9,5));dx=diagnosis.sort_values('TotalBilled_USD',ascending=False);plt.bar(dx.DiagnosisCode,dx.TotalBilled_USD/1e6);plt.xticks(rotation=45,ha='right');plt.ylabel('Total billed (USD millions)');plt.title('Total billed amount by diagnosis');plt.tight_layout();plt.savefig(charts/'03_billed_by_diagnosis.png',dpi=150);plt.close()
    plt.figure(figsize=(8,5));plt.hist(scores.RiskScore,bins=np.linspace(0,1,31));plt.xlabel('RiskScore');plt.ylabel('Claims');plt.title('Model risk score distribution');plt.tight_layout();plt.savefig(charts/'04_risk_score_distribution.png',dpi=150);plt.close()
    plt.figure(figsize=(8,5));plt.hist(scores.AnomalyScore,bins=np.linspace(0,1,31));plt.xlabel('AnomalyScore percentile rank');plt.ylabel('Claims');plt.title('Isolation Forest anomaly score distribution');plt.tight_layout();plt.savefig(charts/'05_anomaly_score_distribution.png',dpi=150);plt.close()

    summary=json.loads((rep/'data_quality_report.json').read_text())
    metrics=json.loads((rep/'model_metrics.json').read_text())
    eda={**summary,'top_diagnoses_by_spend':diagnosis.sort_values('TotalBilled_USD',ascending=False).head(5).to_dict('records'),
         'hospital_tier_summary':tier.to_dict('records'),'region_summary':region.to_dict('records'),
         'risk_band_summary':rband.to_dict('records'),'model_metrics':metrics}
    (rep/'eda_summary.json').write_text(json.dumps(eda,indent=2,default=str))

    top_diag=diagnosis.sort_values('TotalBilled_USD',ascending=False).iloc[0]
    top_tier=tier.sort_values('AverageBilled_USD',ascending=False).iloc[0]
    insights=f'''# Business Insights (Generated Dataset)\n\n> All numbers in this report describe generated records only. They are not observations from an insurer, hospital, payer, or fraud investigation.\n\n## Portfolio snapshot\n- Claims: **{len(claims):,}** across **{claims.PatientID.nunique():,}** referenced patients and **{claims.HospitalID.nunique():,}** hospitals.\n- Total billed amount: **${claims.BilledAmount.sum():,.2f}**; average claim: **${claims.BilledAmount.mean():,.2f}**; median claim: **${claims.BilledAmount.median():,.2f}**.\n- Billing is right-skewed: 95th percentile **${claims.BilledAmount.quantile(.95):,.2f}**, 99th percentile **${claims.BilledAmount.quantile(.99):,.2f}**.\n- Generated positive scenario labels: **{claims.IsFraud.sum():,} ({claims.IsFraud.mean()*100:.2f}%)**. This is an assumption of the generator, not a real fraud rate.\n\n## Exploratory patterns\n- Diagnosis **{top_diag.DiagnosisCode}** has the largest total billed amount in this generated sample (**${top_diag.TotalBilled_USD:,.2f}**, {top_diag.SpendSharePct:.1f}% of spend).\n- **{top_tier.Tier}** has the highest average billed amount per claim (**${top_tier.AverageBilled_USD:,.2f}**). Hospital tier and regional price factors are explicit generator inputs, so this is not an independent empirical finding.\n- Duplicate business-key groups: **{summary['duplicate_business_key_groups']:,}**. These groups are deliberately present for SQL review exercises.\n- Claim volumes and billed amounts vary across months, diagnoses, regions, and hospitals; categories were not equally weighted.\n\n## Model outputs\n- LightGBM ROC-AUC: **{metrics['roc_auc']:.3f}**; average precision / PR-AUC: **{metrics['average_precision_pr_auc']:.3f}** on patient-grouped holdout data.\n- At a 0.85 score cutoff, holdout precision was **{metrics['threshold_0_85']['precision']:.3f}** and recall **{metrics['threshold_0_85']['recall']:.3f}** across {metrics['threshold_0_85']['flagged_claims']:,} flagged claims.\n- Isolation Forest anomaly score is a percentile-rank measure of unusualness, **not a fraud probability**.\n\n## Business interpretation\nUse scores to prioritize manual review, compare charge patterns, and identify billing records needing context. Do not auto-deny a claim or accuse a provider/patient based only on a model score. Validate against adjudicated outcomes and policy rules before production use.\n'''
    (rep/'Business_Insights.md').write_text(insights)
    model_report=f'''# Model Evaluation\n\n## Supervised classification\n- Model: LightGBM binary classifier.\n- Dataset: {len(claims):,} claims; patient-group split of {metrics['train_rows']:,} training rows and {metrics['test_rows']:,} holdout rows.\n- Generated positive share: {metrics['train_positive_rate']*100:.2f}% in training and {metrics['test_positive_rate']*100:.2f}% in holdout.\n- ROC-AUC: {metrics['roc_auc']:.4f}.\n- Average precision / PR-AUC: {metrics['average_precision_pr_auc']:.4f}.\n- At threshold 0.50: precision {metrics['threshold_0_50']['precision']:.4f}, recall {metrics['threshold_0_50']['recall']:.4f}, F1 {metrics['threshold_0_50']['f1']:.4f}, accuracy {metrics['threshold_0_50']['accuracy']:.4f}.\n- At threshold 0.85: precision {metrics['threshold_0_85']['precision']:.4f}, recall {metrics['threshold_0_85']['recall']:.4f}, flagged {metrics['threshold_0_85']['flagged_claims']:,}.\n\n## Unsupervised anomaly detection\nIsolation Forest is trained without the IsFraud target. `AnomalyScore` is the percentile rank of negative Isolation Forest decision scores across this dataset. It indicates relative unusualness and must not be described as a fraud probability.\n\n## Scoring partition caveat\n`outputs/claims_scored.csv` contains full-population scores from the model trained on the 80% training partition. Rows marked `Training population score (in-sample)` were used to fit the model and their scores are optimistic / not independent evaluation results. Rows marked `Held-out test score` are the untouched patient-grouped holdout predictions. Use `holdout_scored.csv` for reported evaluation.\n\n## Limitations\nThe target is synthetic and scenario-created. These metrics show that the model learns generator-created patterns, not how it will perform on actual claims. The subgroup diagnostics are exploratory and are not a fairness certification. Production deployment would require real adjudicated outcomes, temporal validation, leakage review, calibration, threshold governance, privacy controls, and human review.\n'''
    (rep/'Model_Evaluation.md').write_text(model_report)
    print('Created dashboard summary CSVs, subgroup diagnostics, and charts.')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();main(a.root)
