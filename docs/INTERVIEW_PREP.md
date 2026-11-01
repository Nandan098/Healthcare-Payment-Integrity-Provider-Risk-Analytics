# Interview Explanation — 500K Healthcare Claims Project

## 60–90 second project explanation

“I built an end-to-end healthcare payment-integrity analytics project around 500,000 claim records, with linked patient and hospital dimensions. The data is a realistic-style synthetic simulation with uneven distributions across diagnoses, hospital tiers, regions, utilization and billed amounts, so it supports realistic SQL and dashboard exercises without using private patient records.

I used Python and Pandas for data generation, validation and feature engineering, and SQL to answer 40 business questions around claim trends, diagnosis-level billing, hospital utilization, duplicate claim patterns and financial exposure. For modeling, I used a patient-grouped holdout split to avoid claims from the same patient appearing in both training and test. I trained a LightGBM classifier to estimate the generated positive-scenario risk and used Isolation Forest separately to identify unusual billing patterns.

The holdout ROC-AUC was about 0.844 and PR-AUC about 0.540. I exported risk scores and anomaly scores separately and designed a Power BI dashboard for executive overview, risk investigation, hospital / diagnosis analysis, and trends. The scores are review indicators, not confirmed fraud decisions, and all model performance is measured against generated labels.”

## Why use LightGBM and Isolation Forest?

- LightGBM is supervised: it learns patterns associated with the generated positive target and returns a RiskScore.
- Isolation Forest is unsupervised: it learns unusualness from selected billing and utilization features without reading the IsFraud target.
- They answer different questions. A claim can be highly unusual but have a moderate supervised score, or vice versa. Keep separate queues / visuals rather than treating either as a verdict.

## Why patient-grouped splitting?

Claims from one patient can share billing and utilization patterns. If the same patient appeared in both train and test, the metrics could look better than true generalization. GroupShuffleSplit keeps a patient's records on one side of the split. Benchmarks such as diagnosis-level medians are derived from the training groups only.

## What is the business output?

A prioritized list for a human reviewer, supporting context such as diagnosis benchmark ratios, repeat-utilization and duplicate-key counts, anomaly score, risk score, billed amount, hospital and date. `PotentialBilledExposure_085` is the billed value associated with claims above the selected score threshold. It is not actual savings or guaranteed recovery.

## How do you address bias?

“The dataset is deliberately non-uniform rather than equally distributed, but I would not call it bias-free. It is generated from explicit assumptions, including an age mix, regional weights, facility tiers and label-generation rules. I included subgroup diagnostics to inspect positive rates, predicted-positive rates, recall and false-positive rates by gender, age band, region and hospital tier. Before any real deployment, I would need authorized adjudicated data, domain review, temporal validation and a formal fairness / impact assessment.”

## Limitations to acknowledge

1. Data and labels are synthetic; model performance does not establish real-world fraud detection.
2. The score export includes in-sample scores for training rows; use the holdout file for performance claims.
3. Isolation Forest scores are relative unusualness, not probabilities.
4. A high score cannot automatically deny a claim; human review and claim policy context are required.
5. A single grouped split is not a substitute for temporal external validation.
