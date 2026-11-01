# Data Dictionary

All rows are generated and use fictional IDs / fictional hospital names. No direct patient identifiers are included.

## patients (150,000 rows)

| Field | Type | Definition |
|---|---|---|
| PatientID | String | Generated patient key (`P#######`) |
| Age | Integer | Generated age, 18–95 |
| Gender | Category | Female, Male, Other/Unknown; non-uniform proportions |
| State | String | U.S.-style two-letter state code |
| Region | Category | Northeast, Midwest, South, West |
| InsuranceSegment | Category | Medicare, Commercial, Medicaid, Dual Eligible |

## hospitals (600 rows)

| Field | Type | Definition |
|---|---|---|
| HospitalID | String | Generated hospital key |
| Hospital_Name | String | Fictional name containing “Synthetic Medical Center” |
| Tier | Category | Tier 1, Tier 2, Tier 3; 13% / 34% / 53% generator mix |
| State / Region | Category | Generated facility location |
| BedCapacity | Integer | Generated right-skewed capacity estimate |
| TeachingHospital | 0/1 | Generated teaching-facility flag |
| HospitalCostIndex | Decimal | Generated tier/state price multiplier |

## claims (500,000 rows)

| Field | Type | Definition |
|---|---|---|
| ClaimID | String | Unique generated claim key |
| PatientID | String | Foreign key to patients |
| HospitalID | String | Foreign key to hospitals |
| AdmissionDate | Date | Generated admission date |
| DischargeDate | Date | AdmissionDate plus LengthOfStay |
| DiagnosisCode | String | Generated ICD-10-style code from the configured code mix |
| SecondaryDiagnosisCode | String / blank | Optional generated secondary code |
| ProcedureCategory | Category | Medical, imaging, surgery, cardiac, orthopedic, oncology, respiratory, dialysis |
| AdmissionType | Category | Emergency, Urgent, Elective |
| IsEmergency | 0/1 | Generated emergency indicator |
| LengthOfStay | Integer | Generated inpatient stay in days |
| HasComplications | 0/1 | Generated complication indicator |
| BilledAmount | Decimal USD | Simulated billed amount influenced by diagnosis, LOS, tier, location, age, urgency, complexity and random variation |
| IsFraud | 0/1 | Generated positive-scenario target; not a real fraud finding |

## claim_scores (500,000 rows)

| Field | Type | Definition |
|---|---|---|
| ClaimID | String | One-to-one link to a claim |
| RiskScore | Decimal 0–1 | LightGBM estimated probability for generated positive class |
| AnomalyScore | Decimal 0–1 | Dataset-relative percentile rank of Isolation Forest unusualness |
| RiskBand | Category | Low, Moderate, Elevated, High using project cutoffs |
| AnomalyReviewFlag | 0/1 | Top 2% by AnomalyScore in this generated dataset |
| PotentialBilledExposure_085 | Decimal USD | Billed amount when RiskScore ≥ 0.85, otherwise zero |
| ScoringPartition | Category | Training population score (in-sample) vs held-out test score |

## Main derived modeling features

`CostPerDay`, `DiagnosisMedianBill`, `BilledVsDiagnosisMedian`, `HospitalDiagnosisMedianBill`, `BilledVsHospitalDiagnosisMedian`, `PriorPatientClaims`, `DuplicateBusinessKeyCount`, `RepeatUse30dFlag`, `AdmissionMonth`, `AdmissionYear`, `AdmissionDayOfWeek`.

Diagnosis and hospital-diagnosis medians used by the model are estimated from the training patient groups only. These columns in the dashboard export are explanatory derived fields based on that training reference.
