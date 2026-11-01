# Business Insights (Generated Dataset)

> All numbers in this report describe generated records only. They are not observations from an insurer, hospital, payer, or fraud investigation.

## Portfolio snapshot
- Claims: **500,000** across **124,329** referenced patients and **600** hospitals.
- Total billed amount: **$28,686,909,594.97**; average claim: **$57,373.82**; median claim: **$31,580.00**.
- Billing is right-skewed: 95th percentile **$195,869.45**, 99th percentile **$380,614.81**.
- Generated positive scenario labels: **11,555 (2.31%)**. This is an assumption of the generator, not a real fraud rate.

## Exploratory patterns
- Diagnosis **C18.9** has the largest total billed amount in this generated sample (**$3,250,026,489.12**, 11.3% of spend).
- **Tier 1** has the highest average billed amount per claim (**$82,366.93**). Hospital tier and regional price factors are explicit generator inputs, so this is not an independent empirical finding.
- Duplicate business-key groups: **2,003**. These groups are deliberately present for SQL review exercises.
- Claim volumes and billed amounts vary across months, diagnoses, regions, and hospitals; categories were not equally weighted.

## Model outputs
- LightGBM ROC-AUC: **0.844**; average precision / PR-AUC: **0.540** on patient-grouped holdout data.
- At a 0.85 score cutoff, holdout precision was **0.990** and recall **0.356** across 821 flagged claims.
- Isolation Forest anomaly score is a percentile-rank measure of unusualness, **not a fraud probability**.

## Business interpretation
Use scores to prioritize manual review, compare charge patterns, and identify billing records needing context. Do not auto-deny a claim or accuse a provider/patient based only on a model score. Validate against adjudicated outcomes and policy rules before production use.
