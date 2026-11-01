# Model Evaluation

## Supervised classification
- Model: LightGBM binary classifier.
- Dataset: 500,000 claims; patient-group split of 400,194 training rows and 99,806 holdout rows.
- Generated positive share: 2.32% in training and 2.29% in holdout.
- ROC-AUC: 0.8437.
- Average precision / PR-AUC: 0.5396.
- At threshold 0.50: precision 0.5855, recall 0.4928, F1 0.5352, accuracy 0.9804.
- At threshold 0.85: precision 0.9903, recall 0.3558, flagged 821.

## Unsupervised anomaly detection
Isolation Forest is trained without the IsFraud target. `AnomalyScore` is the percentile rank of negative Isolation Forest decision scores across this dataset. It indicates relative unusualness and must not be described as a fraud probability.

## Scoring partition caveat
`outputs/claims_scored.csv` contains full-population scores from the model trained on the 80% training partition. Rows marked `Training population score (in-sample)` were used to fit the model and their scores are optimistic / not independent evaluation results. Rows marked `Held-out test score` are the untouched patient-grouped holdout predictions. Use `holdout_scored.csv` for reported evaluation.

## Limitations
The target is synthetic and scenario-created. These metrics show that the model learns generator-created patterns, not how it will perform on actual claims. The subgroup diagnostics are exploratory and are not a fairness certification. Production deployment would require real adjudicated outcomes, temporal validation, leakage review, calibration, threshold governance, privacy controls, and human review.
