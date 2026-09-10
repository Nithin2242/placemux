
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

JOB_EVENTS_FILE = BASE_DIR / "job_events_demo.csv"
COMPANY_EVENTS_FILE = BASE_DIR / "company_funnel_events_demo.csv"
APPLICATION_EVENTS_FILE = (
    BASE_DIR / "application_funnel_events_demo.csv"
)

OUTPUT_HTML = BASE_DIR / "liquidity_dashboard.html"
OUTPUT_JSON = BASE_DIR / "liquidity_dashboard_summary.json"
OUTPUT_CSV = BASE_DIR / "liquidity_dashboard_metrics.csv"


# ============================================================
# REQUIRED FILE VALIDATION
# ============================================================

required_files = [
    JOB_EVENTS_FILE,
    COMPANY_EVENTS_FILE,
    APPLICATION_EVENTS_FILE,
]

missing_files = [
    str(path)
    for path in required_files
    if not path.exists()
]

if missing_files:

    raise FileNotFoundError(
        "Required Phase 2 demo files are missing:\n"
        + "\n".join(missing_files)
    )


# ============================================================
# LOAD DATA
# ============================================================

job_events = pd.read_csv(
    JOB_EVENTS_FILE,
    parse_dates=["event_timestamp"],
)

company_events = pd.read_csv(
    COMPANY_EVENTS_FILE,
    parse_dates=["event_timestamp"],
)

application_events = pd.read_csv(
    APPLICATION_EVENTS_FILE,
    parse_dates=["event_timestamp"],
)


# ============================================================
# APPROVED EVENT SETS
# ============================================================

JOB_EVENT_NAMES = {
    "job_post_started",
    "job_post_completed",
    "job_post_published",
    "job_post_edited",
    "job_post_paused",
    "job_post_reactivated",
    "job_post_closed",
}

COMPANY_EVENT_NAMES = {
    "search_performed",
    "search_result_viewed",
    "listing_viewed",
    "company_contact_started",
    "engagement_started",
    "match_created",
    "outcome_recorded",
}

APPLICATION_EVENT_NAMES = {
    "application_started",
    "application_submitted",
    "application_reviewed",
    "application_shortlisted",
    "application_next_step",
    "application_selected",
    "application_outcome_recorded",
}


# ============================================================
# VALIDATION HELPERS
# ============================================================

def basic_validation(
    df: pd.DataFrame,
    approved_events: set[str],
    id_columns: list[str],
) -> dict[str, int]:

    results = {
        "total_events": int(len(df)),
        "duplicate_event_ids": int(
            df["event_id"].duplicated().sum()
        ),
        "missing_event_ids": int(
            df["event_id"].isna().sum()
        ),
        "invalid_event_names": int(
            (~df["event_name"].isin(approved_events))
            .sum()
        ),
        "invalid_timestamps": int(
            df["event_timestamp"].isna().sum()
        ),
    }

    for column in id_columns:

        results[f"missing_{column}"] = int(
            df[column].isna().sum()
        )

    return results


job_validation = basic_validation(
    job_events,
    JOB_EVENT_NAMES,
    ["job_id", "seller_id"],
)

company_validation = basic_validation(
    company_events,
    COMPANY_EVENT_NAMES,
    ["company_id"],
)

application_validation = basic_validation(
    application_events,
    APPLICATION_EVENT_NAMES,
    [
        "application_id",
        "candidate_id",
        "company_id",
    ],
)


# ============================================================
# JOB SUPPLY
# ============================================================

active_sellers = job_events[
    job_events["seller_id"].notna()
]["seller_id"].nunique()


job_published = (
    job_events[
        job_events["event_name"]
        == "job_post_published"
    ]
    .drop_duplicates("job_id")
    .copy()
)

job_closed = (
    job_events[
        job_events["event_name"]
        == "job_post_closed"
    ]
    .drop_duplicates("job_id")
    .copy()
)

