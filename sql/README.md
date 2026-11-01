# SQL guide

The delivered database is `data/processed/healthcare_claims_500k.db`. It was built from the raw CSV files and includes `patients`, `hospitals`, `claims`, and `claim_scores`.

- 40 SQLite queries are in `sql/queries/`.
- A query inventory is in `sql/query_catalog.csv`.
- Results and readable explanations are in `reports/sql_results/` and `reports/SQL_Questions_and_Answers.md`.
- Run `python -m src.build_database` to rebuild the SQLite database after changing raw data / model scores.
- Run `python -m src.run_sql_analysis` to execute the query bank again.

An optional MySQL 8 compatible table definition is in `sql/mysql/01_schema.sql`. The included MySQL schema is reference material only; the 40 query scripts were executed and verified in SQLite, not in MySQL.
