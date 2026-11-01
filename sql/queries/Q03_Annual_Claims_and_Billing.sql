SELECT strftime('%Y',AdmissionDate) AS claim_year, COUNT(*) AS claims, ROUND(SUM(BilledAmount),2) AS billed_usd FROM claims GROUP BY claim_year ORDER BY claim_year;
