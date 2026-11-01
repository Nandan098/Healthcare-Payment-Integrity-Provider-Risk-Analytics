# SQL Business Questions & Answers

Executed 40 SQLite analyses against the 500,000-row healthcare claims project. Results are descriptive of generated data.

## Executive Portfolio Snapshot

```sql
SELECT COUNT(*) AS total_claims, COUNT(DISTINCT PatientID) AS unique_patients, COUNT(DISTINCT HospitalID) AS hospitals, ROUND(SUM(BilledAmount),2) AS total_billed_usd, ROUND(AVG(BilledAmount),2) AS avg_claim_usd, ROUND(AVG(LengthOfStay),2) AS avg_los FROM claims;
```

Result rows: **1**

```text
 total_claims  unique_patients  hospitals  total_billed_usd  avg_claim_usd  avg_los
       500000           124329        600      2.868691e+10       57373.82     4.73
```

## Monthly Claims and Billing

```sql
SELECT strftime('%Y-%m',AdmissionDate) AS claim_month, COUNT(*) AS claims, ROUND(SUM(BilledAmount),2) AS billed_usd, ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY claim_month ORDER BY claim_month;
```

Result rows: **37**

```text
claim_month  claims   billed_usd  avg_bill_usd
    2023-01   11493 656052345.35      57082.78
    2023-02   11731 670444327.00      57151.51
    2023-03   13780 785512594.05      57003.82
    2023-04   13679 777800764.05      56860.94
    2023-05   13084 744311168.05      56887.13
    2023-06   12780 723092037.85      56579.97
    2023-07   12141 693446551.68      57116.10
    2023-08   11694 672653841.62      57521.28
    2023-09   11561 658067872.86      56921.36
    2023-10   12164 712645950.53      58586.48
    2023-11   12596 729643719.36      57926.62
    2023-12   14494 819257315.91      56523.89
```

## Annual Claims and Billing

```sql
SELECT strftime('%Y',AdmissionDate) AS claim_year, COUNT(*) AS claims, ROUND(SUM(BilledAmount),2) AS billed_usd FROM claims GROUP BY claim_year ORDER BY claim_year;
```

Result rows: **4**

```text
claim_year  claims   billed_usd
      2023  151197 8.642928e+09
      2024  167562 9.631953e+09
      2025  181224 1.041013e+10
      2026      17 1.900010e+06
```

## Diagnosis Mix

```sql
SELECT DiagnosisCode, COUNT(*) AS claims, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) AS claim_share_pct FROM claims GROUP BY DiagnosisCode ORDER BY claims DESC;
```

Result rows: **16**

```text
DiagnosisCode  claims  claim_share_pct
        J18.9   57627            11.53
        E11.9   50661            10.13
        I50.9   41563             8.31
        N39.0   41003             8.20
        J44.1   40374             8.07
        M54.5   39320             7.86
        N17.9   37519             7.50
       M17.11   35849             7.17
        R07.9   29938             5.99
        G45.9   23536             4.71
     S72.001A   23431             4.69
        I21.4   18892             3.78
```

## Diagnosis Billing Benchmark

```sql
SELECT DiagnosisCode, COUNT(*) AS claims, ROUND(AVG(BilledAmount),2) AS avg_bill_usd, ROUND(MIN(BilledAmount),2) AS min_bill_usd, ROUND(MAX(BilledAmount),2) AS max_bill_usd FROM claims GROUP BY DiagnosisCode ORDER BY avg_bill_usd DESC;
```

Result rows: **16**

```text
DiagnosisCode  claims  avg_bill_usd  min_bill_usd  max_bill_usd
        C18.9   12321     263779.44      21390.89    2231517.58
        A41.9   14149     211146.89      26687.44    2424185.67
        I63.9   15768     154908.47      13017.58    1250000.00
     S72.001A   23431     132199.20      16389.74    1323104.17
        I21.4   18892     128261.78      12465.99    1340905.34
        I50.9   41563      68946.17       7051.66     972195.58
        N17.9   37519      62868.33       6858.33     635465.85
       K35.80   18049      46323.77       4930.36     506529.76
        J44.1   40374      45165.18       4944.41     501541.79
        J18.9   57627      39196.78       4039.84     524247.92
        G45.9   23536      32206.27       2313.25     303622.73
       M17.11   35849      26910.41       2451.40     277028.23
```

## Hospital Tier Benchmark

```sql
SELECT h.Tier, COUNT(*) AS claims, ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd, ROUND(SUM(c.BilledAmount),2) AS total_billed_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Tier ORDER BY avg_bill_usd DESC;
```

Result rows: **3**

```text
  Tier  claims  avg_bill_usd  total_billed_usd
Tier 1  108117      82366.93      8.905266e+09
Tier 2  143350      60265.69      8.639086e+09
Tier 3  248533      44833.31      1.114256e+10
```

