## Day 4 — Data Transformations
**Given:** Clean and reshape the raw data into analysis-ready form via a 
documented, re-runnable transformation script.
**Done:** Coerced column types (survived → bool, pclass → category); 
standardized categorical text (stripped whitespace, lowercased); applied a 
documented missing-value strategy (age imputed with median + age_missing flag, 
deck dropped, 2 rows with missing embarked/embark_town dropped); removed 107 
duplicate rows with before/after row counts logged; derived family_size, 
is_alone, and fare_per_person for future analysis; saved cleaned dataset to 
data/titanic_cleaned.csv, raw file left untouched. All steps documented in 
transform.ipynb with a markdown transformation summary.