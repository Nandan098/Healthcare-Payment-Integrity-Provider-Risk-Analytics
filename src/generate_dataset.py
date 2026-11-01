from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20261030
REGIONS = {
    "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
    "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South": ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}
REGION_NAMES = np.array(list(REGIONS.keys()))
REGION_P = np.array([0.18, 0.21, 0.39, 0.22])
STATE_COST = {
    "CT":1.15,"ME":0.97,"MA":1.17,"NH":1.02,"RI":1.06,"VT":1.00,"NJ":1.18,"NY":1.16,"PA":1.04,
    "IL":1.04,"IN":0.94,"MI":1.00,"OH":0.96,"WI":1.00,"IA":0.93,"KS":0.95,"MN":1.08,"MO":0.95,"NE":0.94,"ND":0.97,"SD":0.96,
    "DE":1.00,"FL":0.98,"GA":0.96,"MD":1.08,"NC":0.96,"SC":0.92,"VA":1.04,"WV":0.91,"AL":0.90,"KY":0.93,"MS":0.88,"TN":0.94,"AR":0.89,"LA":0.94,"OK":0.91,"TX":1.00,
    "AZ":1.00,"CO":1.08,"ID":0.95,"MT":0.96,"NV":1.02,"NM":0.91,"UT":1.00,"WY":0.97,"AK":1.10,"CA":1.22,"HI":1.18,"OR":1.05,"WA":1.13,
}
DIAG = ["J18.9", "I50.9", "E11.9", "N17.9", "S72.001A", "I21.4", "J44.1", "K35.80", "M17.11", "A41.9", "I63.9", "M54.5", "N39.0", "R07.9", "C18.9", "G45.9"]
DIAG_P = np.array([.115,.083,.102,.075,.047,.038,.080,.036,.072,.028,.032,.078,.082,.060,.025,.047])
DIAG_BASE = {"J18.9":18500,"I50.9":28500,"E11.9":9200,"N17.9":26500,"S72.001A":48000,"I21.4":53000,"J44.1":21500,"K35.80":24000,"M17.11":15500,"A41.9":72000,"I63.9":59000,"M54.5":7800,"N39.0":9600,"R07.9":12500,"C18.9":88000,"G45.9":17500}
DIAG_LOS = {"J18.9":4.2,"I50.9":5.6,"E11.9":2.1,"N17.9":5.4,"S72.001A":7.6,"I21.4":5.2,"J44.1":4.0,"K35.80":3.0,"M17.11":2.2,"A41.9":8.2,"I63.9":6.3,"M54.5":1.4,"N39.0":2.7,"R07.9":1.9,"C18.9":8.8,"G45.9":2.4}
DIAG_SEV = {"J18.9":.52,"I50.9":.72,"E11.9":.25,"N17.9":.68,"S72.001A":.75,"I21.4":.86,"J44.1":.56,"K35.80":.53,"M17.11":.32,"A41.9":.93,"I63.9":.88,"M54.5":.18,"N39.0":.29,"R07.9":.38,"C18.9":.91,"G45.9":.53}


def _sample_state(rng, regions):
    out = np.empty(len(regions), dtype=object)
    for reg, states in REGIONS.items():
        ix = np.where(regions == reg)[0]
        if len(ix):
            # More populated states receive more records; this is intentionally not uniform.
            probs = np.array([{"CA":.25,"TX":.23,"FL":.18,"NY":.18,"PA":.12,"IL":.20,"OH":.15,"GA":.13,"NC":.12}.get(s, 1.0) for s in states], float)
            probs /= probs.sum()
            out[ix] = rng.choice(states, size=len(ix), p=probs)
    return out