job_paused = (
    job_events[
        job_events["event_name"]
        == "job_post_paused"
    ]
    .drop_duplicates("job_id")
    .copy()
)

job_reactivated = (
    job_events[
        job_events["event_name"]
        == "job_post_reactivated"
    ]
    .drop_duplicates("job_id")
    .copy()
)


# Determine latest state per job.
job_states: dict[str, str] = {}

for job_id, group in job_events.groupby("job_id"):

    group = group.sort_values(
        ["event_timestamp", "event_id"]
    )

    state = "created"

    for event_name in group["event_name"]:

        if event_name == "job_post_published":
            state = "active"

        elif event_name == "job_post_paused":
            state = "paused"

        elif event_name == "job_post_reactivated":
            state = "active"

        elif event_name == "job_post_closed":
            state = "closed"

    job_states[job_id] = state


active_jobs = sum(
    state == "active"
    for state in job_states.values()
)


# ============================================================
# COMPANY / BUYER ACTIVITY
# ============================================================

searches = company_events[
    company_events["event_name"]
    == "search_performed"
]

result_views = company_events[
    company_events["event_name"]
    == "search_result_viewed"
]

listing_views = company_events[
    company_events["event_name"]
    == "listing_viewed"
]

contacts = company_events[
    company_events["event_name"]
    == "company_contact_started"
]

engagements = company_events[
    company_events["event_name"]
    == "engagement_started"
]

company_matches = company_events[
    company_events["event_name"]
    == "match_created"
]

company_outcomes = company_events[
    company_events["event_name"]
    == "outcome_recorded"
]


active_buyers = searches[
    "company_id"
].nunique()


search_count = searches[
    "search_id"
].nunique()


result_count = len(
    result_views
)

listing_count = len(
    listing_views
)

contact_count = len(
    contacts
)

engagement_count = len(
    engagements
)

company_match_count = len(
    company_matches
)

company_outcome_count = len(
    company_outcomes
)


# ============================================================
# APPLICATION ACTIVITY
# ============================================================

def distinct_applications(
    event_name: str,
) -> int:

    return application_events.loc[
        application_events["event_name"]
        == event_name,
        "application_id",
    ].nunique()


applications_started = distinct_applications(
    "application_started"
)

applications_submitted = distinct_applications(
    "application_submitted"
)

applications_reviewed = distinct_applications(
    "application_reviewed"
)

applications_shortlisted = distinct_applications(
    "application_shortlisted"
)

applications_next_step = distinct_applications(
    "application_next_step"
)

applications_selected = distinct_applications(
    "application_selected"
)

application_outcomes = distinct_applications(
    "application_outcome_recorded"
)

application_matches = applications_selected * 0

# Match count from the application funnel is intentionally derived
# from the application event stream's selection/match-ready stage.
# Day 24 generated a selection stage but no dedicated match event.
# Therefore the company-side match stream is used for marketplace
# liquidity matching while application outcome progression remains
# application-driven.


# ============================================================
# RATE HELPER
# ============================================================

def rate(
    numerator: float,
    denominator: float,
) -> float:

    if denominator == 0:
        return 0.0

    return numerator / denominator * 100


buyer_seller_ratio = (
    active_buyers / active_sellers
    if active_sellers
    else 0.0
)

jobs_per_seller = (
    active_jobs / active_sellers
    if active_sellers
    else 0.0
)

search_to_result = rate(
    result_count,
    search_count,
)

result_to_listing = rate(
    listing_count,
    result_count,
)

listing_to_contact = rate(
    contact_count,
    listing_count,
)

contact_to_application = rate(
    applications_started,
    contact_count,
)

application_submission = rate(
    applications_submitted,
    applications_started,
)

application_to_match = rate(
    company_match_count,
    applications_submitted,
)

match_to_outcome = rate(
    company_outcome_count,
    company_match_count,
)

marketplace_success = rate(
    application_outcomes,
    applications_submitted,
)


# ============================================================
# COMBINED VALIDATION
# ============================================================

