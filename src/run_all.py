from pathlib import Path
from .generate_dataset import generate
from .validate_data import run as validate
from .train_models import fit_and_score
from .build_database import build
from .run_sql_analysis import main as run_sql
from .create_reports import main as create_reports

ROOT=Path(__file__).resolve().parents[1]

def main():
    generate(ROOT,claims_n=500_000,patients_n=150_000,hospitals_n=600)
    validate(ROOT)
    fit_and_score(ROOT)
    build(ROOT)
    run_sql(ROOT)
    create_reports(ROOT)
    print('Complete. Review README.md, reports/, outputs/, and powerbi/.')

if __name__=='__main__':
    main()
