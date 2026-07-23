## Day 1 — System Ingestion & Environment Setup
**Given:** Set up a reproducible Python environment and ingest a starter 
dataset so a notebook can run end-to-end.
**Done:** Created an isolated venv; installed and pinned pandas, numpy, 
matplotlib, jupyter, seaborn in requirements.txt; since no dataset or repo was 
provided, used the public Titanic dataset as a substitute; loaded it into 
analysis.ipynb with .shape, .columns, .head() printed; wrote a first-draft 
data dictionary; ran a smoke test (row count + mean); set up .gitignore, 
initialized git, committed and pushed to GitHub.
**Notable issues resolved:** Hit an SSL certificate error trying to download 
the dataset via Python — fixed by downloading via the browser instead and 
loading locally with pd.read_csv(); cleaned up a stray empty requirements.txt 
duplicate and an accidental nested git repo before the final commit; verified 
reproducibility via Restart Kernel + Run All.

## Day 2 — Pre-Project Data Profiling & Audit
**Given:** Profile the dataset for types, missingness, distributions, and 
duplicates; produce a prioritized data-quality issue list with proposed fixes.
**Done:** Ran df.info() and df.describe(); quantified and visualized missing 
values (deck 77.22%, age 19.87%, embarked/embark_town 0.22%); plotted 
histograms for age and fare to check distributions and skew; checked for 
duplicate rows and a unique ID column; spot-checked all categorical columns 
for inconsistent labels (found none); compiled a prioritized audit table with 
severity and fixes in profiling.ipynb.
**Notable issues resolved:** Initial audit note incorrectly claimed no 
duplicates existed when the code had actually found 107 duplicate rows (~12% 
of the dataset) — caught the mismatch between code output and written 
conclusion and corrected it before final commit; fixed an earlier commit that 
saved with 0 insertions due to the notebook not being saved first.

## Day 3 — The Data Lifecycle
**Given:** Map the end-to-end data lifecycle (source, flow, transformations, 
storage, retirement) and name the source of truth for each key metric.
**Done:** Documented the single data source (static Titanic CSV, confirmed no 
other version exists in the project); built a 5-stage flow diagram (raw 
source → ingestion → profiling/cleaning → analysis → final report), 
recreated in Excalidraw and saved as docs/data_lifecycle.png; wrote 
docs/lineage.md covering source of truth per metric, ownership per pipeline 
stage, retention/privacy notes, and a validated end-to-end trace of the 
average fare metric.
**Notable issues resolved:** Diagram file was initially saved with a typo'd 
filename (docs:data_lifecycle.png) — renamed and correctly placed in docs/ 
before the final commit.

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

## Day 6 — The Art of Data Storytelling
**Given:** Turn analysis into a clear narrative with a one-sentence takeaway 
and a concrete recommendation, structured for a busy decision-maker.
**Done:** Wrote the one-sentence takeaway before building any visual; selected 
a single annotated chart (survival by class and sex) as the minimum evidence 
needed; added a nuance section on family size; ended with a concrete 
recommendation on proportional lifeboat access and its expected impact. Kept 
the report short and led with the answer, not the methodology, in story.ipynb.