## Top Hospitals by Claims

```sql
SELECT h.Hospital_Name,h.Tier,h.State,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS total_billed_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID ORDER BY claims DESC LIMIT 25;
```

Result rows: **25**

```text
                            Hospital_Name   Tier State  claims  total_billed_usd
   Evergreen Synthetic Medical Center 143 Tier 1    VA    2664      205733870.71
      Summit Synthetic Medical Center 372 Tier 1    MA    2445      267496576.71
  Oak Harbor Synthetic Medical Center 046 Tier 1    WV    2270      169441164.15
 Meadowbrook Synthetic Medical Center 157 Tier 1    OH    2166      169184192.27
      Canyon Synthetic Medical Center 515 Tier 1    MD    2102      195458006.96
   Northstar Synthetic Medical Center 298 Tier 1    LA    2004      141797774.02
   Northstar Synthetic Medical Center 207 Tier 1    VA    1902      170556620.00
      Summit Synthetic Medical Center 198 Tier 3    KY    1877       84948414.93
Cedar Valley Synthetic Medical Center 452 Tier 1    HI    1862      177043943.73
   Pinecrest Synthetic Medical Center 289 Tier 1    MS    1844      149145200.72
   Pinecrest Synthetic Medical Center 104 Tier 1    CO    1839      167651562.89
   Northstar Synthetic Medical Center 138 Tier 1    MS    1819      127904846.62
```

## Hospital Region Spend

```sql
SELECT h.Region,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS billed_usd,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Region ORDER BY billed_usd DESC;
```

Result rows: **4**

```text
   Region  claims   billed_usd  avg_bill_usd
    South  192048 1.038869e+10      54094.24
     West  110130 6.536897e+09      59356.19
Northeast   93158 5.891084e+09      63237.55
  Midwest  104664 5.870239e+09      56086.51
```

## Patient Age Band Utilization

```sql
SELECT CASE WHEN p.Age<40 THEN '18-39' WHEN p.Age<65 THEN '40-64' WHEN p.Age<80 THEN '65-79' ELSE '80+' END AS age_band,COUNT(*) AS claims,COUNT(DISTINCT c.PatientID) AS patients,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd,ROUND(SUM(c.BilledAmount),2) AS spend_usd FROM claims c JOIN patients p USING(PatientID) GROUP BY age_band ORDER BY age_band;
```

Result rows: **4**

```text
age_band  claims  patients  avg_bill_usd    spend_usd
   18-39   55203     13711      51536.10 2.844947e+09
   40-64   95374     23620      52526.93 5.009703e+09
   65-79  214490     53420      56200.92 1.205453e+10
     80+  134933     33578      65052.46 8.777724e+09
```

## Patient Claim Frequency

```sql
WITH x AS (SELECT PatientID,COUNT(*) AS n_claims FROM claims GROUP BY PatientID) SELECT CASE WHEN n_claims=1 THEN '1' WHEN n_claims<=3 THEN '2-3' WHEN n_claims<=6 THEN '4-6' WHEN n_claims<=12 THEN '7-12' ELSE '13+' END AS frequency_band,COUNT(*) AS patients FROM x GROUP BY frequency_band ORDER BY MIN(n_claims);
```

Result rows: **5**

```text
frequency_band  patients
             1     30178
           2-3     43938
           4-6     29780
          7-12     15843
           13+      4590
```

## Largest Individual Bills

```sql
SELECT c.ClaimID,c.BilledAmount,c.LengthOfStay,c.DiagnosisCode,h.Hospital_Name,h.Tier,h.State FROM claims c JOIN hospitals h USING(HospitalID) ORDER BY c.BilledAmount DESC LIMIT 50;
```

Result rows: **50**

```text
 ClaimID  BilledAmount  LengthOfStay DiagnosisCode                             Hospital_Name   Tier State
C0396375    2424185.67            15         A41.9 Cedar Valley Synthetic Medical Center 308 Tier 1    MN
C0006030    2231517.58            13         C18.9    Riverside Synthetic Medical Center 485 Tier 1    MN
C0223774    1761703.40            21         C18.9        Maple Synthetic Medical Center 092 Tier 2    NJ
C0315006    1378261.17            19         C18.9   Oak Harbor Synthetic Medical Center 046 Tier 1    WV
C0435263    1340905.34            11         I21.4   Silverline Synthetic Medical Center 188 Tier 3    AK
C0101672    1323104.17             6      S72.001A   Silverline Synthetic Medical Center 193 Tier 2    CO
C0379244    1316726.80             9         A41.9       Summit Synthetic Medical Center 455 Tier 2    VT
C0455449    1301798.32            19         A41.9   Blue Ridge Synthetic Medical Center 167 Tier 3    AR
C0029871    1292931.74            13         C18.9       Canyon Synthetic Medical Center 042 Tier 3    UT
C0099252    1260708.56            21         A41.9   Silverline Synthetic Medical Center 582 Tier 2    TN
C0014783    1250000.00            14         C18.9     Lakeside Synthetic Medical Center 584 Tier 1    WA
C0016651    1250000.00            17         C18.9  Meadowbrook Synthetic Medical Center 387 Tier 1    MA
```