def generate(output_dir: Path, claims_n: int = 500_000, patients_n: int = 150_000, hospitals_n: int = 600, seed: int = SEED):
    if claims_n < 10_000:
        raise ValueError("Use at least 10,000 claims for this project.")
    rng = np.random.default_rng(seed)
    raw = output_dir / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    # Patient dimension: older patients are more common, with a meaningful younger cohort.
    p_region = rng.choice(REGION_NAMES, patients_n, p=REGION_P)
    p_state = _sample_state(rng, p_region)
    age_bucket = rng.choice([0,1,2,3], patients_n, p=[.11,.19,.46,.24])
    age = np.empty(patients_n, dtype=np.int16)
    age[age_bucket == 0] = rng.integers(18, 40, size=(age_bucket == 0).sum())
    age[age_bucket == 1] = rng.integers(40, 65, size=(age_bucket == 1).sum())
    age[age_bucket == 2] = rng.integers(65, 81, size=(age_bucket == 2).sum())
    age[age_bucket == 3] = rng.integers(81, 96, size=(age_bucket == 3).sum())
    gender = rng.choice(["Female", "Male", "Other/Unknown"], patients_n, p=[.525,.463,.012])
    ins_segment = rng.choice(["Medicare", "Commercial", "Medicaid", "Dual Eligible"], patients_n, p=[.59,.20,.12,.09])
    patients = pd.DataFrame({
        "PatientID": [f"P{i:07d}" for i in range(1, patients_n+1)],
        "Age": age,
        "Gender": gender,
        "State": p_state,
        "Region": p_region,
        "InsuranceSegment": ins_segment,
    })

    # Hospital dimension: concentrated facility footprint; tier mix is deliberately skewed.
    h_region = rng.choice(REGION_NAMES, hospitals_n, p=REGION_P)
    h_state = _sample_state(rng, h_region)
    h_tier = rng.choice(["Tier 1", "Tier 2", "Tier 3"], hospitals_n, p=[.13,.34,.53])
    tier_cost = np.select([h_tier == "Tier 1", h_tier == "Tier 2"], [1.20,1.04], default=.91)
    h_beds = np.where(h_tier == "Tier 1", rng.lognormal(np.log(470),.42,hospitals_n),
             np.where(h_tier == "Tier 2", rng.lognormal(np.log(230),.48,hospitals_n), rng.lognormal(np.log(105),.58,hospitals_n)))
    h_beds = np.clip(np.rint(h_beds), 25, 1800).astype(int)
    h_teaching = np.where(h_tier == "Tier 1", rng.random(hospitals_n) < .56,
                 np.where(h_tier == "Tier 2", rng.random(hospitals_n) < .20, rng.random(hospitals_n) < .05))
    h_state_cost = np.array([STATE_COST[s] for s in h_state])
    h_cost_index = tier_cost * h_state_cost * rng.lognormal(0,.055,hospitals_n)
    prefixes = ["Northstar", "Pinecrest", "Riverside", "Cedar Valley", "Summit", "Lakeside", "Meadowbrook", "Canyon", "Maple", "Evergreen", "Fairview", "Redwood", "Silverline", "Blue Ridge", "Oak Harbor"]
    names = [f"{rng.choice(prefixes)} Synthetic Medical Center {i:03d}" for i in range(1,hospitals_n+1)]
    hospitals = pd.DataFrame({
        "HospitalID": [f"H{i:04d}" for i in range(1,hospitals_n+1)],
        "Hospital_Name": names,
        "Tier": h_tier,
        "State": h_state,
        "Region": h_region,
        "BedCapacity": h_beds,
        "TeachingHospital": h_teaching.astype(int),
        "HospitalCostIndex": np.round(h_cost_index,4),
    })

    # Claim rows: long-tailed patient utilization and rising / seasonal month weights.
    duplicate_n = int(round(claims_n * .004))
    repeat_n = int(round(claims_n * .004))
    base_n = claims_n - duplicate_n - repeat_n
    p_weights = rng.lognormal(mean=0, sigma=.85, size=patients_n)
    p_weights = p_weights / p_weights.sum()
    patient_ix = rng.choice(patients_n, base_n, p=p_weights)
    c_age = age[patient_ix]
    c_gender = gender[patient_ix]
    c_region = p_region[patient_ix]
    c_state = p_state[patient_ix]
    c_ins = ins_segment[patient_ix]

    months = pd.date_range("2023-01-01", "2025-12-01", freq="MS")
    month_idx = np.arange(len(months))
    month_weights = (1.0 + .26 * month_idx / max(len(month_idx)-1,1)) * (1 + .10*np.sin(2*np.pi*(month_idx%12)/12 + .6))
    month_weights[[0,1]] *= .88
    month_weights[[11,23,35]] *= 1.08
    month_weights = month_weights / month_weights.sum()
    chosen_month = rng.choice(len(months), base_n, p=month_weights)
    start_days = months.values.astype("datetime64[D]")[chosen_month]
    next_month_days = (months + pd.offsets.MonthBegin(1)).values.astype("datetime64[D]")[chosen_month]
    days_in_month = (next_month_days - start_days).astype(int)
    admission = start_days + rng.integers(0, 31, size=base_n).clip(max=days_in_month-1).astype("timedelta64[D]")
    admission = pd.to_datetime(admission)

    diagnosis = rng.choice(DIAG, base_n, p=DIAG_P)
    diag_base = np.array([DIAG_BASE[d] for d in diagnosis], dtype=float)
    diag_los = np.array([DIAG_LOS[d] for d in diagnosis], dtype=float)
    diag_sev = np.array([DIAG_SEV[d] for d in diagnosis], dtype=float)
    age_factor = 1 + np.maximum(c_age-65,0)*.0038 + np.maximum(45-c_age,0)*.0015
    age_factor = np.clip(age_factor, .93, 1.28)
    severity = np.clip(diag_sev + (c_age >= 80)*.10 + (c_age < 40)*.015 + rng.normal(0,.10,base_n), .05, .99)
    is_emergency = (rng.random(base_n) < np.clip(.08 + .52*severity, .08, .72)).astype(int)
    admission_type = np.where(is_emergency==1, "Emergency", np.where(rng.random(base_n)<.72, "Elective", "Urgent"))
    los_mean = diag_los * (1 + .18*(c_age>=80) + .07*is_emergency)
    los = np.rint(rng.lognormal(np.log(los_mean), .48)).astype(int)
    los = np.clip(los, 1, 75)
    complications = (rng.random(base_n) < np.clip(.025 + .20*severity, .025, .28)).astype(int)

    # More complex episodes are more likely to use higher-acuity hospitals.
    p_t1 = np.clip(.07 + .22*severity + .08*is_emergency, .06, .43)
    p_t2 = np.clip(.26 + .05*severity, .24, .35)
    p_t3 = 1 - p_t1 - p_t2
    tier_draw = rng.random(base_n)
    desired_tier = np.where(tier_draw < p_t1, "Tier 1", np.where(tier_draw < p_t1+p_t2, "Tier 2", "Tier 3"))
    h_ix = np.empty(base_n, dtype=np.int32)
    hospital_weights = np.sqrt(h_beds.astype(float)) * h_cost_index
    for reg in REGION_NAMES:
        for tier in ["Tier 1", "Tier 2", "Tier 3"]:
            ix = np.where((c_region == reg) & (desired_tier == tier))[0]
            if not len(ix):
                continue
            local_candidates = np.where((h_region == reg) & (h_tier == tier))[0]
            candidates = local_candidates if len(local_candidates) >= 3 else np.where(h_tier == tier)[0]
            probs = hospital_weights[candidates]
            probs = probs / probs.sum()
            # A small out-of-region share represents specialist referrals / network leakage.
            remote = rng.random(len(ix)) < .17
            if remote.any():
                national = np.where(h_tier == tier)[0]
                nprobs = hospital_weights[national] / hospital_weights[national].sum()
                h_ix[ix[remote]] = rng.choice(national, remote.sum(), p=nprobs)
            if (~remote).any():
                h_ix[ix[~remote]] = rng.choice(candidates, (~remote).sum(), p=probs)

    hosp_cost = h_cost_index[h_ix]
    hosp_tier = h_tier[h_ix]
    hosp_state = h_state[h_ix]
    hosp_region = h_region[h_ix]
    region_cost = np.array([STATE_COST[s] for s in hosp_state]) / np.array([STATE_COST.get(s,1) for s in hosp_state])
    tier_per_diem = np.where(hosp_tier=="Tier 1",1.18,np.where(hosp_tier=="Tier 2",1.03,.89))
    age_complexity = np.where(c_age>=80,1.15,np.where(c_age>=65,1.08,1.0))
    emergency_factor = 1 + .14*is_emergency
    complication_factor = 1 + complications*rng.uniform(.12,.62,base_n)
    procedure_factor = rng.choice([.82,1.0,1.24,1.58,2.10], base_n, p=[.09,.47,.26,.14,.04])
    per_diem = diag_base * rng.uniform(.055,.105,base_n)
    raw_bill = (diag_base + los*per_diem) * hosp_cost * age_complexity * emergency_factor * complication_factor * procedure_factor
    raw_bill *= rng.lognormal(mean=-.04, sigma=.43, size=base_n)
    billed = np.clip(raw_bill, 650, 1_250_000)
    procedure = rng.choice(["Medical Management","Imaging","Surgery","Cardiac Procedure","Orthopedic Procedure","Oncology","Respiratory Therapy","Dialysis"], base_n, p=[.32,.15,.11,.07,.10,.06,.09,.10])

    claims = pd.DataFrame({
        "ClaimID": [f"C{i:07d}" for i in range(1,base_n+1)],
        "PatientID": patients.iloc[patient_ix]["PatientID"].to_numpy(),
        "HospitalID": hospitals.iloc[h_ix]["HospitalID"].to_numpy(),
        "AdmissionDate": admission.strftime("%Y-%m-%d"),
        "DiagnosisCode": diagnosis,
        "ProcedureCategory": procedure,
        "AdmissionType": admission_type,
        "IsEmergency": is_emergency,
        "LengthOfStay": los,
        "HasComplications": complications,
        "BilledAmount": np.round(billed,2),
        "IsFraud": np.zeros(base_n,dtype=np.int8),
    })

    # Labelled scenario injections: duplicates, short-gap repeats, overbilling, and noisy review positives.
    claims["IsFraud"] = 0
    dup_ix = rng.choice(base_n, duplicate_n, replace=False)
    dup_rows = claims.iloc[dup_ix].copy().reset_index(drop=True)
    dup_rows["ClaimID"] = [f"C{i:07d}" for i in range(base_n+1,base_n+duplicate_n+1)]
    claims.loc[dup_ix, "IsFraud"] = 1
    dup_rows["IsFraud"] = 1

    repeat_ix = rng.choice(np.setdiff1d(np.arange(base_n), dup_ix), repeat_n, replace=False)
    repeat_rows = claims.iloc[repeat_ix].copy().reset_index(drop=True)
    repeat_rows["ClaimID"] = [f"C{i:07d}" for i in range(base_n+duplicate_n+1,claims_n+1)]
    repeat_days = rng.integers(1,15,size=repeat_n)
    repeat_rows["AdmissionDate"] = (pd.to_datetime(repeat_rows["AdmissionDate"]) + pd.to_timedelta(repeat_days,unit="D")).dt.strftime("%Y-%m-%d")
    repeat_rows["BilledAmount"] = np.round(repeat_rows["BilledAmount"].to_numpy() * rng.uniform(.74,1.26,repeat_n),2)
    repeat_rows["LengthOfStay"] = np.clip(np.rint(repeat_rows["LengthOfStay"].to_numpy()*rng.uniform(.65,1.15,repeat_n)),1,75).astype(int)
    repeat_rows["IsFraud"] = 1

    # Overcharge scenarios have varied severity; other naturally expensive claims remain unlabelled.
    over_n = int(round(base_n*.009))
    over_ix = rng.choice(np.setdiff1d(np.arange(base_n), dup_ix), over_n, replace=False)
    over_mult = rng.choice([0,1,2], over_n, p=[.56,.32,.12])
    multipliers = np.choose(over_mult, [rng.uniform(1.25,1.65,over_n), rng.uniform(1.66,2.55,over_n), rng.uniform(2.56,4.20,over_n)])
    claims.loc[over_ix, "BilledAmount"] = np.round(claims.loc[over_ix, "BilledAmount"].to_numpy()*multipliers,2)
    claims.loc[over_ix, "IsFraud"] = 1

    # Low-frequency background review positives create label noise / overlap.
    remaining = np.where(claims["IsFraud"].to_numpy()==0)[0]
    bg_n = min(int(round(base_n*.0022)),len(remaining))
    bg_ix = rng.choice(remaining,bg_n,replace=False)
    claims.loc[bg_ix,"IsFraud"] = 1

    claims = pd.concat([claims,dup_rows,repeat_rows],ignore_index=True)
    # Derive end date; end dates can be beyond the study window for late admissions, which is expected.
    los_arr = claims["LengthOfStay"].to_numpy()
    claims["DischargeDate"] = (pd.to_datetime(claims["AdmissionDate"]) + pd.to_timedelta(los_arr,unit="D")).dt.strftime("%Y-%m-%d")

    # A few validly missing secondary diagnosis values mimic real-world optional fields.
    secondary_probs = rng.choice(DIAG, len(claims), p=DIAG_P)
    has_secondary = rng.random(len(claims)) < .34
    claims["SecondaryDiagnosisCode"] = np.where(has_secondary, secondary_probs, "")
    # Keep dimensions and IDs deterministic and privacy-safe; no names, addresses, or real identifiers.
    patients.to_csv(raw/"patients.csv",index=False)
    hospitals.to_csv(raw/"hospitals.csv",index=False)
    claims.to_csv(raw/"claims.csv",index=False)

    # Generation summary for audit.
    summary = {
        "seed": int(seed), "claims": int(len(claims)), "base_claims": int(base_n),
        "duplicate_copy_rows": int(duplicate_n), "short_gap_repeat_rows": int(repeat_n),
        "overcharge_injected_base_rows": int(over_n), "background_positive_rows": int(bg_n),
        "positive_claim_rows": int(claims["IsFraud"].sum()), "positive_rate": float(claims["IsFraud"].mean()),
        "patients": int(len(patients)), "hospitals": int(len(hospitals)),
        "date_min": str(claims["AdmissionDate"].min()), "date_max": str(claims["AdmissionDate"].max()),
        "disclaimer": "All records and scenario labels are synthetic; not real healthcare data or observed fraud.",
    }
    pd.Series(summary).to_json(output_dir/"reports"/"generation_summary.json", indent=2)
    print(pd.Series(summary).to_string())

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--claims",type=int,default=500_000)
    ap.add_argument("--patients",type=int,default=150_000)
    ap.add_argument("--hospitals",type=int,default=600)
    ap.add_argument("--seed",type=int,default=SEED)
    a=ap.parse_args()
    generate(a.output_dir,a.claims,a.patients,a.hospitals,a.seed)
