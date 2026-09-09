from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EVENTS_FILE = BASE_DIR / "job_events_demo.csv"
SUMMARY_FILE = BASE_DIR / "jobs_posted_summary.csv"
VALIDATION_FILE = BASE_DIR / "job_event_validation.json"
HTML_FILE = BASE_DIR / "jobs_posted_view.html"

RANDOM_SEED = 42

START_DATE = datetime(2026, 8, 1)
DAYS = 30

SELLERS = [f"S{n:03d}" for n in range(1, 31)]

CATEGORIES = [
    "Data Analyst",
    "Software Developer",
    "Business Analyst",
    "UI/UX Designer",
    "Digital Marketer",
]

LOCATIONS = [
    "Bengaluru",
    "Hyderabad",
    "Mumbai",
    "Pune",
    "Chennai",
]

APPROVED_EVENTS = {
    "job_post_started",
    "job_post_completed",
    "job_post_published",
    "job_post_edited",
    "job_post_paused",
    "job_post_reactivated",
    "job_post_closed",
}


# ============================================================
# 1. GENERATE SYNTHETIC MARKETPLACE EVENTS
# ============================================================

random.seed(RANDOM_SEED)

events = []

event_counter = 1
job_counter = 1


def add_event(
    event_name: str,
    timestamp: datetime,
    seller_id: str,
    job_id: str,
    category: str,
    location: str,
    session_id: str,
    extra: dict | None = None,
) -> None:
    """Append one marketplace event."""

    global event_counter

    event = {
        "event_id": f"E{event_counter:06d}",
        "event_name": event_name,
        "event_timestamp": timestamp.isoformat(),
        "seller_id": seller_id,
        "job_id": job_id,
        "session_id": session_id,
        "source": "synthetic_demo",
        "platform": random.choice(["web", "mobile"]),
        "event_version": "1.0",
        "job_category": category,
        "location": location,
    }

    if extra:
        event.update(extra)

    events.append(event)

    event_counter += 1


for day_offset in range(DAYS):

    current_day = START_DATE + timedelta(days=day_offset)

    # Different volume by weekday/weekend to make the trend realistic.
    weekday = current_day.weekday()

    if weekday < 5:
        jobs_today = random.randint(8, 12)
    else:
        jobs_today = random.randint(5, 8)

    for _ in range(jobs_today):

        # IMPORTANT:
        # Each iteration creates a NEW job_id.
        job_id = f"J{job_counter:04d}"
        seller_id = random.choice(SELLERS)
        category = random.choice(CATEGORIES)
        location = random.choice(LOCATIONS)
        session_id = f"SESS_{job_id}"

        started_at = current_day + timedelta(
            hours=random.randint(8, 17),
            minutes=random.randint(0, 59),
        )

        completed_at = started_at + timedelta(
            minutes=random.randint(5, 45)
        )

        published_at = completed_at + timedelta(
            minutes=random.randint(5, 120)
        )

        # ----------------------------------------------------
        # STARTED
        # ----------------------------------------------------

        add_event(
            "job_post_started",
            started_at,
            seller_id,
            job_id,
            category,
            location,
            session_id,
        )

        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        add_event(
            "job_post_completed",
            completed_at,
            seller_id,
            job_id,
            category,
            location,
            session_id,
            {
                "skill_count": random.randint(2, 7),
            },
        )

        # ----------------------------------------------------
        # PUBLICATION
        # ----------------------------------------------------

        is_published = random.random() < 0.92

        if is_published:

            add_event(
                "job_post_published",
                published_at,
                seller_id,
                job_id,
                category,
                location,
                session_id,
                {
                    "publication_status": "published",
                },
            )

            # ------------------------------------------------
            # OPTIONAL EDIT
            # ------------------------------------------------

            if random.random() < 0.20:

                edit_time = published_at + timedelta(
                    minutes=random.randint(30, 300)
                )

                add_event(
                    "job_post_edited",
                    edit_time,
                    seller_id,
                    job_id,
                    category,
                    location,
                    session_id,
                    {
                        "changed_fields": random.choice(
                            [
                                "skills",
                                "description",
                                "location",
                                "salary",
                            ]
                        )
                    },
                )

            # ------------------------------------------------
            # OPTIONAL PAUSE / REACTIVATE
            # ------------------------------------------------

            if random.random() < 0.10:

                pause_time = published_at + timedelta(
                    days=random.randint(1, 4)
                )

                add_event(
                    "job_post_paused",
                    pause_time,
                    seller_id,
                    job_id,
                    category,
                    location,
                    session_id,
                    {
                        "pause_reason": random.choice(
                            [
                                "temporary_hold",
                                "seller_review",
                                "low_response",
                            ]
                        )
                    },
                )

                reactivate_time = pause_time + timedelta(
                    days=random.randint(1, 3)
                )

                add_event(
                    "job_post_reactivated",
                    reactivate_time,
                    seller_id,
                    job_id,
                    category,
                    location,
                    session_id,
                )

            # ------------------------------------------------
            # OPTIONAL CLOSE
            # ------------------------------------------------

            if random.random() < 0.30:

                close_time = published_at + timedelta(
                    days=random.randint(2, 15)
                )

                add_event(
                    "job_post_closed",
                    close_time,
                    seller_id,
                    job_id,
                    category,
                    location,
                    session_id,
                    {
                        "close_reason": random.choice(
                            [
                                "position_filled",
                                "seller_closed",
                                "expired",
                            ]
                        )
                    },
                )

        # CRITICAL:
        # Move to the next job after the current job is finished.
        job_counter += 1