validation_checks = {
    "job_events": job_validation,
    "company_events": company_validation,
    "application_events": application_validation,
}

all_validation_values = []

for dataset_results in validation_checks.values():

    for key, value in dataset_results.items():

        if key != "total_events":
            all_validation_values.append(
                value
            )

combined_validation_passed = all(
    value == 0
    for value in all_validation_values
)


total_events = (
    len(job_events)
    + len(company_events)
    + len(application_events)
)


# ============================================================
# HEALTH SIGNAL
# ============================================================

# Demonstration thresholds; these are intentionally simple and
# should be calibrated against production baselines.

watch_conditions = 0

if search_to_result < 85:
    watch_conditions += 1

if listing_to_contact < 35:
    watch_conditions += 1

if marketplace_success < 8:
    watch_conditions += 1

if active_jobs < active_buyers:
    watch_conditions += 1


if watch_conditions >= 2:

    health_status = "RISK"

elif watch_conditions == 1:

    health_status = "WATCH"

else:

    health_status = "HEALTHY"


# ============================================================
# DAILY COMBINED TREND
# ============================================================

job_daily = (
    job_events[
        job_events["event_name"]
        == "job_post_completed"
    ]
    .assign(
        date=lambda df:
        df["event_timestamp"].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")
    .size()
    .rename("jobs_posted")
)

search_daily = (
    searches.assign(
        date=lambda df:
        df["event_timestamp"].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")
    .size()
    .rename("searches")
)

application_daily = (
    application_events[
        application_events["event_name"]
        == "application_submitted"
    ]
    .assign(
        date=lambda df:
        df["event_timestamp"].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")
    .size()
    .rename("applications_submitted")
)

trend = pd.concat(
    [
        job_daily,
        search_daily,
        application_daily,
    ],
    axis=1,
).fillna(0)

trend = trend.reset_index()

trend.columns = [
    "date",
    "jobs_posted",
    "searches",
    "applications_submitted",
]

trend = trend.sort_values(
    "date"
)


# ============================================================
# METRIC TABLE
# ============================================================

metrics = [
    ("Active Buyers", active_buyers),
    ("Active Sellers", active_sellers),
    ("Active Jobs", active_jobs),
    (
        "Buyer-to-Seller Ratio",
        round(buyer_seller_ratio, 2),
    ),
    (
        "Jobs per Active Seller",
        round(jobs_per_seller, 2),
    ),
    (
        "Search-to-Result Rate",
        round(search_to_result, 1),
    ),
    (
        "Result-to-Listing Rate",
        round(result_to_listing, 1),
    ),
    (
        "Listing-to-Contact Rate",
        round(listing_to_contact, 1),
    ),
    (
        "Contact-to-Application Rate",
        round(contact_to_application, 1),
    ),
    (
        "Application Submission Rate",
        round(application_submission, 1),
    ),
    (
        "Application-to-Match Rate",
        round(application_to_match, 1),
    ),
    (
        "Match-to-Outcome Rate",
        round(match_to_outcome, 1),
    ),
    (
        "Marketplace Success Rate",
        round(marketplace_success, 1),
    ),
]

metrics_df = pd.DataFrame(
    metrics,
    columns=[
        "metric",
        "value",
    ],
)

metrics_df.to_csv(
    OUTPUT_CSV,
    index=False,
)


# ============================================================
# SUMMARY JSON
# ============================================================

summary = {
    "total_events": total_events,
    "active_buyers": int(active_buyers),
    "active_sellers": int(active_sellers),
    "active_jobs": int(active_jobs),
    "buyer_to_seller_ratio": round(
        buyer_seller_ratio,
        2,
    ),
    "jobs_per_active_seller": round(
        jobs_per_seller,
        2,
    ),
    "searches": int(search_count),
    "result_views": int(result_count),
    "listing_views": int(listing_count),
    "contacts": int(contact_count),
    "applications_started": int(
        applications_started
    ),
    "applications_submitted": int(
        applications_submitted
    ),
    "matches": int(
        company_match_count
    ),
    "successful_outcomes": int(
        company_outcome_count
    ),
    "marketplace_success_rate": round(
        marketplace_success,
        1,
    ),
    "health_status": health_status,
    "validation_passed": bool(
        combined_validation_passed
    ),
    "validation": validation_checks,
}

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        summary,
        file,
        indent=2,
    )


# ============================================================
# HTML DATA
# ============================================================

trend_data = trend.to_dict(
    orient="records"
)


trend_json = json.dumps(
    trend_data,
    default=str,
)


# ============================================================
# HTML DASHBOARD
# ============================================================

health_class = (
    "healthy"
    if health_status == "HEALTHY"
    else "watch"
    if health_status == "WATCH"
    else "risk"
)

validation_class = (
    "pass"
    if combined_validation_passed
    else "fail"
)


html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
PlaceMux — Marketplace Liquidity Dashboard
</title>


<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f5f7fa;
    color: #1f2937;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
}}