## Length of Stay Distribution

```sql
SELECT CASE WHEN LengthOfStay<=1 THEN '1 day' WHEN LengthOfStay<=3 THEN '2-3 days' WHEN LengthOfStay<=7 THEN '4-7 days' WHEN LengthOfStay<=14 THEN '8-14 days' ELSE '15+ days' END AS los_band,COUNT(*) AS claims,ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY los_band ORDER BY MIN(LengthOfStay);
```

Result rows: **5**

```text
 los_band  claims  avg_bill_usd
    1 day   55011      17009.31
 2-3 days  181984      28246.99
 4-7 days  179306      61830.52
8-14 days   71300     122422.29
 15+ days   12399     225455.03
```

## Cost Per Day Outlier Screen

```sql
SELECT ClaimID,DiagnosisCode,LengthOfStay,ROUND(BilledAmount/LengthOfStay,2) AS cost_per_day_usd,BilledAmount FROM claims WHERE BilledAmount/LengthOfStay>(SELECT AVG(BilledAmount/LengthOfStay)+3.0*AVG(ABS((BilledAmount/LengthOfStay)-(SELECT AVG(BilledAmount/LengthOfStay) FROM claims))) FROM claims) ORDER BY cost_per_day_usd DESC LIMIT 100;
```

Result rows: **100**

```text
 ClaimID DiagnosisCode  LengthOfStay  cost_per_day_usd  BilledAmount
C0137368         I63.9             4         273851.84    1095407.35
C0165214         C18.9             4         257124.77    1028499.06
C0299155         I21.4             1         252800.92     252800.92
C0465294         I21.4             2         240722.35     481444.69
C0311722         C18.9             2         239997.73     479995.46
C0104365         A41.9             1         239643.76     239643.76
C0388993         I21.4             2         239556.61     479113.22
C0059036         I63.9             2         237949.45     475898.90
C0314522         E11.9             1         237348.42     237348.42
C0325070         I21.4             4         232285.53     929142.13
C0497020         I21.4             4         232285.53     929142.13
C0379463         I63.9             2         231106.98     462213.96
```

## Duplicate Business Key Groups

```sql
SELECT PatientID,HospitalID,AdmissionDate,DiagnosisCode,COUNT(*) AS group_rows,ROUND(SUM(BilledAmount),2) AS group_billed_usd FROM claims GROUP BY PatientID,HospitalID,AdmissionDate,DiagnosisCode HAVING COUNT(*)>1 ORDER BY group_rows DESC,group_billed_usd DESC LIMIT 250;
```

Result rows: **250**

```text
PatientID HospitalID AdmissionDate DiagnosisCode  group_rows  group_billed_usd
 P0107150      H0320    2023-08-31         I21.4           2        1858284.26
 P0060308      H0593    2025-01-16         C18.9           2        1642002.28
 P0140388      H0198    2025-01-08         C18.9           2        1555816.08
 P0002388      H0518    2023-05-19         A41.9           2        1228535.32
 P0106040      H0532    2023-02-27         C18.9           2        1115011.78
 P0093323      H0591    2025-04-12         A41.9           2        1097538.12
 P0073369      H0134    2023-09-29         C18.9           2        1045070.08
 P0110143      H0017    2024-10-03         A41.9           2        1011654.32
 P0104694      H0387    2025-08-18         I63.9           2         929877.06
 P0048201      H0463    2025-10-12      S72.001A           2         923759.14
 P0020177      H0262    2025-05-28      S72.001A           2         899506.26
 P0064339      H0092    2024-09-20         C18.9           2         889765.10
```

## Billing Above Diagnosis Average

```sql
WITH d AS (SELECT DiagnosisCode,AVG(BilledAmount) AS avg_bill FROM claims GROUP BY DiagnosisCode) SELECT c.ClaimID,c.DiagnosisCode,c.BilledAmount,ROUND(d.avg_bill,2) AS diagnosis_avg,ROUND(c.BilledAmount/d.avg_bill,2) AS ratio FROM claims c JOIN d USING(DiagnosisCode) WHERE c.BilledAmount>2*d.avg_bill ORDER BY ratio DESC LIMIT 250;
```

Result rows: **250**

