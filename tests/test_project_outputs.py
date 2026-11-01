from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def test_500k_claims_and_unique_ids():
    q=pd.read_csv(ROOT/'data/raw/claims.csv',usecols=['ClaimID'])
    assert len(q)==500_000
    assert q.ClaimID.is_unique

def test_referential_integrity():
    c=pd.read_csv(ROOT/'data/raw/claims.csv',usecols=['PatientID','HospitalID'])
    p=set(pd.read_csv(ROOT/'data/raw/patients.csv',usecols=['PatientID']).PatientID)
    h=set(pd.read_csv(ROOT/'data/raw/hospitals.csv',usecols=['HospitalID']).HospitalID)
    assert c.PatientID.isin(p).all()
    assert c.HospitalID.isin(h).all()

def test_generated_target_is_imbalanced():
    y=pd.read_csv(ROOT/'data/raw/claims.csv',usecols=['IsFraud']).IsFraud
    assert y.isin([0,1]).all()
    assert 0 < y.mean() < .10

def test_scores_cover_all_claims():
    s=pd.read_csv(ROOT/'outputs/claim_scores.csv',usecols=['ClaimID','RiskScore','AnomalyScore'])
    assert len(s)==500_000
    assert s.ClaimID.is_unique
    assert s.RiskScore.between(0,1).all()
    assert s.AnomalyScore.between(0,1).all()

def test_quality_checks_pass():
    q=pd.read_csv(ROOT/'reports/data_quality_checks.csv')
    assert q.passed.all()


def test_model_metrics_have_holdout_evaluation():
    m=json.loads((ROOT/'reports/model_metrics.json').read_text())
    assert m['test_rows'] > 0
    assert 0 <= m['roc_auc'] <= 1
    assert 0 <= m['average_precision_pr_auc'] <= 1
