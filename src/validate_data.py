from pathlib import Path
import json
import pandas as pd

def run(root: Path):
    raw=root/'data'/'raw'; rep=root/'reports'; rep.mkdir(parents=True,exist_ok=True)
    patients=pd.read_csv(raw/'patients.csv')
    hospitals=pd.read_csv(raw/'hospitals.csv')
    claims=pd.read_csv(raw/'claims.csv')
    checks=[]
    def add(name, passed, value, expected):
        checks.append({"check":name,"passed":bool(passed),"observed":str(value),"expected":str(expected)})
    add('claims_row_count',len(claims)==500_000,len(claims),'500000')
    add('patient_id_unique',patients.PatientID.is_unique,patients.PatientID.nunique(),len(patients))
    add('hospital_id_unique',hospitals.HospitalID.is_unique,hospitals.HospitalID.nunique(),len(hospitals))
    add('claim_id_unique',claims.ClaimID.is_unique,claims.ClaimID.nunique(),len(claims))
    add('patient_foreign_keys_valid',claims.PatientID.isin(patients.PatientID).all(),int((~claims.PatientID.isin(patients.PatientID)).sum()),0)
    add('hospital_foreign_keys_valid',claims.HospitalID.isin(hospitals.HospitalID).all(),int((~claims.HospitalID.isin(hospitals.HospitalID)).sum()),0)
    add('billed_amount_positive',(claims.BilledAmount>0).all(),float(claims.BilledAmount.min()),'>0')
    add('length_of_stay_positive',(claims.LengthOfStay>0).all(),int(claims.LengthOfStay.min()),'>0')
    add('fraud_target_binary',set(claims.IsFraud.unique()).issubset({0,1}),sorted(claims.IsFraud.unique().tolist()),'[0,1]')
    dates=pd.to_datetime(claims.AdmissionDate,errors='coerce')
    add('admission_dates_parse',dates.notna().all(),int(dates.isna().sum()),0)
    dis=pd.to_datetime(claims.DischargeDate,errors='coerce')
    add('discharge_on_or_after_admission',(dis>=dates).all(),int((dis<dates).sum()),0)
    add('all_claims_have_patient',claims.PatientID.notna().all(),int(claims.PatientID.isna().sum()),0)
    add('all_claims_have_hospital',claims.HospitalID.notna().all(),int(claims.HospitalID.isna().sum()),0)
    add('non_uniform_diagnosis_mix',claims.DiagnosisCode.value_counts(normalize=True).std()>0.005,round(float(claims.DiagnosisCode.value_counts(normalize=True).std()),4),'>0.005')
    add('non_uniform_hospital_use',claims.HospitalID.value_counts(normalize=True).std()>0.00001,round(float(claims.HospitalID.value_counts(normalize=True).std()),6),'>0.00001')
    df=pd.DataFrame(checks)
    df.to_csv(rep/'data_quality_checks.csv',index=False)
    missing=pd.concat([patients.isna().mean().rename('patients'),hospitals.isna().mean().rename('hospitals'),claims.isna().mean().rename('claims')],axis=1).fillna(0)
    missing.to_csv(rep/'missingness_report.csv')
    summary={
      'claims':len(claims),'patients':len(patients),'hospitals':len(hospitals),'positive_claims':int(claims.IsFraud.sum()),
      'positive_rate':float(claims.IsFraud.mean()),'total_billed_usd':float(claims.BilledAmount.sum()),
      'average_billed_usd':float(claims.BilledAmount.mean()),'median_billed_usd':float(claims.BilledAmount.median()),
      'p95_billed_usd':float(claims.BilledAmount.quantile(.95)),'p99_billed_usd':float(claims.BilledAmount.quantile(.99)),
      'duplicate_business_key_groups':int((claims.groupby(['PatientID','HospitalID','AdmissionDate','DiagnosisCode']).size()>1).sum()),
      'date_min':str(dates.min().date()),'date_max':str(dates.max().date()),'checks_passed':int(df.passed.sum()),'checks_total':len(df),
      'all_checks_passed':bool(df.passed.all())
    }
    (rep/'data_quality_report.json').write_text(json.dumps(summary,indent=2))
    if not df.passed.all():
        raise RuntimeError('One or more data quality checks failed: '+', '.join(df.loc[~df.passed,'check']))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();run(a.root)