```text
 ClaimID DiagnosisCode  BilledAmount  diagnosis_avg  ratio
C0019462         E11.9     277256.10       15583.91  17.79
C0314522         E11.9     237348.42       15583.91  15.23
C0009566         R07.9     308615.64       21448.23  14.39
C0130085         I50.9     972195.58       68946.17  14.10
C0469424         J18.9     524247.92       39196.78  13.37
C0107079         N39.0     221382.20       17143.68  12.91
C0116196         I50.9     853824.52       68946.17  12.38
C0336200         N39.0     208391.84       17143.68  12.16
C0394176         M54.5     146245.08       12361.60  11.83
C0480355         I50.9     801895.78       68946.17  11.63
C0396375         A41.9    2424185.67      211146.89  11.48
C0106042         I50.9     768031.10       68946.17  11.14
```

## Simulated Positive Rate by Diagnosis

```sql
SELECT DiagnosisCode,COUNT(*) AS claims,SUM(IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(IsFraud),2) AS generated_positive_rate_pct FROM claims GROUP BY DiagnosisCode ORDER BY generated_positive_rate_pct DESC;
```

Result rows: **16**

```text
DiagnosisCode  claims  generated_positive_rows  generated_positive_rate_pct
     S72.001A   23431                      600                         2.56
        J44.1   40374                     1012                         2.51
        M54.5   39320                      958                         2.44
        R07.9   29938                      713                         2.38
        G45.9   23536                      556                         2.36
        N39.0   41003                      952                         2.32
        I50.9   41563                      949                         2.28
        N17.9   37519                      855                         2.28
        E11.9   50661                     1146                         2.26
       K35.80   18049                      408                         2.26
        I21.4   18892                      425                         2.25
        J18.9   57627                     1298                         2.25
```

## Generated Positive Rate by Hospital Tier

```sql
SELECT h.Tier,COUNT(*) AS claims,SUM(c.IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(c.IsFraud),2) AS generated_positive_rate_pct FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.Tier;
```

Result rows: **3**

```text
  Tier  claims  generated_positive_rows  generated_positive_rate_pct
Tier 1  108117                     2541                         2.35
Tier 2  143350                     3266                         2.28
Tier 3  248533                     5748                         2.31
```

## Generated Positive Label Billed Exposure

```sql
SELECT SUM(IsFraud) AS generated_positive_claims,ROUND(SUM(CASE WHEN IsFraud=1 THEN BilledAmount ELSE 0 END),2) AS billed_amount_on_generated_positive_rows FROM claims;
```

Result rows: **1**

```text
 generated_positive_claims  billed_amount_on_generated_positive_rows
                     11555                              875314286.88
```

## Diagnosis Share of Total Spend

```sql
SELECT DiagnosisCode,ROUND(SUM(BilledAmount),2) AS billed_usd,ROUND(100.0*SUM(BilledAmount)/(SELECT SUM(BilledAmount) FROM claims),2) AS spend_share_pct FROM claims GROUP BY DiagnosisCode ORDER BY billed_usd DESC;
```

Result rows: **16**

```text
DiagnosisCode   billed_usd  spend_share_pct
        C18.9 3.250026e+09            11.33
     S72.001A 3.097559e+09            10.80
        A41.9 2.987517e+09            10.41
        I50.9 2.865610e+09             9.99
        I63.9 2.442597e+09             8.51
        I21.4 2.423121e+09             8.45
        N17.9 2.358757e+09             8.22
        J18.9 2.258793e+09             7.87
        J44.1 1.823499e+09             6.36
       M17.11 9.647112e+08             3.36
       K35.80 8.360977e+08             2.91
        E11.9 7.894963e+08             2.75
```

## Gender and Claim Profile

```sql
SELECT p.Gender,COUNT(*) AS claims,COUNT(DISTINCT p.PatientID) AS patients,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd,ROUND(SUM(c.BilledAmount),2) AS spend_usd FROM claims c JOIN patients p USING(PatientID) GROUP BY p.Gender;
```

Result rows: **3**

```text
       Gender  claims  patients  avg_bill_usd    spend_usd
       Female  263355     65200      57265.28 1.508110e+10
         Male  230567     57639      57518.30 1.326182e+10
Other/Unknown    6078      1490      56596.02 3.439906e+08
```

## Admission Type and Emergency Profile

```sql
SELECT AdmissionType,IsEmergency,COUNT(*) AS claims,ROUND(AVG(LengthOfStay),2) AS avg_los,ROUND(AVG(BilledAmount),2) AS avg_bill_usd FROM claims GROUP BY AdmissionType,IsEmergency ORDER BY claims DESC;
```

Result rows: **3**

```text
AdmissionType  IsEmergency  claims  avg_los  avg_bill_usd
     Elective            0  230365     4.21      45018.49
    Emergency            1  180254     5.66      79307.78
       Urgent            0   89381     4.20      44983.61
```

## Hospital State Claims and Spend

```sql
SELECT h.State,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS billed_usd,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.State ORDER BY billed_usd DESC;
```

Result rows: **50**

