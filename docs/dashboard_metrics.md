# Dashboard Metric Dictionary — Day 20

| Metric | Definition | Source |
|---|---|---|
| Filtered Survival Rate | Mean of `survived` for passengers matching the active filters | `data/titanic_cleaned.csv` |
| Passengers Shown | Number of rows matching the active filters | `data/titanic_cleaned.csv` |
| Worst Class | Passenger class with the lowest observed survival rate in the filtered population | `pclass`, `survived` |
| Class Survival Gap | Difference between highest and lowest class survival rates in the filtered population | `pclass`, `survived` |
| Sex Survival Rate | Mean `survived` within each sex group | `sex`, `survived` |
| Port Survival Rate | Mean `survived` within each embarkation town | `embark_town`, `survived` |
| Worst Segment | Class × sex combination with the lowest observed survival rate | `pclass`, `sex`, `survived` |

## Interpretation Rules

- Survival rates are descriptive percentages.
- Filtered values describe only the currently selected population.
- Differences should be interpreted as associations.
- The dataset is historical observational data; dashboard results do not establish causation.