.container {{
    max-width: 1280px;
    margin: auto;
    padding: 30px;
}}

h1 {{
    font-size: 36px;
    margin-bottom: 5px;
}}

.subtitle {{
    color: #64748b;
    margin-bottom: 28px;
}}

.section {{
    background: white;
    border-radius: 14px;
    padding: 24px;
    margin-top: 22px;
    box-shadow:
        0 3px 12px rgba(0,0,0,.07);
}}

.section h2 {{
    margin-top: 0;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);
    gap: 15px;
}}

.card {{
    background: white;
    border-radius: 14px;
    padding: 20px;
    box-shadow:
        0 3px 12px rgba(0,0,0,.07);
}}

.card h3 {{
    margin: 0;
    font-size: 13px;
    color: #64748b;
}}

.value {{
    margin-top: 8px;
    font-size: 29px;
    font-weight: 700;
}}

.health {{
    display: inline-block;
    padding: 8px 15px;
    border-radius: 22px;
    font-weight: 700;
}}

.healthy {{
    background: #dcfce7;
    color: #166534;
}}

.watch {{
    background: #fef3c7;
    color: #92400e;
}}

.risk {{
    background: #fee2e2;
    color: #991b1b;
}}

.validation {{
    display: inline-block;
    padding: 8px 14px;
    border-radius: 20px;
    font-weight: 700;
}}

.pass {{
    background: #dcfce7;
    color: #166534;
}}

.fail {{
    background: #fee2e2;
    color: #991b1b;
}}

.metric-grid {{
    display: grid;
    grid-template-columns:
        repeat(3, 1fr);
    gap: 13px;
}}

.metric {{
    background: #f8fafc;
    padding: 16px;
    border-radius: 10px;
}}

.funnel {{
    display: flex;
    flex-direction: column;
    gap: 11px;
}}

.stage {{
    background: #f8fafc;
    padding: 14px;
    border-radius: 10px;
}}

.stage-header {{
    display: flex;
    justify-content: space-between;
    font-weight: 700;
}}

.bar {{
    height: 13px;
    margin-top: 8px;
    background: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}}

.fill {{
    height: 100%;
    background: #64748b;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    text-align: left;
    padding: 11px;
    border-bottom:
        1px solid #e5e7eb;
}}

th {{
    color: #64748b;
}}

canvas {{
    width: 100%;
    height: 320px;
}}

.note {{
    padding: 14px;
    background: #f8fafc;
    border-radius: 10px;
    line-height: 1.5;
}}

code {{
    background: #f1f5f9;
    padding: 3px 6px;
    border-radius: 5px;
}}

@media (max-width: 950px) {{

    .grid {{
        grid-template-columns:
            repeat(2, 1fr);
    }}

    .metric-grid {{
        grid-template-columns:
            repeat(2, 1fr);
    }}
}}

@media (max-width: 600px) {{

    .container {{
        padding: 16px;
    }}

    .grid,
    .metric-grid {{
        grid-template-columns: 1fr;
    }}

    h1 {{
        font-size: 28px;
    }}
}}

