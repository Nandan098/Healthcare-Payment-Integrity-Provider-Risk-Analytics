from pathlib import Path
import sqlite3, csv
import pandas as pd

QUERIES = {
'Q01_Executive_Portfolio_Snapshot': '''SELECT COUNT(*) AS total_claims, COUNT(DISTINCT PatientID) AS unique_patients, COUNT(DISTINCT HospitalID) AS hospitals, ROUND(SUM(BilledAmount),2) AS total_billed_usd, ROUND(AVG(BilledAmount),2) AS avg_claim_usd, ROUND(AVG(LengthOfStay),2) AS avg_los FROM claims;''',
'Q02_Monthly_Claims_and_Billing': '''SELECT strftime('%Y-%m',AdmissionDate) AS claim_month, COUNT(*) AS claims, ROUND(SUM(BilledAmount),2) AS billed_usd, ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY claim_month ORDER BY claim_month;''',
'Q03_Annual_Claims_and_Billing': '''SELECT strftime('%Y',AdmissionDate) AS claim_year, COUNT(*) AS claims, ROUND(SUM(BilledAmount),2) AS billed_usd FROM claims GROUP BY claim_year ORDER BY claim_year;''',
'Q04_Diagnosis_Mix': '''SELECT DiagnosisCode, COUNT(*) AS claims, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) AS claim_share_pct FROM claims GROUP BY DiagnosisCode ORDER BY claims DESC;''',
'Q05_Diagnosis_Billing_Benchmark': '''SELECT DiagnosisCode, COUNT(*) AS claims, ROUND(AVG(BilledAmount),2) AS avg_bill_usd, ROUND(MIN(BilledAmount),2) AS min_bill_usd, ROUND(MAX(BilledAmount),2) AS max_bill_usd FROM claims GROUP BY DiagnosisCode ORDER BY avg_bill_usd DESC;''',
'Q06_Hospital_Tier_Benchmark': '''SELECT h.Tier, COUNT(*) AS claims, ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd, ROUND(SUM(c.BilledAmount),2) AS total_billed_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Tier ORDER BY avg_bill_usd DESC;''',
'Q07_Top_Hospitals_by_Claims': '''SELECT h.Hospital_Name,h.Tier,h.State,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS total_billed_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID ORDER BY claims DESC LIMIT 25;''',
'Q08_Hospital_Region_Spend': '''SELECT h.Region,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS billed_usd,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Region ORDER BY billed_usd DESC;''',
'Q09_Patient_Age_Band_Utilization': '''SELECT CASE WHEN p.Age<40 THEN '18-39' WHEN p.Age<65 THEN '40-64' WHEN p.Age<80 THEN '65-79' ELSE '80+' END AS age_band,COUNT(*) AS claims,COUNT(DISTINCT c.PatientID) AS patients,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd,ROUND(SUM(c.BilledAmount),2) AS spend_usd FROM claims c JOIN patients p USING(PatientID) GROUP BY age_band ORDER BY age_band;''',
'Q10_Patient_Claim_Frequency': '''WITH x AS (SELECT PatientID,COUNT(*) AS n_claims FROM claims GROUP BY PatientID) SELECT CASE WHEN n_claims=1 THEN '1' WHEN n_claims<=3 THEN '2-3' WHEN n_claims<=6 THEN '4-6' WHEN n_claims<=12 THEN '7-12' ELSE '13+' END AS frequency_band,COUNT(*) AS patients FROM x GROUP BY frequency_band ORDER BY MIN(n_claims);''',
'Q11_Largest_Individual_Bills': '''SELECT c.ClaimID,c.BilledAmount,c.LengthOfStay,c.DiagnosisCode,h.Hospital_Name,h.Tier,h.State FROM claims c JOIN hospitals h USING(HospitalID) ORDER BY c.BilledAmount DESC LIMIT 50;''',
'Q12_Length_of_Stay_Distribution': '''SELECT CASE WHEN LengthOfStay<=1 THEN '1 day' WHEN LengthOfStay<=3 THEN '2-3 days' WHEN LengthOfStay<=7 THEN '4-7 days' WHEN LengthOfStay<=14 THEN '8-14 days' ELSE '15+ days' END AS los_band,COUNT(*) AS claims,ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY los_band ORDER BY MIN(LengthOfStay);''',
'Q13_Cost_Per_Day_Outlier_Screen': '''SELECT ClaimID,DiagnosisCode,LengthOfStay,ROUND(BilledAmount/LengthOfStay,2) AS cost_per_day_usd,BilledAmount FROM claims WHERE BilledAmount/LengthOfStay>(SELECT AVG(BilledAmount/LengthOfStay)+3.0*AVG(ABS((BilledAmount/LengthOfStay)-(SELECT AVG(BilledAmount/LengthOfStay) FROM claims))) FROM claims) ORDER BY cost_per_day_usd DESC LIMIT 100;''',
'Q14_Duplicate_Business_Key_Groups': '''SELECT PatientID,HospitalID,AdmissionDate,DiagnosisCode,COUNT(*) AS group_rows,ROUND(SUM(BilledAmount),2) AS group_billed_usd FROM claims GROUP BY PatientID,HospitalID,AdmissionDate,DiagnosisCode HAVING COUNT(*)>1 ORDER BY group_rows DESC,group_billed_usd DESC LIMIT 250;''',
'Q15_Billing_Above_Diagnosis_Average': '''WITH d AS (SELECT DiagnosisCode,AVG(BilledAmount) AS avg_bill FROM claims GROUP BY DiagnosisCode) SELECT c.ClaimID,c.DiagnosisCode,c.BilledAmount,ROUND(d.avg_bill,2) AS diagnosis_avg,ROUND(c.BilledAmount/d.avg_bill,2) AS ratio FROM claims c JOIN d USING(DiagnosisCode) WHERE c.BilledAmount>2*d.avg_bill ORDER BY ratio DESC LIMIT 250;''',
'Q16_Simulated_Positive_Rate_by_Diagnosis': '''SELECT DiagnosisCode,COUNT(*) AS claims,SUM(IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(IsFraud),2) AS generated_positive_rate_pct FROM claims GROUP BY DiagnosisCode ORDER BY generated_positive_rate_pct DESC;''',
'Q17_Generated_Positive_Rate_by_Hospital_Tier': '''SELECT h.Tier,COUNT(*) AS claims,SUM(c.IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(c.IsFraud),2) AS generated_positive_rate_pct FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Tier;''',
'Q18_Generated_Positive_Label_Billed_Exposure': '''SELECT SUM(IsFraud) AS generated_positive_claims,ROUND(SUM(CASE WHEN IsFraud=1 THEN BilledAmount ELSE 0 END),2) AS billed_amount_on_generated_positive_rows FROM claims;''',
'Q19_Diagnosis_Share_of_Total_Spend': '''SELECT DiagnosisCode,ROUND(SUM(BilledAmount),2) AS billed_usd,ROUND(100.0*SUM(BilledAmount)/(SELECT SUM(BilledAmount) FROM claims),2) AS spend_share_pct FROM claims GROUP BY DiagnosisCode ORDER BY billed_usd DESC;''',
'Q20_Gender_and_Claim_Profile': '''SELECT p.Gender,COUNT(*) AS claims,COUNT(DISTINCT p.PatientID) AS patients,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd,ROUND(SUM(c.BilledAmount),2) AS spend_usd FROM claims c JOIN patients p USING(PatientID) GROUP BY p.Gender;''',
'Q21_Admission_Type_and_Emergency_Profile': '''SELECT AdmissionType,IsEmergency,COUNT(*) AS claims,ROUND(AVG(LengthOfStay),2) AS avg_los,ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY AdmissionType,IsEmergency ORDER BY claims DESC;''',
'Q22_Hospital_State_Claims_and_Spend': '''SELECT h.State,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS billed_usd,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.State ORDER BY billed_usd DESC;''',
'Q23_Quarterly_Claims_and_Billing': '''SELECT strftime('%Y',AdmissionDate)||'-Q'||((CAST(strftime('%m',AdmissionDate) AS INTEGER)+2)/3) AS quarter,COUNT(*) AS claims,ROUND(SUM(BilledAmount),2) AS billed_usd FROM claims GROUP BY quarter ORDER BY quarter;''',
'Q24_Duplicate_Key_Groups_by_Hospital': '''WITH d AS (SELECT HospitalID,PatientID,AdmissionDate,DiagnosisCode,COUNT(*) n FROM claims GROUP BY HospitalID,PatientID,AdmissionDate,DiagnosisCode HAVING COUNT(*)>1) SELECT h.Hospital_Name,h.Tier,COUNT(*) AS duplicate_groups,SUM(d.n) AS rows_in_duplicate_groups FROM d JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID ORDER BY duplicate_groups DESC LIMIT 50;''',
'Q25_High_Utilization_Patients': '''SELECT c.PatientID,p.Age,p.Gender,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS total_billed_usd,COUNT(DISTINCT c.HospitalID) AS hospitals_used FROM claims c JOIN patients p USING(PatientID) GROUP BY c.PatientID ORDER BY claims DESC,total_billed_usd DESC LIMIT 100;''',
'Q26_Hospital_Diagnosis_Billing_Cells': '''SELECT h.Hospital_Name,h.Tier,c.DiagnosisCode,COUNT(*) AS claims,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID,c.DiagnosisCode HAVING COUNT(*)>=20 ORDER BY avg_bill_usd DESC LIMIT 200;''',
'Q27_Hospital_Concentration': '''WITH h AS (SELECT HospitalID,SUM(BilledAmount) spend FROM claims GROUP BY HospitalID) SELECT COUNT(*) AS facilities,ROUND(MAX(spend),2) AS largest_hospital_spend,ROUND(100.0*MAX(spend)/(SELECT SUM(BilledAmount) FROM claims),2) AS largest_hospital_spend_share_pct FROM h;''',
'Q28_Repeat_Patient_Diagnosis_Within_30_Days': '''WITH x AS (SELECT PatientID,DiagnosisCode,AdmissionDate,LAG(AdmissionDate) OVER(PARTITION BY PatientID,DiagnosisCode ORDER BY AdmissionDate) AS prior_date FROM claims) SELECT COUNT(*) AS repeat_episode_rows FROM x WHERE prior_date IS NOT NULL AND julianday(AdmissionDate)-julianday(prior_date)<=30;''',
'Q29_Average_Bill_by_LOS_Band': '''SELECT CASE WHEN LengthOfStay<=2 THEN '1-2' WHEN LengthOfStay<=5 THEN '3-5' WHEN LengthOfStay<=10 THEN '6-10' WHEN LengthOfStay<=20 THEN '11-20' ELSE '21+' END AS los_band,COUNT(*) claims,ROUND(AVG(BilledAmount),2) avg_bill_usd,ROUND(AVG(BilledAmount/LengthOfStay),2) avg_cost_per_day_usd FROM claims GROUP BY los_band ORDER BY MIN(LengthOfStay);''',
'Q30_Billed_Amount_Bands': '''SELECT CASE WHEN BilledAmount<10000 THEN '<$10k' WHEN BilledAmount<25000 THEN '$10k-$25k' WHEN BilledAmount<50000 THEN '$25k-$50k' WHEN BilledAmount<100000 THEN '$50k-$100k' WHEN BilledAmount<250000 THEN '$100k-$250k' ELSE '$250k+' END AS billed_band,COUNT(*) claims,ROUND(SUM(BilledAmount),2) spend_usd FROM claims GROUP BY billed_band ORDER BY MIN(BilledAmount);''',
'Q31_Secondary_Diagnosis_Coverage': '''SELECT CASE WHEN SecondaryDiagnosisCode IS NULL OR SecondaryDiagnosisCode='' THEN 'Missing/None' ELSE 'Present' END AS secondary_diagnosis_status,COUNT(*) claims,ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) share_pct FROM claims GROUP BY secondary_diagnosis_status;''',
'Q32_Risk_Band_Summary': '''SELECT RiskBand,COUNT(*) AS claims,ROUND(AVG(RiskScore),4) AS avg_risk_score,ROUND(SUM(PotentialBilledExposure_085),2) AS flagged_billed_exposure_usd FROM claim_scores GROUP BY RiskBand ORDER BY avg_risk_score DESC;''',
'Q33_High_Risk_Exposure_by_Hospital_Tier': '''SELECT h.Tier,COUNT(*) AS scored_claims,SUM(CASE WHEN s.RiskScore>=.85 THEN 1 ELSE 0 END) AS high_risk_claims,ROUND(SUM(s.PotentialBilledExposure_085),2) AS potential_billed_exposure_usd FROM claim_scores s JOIN claims c USING(ClaimID) JOIN hospitals h USING(HospitalID) GROUP BY h.Tier ORDER BY potential_billed_exposure_usd DESC;''',
'Q34_Risk_Score_vs_Generated_Label': '''SELECT CASE WHEN RiskScore<.2 THEN 'Low' WHEN RiskScore<.5 THEN 'Moderate' WHEN RiskScore<.85 THEN 'Elevated' ELSE 'High' END AS risk_band,COUNT(*) claims,SUM(c.IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(c.IsFraud),3) AS generated_positive_rate_pct FROM claim_scores s JOIN claims c USING(ClaimID) GROUP BY risk_band ORDER BY MIN(RiskScore);''',
'Q35_Highest_Anomaly_Score_Claims': '''SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore FROM claims c JOIN claim_scores s USING(ClaimID) ORDER BY s.AnomalyScore DESC,c.BilledAmount DESC LIMIT 100;''',
'Q36_Anomaly_Risk_Disagreement': '''SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore FROM claims c JOIN claim_scores s USING(ClaimID) WHERE s.AnomalyScore>=.98 AND s.RiskScore<.50 ORDER BY s.AnomalyScore DESC,c.BilledAmount DESC LIMIT 100;''',
'Q37_Top_Risk_Claims': '''SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore,s.PotentialBilledExposure_085 FROM claims c JOIN claim_scores s USING(ClaimID) ORDER BY s.RiskScore DESC,c.BilledAmount DESC LIMIT 100;''',
'Q38_Risk_Score_by_Diagnosis': '''SELECT c.DiagnosisCode,COUNT(*) claims,ROUND(AVG(s.RiskScore),4) avg_risk_score,SUM(CASE WHEN s.RiskScore>=.85 THEN 1 ELSE 0 END) high_risk_claims,ROUND(SUM(s.PotentialBilledExposure_085),2) potential_billed_exposure_usd FROM claims c JOIN claim_scores s USING(ClaimID) GROUP BY c.DiagnosisCode ORDER BY avg_risk_score DESC;''',
'Q39_Risk_and_Anomaly_Cross_Tab': '''SELECT CASE WHEN RiskScore>=.85 THEN 'High risk' WHEN RiskScore>=.5 THEN 'Elevated risk' ELSE 'Below .50 risk' END AS risk_group,CASE WHEN AnomalyScore>=.98 THEN 'Top 2% anomaly' ELSE 'Other anomaly range' END AS anomaly_group,COUNT(*) claims FROM claim_scores GROUP BY risk_group,anomaly_group ORDER BY risk_group,anomaly_group;''',
'Q40_High_Risk_Claims_by_Month': '''SELECT strftime('%Y-%m',c.AdmissionDate) AS claim_month,COUNT(*) AS high_risk_claims,ROUND(SUM(c.BilledAmount),2) AS billed_exposure_usd FROM claims c JOIN claim_scores s USING(ClaimID) WHERE s.RiskScore>=.85 GROUP BY claim_month ORDER BY claim_month;''',
}

