SELECT c.ClaimID,c.BilledAmount,c.LengthOfStay,c.DiagnosisCode,h.Hospital_Name,h.Tier,h.State FROM claims c JOIN hospitals h USING(HospitalID) ORDER BY c.BilledAmount DESC LIMIT 50;