events_df = pd.DataFrame(events)

events_df["event_timestamp"] = pd.to_datetime(
    events_df["event_timestamp"]
)

events_df = events_df.sort_values(
    ["job_id", "event_timestamp", "event_id"]
).reset_index(drop=True)

events_df.to_csv(
    EVENTS_FILE,
    index=False,
)


# ============================================================
# 2. EVENT VALIDATION
# ============================================================

validation = {}

validation["total_events"] = int(len(events_df))

validation["invalid_event_names"] = int(
    (~events_df["event_name"].isin(APPROVED_EVENTS)).sum()
)

validation["missing_event_id"] = int(
    events_df["event_id"].isna().sum()
)

validation["duplicate_event_ids"] = int(
    events_df["event_id"].duplicated().sum()
)

validation["missing_job_id"] = int(
    events_df["job_id"].isna().sum()
)

seller_events = events_df[
    events_df["event_name"].isin(
        [
            "job_post_started",
            "job_post_completed",
            "job_post_edited",
            "job_post_paused",
            "job_post_reactivated",
            "job_post_closed",
        ]
    )
]

validation["missing_seller_id"] = int(
    seller_events["seller_id"].isna().sum()
)

validation["invalid_timestamps"] = int(
    events_df["event_timestamp"].isna().sum()
)


# ============================================================
# LIFECYCLE VALIDATION
# ============================================================

lifecycle_issues: list[str] = []

for job_id, group in events_df.groupby("job_id"):

    group = group.sort_values(
        ["event_timestamp", "event_id"]
    )

    names = group["event_name"].tolist()

    # Published requires completed.
    if (
        "job_post_published" in names
        and "job_post_completed" not in names
    ):
        lifecycle_issues.append(
            f"{job_id}: published_without_completed"
        )

    # Closed requires published.
    if (
        "job_post_closed" in names
        and "job_post_published" not in names
    ):
        lifecycle_issues.append(
            f"{job_id}: closed_without_published"
        )

    # Reactivation requires pause.
    if (
        "job_post_reactivated" in names
        and "job_post_paused" not in names
    ):
        lifecycle_issues.append(
            f"{job_id}: reactivated_without_paused"
        )

    # Check chronological lifecycle positions.
    if "job_post_started" in names and "job_post_completed" in names:

        started_time = group.loc[
            group["event_name"] == "job_post_started",
            "event_timestamp",
        ].min()

        completed_time = group.loc[
            group["event_name"] == "job_post_completed",
            "event_timestamp",
        ].min()

        if completed_time < started_time:
            lifecycle_issues.append(
                f"{job_id}: completed_before_started"
            )

    if "job_post_completed" in names and "job_post_published" in names:

        completed_time = group.loc[
            group["event_name"] == "job_post_completed",
            "event_timestamp",
        ].min()

        published_time = group.loc[
            group["event_name"] == "job_post_published",
            "event_timestamp",
        ].min()

        if published_time < completed_time:
            lifecycle_issues.append(
                f"{job_id}: published_before_completed"
            )