def main(root:Path):
    db=root/'data/processed/healthcare_claims_500k.db'
    qdir=root/'sql/queries';qdir.mkdir(parents=True,exist_ok=True)
    outdir=root/'reports/sql_results';outdir.mkdir(parents=True,exist_ok=True)
    report=['# SQL Business Questions & Answers','',f'Executed {len(QUERIES)} SQLite analyses against the 500,000-row healthcare claims project. Results are descriptive of generated data.','']
    con=sqlite3.connect(db)
    catalog=[]
    for name,sql in QUERIES.items():
        qfile=qdir/(name+'.sql');qfile.write_text(sql.strip()+'\n')
        try:
            res=pd.read_sql_query(sql,con)
            res.to_csv(outdir/(name+'.csv'),index=False)
            catalog.append({'Question_ID':name.split('_')[0],'Question':name.split('_',1)[1].replace('_',' '),'Rows_Returned':len(res),'Status':'PASS','SQL_File':str(qfile.relative_to(root))})
            report += [f'## {name.split("_",1)[1].replace("_"," ")}', '', '```sql', sql.strip(), '```', '', f'Result rows: **{len(res)}**', '']
            if len(res):
                report += ['```text',res.head(12).to_string(index=False),'```','']
        except Exception as e:
            catalog.append({'Question_ID':name.split('_')[0],'Question':name,'Rows_Returned':0,'Status':'FAIL: '+str(e),'SQL_File':str(qfile.relative_to(root))})
            report += [f'## {name}', '', f'**Execution failed:** {e}', '']
    con.close()
    pd.DataFrame(catalog).to_csv(root/'sql/query_catalog.csv',index=False)
    (root/'reports/SQL_Questions_and_Answers.md').write_text('\n'.join(report))
    n_pass=sum(x['Status']=='PASS' for x in catalog)
    print(f'SQL queries passed: {n_pass}/{len(catalog)}')
    if n_pass!=len(catalog):
        print(pd.DataFrame(catalog).query("Status != 'PASS'").to_string(index=False))
        raise RuntimeError('Some SQL questions failed.')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();main(a.root)