</style>

</head>


<body>

<div class="container">


<h1>
Marketplace Liquidity Dashboard
</h1>

<div class="subtitle">

PlaceMux Phase 2 —
Marketplace Health Monitoring ·
Synthetic Demonstration Data

</div>


<!-- ===================================================== -->
<!-- HEALTH -->
<!-- ===================================================== -->

<div class="section">

<h2>
Marketplace Health
</h2>

<p>

Current demonstration status:

<span class="health {health_class}">
{health_status}
</span>

</p>

<p class="note">

Health is a rules-based demonstration signal combining
demand, supply, and conversion indicators.
Production thresholds should be calibrated from real marketplace
baselines.

</p>

</div>


<!-- ===================================================== -->
<!-- TOP KPIs -->
<!-- ===================================================== -->

<div class="grid">

<div class="card">

<h3>
Active Buyers
</h3>

<div class="value">
{active_buyers}
</div>

</div>


<div class="card">

<h3>
Active Sellers
</h3>

<div class="value">
{active_sellers}
</div>

</div>


<div class="card">

<h3>
Active Jobs
</h3>

<div class="value">
{active_jobs}
</div>

</div>


<div class="card">

<h3>
Buyer / Seller Ratio
</h3>

<div class="value">
{buyer_seller_ratio:.2f}
</div>

</div>


<div class="card">

<h3>
Jobs / Active Seller
</h3>

<div class="value">
{jobs_per_seller:.2f}
</div>

</div>


<div class="card">

<h3>
Searches
</h3>

<div class="value">
{search_count}
</div>

</div>


<div class="card">

<h3>
Applications Submitted
</h3>

<div class="value">
{applications_submitted}
</div>

</div>


<div class="card">

<h3>
Successful Outcomes
</h3>

<div class="value">
{application_outcomes}
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- DEMAND -->
<!-- ===================================================== -->

<div class="section">

<h2>
Demand & Discovery
</h2>

<div class="metric-grid">

<div class="metric">

<strong>
Searches
</strong>

<br>

{search_count}

</div>


<div class="metric">

<strong>
Result Views
</strong>

<br>

{result_count}

</div>


<div class="metric">

<strong>
Search → Result
</strong>

<br>

{search_to_result:.1f}%

</div>


<div class="metric">

<strong>
Listing Views
</strong>

<br>

{listing_count}

</div>


<div class="metric">

<strong>
Listing → Contact
</strong>

<br>

{listing_to_contact:.1f}%

</div>


<div class="metric">

<strong>
Contacts
</strong>

<br>

{contact_count}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- SUPPLY -->
<!-- ===================================================== -->

<div class="section">

<h2>
Supply
</h2>

<div class="metric-grid">

<div class="metric">

<strong>
Active Sellers
</strong>

<br>

{active_sellers}

</div>


<div class="metric">

<strong>
Active Jobs
</strong>

<br>

{active_jobs}

</div>


<div class="metric">

<strong>
Jobs / Seller
</strong>

<br>

{jobs_per_seller:.2f}

</div>


<div class="metric">

<strong>
Buyer / Seller Ratio
</strong>

<br>

{buyer_seller_ratio:.2f}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- FUNNEL -->
<!-- ===================================================== -->

<div class="section">

<h2>
Marketplace Conversion Funnel
</h2>

<div class="funnel">

<div class="stage">

<div class="stage-header">
<span>Searches</span>
<span>{search_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="width:100%"
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Result Views</span>
<span>{result_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            search_to_result
        }%
    "
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Listing Views</span>
<span>{listing_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            listing_count /
            max(search_count, 1) *
            100
        }%
    "
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Contacts</span>
<span>{contact_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            contact_count /
            max(search_count, 1) *
            100
        }%
    "
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Applications Submitted</span>
<span>{applications_submitted}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            applications_submitted /
            max(search_count, 1) *
            100
        }%
    "
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Matches</span>
<span>{company_match_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            company_match_count /
            max(search_count, 1) *
            100
        }%
    "
