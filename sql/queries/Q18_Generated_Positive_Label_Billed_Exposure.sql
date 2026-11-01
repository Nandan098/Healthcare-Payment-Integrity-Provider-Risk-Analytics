SELECT SUM(IsFraud) AS generated_positive_claims,ROUND(SUM(CASE WHEN IsFraud=1 THEN BilledAmount ELSE 0 END),2) AS billed_amount_on_generated_positive_rows FROM claims;