```text
State  claims   billed_usd  avg_bill_usd
   MA   19118 1.462968e+09      76523.09
   KY   22313 1.231508e+09      55192.39
   MS   21708 1.179691e+09      54343.60
   NJ   17142 1.089457e+09      63554.82
   VA   15780 9.926785e+08      62907.38
   CO   13619 9.419899e+08      69167.33
   MD   14366 9.272315e+08      64543.47
   WV   17163 8.967903e+08      52251.37
   LA   17040 8.919106e+08      52342.17
   NH   14235 8.828806e+08      62021.82
   MN   14111 8.712148e+08      61740.12
   WA   12653 8.576713e+08      67784.03
```

## Quarterly Claims and Billing

```sql
SELECT strftime('%Y',AdmissionDate)||'-Q'||((CAST(strftime('%m',AdmissionDate) AS INTEGER)+2)/3) AS quarter,COUNT(*) AS claims,ROUND(SUM(BilledAmount),2) AS billed_usd FROM claims GROUP BY quarter ORDER BY quarter;
```

Result rows: **13**

```text
quarter  claims   billed_usd
2023-Q1   37004 2.112009e+09
2023-Q2   39543 2.245204e+09
2023-Q3   35396 2.024168e+09
2023-Q4   39254 2.261547e+09
2024-Q1   44034 2.536342e+09
2024-Q2   42519 2.447150e+09
2024-Q3   38365 2.214748e+09
2024-Q4   42644 2.433713e+09
2025-Q1   47561 2.727865e+09
2025-Q2   46310 2.667289e+09
2025-Q3   41792 2.397071e+09
2025-Q4   45561 2.617903e+09
```

## Duplicate Key Groups by Hospital

```sql
WITH d AS (SELECT HospitalID,PatientID,AdmissionDate,DiagnosisCode,COUNT(*) n FROM claims GROUP BY HospitalID,PatientID,AdmissionDate,DiagnosisCode HAVING COUNT(*)>1) SELECT h.Hospital_Name,h.Tier,COUNT(*) AS duplicate_groups,SUM(d.n) AS rows_in_duplicate_groups FROM d JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID ORDER BY duplicate_groups DESC LIMIT 50;
```

Result rows: **50**

```text
                            Hospital_Name   Tier  duplicate_groups  rows_in_duplicate_groups
Cedar Valley Synthetic Medical Center 238 Tier 1                12                        24
   Evergreen Synthetic Medical Center 143 Tier 1                12                        24
   Pinecrest Synthetic Medical Center 004 Tier 2                12                        24
      Canyon Synthetic Medical Center 515 Tier 1                11                        22
  Silverline Synthetic Medical Center 186 Tier 3                11                        22
 Meadowbrook Synthetic Medical Center 175 Tier 1                11                        22
 Meadowbrook Synthetic Medical Center 157 Tier 1                11                        22
       Maple Synthetic Medical Center 017 Tier 2                11                        22
Cedar Valley Synthetic Medical Center 452 Tier 1                10                        20
     Redwood Synthetic Medical Center 393 Tier 3                10                        20
 Meadowbrook Synthetic Medical Center 387 Tier 1                10                        20
  Silverline Synthetic Medical Center 320 Tier 1                10                        20
```

## High Utilization Patients

```sql
SELECT c.PatientID,p.Age,p.Gender,COUNT(*) AS claims,ROUND(SUM(c.BilledAmount),2) AS total_billed_usd,COUNT(DISTINCT c.HospitalID) AS hospitals_used FROM claims c JOIN patients p USING(PatientID) GROUP BY c.PatientID ORDER BY claims DESC,total_billed_usd DESC LIMIT 100;
```

Result rows: **100**

```text
PatientID  Age Gender  claims  total_billed_usd  hospitals_used
 P0060252   70 Female      81        4487506.71              65
 P0136499   46   Male      81        3236912.99              70
 P0137812   77 Female      71        4135050.58              56
 P0048136   76   Male      71        3979117.80              50
 P0134468   40 Female      70        3438239.77              59
 P0054309   75   Male      68        4732628.24              56
 P0038424   67 Female      67        3830396.66              53
 P0040431   40   Male      65        2659336.01              48
 P0144680   47   Male      62        2664125.72              50
 P0148531   36   Male      62        2089618.73              57
 P0103036   74   Male      61        2756925.80              51
 P0075858   90 Female      60        2378939.17              52
```

## Hospital Diagnosis Billing Cells

```sql
SELECT h.Hospital_Name,h.Tier,c.DiagnosisCode,COUNT(*) AS claims,ROUND(AVG(c.BilledAmount),2) AS avg_bill_usd FROM claims c JOIN hospitals h USING(HospitalID) GROUP BY h.HospitalID,c.DiagnosisCode HAVING COUNT(*)>=20 ORDER BY avg_bill_usd DESC LIMIT 200;
```

