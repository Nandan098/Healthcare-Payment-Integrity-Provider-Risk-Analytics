# Healthcare Payment Integrity & Claims Risk Analytics

## Project Overview

Healthcare claims contain clinical, provider, utilization, and financial information. Reviewing every claim manually can be time-consuming, so an analytics workflow can help identify unusual billing patterns and arrange claims in a practical order for further investigation.

This project combines **SQL-based payment analysis**, **supervised risk modelling**, **unsupervised anomaly detection**, and a **Power BI dashboard** to support healthcare payment-integrity review.

The objective is to identify claims that may deserve closer attention—not to automatically determine that a provider or claim is fraudulent.

## Problem Statement

The project addresses four connected business questions:

1. **Where is the money going?** Understand billed amounts, allowed amounts, and payments across providers, procedures, diagnoses, and service categories.
2. **Which claims look higher risk?** Use a supervised model to estimate a claim-level risk score based on the target label available in the modelling dataset.
3. **Which claims look unusual?** Use an unsupervised model to identify claims with unusual combinations of billing, utilization, or service characteristics, without requiring a target label.
4. **What should an analyst review first?** Bring the model outputs and financial context together to rank claims for investigation and present the results in Power BI.

## Project Workflow

```text
Claims and provider-service data
            |
            v
Data validation and preparation
            |
            v
Feature engineering and SQL analysis
            |
            +-------------------------------+
            |                               |
            v                               v
Random Forest classifier             Isolation Forest
(supervised risk score)              (unsupervised anomaly score)
            |                               |
            +---------------+---------------+
                            |
                            v
              Claim-level review prioritisation
                            |
                            v
                 SQL ranking and investigation queue
                            |
                            v
                    Power BI dashboard
```

## Data Used

The analysis uses structured healthcare claim / provider-service records. The fields are organised around the following business dimensions:

| Data dimension | Example field types | How the data is used |
|---|---|---|
| Claim and record identifiers | Claim ID, line ID, patient/member ID | Record linkage, deduplication, grouping, and traceability; identifiers are not automatically treated as predictive features. |
| Provider information | Provider ID/NPI, provider type or specialty | Provider-level summaries and peer comparisons. |
| Patient / beneficiary information | Age band or beneficiary attributes, where available | Utilization and claim-context analysis. |
| Clinical and service information | Diagnosis code, procedure/HCPCS code, place of service, service date | Procedure-level and service-level comparisons. |
| Utilization information | Service units, number of services, beneficiary count | Frequency and intensity analysis. |
| Financial information | Billed/submitted charge, allowed amount, paid amount or Medicare payment | Cost analysis, payment gaps, ratios, and outlier detection. |
| Time information | Claim/service date, year, month | Trend analysis and time-based aggregation. |

> **Schema note:** The table above describes the types of fields used in this kind of workflow. Exact source-column names vary by extract. Use the names in the repository's data dictionary / loading scripts when reproducing the analysis. IDs and post-outcome fields should be excluded from model inputs where they could cause leakage.

## Data Preparation

The preparation workflow includes:

- Inspecting column types, null counts, duplicates, and basic value distributions.
- Validating numeric amounts and utilization fields for invalid or inconsistent values.
- Standardising categorical values and date formats where needed.
- Checking the grain of the data (for example, claim-level versus claim-line or provider-service-level) before aggregating.
- Separating identifiers and target/outcome columns from the predictive feature matrix.
- Splitting data by patient/member where appropriate, so records belonging to the same person do not appear in both training and holdout sets.
- Fitting imputers, encoders, and other preprocessing steps using training data only, then applying the fitted transformations to validation/holdout data.

## Feature Engineering

Feature engineering translates raw claim fields into measures that help describe billing intensity, utilization, and financial variation. Depending on the columns available in the source extract, the workflow can include:

| Engineered feature | Illustrative calculation | Business interpretation |
|---|---|---|
| Payment gap | Billed amount − paid amount | Difference between the amount submitted and the amount paid. Interpret alongside allowed amount and payment rules. |
| Billed-to-allowed ratio | Billed amount / allowed amount | Shows how submitted charges compare with the allowed amount. Guard against zero or missing denominators. |
| Paid-to-allowed ratio | Paid amount / allowed amount | Describes the proportion of the allowed amount that was paid. |
| Cost per service unit | Billed or paid amount / service units | Helps compare unit-level cost patterns when service units are comparable. |
| Provider / procedure benchmarks | Claim metric compared with a peer-group median or distribution | Highlights deviations relative to comparable providers or services. |
| Time features | Year, month, or service-period indicators derived from date | Supports trend and seasonality analysis. |
| Utilization summaries | Service counts or beneficiary/service ratios | Helps identify unusually high service volume or intensity. |

