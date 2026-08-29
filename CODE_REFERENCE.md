# Code Reference — PlaceMux Project

A running cheat sheet of every command used across the project, in plain English.
Add a new row under the right section whenever a new command shows up — keep the
same two-column format so it stays easy to scan.

**Format for new entries:** `| \`code\` | one-line plain-English explanation |`

---

## Loading data
| Code | What it does |
|---|---|
| `import pandas as pd` | Loads the pandas library, nicknamed `pd` |
| `pd.read_csv("path.csv")` | Reads a CSV file into a DataFrame (table) |

## Looking at data
| Code | What it does |
|---|---|
| `df.head()` | Shows the first 5 rows |
| `df.shape` | Shows (number of rows, number of columns) |
| `df.columns` | Lists all column names |
| `df.info()` | Shows column names, types, and non-missing counts |
| `df.describe()` | Shows min/max/average/etc for numeric columns |

## Selecting data
| Code | What it does |
|---|---|
| `df["col"]` | Selects a single column |
| `df[["col1", "col2"]]` | Selects multiple columns at once |

## Missing values & duplicates
| Code | What it does |
|---|---|
| `df.isna()` | True/False table marking missing values |
| `df.isna().sum()` | Counts missing values per column |
| `df.duplicated()` | True/False marking exact duplicate rows |
| `df.duplicated().sum()` | Counts how many duplicate rows exist |
| `df.drop_duplicates()` | Removes duplicate rows |
| `df["col"].fillna(value)` | Replaces missing values with something you choose |
| `df.dropna(subset=["col"])` | Removes rows missing values in specific columns |
| `df.drop(columns=["col"])` | Deletes an entire column |

## Grouping & summarizing
| Code | What it does |
|---|---|
| `df.groupby("col")["target"].mean()` | Averages `target`, split by groups in `col` |
| `df.groupby(["col1","col2"])["target"].mean()` | Same, but split by two columns combined |
| `.agg(["mean", "count"])` | Gets multiple stats at once instead of just one |

## Cleaning & transforming
| Code | What it does |
|---|---|
| `df["col"].astype(bool)` | Converts a column to a new data type |
| `df["col"].astype(str).str.strip().str.lower()` | Converts to text, trims spaces, lowercases |
| `df["new_col"] = df["a"] + df["b"]` | Creates a new column from math on existing ones |
| `df["new_col"] = df["col"] == value` | Creates a True/False column from a condition |
| `df.to_csv("path.csv", index=False)` | Saves the DataFrame to a new CSV file |

## Charts
| Code | What it does |
|---|---|
| `import matplotlib.pyplot as plt` | Loads the base charting library |
| `import seaborn as sns` | Loads a friendlier charting library built on matplotlib |
| `df["col"].hist(bins=30)` | Draws a histogram |
| `sns.barplot(data=df, x=.., y=.., hue=..)` | Draws a grouped bar chart |
| `sns.scatterplot(data=df, x=.., y=.., hue=..)` | Draws a scatter plot |
| `plt.title("...")` | Adds a chart title |
| `plt.show()` | Displays the chart |

## Git (saving your work)
| Code | What it does |
|---|---|
| `git status` | Shows what's changed, staged, or committed |
| `git add filename` | Stages a file, marking it ready to save |
| `git commit -m "message"` | Saves a checkpoint with a description |
| `git push` | Uploads your commits to GitHub |

## New section template
When a whole new category of command shows up (e.g. merging tables, SQL, modeling),
copy this block, rename the heading, and start filling it in:

```
## <New category name>
| Code | What it does |
|---|---|

```

### Statistical Analysis
`from scipy import stats` — import SciPy statistical functions
`from statsmodels.stats.proportion import proportions_ztest` — two-proportion z-test
`from statsmodels.stats.proportion import proportion_effectsize` — standardized effect size for two proportions
`from statsmodels.stats.power import NormalIndPower` — power/sample-size analysis
`stats.norm.ppf(0.975)` — two-sided 95% normal critical value
`np.sqrt(...)` — calculate standard error
`pd.DataFrame({...})` — construct a results summary table
`plt.bar(...)` — create a categorical bar chart
`plt.text(...)` — add value labels to a chart

### Validation
`assert condition, "message"` — stop execution when a data-quality condition fails
`df["column"].unique()` — inspect unique values
`df["column"].value_counts()` — count categorical/binary outcomes
`df[["col1", "col2"]].isna().sum().sum()` — count missing values in selected columns
`df.duplicated().sum()` — count duplicate rows