Result rows: **200**

```text
                            Hospital_Name   Tier DiagnosisCode  claims  avg_bill_usd
 Meadowbrook Synthetic Medical Center 387 Tier 1         C18.9      52     435828.27
       Maple Synthetic Medical Center 092 Tier 2         C18.9      27     414126.86
   Pinecrest Synthetic Medical Center 446 Tier 1         C18.9      57     410166.08
      Summit Synthetic Medical Center 372 Tier 1         C18.9      75     392625.37
  Blue Ridge Synthetic Medical Center 568 Tier 2         C18.9      29     390453.40
   Riverside Synthetic Medical Center 485 Tier 1         C18.9      58     383115.64
      Summit Synthetic Medical Center 297 Tier 1         C18.9      61     367184.29
       Maple Synthetic Medical Center 518 Tier 1         C18.9      65     363385.62
   Evergreen Synthetic Medical Center 325 Tier 1         C18.9      38     360210.56
    Lakeside Synthetic Medical Center 584 Tier 1         C18.9      59     360106.35
Cedar Valley Synthetic Medical Center 308 Tier 1         C18.9      44     359341.83
     Redwood Synthetic Medical Center 398 Tier 2         C18.9      30     354121.97
```

## Hospital Concentration

```sql
WITH h AS (SELECT HospitalID,SUM(BilledAmount) spend FROM claims GROUP BY HospitalID) SELECT COUNT(*) AS facilities,ROUND(MAX(spend),2) AS largest_hospital_spend,ROUND(100.0*MAX(spend)/(SELECT SUM(BilledAmount) FROM claims),2) AS largest_hospital_spend_share_pct FROM h;
```

Result rows: **1**

```text
 facilities  largest_hospital_spend  largest_hospital_spend_share_pct
        600            267496576.71                              0.93
```

## Repeat Patient Diagnosis Within 30 Days

```sql
WITH x AS (SELECT PatientID,DiagnosisCode,AdmissionDate,LAG(AdmissionDate) OVER(PARTITION BY PatientID,DiagnosisCode ORDER BY AdmissionDate) AS prior_date FROM claims) SELECT COUNT(*) AS repeat_episode_rows FROM x WHERE prior_date IS NOT NULL AND julianday(AdmissionDate)-julianday(prior_date)<=30;
```

Result rows: **1**

```text
 repeat_episode_rows
               11008
```

## Average Bill by LOS Band

```sql
SELECT CASE WHEN LengthOfStay<=2 THEN '1-2' WHEN LengthOfStay<=5 THEN '3-5' WHEN LengthOfStay<=10 THEN '6-10' WHEN LengthOfStay<=20 THEN '11-20' ELSE '21+' END AS los_band,COUNT(*) claims,ROUND(AVG(BilledAmount),2) avg_bill_usd,ROUND(AVG(BilledAmount/LengthOfStay),2) avg_cost_per_day_usd FROM claims GROUP BY los_band ORDER BY MIN(LengthOfStay);
```

Result rows: **5**

```text
los_band  claims  avg_bill_usd  avg_cost_per_day_usd
     1-2  153052      21169.39              13641.50
     3-5  198268      44479.79              11561.19
    6-10  112726      91162.55              12247.36
   11-20   33169     166258.73              12344.87
     21+    2785     300519.60              12048.02
```

## Billed Amount Bands

```sql
SELECT CASE WHEN BilledAmount<10000 THEN '<$10k' WHEN BilledAmount<25000 THEN '$10k-$25k' WHEN BilledAmount<50000 THEN '$25k-$50k' WHEN BilledAmount<100000 THEN '$50k-$100k' WHEN BilledAmount<250000 THEN '$100k-$250k' ELSE '$250k+' END AS billed_band,COUNT(*) claims,ROUND(SUM(BilledAmount),2) spend_usd FROM claims GROUP BY billed_band ORDER BY MIN(BilledAmount);
```

Result rows: **6**

```text
billed_band  claims    spend_usd
      <$10k   49523 3.685382e+08
  $10k-$25k  154434 2.617837e+09
  $25k-$50k  130402 4.657221e+09
 $50k-$100k   91280 6.386010e+09
$100k-$250k   59453 9.001359e+09
     $250k+   14908 5.655944e+09
```

## Secondary Diagnosis Coverage

```sql
SELECT CASE WHEN SecondaryDiagnosisCode IS NULL OR SecondaryDiagnosisCode='' THEN 'Missing/None' ELSE 'Present' END AS secondary_diagnosis_status,COUNT(*) claims,ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) share_pct FROM claims GROUP BY secondary_diagnosis_status;
```

Result rows: **2**

```text
secondary_diagnosis_status  claims  share_pct
              Missing/None  329560      65.91
                   Present  170440      34.09
```

## Risk Band Summary