Peer benchmarks and aggregate features should be calculated from the appropriate training/reference population when they are used as model inputs. Avoid using future information or target-derived values that would not have been available at prediction time.

## SQL Analysis

SQL is used to aggregate claim and payment information, compare providers and procedures, and produce investigation-oriented summaries. The examples below use illustrative table and column names; adjust them to match the actual database schema.

### 1. Total claim volume and financial amounts

```sql
SELECT
    COUNT(DISTINCT claim_id) AS total_claims,
    SUM(billed_amount) AS total_billed_amount,
    SUM(allowed_amount) AS total_allowed_amount,
    SUM(paid_amount) AS total_paid_amount
FROM healthcare_claims;
```

### 2. Provider-level billing summary

```sql
SELECT
    provider_id,
    COUNT(DISTINCT claim_id) AS claim_count,
    SUM(billed_amount) AS total_billed,
    SUM(paid_amount) AS total_paid,
    AVG(billed_amount) AS avg_billed_per_record
FROM healthcare_claims
GROUP BY provider_id
HAVING COUNT(DISTINCT claim_id) >= 10
ORDER BY total_billed DESC;
```

### 3. Procedure-level financial comparison

```sql
SELECT
    procedure_code,
    COUNT(*) AS record_count,
    AVG(billed_amount) AS avg_billed_amount,
    AVG(allowed_amount) AS avg_allowed_amount,
    AVG(paid_amount) AS avg_paid_amount
FROM healthcare_claims
GROUP BY procedure_code
ORDER BY avg_billed_amount DESC;
```

### 4. Monthly payment trend

```sql
SELECT
    YEAR(service_date) AS service_year,
    MONTH(service_date) AS service_month,
    SUM(billed_amount) AS billed_amount,
    SUM(allowed_amount) AS allowed_amount,
    SUM(paid_amount) AS paid_amount
FROM healthcare_claims
GROUP BY YEAR(service_date), MONTH(service_date)
ORDER BY service_year, service_month;
```

### 5. Rank claims for review using model outputs

```sql
SELECT
    claim_id,
    provider_id,
    billed_amount,
    risk_score,
    anomaly_score,
    ROW_NUMBER() OVER (
        ORDER BY
            risk_score DESC,
            anomaly_score DESC,
            billed_amount DESC
    ) AS review_priority
FROM claim_model_outputs
ORDER BY review_priority;
```

The ranking uses the supervised risk score as the primary sort, the anomaly score as a secondary sort, and billed amount as a tertiary sort. This creates a review queue; it is **not** a calibrated combined probability or a fraud verdict.

## Machine Learning

### 1. Random Forest — Supervised Risk Classification

Random Forest is an ensemble model that trains multiple decision trees and combines their predictions. In this project, it is used as a supervised model to estimate claim risk from the available labelled training examples.

**Input features** are selected from the claim, provider, service, utilization, and financial fields that are available at the time the risk assessment is made. Identifier columns and target/outcome columns are excluded from the predictor set.

**Output:** a claim-level risk score / predicted probability for prioritising review. The score indicates model-estimated risk relative to the training target; it does not establish fraud.

### 2. Isolation Forest — Unsupervised Anomaly Detection

Isolation Forest is an unsupervised algorithm that isolates observations using randomly selected features and split points. Records that can be isolated with shorter paths are generally considered more unusual than the majority of records.

It is used as a complementary detector to surface unusual billing or utilization patterns without requiring labelled fraud examples.

**Output:** an anomaly score or anomaly flag. The exact direction of the score depends on the scoring function and transformation used in the implementation; interpret the stored output according to the project's scoring code.

### Why use both models?

| Model | Learning type | What it contributes | Main limitation |
|---|---|---|---|
| Random Forest | Supervised | Learns patterns associated with the available risk label and produces a risk score. | Depends on the quality and representativeness of the labelled examples. |
| Isolation Forest | Unsupervised | Finds unusual records that may not resemble the labelled examples. | An unusual claim is not necessarily an incorrect or fraudulent claim. |

