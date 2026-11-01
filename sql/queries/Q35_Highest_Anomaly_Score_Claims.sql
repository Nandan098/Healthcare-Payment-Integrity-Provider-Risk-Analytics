SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore FROM claims c JOIN claim_scores s USING(ClaimID) ORDER BY s.AnomalyScore DESC,c.BilledAmount DESC LIMIT 100;
