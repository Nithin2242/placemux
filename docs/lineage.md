# Data Lifecycle & Lineage — Titanic Project

## 1. Data sources
| Source | Update frequency | Notes |
|---|---|---|
| `data/titanic.csv` | Static — one-time snapshot, does not update | Public historical dataset, no live feed |

This project has exactly one data source. No other version of this data exists elsewhere in the project.

## 2. Flow diagram
See `docs/data_lifecycle.png` — raw CSV → DataFrame load → profiling/cleaning → analysis notebook → final report.

## 3. Source of truth per metric
| Metric | Source of truth |
|---|---|
| `survived`, `pclass`, `sex`, `age`, `sibsp`, `parch`, `fare`, `embarked`, `class`, `who`, `adult_male`, `deck`, `embark_town`, `alive`, `alone` | `data/titanic.csv` — the only copy of this data; no transformed or duplicate version exists elsewhere |

## 4. Transformations & ownership
| Stage | Transformation applied | Owner |
|---|---|---|
| Raw CSV | None — original file as provided | External (data source) |
| Ingestion | `pd.read_csv()` loads file into DataFrame, no changes to values | Nithin (analyst) |
| Profiling & cleaning | Missing-value counts, duplicate checks, distribution checks — no values altered yet, findings only | Nithin (analyst) |
| Analysis | Aggregate calculations (e.g. `.mean()`, `.shape`) computed directly from the DataFrame | Nithin (analyst) |
| Final report | Notebook outputs + written summaries | Nithin (analyst) |

## 5. Retention & privacy
- Dataset is public historical data; no personally identifiable information of living individuals.
- No privacy constraints apply.
- No deletion schedule required — data retained for the duration of the project.

## 6. Validated trace — example metric: average fare
1. Source: `fare` column in `data/titanic.csv`
2. Ingestion: loaded via `pd.read_csv("data/titanic.csv")` in `analysis.ipynb` and `profiling.ipynb`
3. Transformation: none applied to raw values
4. Calculation: `df['fare'].mean()` computed directly in `analysis.ipynb`
5. Reported value: ~32.20 (see Day 1 smoke test output)

This confirms the number in the report traces directly back to the raw file with no untracked intermediate steps.