validation["lifecycle_issues"] = len(lifecycle_issues)

validation["lifecycle_issue_examples"] = lifecycle_issues[:10]

validation["validation_passed"] = all(
    [
        validation["invalid_event_names"] == 0,
        validation["missing_event_id"] == 0,
        validation["duplicate_event_ids"] == 0,
        validation["missing_job_id"] == 0,
        validation["missing_seller_id"] == 0,
        validation["invalid_timestamps"] == 0,
        validation["lifecycle_issues"] == 0,
    ]
)


with open(
    VALIDATION_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        validation,
        file,
        indent=2,
    )


# ============================================================
# 3. JOB-LEVEL TABLES
# ============================================================

completed = (
    events_df[
        events_df["event_name"] == "job_post_completed"
    ]
    .drop_duplicates("job_id")
    .copy()
)

published = (
    events_df[
        events_df["event_name"] == "job_post_published"
    ]
    .drop_duplicates("job_id")
    .copy()
)

closed = (
    events_df[
        events_df["event_name"] == "job_post_closed"
    ]
    .drop_duplicates("job_id")
    .copy()
)


# ============================================================
# 4. DAILY JOB-SUPPLY SUMMARY
# ============================================================

completed_daily = (
    completed.groupby(
        completed["event_timestamp"].dt.date
    )
    .size()
    .rename("jobs_posted")
)

published_daily = (
    published.groupby(
        published["event_timestamp"].dt.date
    )
    .size()
    .rename("jobs_published")
)

all_dates = pd.date_range(
    START_DATE.date(),
    (START_DATE + timedelta(days=DAYS - 1)).date(),
    freq="D",
)

summary = pd.DataFrame(
    index=all_dates
)

summary["jobs_posted"] = (
    completed_daily
    .reindex(summary.index.date, fill_value=0)
    .to_numpy()
)

summary["jobs_published"] = (
    published_daily
    .reindex(summary.index.date, fill_value=0)
    .to_numpy()
)

summary = summary.reset_index()

summary.rename(
    columns={"index": "date"},
    inplace=True,
)

summary["date"] = pd.to_datetime(
    summary["date"]
).dt.strftime("%Y-%m-%d")

summary["jobs_posted"] = summary[
    "jobs_posted"
].astype(int)

summary["jobs_published"] = summary[
    "jobs_published"
].astype(int)


# ============================================================
# 5. ACTIVE JOB STATE
# ============================================================

latest_state: dict[str, str] = {}

for job_id, group in events_df.groupby("job_id"):

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

    latest_state[job_id] = state


active_job_ids = [
    job_id
    for job_id, state in latest_state.items()
    if state == "active"
]

active_jobs = len(active_job_ids)


# ============================================================
# 6. KPI CALCULATIONS
# ============================================================

started_jobs = events_df.loc[
    events_df["event_name"] == "job_post_started",
    "job_id",
].nunique()

completed_jobs = completed["job_id"].nunique()
published_jobs = published["job_id"].nunique()
closed_jobs = closed["job_id"].nunique()

completion_rate = (
    completed_jobs / started_jobs * 100
    if started_jobs > 0
    else 0
)

publication_rate = (
    published_jobs / completed_jobs * 100
    if completed_jobs > 0
    else 0
)


# ============================================================
# 7. SELLER SUPPLY
# ============================================================

active_jobs_df = published[
    published["job_id"].isin(active_job_ids)
]

seller_supply = (
    active_jobs_df.groupby("seller_id")
    .size()
    .sort_values(ascending=False)
)


# ============================================================
# 8. CATEGORY SUPPLY
# ============================================================

category_supply = (
    completed.groupby("job_category")
    .size()
    .sort_values(ascending=False)
)


summary.to_csv(
    SUMMARY_FILE,
    index=False,
)


# ============================================================
# 9. HTML DASHBOARD DATA
# ============================================================

daily_data = summary.to_dict(
    orient="records"
)

seller_data = [
    {
        "seller": str(seller),
        "jobs": int(jobs),
    }
    for seller, jobs in seller_supply.head(10).items()
]

category_data = [
    {
        "category": str(category),
        "jobs": int(jobs),
    }
    for category, jobs in category_supply.items()
]