></div>

</div>

</div>


<div class="stage">

<div class="stage-header">
<span>Successful Outcomes</span>
<span>{company_outcome_count}</span>
</div>

<div class="bar">

<div
    class="fill"
    style="
        width:
        {
            company_outcome_count /
            max(search_count, 1) *
            100
        }%
    "
></div>

</div>

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- CONVERSION TABLE -->
<!-- ===================================================== -->

<div class="section">

<h2>
Liquidity Conversion Metrics
</h2>

<table>

<thead>

<tr>

<th>
Metric
</th>

<th>
Value
</th>

</tr>

</thead>

<tbody>

<tr>
<td>Search → Result</td>
<td>{search_to_result:.1f}%</td>
</tr>

<tr>
<td>Result → Listing</td>
<td>{result_to_listing:.1f}%</td>
</tr>

<tr>
<td>Listing → Contact</td>
<td>{listing_to_contact:.1f}%</td>
</tr>

<tr>
<td>Contact → Application</td>
<td>{contact_to_application:.1f}%</td>
</tr>

<tr>
<td>Application Submission</td>
<td>{application_submission:.1f}%</td>
</tr>

<tr>
<td>Application → Match</td>
<td>{application_to_match:.1f}%</td>
</tr>

<tr>
<td>Match → Outcome</td>
<td>{match_to_outcome:.1f}%</td>
</tr>

<tr>
<td>Marketplace Success</td>
<td>{marketplace_success:.1f}%</td>
</tr>

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- TREND -->
<!-- ===================================================== -->

<div class="section">

<h2>
Marketplace Activity Over Time
</h2>

<canvas id="trendChart"></canvas>

</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Instrumentation Validation
</h2>

<p>

Validation status:

<span class="validation {validation_class}">

{"PASS" if combined_validation_passed else "FAIL"}

</span>

</p>


<div class="metric-grid">

<div class="metric">

<strong>
Total Events
</strong>

<br>

{total_events}

</div>


<div class="metric">

<strong>
Job Event Duplicates
</strong>

<br>

{job_validation["duplicate_event_ids"]}

</div>


<div class="metric">

<strong>
Company Event Duplicates
</strong>

<br>

{company_validation["duplicate_event_ids"]}

</div>


<div class="metric">

<strong>
Application Event Duplicates
</strong>

<br>

{application_validation["duplicate_event_ids"]}

</div>


<div class="metric">

<strong>
Job Missing IDs
</strong>

<br>

{job_validation["missing_job_id"]}

</div>


<div class="metric">

<strong>
Application Missing IDs
</strong>

<br>

{application_validation["missing_application_id"]}

</div>


</div>

</div>


<!-- ===================================================== -->
<!-- DEFINITIONS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Source & Definitions
</h2>

<p>

<strong>
Source:
</strong>

Synthetic Phase 2 event streams generated for Days 22, 23, and 24.

</p>

<p>

<strong>
Active Buyers:
</strong>

Distinct companies with valid search activity.

</p>

<p>

<strong>
Active Sellers:
</strong>

Distinct sellers represented in valid job-post activity.

</p>

<p>

<strong>
Active Jobs:
</strong>

Jobs whose latest validated lifecycle state is active.

</p>

<p>

<strong>
Important:
</strong>

The current streams are separate synthetic demonstrations.
Cross-stream metrics such as Contact → Application are aggregate
directional indicators. A production implementation should use shared
journey identifiers for exact cohort conversion.

</p>

</div>


</div>


<script>

const data =
{trend_json};

const canvas =
document.getElementById(
    "trendChart"
);

const ctx =
canvas.getContext("2d");


