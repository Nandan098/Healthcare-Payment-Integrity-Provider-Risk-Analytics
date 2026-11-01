# Data Governance, Bias and Limitations

## Provenance and privacy

All records are generated from code. They are not sourced from patient records, provider systems, insurers, public claims extracts or an actual investigation. Patient and hospital IDs are fictional. No names, addresses, member numbers or direct personal identifiers are present. Hospital names visibly include “Synthetic”.

## Bias / representativeness

The dataset is not equally weighted. Age, gender, region, insurance segment, diagnosis, facility tier, facility size, claim frequency, utilization, dates and charges have intentionally unequal distributions and some modeled dependencies. This is intended to avoid a simplistic balanced classroom dataset.

That does **not** mean the data are unbiased. The distributions and relationships reflect the generator author's assumptions. The age mix is Medicare-oriented; regional and facility cost differences are assumptions; generated positive-label probability is not empirically calibrated. A model trained on these rows can inherit those assumptions. Group diagnostics are included in `outputs/subgroup_model_diagnostics.csv` as a basic screening view only. They do not establish fairness, legal compliance or absence of disparate impact.

## Modeling limitations

- `IsFraud` is a simulated target, not an adjudicated label.
- The supervised model may learn injected scenario patterns. Its metrics do not establish generalization to real claims.
- There is one patient-grouped holdout split, not prospective / temporal external validation.
- The score export has in-sample scores for training-population rows. The holdout file is separate and should be used for evaluation claims.
- Isolation Forest measures unusualness, not wrongdoing.
- The score threshold is configurable. A claim should be reviewed with claim policy, coding, clinical and contract context; a score is not a denial reason.
- PotentialBilledExposure is gross billed amount flagged, not actual recoverable savings.
- The project does not implement a full FWA (fraud, waste and abuse) rule library, clinical validation, network adjudication, provider attribution or production controls.

## Production requirements not covered

Real-world use would require authorized de-identified data, privacy and security review, adjudicated outcomes, domain-expert validation, prospective validation, subgroup impact review, monitoring, score calibration, explainability, audit logs, human review processes and legal / compliance approval.
