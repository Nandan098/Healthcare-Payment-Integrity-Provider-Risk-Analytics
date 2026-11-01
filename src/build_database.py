from pathlib import Path
import sqlite3, pandas as pd

def build(root: Path):
    db=root/'data'/'processed'/'healthcare_claims_500k.db'
    db.parent.mkdir(parents=True,exist_ok=True)
    if db.exists(): db.unlink()
    con=sqlite3.connect(db)
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('PRAGMA temp_store=MEMORY')
    con.executescript('''
    CREATE TABLE patients (
      PatientID TEXT PRIMARY KEY, Age INTEGER NOT NULL, Gender TEXT NOT NULL,
      State TEXT NOT NULL, Region TEXT NOT NULL, InsuranceSegment TEXT NOT NULL
    );
    CREATE TABLE hospitals (
      HospitalID TEXT PRIMARY KEY, Hospital_Name TEXT NOT NULL, Tier TEXT NOT NULL,
      State TEXT NOT NULL, Region TEXT NOT NULL, BedCapacity INTEGER NOT NULL,
      TeachingHospital INTEGER NOT NULL, HospitalCostIndex REAL NOT NULL
    );
    CREATE TABLE claims (
      ClaimID TEXT PRIMARY KEY, PatientID TEXT NOT NULL, HospitalID TEXT NOT NULL,
      AdmissionDate TEXT NOT NULL, DiagnosisCode TEXT NOT NULL, ProcedureCategory TEXT NOT NULL,
      AdmissionType TEXT NOT NULL, IsEmergency INTEGER NOT NULL, LengthOfStay INTEGER NOT NULL,
      HasComplications INTEGER NOT NULL, BilledAmount REAL NOT NULL, IsFraud INTEGER NOT NULL,
      DischargeDate TEXT NOT NULL, SecondaryDiagnosisCode TEXT,
      FOREIGN KEY(PatientID) REFERENCES patients(PatientID),
      FOREIGN KEY(HospitalID) REFERENCES hospitals(HospitalID)
    );
    CREATE TABLE claim_scores (
      ClaimID TEXT PRIMARY KEY, RiskScore REAL NOT NULL, AnomalyScore REAL NOT NULL,
      RiskBand TEXT NOT NULL, AnomalyReviewFlag INTEGER NOT NULL,
      PotentialBilledExposure_085 REAL NOT NULL, ScoringPartition TEXT NOT NULL,
      FOREIGN KEY(ClaimID) REFERENCES claims(ClaimID)
    );
    ''')
    # Load parent dimensions before their fact / score children.
    files=[('patients','data/raw/patients.csv'),('hospitals','data/raw/hospitals.csv'),('claims','data/raw/claims.csv')]
    for table,rel in files:
        for chunk in pd.read_csv(root/rel,chunksize=25000):
            chunk.to_sql(table,con,if_exists='append',index=False,method=None,chunksize=5000)
    score_path=root/'outputs'/'claim_scores.csv'
    for chunk in pd.read_csv(score_path,chunksize=25000):
        chunk.to_sql('claim_scores',con,if_exists='append',index=False,method=None,chunksize=5000)
    indexes=[
      'CREATE INDEX idx_claims_patient ON claims(PatientID)',
      'CREATE INDEX idx_claims_hospital ON claims(HospitalID)',
      'CREATE INDEX idx_claims_date ON claims(AdmissionDate)',
      'CREATE INDEX idx_claims_diag ON claims(DiagnosisCode)',
      'CREATE INDEX idx_scores_risk ON claim_scores(RiskScore)',
      'CREATE INDEX idx_scores_anomaly ON claim_scores(AnomalyScore)',
      'CREATE INDEX idx_claims_business_key ON claims(PatientID,HospitalID,AdmissionDate,DiagnosisCode)',
    ]
    for sql in indexes: con.execute(sql)
    con.commit()
    counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['patients','hospitals','claims','claim_scores']}
    fk_errors=con.execute('PRAGMA foreign_key_check').fetchall()
    integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
    con.close()
    if fk_errors or integrity!='ok':
        raise RuntimeError(f'Database integrity error: fk={fk_errors[:5]}, integrity={integrity}')
    print('Created',db,'rows',counts,'size_mb',round(db.stat().st_size/1024/1024,2),'integrity',integrity,'FK errors',len(fk_errors))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();build(a.root)
