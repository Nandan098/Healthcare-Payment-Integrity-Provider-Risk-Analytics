# Download package notes

This smaller package contains the complete source project, all three raw CSV datasets (500,000 claims, 150,000 patients, 600 fictional hospitals), trained model files, the compact 500,000-row claim_scores.csv table, SQL queries/results, reports, Power BI guide/DAX, and tests.

To reduce download size, two large convenience artifacts are kept in optional companion downloads rather than this core ZIP:
- `outputs/claims_scored.csv` (wide all-claims scoring export)
- `data/processed/healthcare_claims_500k.db` (prebuilt SQLite database)

The project source can regenerate both. `python -m src.train_models` regenerates scored model outputs, and `python -m src.build_database` rebuilds the SQLite database from raw CSVs and `outputs/claim_scores.csv`.

Run the complete pipeline using `python -m src.run_all` after installing `requirements.txt`.

Data provenance: all generated claim, patient, hospital, and model-label records are synthetic realistic-style portfolio data, not real patient, provider, insurer, or investigation records. The generated target is not verified fraud ground truth. No guarantee of zero bias or real-world representativeness is made.