# ============================================================
# 10. BUILD HTML DASHBOARD
# ============================================================

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
PlaceMux — Jobs Posted View
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
    max-width: 1250px;
    margin: auto;
    padding: 30px;
}}

h1 {{
    margin-bottom: 5px;
    font-size: 36px;
}}

.subtitle {{
    color: #6b7280;
    margin-bottom: 28px;
    font-size: 16px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(5, 1fr);
    gap: 16px;
}}

.card {{
    background: white;
    border-radius: 14px;
    padding: 22px;
    box-shadow:
        0 3px 12px rgba(0,0,0,0.07);
}}

.card h3 {{
    margin: 0;
    font-size: 14px;
    color: #6b7280;
}}

.value {{
    margin-top: 8px;
    font-size: 30px;
    font-weight: 700;
}}

.section {{
    background: white;
    margin-top: 22px;
    padding: 24px;
    border-radius: 14px;
    box-shadow:
        0 3px 12px rgba(0,0,0,0.07);
}}

.section h2 {{
    margin-top: 0;
}}

.status {{
    display: inline-block;
    padding: 7px 12px;
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

.metric-row {{
    display: grid;
    grid-template-columns:
        repeat(3, 1fr);
    gap: 15px;
}}

.metric-box {{
    background: #f8fafc;
    border-radius: 10px;
    padding: 16px;
}}

canvas {{
    width: 100%;
    height: 320px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 12px;
    text-align: left;
    border-bottom:
        1px solid #e5e7eb;
}}

th {{
    color: #6b7280;
}}

code {{
    background: #f1f5f9;
    padding: 3px 6px;
    border-radius: 5px;
}}

@media (max-width: 1000px) {{

    .grid {{
        grid-template-columns:
            repeat(2, 1fr);
    }}

    .metric-row {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 600px) {{

    .container {{
        padding: 16px;
    }}

    .grid {{
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
Jobs Posted View
</h1>

<div class="subtitle">

PlaceMux Phase 2 — Job Supply Monitoring ·
Synthetic Demonstration Dataset

</div>


<!-- ===================================================== -->
<!-- KPIs -->
<!-- ===================================================== -->

<div class="grid">

<div class="card">

<h3>
Jobs Posted
</h3>

<div class="value">
{completed_jobs}
</div>

</div>


<div class="card">

<h3>
Jobs Published
</h3>

<div class="value">
{published_jobs}
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
Completion Rate
</h3>

<div class="value">
{completion_rate:.1f}%
</div>

</div>


<div class="card">

<h3>
Publication Rate
</h3>

<div class="value">
{publication_rate:.1f}%
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Event Validation
</h2>

<p>

Validation status:

<span class="
status
{"pass" if validation["validation_passed"] else "fail"}
">

{"PASS" if validation["validation_passed"] else "FAIL"}

</span>

</p>


<div class="metric-row">

<div class="metric-box">

<strong>
Total Events
</strong>

<br>

{validation["total_events"]}

</div>


<div class="metric-box">

<strong>
Duplicate Event IDs
</strong>

<br>

{validation["duplicate_event_ids"]}

</div>


<div class="metric-box">

<strong>
Missing Job IDs
</strong>

<br>

{validation["missing_job_id"]}

</div>


<div class="metric-box">

<strong>
Missing Seller IDs
</strong>

<br>

{validation["missing_seller_id"]}

</div>


<div class="metric-box">

<strong>
Invalid Event Names
</strong>

<br>

{validation["invalid_event_names"]}

</div>


<div class="metric-box">

<strong>
Lifecycle Issues
</strong>

<br>

{validation["lifecycle_issues"]}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- TREND -->
<!-- ===================================================== -->

<div class="section">

<h2>
Jobs Posted Over Time
</h2>

<canvas id="trendChart"></canvas>

</div>


<!-- ===================================================== -->
<!-- SELLER -->
<!-- ===================================================== -->

<div class="section">

<h2>
Active Job Supply by Seller
</h2>

<table>

<thead>

<tr>

<th>
Seller
</th>

<th>
Active Jobs
</th>

</tr>

</thead>

<tbody>

{
"".join(
    f'''
    <tr>
        <td>{row["seller"]}</td>
        <td>{row["jobs"]}</td>
    </tr>
    '''
    for row in seller_data
)
}

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- CATEGORY -->
<!-- ===================================================== -->

<div class="section">

<h2>
Jobs Posted by Category
</h2>

<table>

<thead>

<tr>

<th>
Category
</th>

<th>
Jobs Posted
</th>

</tr>

</thead>

<tbody>

{
"".join(
    f'''
    <tr>
        <td>{row["category"]}</td>
        <td>{row["jobs"]}</td>
    </tr>
    '''
    for row in category_data
)
}

</tbody>

</table>

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

Synthetic marketplace job-post event stream
created specifically for the Day 22 demonstration.

</p>

<p>

<strong>
Jobs Posted:
</strong>

Distinct jobs with a valid
<code>
job_post_completed
</code>
event.

</p>

<p>

<strong>
Jobs Published:
</strong>

Distinct jobs with a valid
<code>
job_post_published
</code>
event.

</p>

<p>

<strong>
Active Jobs:
</strong>

Jobs whose latest validated lifecycle
state is active.

</p>

</div>


</div>


<script>

const data =
{json.dumps(daily_data, default=str)};

const canvas =
document.getElementById("trendChart");

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

    ctx.scale(dpr, dpr);

    const padding = 45;

    const chartWidth =
        width - padding * 2;

    const chartHeight =
        height - padding * 2;

    const maxValue =
        Math.max(
            ...data.map(
                d =>
                    Math.max(
                        Number(d.jobs_posted),
                        Number(d.jobs_published)
                    )
            )
        );

    function x(i) {{
        return padding +
            (
                i *
                chartWidth /
                Math.max(data.length - 1, 1)
            );
    }}

    function y(value) {{
        return height -
            padding -
            (
                value /
                maxValue
            ) *
            chartHeight;
    }}

    function drawSeries(key) {{

        ctx.beginPath();

        data.forEach((row, index) => {{

            const px = x(index);

            const py = y(
                Number(row[key])
            );

            if (index === 0) {{
                ctx.moveTo(px, py);
            }} else {{
                ctx.lineTo(px, py);
            }}

        }});

        ctx.stroke();

    }}


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    // Axis

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


    // Grid lines

    for (
        let i = 0;
        i <= 5;
        i++
    ) {{

        const value =
            maxValue *
            i /
            5;

        const py =
            y(value);

        ctx.beginPath();

        ctx.moveTo(
            padding,
            py
        );

        ctx.lineTo(
            width - padding,
            py
        );

        ctx.stroke();

    }}


    // Posted series

    drawSeries(
        "jobs_posted"
    );


    // Published series

    drawSeries(
        "jobs_published"
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


HTML_FILE.write_text(
    html,
    encoding="utf-8",
)


# ============================================================
# 11. TERMINAL OUTPUT
# ============================================================

print("=" * 60)
print("DAY 22 — JOB SUPPLY DEMO")
print("=" * 60)

print(
    f"Events generated       : {len(events_df):,}"
)

print(
    f"Distinct jobs          : "
    f"{events_df['job_id'].nunique():,}"
)

print(
    f"Jobs posted            : "
    f"{completed_jobs:,}"
)

print(
    f"Jobs published         : "
    f"{published_jobs:,}"
)

print(
    f"Active jobs            : "
    f"{active_jobs:,}"
)

print(
    f"Jobs closed            : "
    f"{closed_jobs:,}"
)

print(
    f"Completion rate        : "
    f"{completion_rate:.1f}%"
)

print(
    f"Publication rate       : "
    f"{publication_rate:.1f}%"
)

print()
print("VALIDATION")
print("-" * 60)

print(
    f"Duplicate event IDs    : "
    f"{validation['duplicate_event_ids']}"
)

print(
    f"Missing job IDs        : "
    f"{validation['missing_job_id']}"
)

print(
    f"Missing seller IDs     : "
    f"{validation['missing_seller_id']}"
)

print(
    f"Invalid event names    : "
    f"{validation['invalid_event_names']}"
)

print(
    f"Invalid timestamps     : "
    f"{validation['invalid_timestamps']}"
)

print(
    f"Lifecycle issues       : "
    f"{validation['lifecycle_issues']}"
)

print(
    f"Validation status      : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 60)

print(EVENTS_FILE)
print(SUMMARY_FILE)
print(VALIDATION_FILE)
print(HTML_FILE)