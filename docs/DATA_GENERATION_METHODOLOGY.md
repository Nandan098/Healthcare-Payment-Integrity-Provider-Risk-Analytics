# Data Generation Methodology

## Purpose

Create a repeatable claims analytics dataset with operational-style relationships and non-uniform distributions for SQL, ML and Power BI practice. It is a simulation, not a substitute for real claims data.

## Non-uniform data design

- 150K patient-like records with a Medicare-heavy age mix (a mix of ages 18–95), a gender mix that is not exactly 50/50, and uneven region / insurance-segment proportions.
- 600 fictional hospitals across 4 U.S.-style regions and multiple states. Facility tiers are intentionally skewed (roughly 13% Tier 1, 34% Tier 2, 53% Tier 3); bed capacity and hospital selection are long-tailed.
- 16 diagnosis-code categories with unequal probabilities. Diagnosis influences typical severity, length of stay and base charge.
- Patient claim frequency follows a long-tailed sampling distribution rather than equal claims per patient.
- Monthly claim generation has a trend and seasonal variation. Hospital region, tier, state-cost index and capacity affect facility selection / billing.
- Length of stay is generated from diagnosis-specific distributions with age and admission-type effects. BilledAmount has multiplicative cost factors and log-normal noise, producing a right-skewed distribution and legitimate high-cost tail cases.

## Scenario label generation

`IsFraud` represents a generated positive review scenario. Positive rows are introduced through a mix of:

1. Duplicate billing copies with the same patient, hospital, admission date and diagnosis, but a new ClaimID.
2. Short-gap repeated patient / hospital / diagnosis episodes with nearby dates.
3. Selected overbilling multipliers of varied sizes on existing claims.
4. A small background positive-label component to avoid making labels a perfect one-rule mapping.

The generated label rate in the provided seed is **2.311%**. This is a design parameter and not a real-world incidence rate. Some legitimate high-cost claims are unlabeled; generated positives may overlap on more than one pattern.

## Random seed and date boundaries

- Seed: `20261030`.
- Core base claim dates: 2023-01-01 through 2025-12-31.
- Short-gap repeat-copy records can extend to 2026-01-12 in the provided run.

## What “realistic” does and does not mean

The generator creates skew, dependencies, repeat utilization, facility variation, missing optional secondary diagnoses, and a small number of review scenarios. It does not reproduce all coding, contracting, reimbursement, adjudication, policy, geography, provider behavior or population dynamics of a real payer. All entities and outcomes are fictitious.
