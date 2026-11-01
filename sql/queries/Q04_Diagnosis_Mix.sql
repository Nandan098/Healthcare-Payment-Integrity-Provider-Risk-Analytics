SELECT DiagnosisCode, COUNT(*) AS claims, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) AS claim_share_pct FROM claims GROUP BY DiagnosisCode ORDER BY claims DESC;