Using both provides two complementary views: **known risk patterns** and **unusual behaviour**.

## Claim Prioritisation and Review Decision

The model outputs are used to arrange claims for human review. The implemented SQL ordering is:

1. **Risk score — descending:** claims with higher supervised risk scores appear first.
2. **Anomaly score — descending:** among claims with similar risk priority, more unusual records are moved higher, assuming the stored anomaly score is oriented so that higher means more anomalous.
3. **Billed amount — descending:** the larger billed amount is used as the final tie-breaker.

In SQL, this is represented as:

```sql
ORDER BY risk_score DESC,
         anomaly_score DESC,
         billed_amount DESC
```

This is a **lexicographic ranking / tie-break approach**, not a weighted fusion of the two model scores. The anomaly score is a secondary ranking signal, not an independent final decision. Analysts should review supporting claim details, applicable payment rules, documentation, and provider context before reaching a conclusion.

## Model Evaluation

For the supervised classifier, useful evaluation measures include:

- **ROC-AUC:** measures ranking/discrimination across classification thresholds.
- **PR-AUC:** particularly informative when the risk-positive class is uncommon.
- **Precision:** proportion of flagged claims that belong to the positive class.
- **Recall:** proportion of positive claims captured by the model.
- **F1-score:** harmonic mean of precision and recall at a selected threshold.

Accuracy should not be interpreted alone when the classes are imbalanced. Thresholds should be selected using validation data based on the operational balance between false positives and missed high-risk claims.

Isolation Forest is evaluated differently because it does not train on a class label. Its outputs are reviewed through anomaly-score distributions, flagged-record investigation, and comparison with relevant billing/utilization context. Do not report classifier metrics such as ROC-AUC for Isolation Forest unless a suitable labelled evaluation set is available and the evaluation is explicitly performed.

## Power BI Dashboard

A three-page Power BI report presents the analysis in a business-friendly format:

### Page 1 — Payment Integrity Overview

- Claim / record volume.
- Total billed, allowed, and paid amounts.
- Payment trends over time.
- High-level risk indicators.

### Page 2 — Provider and Service Analysis

- Provider-level utilization and payment comparisons.
- Diagnosis / procedure-level financial patterns.
- Service-category trends and peer comparisons.
- Views of unusual billing or utilization patterns.

### Page 3 — Risk and Investigation Prioritisation

- Risk-score distribution and high-risk claim counts.
- Anomaly flags / anomaly-score distribution.
- Prioritised claim table with provider, service, financial, risk, and anomaly context.
- Filters to help analysts focus on providers, procedures, dates, and claim segments.

The dashboard is intended to support exploration and investigation prioritisation, not to automatically adjudicate claims.

## Technology Stack

- **Python:** data preparation, feature engineering, and modelling.
- **Pandas / NumPy:** data manipulation and numerical analysis.
- **Scikit-learn:** Random Forest and Isolation Forest workflows, where implemented.
- **SQL / MySQL:** aggregations, provider and procedure analysis, and claim prioritisation.
- **Power BI:** interactive reporting and dashboard development.

## Limitations and Responsible Use

- A high risk score or anomaly score is a signal for review, not proof of fraud, abuse, or error.
- Model quality depends on data quality, label quality, and whether the evaluation split represents future use.
- Provider, procedure, and service comparisons must account for differences in case mix and legitimate clinical variation.
- Identifiers should be retained for joining and traceability but excluded from model predictors unless there is a justified, validated reason.
- Financial ratios require careful handling of zero, null, and very small denominators.
- Human review and applicable policy / clinical context remain necessary before payment or compliance decisions.

## Repository Structure

The exact folder names may vary, but a typical layout is:

```text
healthcare-claims-payment-integrity/
├── data/
│   ├── raw/                 # Source extracts (not committed if restricted)
│   └── processed/           # Validated and feature-engineered data
├── notebooks/               # EDA and modelling experiments
├── sql/                     # Analysis and prioritisation queries
├── src/                     # Reusable preparation and modelling code
├── reports/                 # Evaluation outputs and exported summaries
├── powerbi/                 # Power BI report file / screenshots
└── README.md
```


This project brings together SQL, supervised learning, unsupervised anomaly detection, and business intelligence to help payment-integrity teams **understand claim patterns, surface unusual records, and prioritise human investigation more effectively**.
