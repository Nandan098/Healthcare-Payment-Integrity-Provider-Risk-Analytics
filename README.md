# Healthcare Claims Risk & Payment Integrity Analytics — 500K Claims

**Portfolio project for Business Analyst – Analytics / Decision Analytics roles.** This project demonstrates the end-to-end workflow: data generation and validation, relational modeling, SQL analysis, supervised risk scoring, unsupervised anomaly detection, and Power BI reporting.

> **Data provenance — read this first:** The included records are **synthetic, realistic-style generated data**. They are not real patient, hospital, insurer, provider, claims, or fraud-investigation records. The `IsFraud` field is a generated scenario label, not an adjudicated fraud outcome. Do not describe the data or model results as real-world findings. The distributions are intentionally uneven and designed with plausible relationships, but no synthetic dataset can be guaranteed bias-free or representative of an actual payer population.

## Project scale

| Table / artefact | Rows | Description |
|---|---:|---|
| `patients.csv` | 150,000 | Synthetic patient-like dimension; no names or real identifiers |
| `hospitals.csv` | 600 | Fictional hospitals across U.S.-style states and regions |
| `claims.csv` | 500,000 | Claim-level facts, dates, diagnoses, LOS, billing and generated target |
| `claim_scores.csv` | 500,000 | Risk score, anomaly score, risk band and exposure proxy |
| `claims_scored.csv` | 500,000 | Wide convenience export combining claim, dimension and score fields |

The base claim dates cover 2023–2025. Short-gap repeat scenarios can extend a small number of admission dates into January 2026. The generated positive label share is **2.311% (11,555/500,000)**. This is a generator setting, not a real fraud prevalence estimate.

## Business question

How could a payer analytics team prioritize claims for human review by combining charge benchmarks, repeated-use patterns, duplicate billing indicators, a supervised claim-risk score, an independent anomaly score, and SQL-based business reporting?

## Project workflow

1. Generate a 500K claim fact table and patient / hospital dimensions with skewed, non-uniform distributions.
2. Run 15 automated row-count, uniqueness, referential-integrity, date, amount, and distribution checks.
3. Engineer leakage-aware features and calculate peer benchmarks using training-patient data only.
4. Split train and holdout groups by `PatientID` to avoid placing a patient's claims in both partitions.
5. Train a LightGBM classifier and evaluate ROC-AUC, PR-AUC, precision, recall, F1 and threshold behavior.
6. Fit Isolation Forest without using the generated target; export anomaly percentile scores as a separate signal.
7. Build a SQLite database and execute 40 SQL business questions.
8. Export full-population scores, holdout predictions, business summaries, a review queue and Power BI guidance.

## Quick start

Python 3.10+ is recommended. On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.run_all
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.run_all
```

The included `data/raw/` and `outputs/` folders mean you can inspect the delivered project without running the full pipeline again. `python -m src.run_all` regenerates the fixed-seed dataset and reruns every stage.

## Main files

- `data/raw/claims.csv`, `patients.csv`, `hospitals.csv` — the raw dataset.
- `outputs/claims_scored.csv` — all 500K records with risk and anomaly scores; includes a scoring-partition label.
- `outputs/holdout_scored.csv` — untouched patient-group holdout predictions used for performance reporting.
- `outputs/claim_scores.csv` — compact Power BI score table keyed by `ClaimID`.
- `outputs/high_risk_review_queue_top_1000.csv` — top risk-ranked claims for investigation practice.
- `outputs/anomaly_review_queue_top_1000.csv` — top anomaly-ranked claims for a distinct review queue.
- `outputs/subgroup_model_diagnostics.csv` — exploratory holdout metrics by demographic / facility group; not a fairness certification.
- `data/processed/healthcare_claims_500k.db` — SQLite database containing four relational tables.
- `sql/queries/` and `reports/SQL_Questions_and_Answers.md` — 40 SQL questions, source queries and outputs.
- `models/` — fitted supervised and unsupervised model artefacts.
- `powerbi/` — data model, dashboard design and DAX measures.
- `docs/` — data dictionary, data-generation method, governance, limitations and interview notes.

## Model results (provided run)

The single patient-group split contains 400,194 training rows and 99,806 holdout rows. On the holdout set:

| Metric | Result |
|---|---:|
| ROC-AUC | 0.8437 |
| Average precision / PR-AUC | 0.5396 |
| Precision at 0.50 | 0.5855 |
| Recall at 0.50 | 0.4928 |
| F1 at 0.50 | 0.5352 |
| Precision at 0.85 | 0.9903 |
| Recall at 0.85 | 0.3558 |
| Claims flagged at 0.85 | 821 |

These figures measure how well the model recovered generator-created labels. They do **not** establish real-world fraud detection effectiveness.

## Important interpretation rules

- `RiskScore` is the LightGBM estimated probability of the **generated positive class**.
- `AnomalyScore` is a percentile rank of an Isolation Forest unusualness score. It is not a fraud probability and is not trained on `IsFraud`.
- `PotentialBilledExposure_085` is the full billed amount on claims above a configurable score cutoff. It is a gross billed-exposure proxy, not a confirmed saving, avoidable amount or recovery.
- `outputs/claims_scored.csv` contains scores from the model trained on the 80% training groups. Rows marked `Training population score (in-sample)` are in-sample predictions; they are for dashboard exploration, not independent model evaluation. Use `holdout_scored.csv` and `reports/Model_Evaluation.md` for reported model performance.
- Model scores should prioritize human review only. They must not be used to auto-deny claims or accuse a patient / provider.

## Suggested GitHub description

> End-to-end healthcare payment-integrity analytics portfolio project using a 500K-row realistic-style synthetic claims dataset, Python, SQL, LightGBM, Isolation Forest and Power BI reporting, with patient-grouped holdout evaluation and documented data-governance limitations.
