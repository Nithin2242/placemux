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


## Day 7 — Baseline Report Aggregation
**Given:** Aggregate the cleaned data into a baseline reporting layer — the 
standard metrics the business tracks every period; deliver a baseline report 
and a metric dictionary with definitions and sources. Scored on 5 criteria 
including real-data correctness, live verification, and edge-case handling.
**Done:** Defined 6 core metrics precisely before computing them (total 
passengers, overall survival rate, survival by class, survival by sex, 
average fare, average age), each with an explicit aggregation grain. Built 
deterministic pandas aggregations in baseline.ipynb. Validated the row count 
against Day 2's known duplicate count using an assert statement rather than 
trusting the number blindly. Checked for edge cases (negative/zero fares). 
Recorded every metric in a metric dictionary with definition, grain, source, 
and value.
**Notable issues resolved:** The validation assert caught a real bug — the 
row count kept coming back wrong (778, then 889, then 784) instead of the 
expected value. Root-caused it to transform.ipynb's cell order: duplicate 
removal was running after age imputation and after dropping the deck column, 
which meant rows that were genuinely distinct in the raw data were being 
merged as "duplicates" once distinguishing information had already been 
altered or removed. Fixed by moving deduplication to run immediately after 
loading the raw CSV, before any other transformation — and cleaned up several 
leftover duplicate `drop_duplicates()` cells left over from earlier edits, 
which were silently re-running and overwriting the fix. Also caught a math 
error in the validation itself: the original assert expected 784 rows but 
never accounted for the 2 rows later dropped for missing embarked/embark_town 
— corrected the expected value to 782 (891 − 107 duplicates − 2 missing 
embarked rows), which is the true final row count. This was the most 
significant reproducibility bug of the project so far, and directly validates 
why the brief's "validate totals against a known reference" step exists — 
without it, an incorrect baseline would have silently propagated into every 
later day's work.

## Day 8 — The Executive Insight
**Given:** Distil the baseline into 3-5 executive-level metrics with current 
value, benchmark, and "so what" for each; highlight the single most important 
finding; recommend one action.
**Done:** Selected 4 decision-relevant metrics (overall survival, survival by 
class, survival by sex, and 3rd-class men specifically) from the Day 7 
baseline; built a one-page summary table with a "so what" per row; highlighted 
3rd-class men (15.8% survival, worst group on the ship) as the single most 
important finding; recommended proportional lifeboat access across cabin 
classes with an estimated impact of 70+ additional survivors had access been 
equalized; built one annotated horizontal bar chart benchmarked against the 
overall average, in exec_summary.ipynb.


## Day 9 — Trend Forecasting
**Given:** Forecast a key trend forward using historical patterns, with 
validation error against a baseline and clearly shown uncertainty.
**Done:** Since the Titanic dataset has no time dimension, substituted a 
genuine time-series dataset (atmospheric CO2, bundled in statsmodels — no 
download needed). Visualized trend and yearly seasonality; split cleanly by 
time (no shuffling) into train (1958-1999) and a 24-month validation holdout 
(2000-2001); built a seasonal naive baseline; fit a SARIMA model; compared 
both by MAE (naive: 1.882 ppm, SARIMA: 0.350 ppm — 81.4% improvement); 
produced forecasts with 95% confidence intervals shown visually rather than 
as a single number; documented assumptions and where the forecast is least 
reliable, in forecast.ipynb.
**Notable issues resolved:** Recognized early that the primary project dataset 
was structurally incompatible with this task (no time dimension) rather than 
forcing a workaround, and substituted an appropriate dataset instead — same 
approach used successfully on Day 1.


## Day 10 — Comparative Insights
**Given:** Produce comparative insights identifying which segments drive the 
overall result, normalizing for group size and checking for Simpson's Paradox 
before concluding.
**Done:** Compared survival rate by port of embarkation (Cherbourg 58.1%, 
Southampton 37.1%, Queenstown 33.9%, vs 41.0% overall), always shown alongside 
group counts. Controlled for passenger class by adding it as a second grouping 
variable and checking the class composition per port. Found Cherbourg's 
advantage is partly explained by carrying more 1st-class passengers (53.5% 
vs Southampton's 22.4%), but confirmed no reversal occurs — Cherbourg 
out-survives Southampton within every class group too, ruling out a full 
Simpson's Paradox while identifying a genuine, partially class-independent 
port effect, in comparative.ipynb.
**Notable issues resolved:** None — pipeline and validated dataset from Day 7 
onward worked cleanly throughout.


## Day 12 — Executive Dashboarding
**Given:** Build a working executive dashboard wired to defined metrics, with 
filters and freshness indicators, demonstrable live on real data.
**Done:** Built a Streamlit dashboard (app.py) showing data source and last-
updated timestamp at the top; three headline metric tiles (overall survival 
rate, worst-performing class, passenger count) each with hover-help 
definitions; live multi-select filters for class, sex, and port that update 
every tile and chart in real time; three breakdown charts all benchmarked 
against the same unfiltered overall average line for consistency; tested live 
by filtering to 3rd-class men and confirming the dashboard reproduces the 
15.8% survival rate finding from Day 8 without any code changes.
**Notable issues resolved:** Streamlit was launching under a different global 
Python 3.11 install instead of the project's venv (Python 3.14), causing a 
seaborn ModuleNotFoundError despite seaborn being correctly installed in the 
venv. Fixed by launching with `python3 -m streamlit run app.py` instead of the 
bare `streamlit` command, forcing it to use the active virtual environment's 
Python explicitly.