```sql
SELECT RiskBand,COUNT(*) AS claims,ROUND(AVG(RiskScore),4) AS avg_risk_score,ROUND(SUM(PotentialBilledExposure_085),2) AS flagged_billed_exposure_usd FROM claim_scores GROUP BY RiskBand ORDER BY avg_risk_score DESC;
```

Result rows: **4**

```text
RiskBand  claims  avg_risk_score  flagged_billed_exposure_usd
    High    4139          0.9954                 242375793.66
Elevated    5760          0.6471                         0.00
Moderate   13564          0.3135                         0.00
     Low  476537          0.0448                         0.00
```

## High Risk Exposure by Hospital Tier

```sql
SELECT h.Tier,COUNT(*) AS scored_claims,SUM(CASE WHEN s.RiskScore>=.85 THEN 1 ELSE 0 END) AS high_risk_claims,ROUND(SUM(s.PotentialBilledExposure_085),2) AS potential_billed_exposure_usd FROM claim_scores s JOIN claims c USING(ClaimID) JOIN hospitals h USING(HospitalID) GROUP BY h.Tier ORDER BY potential_billed_exposure_usd DESC;
```

Result rows: **3**

```text
  Tier  scored_claims  high_risk_claims  potential_billed_exposure_usd
Tier 3         248533              2040                    94455199.94
Tier 1         108117               927                    80710600.88
Tier 2         143350              1172                    67209992.84
```

## Risk Score vs Generated Label

```sql
SELECT CASE WHEN RiskScore<.2 THEN 'Low' WHEN RiskScore<.5 THEN 'Moderate' WHEN RiskScore<.85 THEN 'Elevated' ELSE 'High' END AS risk_band,COUNT(*) claims,SUM(c.IsFraud) AS generated_positive_rows,ROUND(100.0*AVG(c.IsFraud),3) AS generated_positive_rate_pct FROM claim_scores s JOIN claims c USING(ClaimID) GROUP BY risk_band ORDER BY MIN(RiskScore);
```

Result rows: **4**

```text
risk_band  claims  generated_positive_rows  generated_positive_rate_pct
      Low  476537                     3829                        0.804
 Moderate   13564                     1401                       10.329
 Elevated    5760                     2210                       38.368
     High    4139                     4115                       99.420
```

## Highest Anomaly Score Claims

```sql
SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore FROM claims c JOIN claim_scores s USING(ClaimID) ORDER BY s.AnomalyScore DESC,c.BilledAmount DESC LIMIT 100;
```

Result rows: **100**

```text
 ClaimID HospitalID DiagnosisCode  BilledAmount  RiskScore  AnomalyScore
C0133594      H0451         I21.4    1037566.80   0.730154      1.000000
C0396375      H0308         A41.9    2424185.67   0.631467      0.999998
C0101672      H0193      S72.001A    1323104.17   0.690465      0.999996
C0435263      H0188         I21.4    1340905.34   0.724982      0.999994
C0006030      H0485         C18.9    2231517.58   0.286059      0.999991
C0484209      H0354      S72.001A    1250000.00   0.263510      0.999991
C0014042      H0569      S72.001A    1047649.22   0.053806      0.999987
C0480355      H0103         I50.9     801895.78   0.150636      0.999987
C0137368      H0175         I63.9    1095407.35   0.331651      0.999983
C0130085      H0207         I50.9     972195.58   0.345434      0.999983
C0324804      H0477         I63.9    1172105.41   0.575709      0.999980
C0269227      H0326         A41.9    1018802.67   0.322113      0.999978
```

## Anomaly Risk Disagreement

```sql
SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore FROM claims c JOIN claim_scores s USING(ClaimID) WHERE s.AnomalyScore>=.98 AND s.RiskScore<.50 ORDER BY s.AnomalyScore DESC,c.BilledAmount DESC LIMIT 100;
```

Result rows: **100**

```text
 ClaimID HospitalID DiagnosisCode  BilledAmount  RiskScore  AnomalyScore
C0006030      H0485         C18.9    2231517.58   0.286059      0.999991
C0484209      H0354      S72.001A    1250000.00   0.263510      0.999991
C0014042      H0569      S72.001A    1047649.22   0.053806      0.999987
C0480355      H0103         I50.9     801895.78   0.150636      0.999987
C0137368      H0175         I63.9    1095407.35   0.331651      0.999983
C0130085      H0207         I50.9     972195.58   0.345434      0.999983
C0269227      H0326         A41.9    1018802.67   0.322113      0.999978
C0127778      H0498         I63.9    1250000.00   0.189296      0.999975
C0461001      H0446         I63.9    1250000.00   0.096520      0.999972
C0431072      H0452      S72.001A    1250000.00   0.315542      0.999970
C0056286      H0372         I63.9    1237905.31   0.230955      0.999967
C0223774      H0092         C18.9    1761703.40   0.412544      0.999963
```

