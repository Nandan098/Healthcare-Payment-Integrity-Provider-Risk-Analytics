# Power BI Build Guide — Healthcare Claims Risk & Payment Integrity

## Recommended data model

Load the four CSVs from the project:

- `data/raw/patients.csv` → table name **Patients**
- `data/raw/hospitals.csv` → table name **Hospitals**
- `data/raw/claims.csv` → table name **Claims**
- `outputs/claim_scores.csv` → table name **ClaimScores**

Create these relationships in Model view:

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| Patients[PatientID] | Claims[PatientID] | 1 to many | Single |
| Hospitals[HospitalID] | Claims[HospitalID] | 1 to many | Single |
| Claims[ClaimID] | ClaimScores[ClaimID] | 1 to 1 | Single (Claims filters ClaimScores) |

`ClaimScores` contains one score row per claim. Check uniqueness of `ClaimScores[ClaimID]` and the one-to-one relationship after import. Do not create a many-to-many relationship.

The all-in-one convenience file `outputs/claims_scored.csv` already combines claim, dimension and score fields. It can be loaded as a single table for a quick demo, but do not load it alongside all four relational CSVs unless you intentionally manage duplicated columns and relationships.

## Page 1 — Executive Overview

**Cards:** Total Claims, Total Billed Amount, Average Claim Amount, Unique Patients, Hospitals, Generated Positive Label Rows.

**Charts:**
- Monthly claim volume and billed amount: `AdmissionDate` by month.
- Claims by hospital tier: `Hospitals[Tier]`.
- Spend by region: `Hospitals[Region]`.
- Top diagnosis by billed amount: `Claims[DiagnosisCode]` and `Claims[BilledAmount]`.
- Billed amount distribution: histogram / bins on `Claims[BilledAmount]`.

**Slicers:** AdmissionDate, DiagnosisCode, Hospital tier, Hospital state, patient region, admission type.

## Page 2 — Fraud Risk & Anomaly Analysis

Use **Claims + ClaimScores + Hospitals**.

**KPI cards:** Total Claims; High-Risk Claims (RiskScore ≥ 0.85); Average Risk Score; High-Risk Billed Exposure; Top-2%-Anomaly Claims.

**Visuals:**
1. Risk score distribution — clustered column chart; X = `ClaimScores[RiskScore]` bins (0.10 or 0.20 size), Y = count of ClaimScores[ClaimID].
2. Anomaly score distribution — clustered column chart; X = `ClaimScores[AnomalyScore]` bins, Y = count of ClaimScores[ClaimID].
3. Risk band mix — donut or bar; axis/legend = `ClaimScores[RiskBand]`, values = claim count.
4. Top 10 high-risk claims — table: ClaimID, Hospital_Name, DiagnosisCode, AdmissionDate, BilledAmount, RiskScore, AnomalyScore. Visual filter: Top N = 10 by RiskScore, descending.
5. Top 10 anomalous claims — table with same fields, Top N = 10 by AnomalyScore.
6. Risk score vs billed amount — scatter chart: X = BilledAmount, Y = RiskScore, Size = BilledAmount, Details = ClaimID, Legend = RiskBand.
7. High risk vs high anomaly — scatter chart or matrix to distinguish model signals. Do not combine scores into a single “fraud probability”.

**Slicers:** AdmissionDate, hospital tier, hospital state, diagnosis code, patient region, RiskBand.

**Review interpretation:** RiskScore estimates generated positive-label likelihood. AnomalyScore is relative unusualness from Isolation Forest and is not a fraud probability. A high anomaly / low risk claim can still warrant review; it is not proof of fraud.

## Page 3 — Hospital & Diagnosis Analysis

**Visuals:** spend by hospital tier; top 20 hospitals by billed amount; average billed amount by tier; diagnosis-wise billed amount vs diagnosis median; hospital–diagnosis average billing matrix; claims by hospital state; cost per day by hospital.

Use Claims[BilledAmount], Claims[LengthOfStay], Claims[DiagnosisCode], Hospitals[Hospital_Name], Hospitals[Tier], Hospitals[State], Hospitals[Region]. Use median comparisons carefully: dashboard-wide medians are descriptive; the model's benchmark fields were calculated from training data.

## Page 4 — Claims Trends & Financial Exposure

**Visuals:** monthly / quarterly claim volume; monthly billed amount; billed amount by age band; LOS distribution; repeat utilization within 30 days; duplicate business-key groups; high-risk billed exposure by month / tier / diagnosis.

Use the optional summary extracts in `outputs/` for quick visual setup. For model evaluation, use `outputs/holdout_scored.csv`, not training-population scores.

## Power BI import steps

1. Home → Get Data → Text/CSV; select each of the four CSVs above.
2. In Power Query, set AdmissionDate and DischargeDate to Date; BilledAmount and model scores to Decimal Number; indicator columns to Whole Number; IDs and diagnosis codes to Text.
3. Rename each query exactly as Patients, Hospitals, Claims, ClaimScores.
4. Close & Apply, then create the relationships described above.
5. Create the DAX measures in `DAX_Measures.dax` (or copy them from that file into Modeling → New measure).
6. Add a Date table if you want time-intelligence comparisons. Mark it as a Date table and relate Date[Date] to Claims[AdmissionDate].
7. Format BilledAmount measures as USD. Use clear labels such as “Potential billed exposure” rather than “Savings”.

## Suggested styling

Use a light background, dark navy headings, muted blue for RiskScore, teal for AnomalyScore, and amber/red only for high-priority review indicators. Keep the two model signals visually separate. Show the synthetic-data notice in a small footer on each page.

**Footer text:** “Portfolio simulation using synthetic data. Model scores indicate review priority, not confirmed fraud.”