function drawChart() {{

    const width =
        canvas.clientWidth || 1100;

    const height = 320;

    const dpr =
        window.devicePixelRatio || 1;

    canvas.width =
        width * dpr;

    canvas.height =
        height * dpr;

    ctx.scale(
        dpr,
        dpr
    );

    const padding = 45;

    const chartWidth =
        width - padding * 2;

    const chartHeight =
        height - padding * 2;


    const maxValue =
        Math.max(
            ...data.flatMap(
                row => [
                    Number(
                        row.jobs_posted
                    ),
                    Number(
                        row.searches
                    ),
                    Number(
                        row.applications_submitted
                    )
                ]
            )
        );


    function x(index) {{

        return padding +
            index *
            chartWidth /
            Math.max(
                data.length - 1,
                1
            );

    }}


    function y(value) {{

        return height -
            padding -
            value /
            Math.max(
                maxValue,
                1
            ) *
            chartHeight;

    }}


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    // Axes

    ctx.beginPath();

    ctx.moveTo(
        padding,
        padding
    );

    ctx.lineTo(
        padding,
        height - padding
    );

    ctx.lineTo(
        width - padding,
        height - padding
    );

    ctx.stroke();


    function drawSeries(
        key
    ) {{

        ctx.beginPath();


        data.forEach(
            (row, index) => {{

                const px =
                    x(index);

                const py =
                    y(
                        Number(
                            row[key]
                        )
                    );


                if (index === 0) {{

                    ctx.moveTo(
                        px,
                        py
                    );

                }} else {{

                    ctx.lineTo(
                        px,
                        py
                    );

                }}

            }}
        );


        ctx.stroke();

    }}


    drawSeries(
        "jobs_posted"
    );

    drawSeries(
        "searches"
    );

    drawSeries(
        "applications_submitted"
    );

}}


drawChart();

window.addEventListener(
    "resize",
    drawChart
);

</script>

</body>

</html>
"""


OUTPUT_HTML.write_text(
    html,
    encoding="utf-8",
)


# ============================================================
# TERMINAL OUTPUT
# ============================================================

print("=" * 65)
print("DAY 25 — MARKETPLACE LIQUIDITY DASHBOARD")
print("=" * 65)

print(
    f"Total events              : {total_events:,}"
)

print(
    f"Active buyers             : {active_buyers:,}"
)

print(
    f"Active sellers            : {active_sellers:,}"
)

print(
    f"Active jobs               : {active_jobs:,}"
)

print(
    f"Buyer/Seller ratio        : "
    f"{buyer_seller_ratio:.2f}"
)

print(
    f"Jobs per active seller    : "
    f"{jobs_per_seller:.2f}"
)

print(
    f"Searches                  : {search_count:,}"
)

print(
    f"Listings                  : {listing_count:,}"
)

print(
    f"Contacts                  : {contact_count:,}"
)

print(
    f"Applications submitted    : "
    f"{applications_submitted:,}"
)

print(
    f"Matches                   : "
    f"{company_match_count:,}"
)

print(
    f"Successful outcomes       : "
    f"{company_outcome_count:,}"
)

print(
    f"Marketplace success       : "
    f"{marketplace_success:.1f}%"
)

print(
    f"Marketplace health        : "
    f"{health_status}"
)

print()
print("VALIDATION")
print("-" * 65)

print(
    f"Job events duplicates     : "
    f"{job_validation['duplicate_event_ids']}"
)

print(
    f"Company event duplicates  : "
    f"{company_validation['duplicate_event_ids']}"
)

print(
    f"Application duplicates    : "
    f"{application_validation['duplicate_event_ids']}"
)

print(
    f"Job invalid event names   : "
    f"{job_validation['invalid_event_names']}"
)

print(
    f"Company invalid names     : "
    f"{company_validation['invalid_event_names']}"
)

print(
    f"Application invalid names : "
    f"{application_validation['invalid_event_names']}"
)

print(
    f"Validation status         : "
    f"{'PASS' if combined_validation_passed else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 65)

print(OUTPUT_HTML)
print(OUTPUT_JSON)
print(OUTPUT_CSV)