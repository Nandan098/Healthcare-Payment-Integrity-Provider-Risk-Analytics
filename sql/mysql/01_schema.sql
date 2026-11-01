CREATE DATABASE IF NOT EXISTS healthcare_claims_analytics;
USE healthcare_claims_analytics;

CREATE TABLE patients (
  PatientID VARCHAR(16) PRIMARY KEY,
  Age TINYINT UNSIGNED NOT NULL,
  Gender VARCHAR(30) NOT NULL,
  State CHAR(2) NOT NULL,
  Region VARCHAR(20) NOT NULL,
  InsuranceSegment VARCHAR(30) NOT NULL
);

CREATE TABLE hospitals (
  HospitalID VARCHAR(12) PRIMARY KEY,
  Hospital_Name VARCHAR(120) NOT NULL,
  Tier VARCHAR(10) NOT NULL,
  State CHAR(2) NOT NULL,
  Region VARCHAR(20) NOT NULL,
  BedCapacity SMALLINT UNSIGNED NOT NULL,
  TeachingHospital TINYINT NOT NULL,
  HospitalCostIndex DECIMAL(8,4) NOT NULL
);

CREATE TABLE claims (
  ClaimID VARCHAR(16) PRIMARY KEY,
  PatientID VARCHAR(16) NOT NULL,
  HospitalID VARCHAR(12) NOT NULL,
  AdmissionDate DATE NOT NULL,
  DischargeDate DATE NOT NULL,
  DiagnosisCode VARCHAR(12) NOT NULL,
  SecondaryDiagnosisCode VARCHAR(12) NULL,
  ProcedureCategory VARCHAR(40) NOT NULL,
  AdmissionType VARCHAR(20) NOT NULL,
  IsEmergency TINYINT NOT NULL,
  LengthOfStay SMALLINT UNSIGNED NOT NULL,
  HasComplications TINYINT NOT NULL,
  BilledAmount DECIMAL(14,2) NOT NULL,
  IsFraud TINYINT NOT NULL,
  CONSTRAINT fk_claim_patient FOREIGN KEY (PatientID) REFERENCES patients(PatientID),
  CONSTRAINT fk_claim_hospital FOREIGN KEY (HospitalID) REFERENCES hospitals(HospitalID),
  INDEX idx_claim_date (AdmissionDate),
  INDEX idx_claim_diag (DiagnosisCode),
  INDEX idx_claim_business_key (PatientID,HospitalID,AdmissionDate,DiagnosisCode)
);

CREATE TABLE claim_scores (
  ClaimID VARCHAR(16) PRIMARY KEY,
  RiskScore DECIMAL(10,8) NOT NULL,
  AnomalyScore DECIMAL(10,8) NOT NULL,
  RiskBand VARCHAR(16) NOT NULL,
  AnomalyReviewFlag TINYINT NOT NULL,
  PotentialBilledExposure_085 DECIMAL(14,2) NOT NULL,
  ScoringPartition VARCHAR(60) NOT NULL,
  CONSTRAINT fk_score_claim FOREIGN KEY (ClaimID) REFERENCES claims(ClaimID),
  INDEX idx_score_risk (RiskScore),
  INDEX idx_score_anomaly (AnomalyScore)
);
