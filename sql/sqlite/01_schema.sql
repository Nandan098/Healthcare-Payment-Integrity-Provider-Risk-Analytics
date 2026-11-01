PRAGMA foreign_keys=ON;
CREATE TABLE patients (
  PatientID TEXT PRIMARY KEY, Age INTEGER NOT NULL, Gender TEXT NOT NULL,
  State TEXT NOT NULL, Region TEXT NOT NULL, InsuranceSegment TEXT NOT NULL
);
CREATE TABLE hospitals (
  HospitalID TEXT PRIMARY KEY, Hospital_Name TEXT NOT NULL, Tier TEXT NOT NULL,
  State TEXT NOT NULL, Region TEXT NOT NULL, BedCapacity INTEGER NOT NULL,
  TeachingHospital INTEGER NOT NULL, HospitalCostIndex REAL NOT NULL
);
CREATE TABLE claims (
  ClaimID TEXT PRIMARY KEY, PatientID TEXT NOT NULL, HospitalID TEXT NOT NULL,
  AdmissionDate TEXT NOT NULL, DiagnosisCode TEXT NOT NULL, ProcedureCategory TEXT NOT NULL,
  AdmissionType TEXT NOT NULL, IsEmergency INTEGER NOT NULL, LengthOfStay INTEGER NOT NULL,
  HasComplications INTEGER NOT NULL, BilledAmount REAL NOT NULL, IsFraud INTEGER NOT NULL,
  DischargeDate TEXT NOT NULL, SecondaryDiagnosisCode TEXT,
  FOREIGN KEY(PatientID) REFERENCES patients(PatientID),
  FOREIGN KEY(HospitalID) REFERENCES hospitals(HospitalID)
);
CREATE TABLE claim_scores (
  ClaimID TEXT PRIMARY KEY, RiskScore REAL NOT NULL, AnomalyScore REAL NOT NULL,
  RiskBand TEXT NOT NULL, AnomalyReviewFlag INTEGER NOT NULL,
  PotentialBilledExposure_085 REAL NOT NULL, ScoringPartition TEXT NOT NULL,
  FOREIGN KEY(ClaimID) REFERENCES claims(ClaimID)
);
CREATE INDEX idx_claims_patient ON claims(PatientID);
CREATE INDEX idx_claims_hospital ON claims(HospitalID);
CREATE INDEX idx_claims_date ON claims(AdmissionDate);
CREATE INDEX idx_claims_diag ON claims(DiagnosisCode);
CREATE INDEX idx_scores_risk ON claim_scores(RiskScore);
CREATE INDEX idx_scores_anomaly ON claim_scores(AnomalyScore);
CREATE INDEX idx_claims_business_key ON claims(PatientID,HospitalID,AdmissionDate,DiagnosisCode);