## Top Risk Claims

```sql
SELECT c.ClaimID,c.HospitalID,c.DiagnosisCode,c.BilledAmount,s.RiskScore,s.AnomalyScore,s.PotentialBilledExposure_085 FROM claims c JOIN claim_scores s USING(ClaimID) ORDER BY s.RiskScore DESC,c.BilledAmount DESC LIMIT 100;
```

Result rows: **100**

```text
 ClaimID HospitalID DiagnosisCode  BilledAmount  RiskScore  AnomalyScore  PotentialBilledExposure_085
C0496749      H0121         C18.9     402882.34   0.999815      0.971762                    402882.34
C0497679      H0109         N39.0      14003.59   0.999813      0.011000                     14003.59
C0497774      H0336         E11.9       4077.97   0.999810      0.704557                      4077.97
C0497035      H0343         C18.9     329331.55   0.999808      0.975330                    329331.55
C0497021      H0550         J18.9      19098.28   0.999807      0.179352                     19098.28
C0496327      H0196         M54.5       3704.34   0.999806      0.677444                      3704.34
C0496709      H0075         J18.9      17299.01   0.999791      0.741820                     17299.01
C0497902      H0459      S72.001A      57307.96   0.999787      0.692830                     57307.96
C0497854      H0036         C18.9     335170.25   0.999779      0.945382                    335170.25
C0497899      H0209         G45.9      14330.44   0.999776      0.722974                     14330.44
C0496839      H0132         C18.9     185658.65   0.999774      0.891926                    185658.65
C0496548      H0288         R07.9      21231.95   0.999772      0.239800                     21231.95
```

## Risk Score by Diagnosis

```sql
SELECT c.DiagnosisCode,COUNT(*) claims,ROUND(AVG(s.RiskScore),4) avg_risk_score,SUM(CASE WHEN s.RiskScore>=.85 THEN 1 ELSE 0 END) high_risk_claims,ROUND(SUM(s.PotentialBilledExposure_085),2) potential_billed_exposure_usd FROM claims c JOIN claim_scores s USING(ClaimID) GROUP BY c.DiagnosisCode ORDER BY avg_risk_score DESC;
```

Result rows: **16**

```text
DiagnosisCode  claims  avg_risk_score  high_risk_claims  potential_billed_exposure_usd
        J44.1   40374          0.0705               392                    16637299.35
        G45.9   23536          0.0704               181                     5982198.62
        R07.9   29938          0.0701               253                     5387395.01
        M54.5   39320          0.0700               336                     4567874.90
        J18.9   57627          0.0676               440                    17643609.48
     S72.001A   23431          0.0675               243                    33840676.89
        N39.0   41003          0.0668               328                     5910449.97
        E11.9   50661          0.0667               417                     6720050.18
       K35.80   18049          0.0663               152                     6505426.26
       M17.11   35849          0.0659               257                     6349670.67
        I50.9   41563          0.0657               324                    21592946.67
        N17.9   37519          0.0651               320                    19295353.07
```

## Risk and Anomaly Cross Tab

```sql
SELECT CASE WHEN RiskScore>=.85 THEN 'High risk' WHEN RiskScore>=.5 THEN 'Elevated risk' ELSE 'Below .50 risk' END AS risk_group,CASE WHEN AnomalyScore>=.98 THEN 'Top 2% anomaly' ELSE 'Other anomaly range' END AS anomaly_group,COUNT(*) claims FROM claim_scores GROUP BY risk_group,anomaly_group ORDER BY risk_group,anomaly_group;
```

Result rows: **6**

```text
    risk_group       anomaly_group  claims
Below .50 risk Other anomaly range  480987
Below .50 risk      Top 2% anomaly    9114
 Elevated risk Other anomaly range    4960
 Elevated risk      Top 2% anomaly     800
     High risk Other anomaly range    4052
     High risk      Top 2% anomaly      87
```

## High Risk Claims by Month

```sql
SELECT strftime('%Y-%m',c.AdmissionDate) AS claim_month,COUNT(*) AS high_risk_claims,ROUND(SUM(c.BilledAmount),2) AS billed_exposure_usd FROM claims c JOIN claim_scores s USING(ClaimID) WHERE s.RiskScore>=.85 GROUP BY claim_month ORDER BY claim_month;
```

Result rows: **37**

```text
claim_month  high_risk_claims  billed_exposure_usd
    2023-01                94           3672562.80
    2023-02               147           8453431.40
    2023-03               126           6253162.85
    2023-04                80           5733219.74
    2023-05                97           5017427.97
    2023-06               129           5800691.77
    2023-07               112           5356800.73
    2023-08               108           7633259.86
    2023-09               101           7195637.51
    2023-10               125           8687491.25
    2023-11                95           4613939.68
    2023-12               116           6843033.08
```
