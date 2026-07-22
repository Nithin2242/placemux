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

## Day 5 — The Discovery Phase (EDA)
**Given:** Run exploratory data analysis using stats and visuals to discover 
structure, patterns, and surprises; produce a shortlist of candidate insights 
and follow-up questions.
**Done:** Plotted distributions for age, fare, and family_size; compared 
survival rates across sex (73.8% women vs 21.7% men) and class (1st: 63.3%, 
2nd: 50.6%, 3rd: 25.7%); combined sex+class group-by revealing 1st-class women 
at 96.7% survival vs 3rd-class men at 15.9% (the largest passenger group); 
explored age vs fare relationship via scatter plot; wrote four candidate 
insights with follow-up questions rather than causal claims, in eda.ipynb.
