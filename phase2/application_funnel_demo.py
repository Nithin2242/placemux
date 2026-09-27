from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EVENTS_FILE = BASE_DIR / "application_funnel_events_demo.csv"
SUMMARY_FILE = BASE_DIR / "application_funnel_summary.csv"
VALIDATION_FILE = BASE_DIR / "application_funnel_validation.json"
HTML_FILE = BASE_DIR / "application_funnel_view.html"

RANDOM_SEED = 42

START_DATE = datetime(2026, 8, 1)
DAYS = 30

CANDIDATES = [
    f"CAN{n:03d}"
    for n in range(1, 81)
]

COMPANIES = [
    f"CMP{n:03d}"
    for n in range(1, 31)
]

JOBS = [
    f"JOB{n:03d}"
    for n in range(1, 61)
]

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
    "application_started",
    "application_submitted",
    "application_reviewed",
    "application_shortlisted",
    "application_next_step",
    "application_selected",
    "application_outcome_recorded",
}


random.seed(RANDOM_SEED)

events = []

event_counter = 1
application_counter = 1


def add_event(
    event_name: str,
    timestamp: datetime,
    candidate_id: str,
    company_id: str,
    job_id: str,
    application_id: str,
    category: str,
    location: str,
    session_id: str,
    extra: dict | None = None,
) -> None:

    global event_counter

    row = {
        "event_id": f"E{event_counter:06d}",
        "event_name": event_name,
        "event_timestamp": timestamp.isoformat(),
        "candidate_id": candidate_id,
        "company_id": company_id,
        "job_id": job_id,
        "application_id": application_id,
        "session_id": session_id,
        "job_category": category,
        "location": location,
        "platform": random.choice(["web", "mobile"]),
        "source": random.choice(
            [
                "organic",
                "direct",
                "referral",
                "campaign",
            ]
        ),
        "event_version": "1.0",
    }

    if extra:
        row.update(extra)

    events.append(row)

    event_counter += 1


# ============================================================
# GENERATE APPLICATIONS
# ============================================================

for day_offset in range(DAYS):

    current_day = START_DATE + timedelta(
        days=day_offset
    )

    weekday = current_day.weekday()

    applications_today = (
        random.randint(18, 26)
        if weekday < 5
        else random.randint(10, 17)
    )

    for _ in range(applications_today):

        application_id = (
            f"APP{application_counter:05d}"
        )

        candidate_id = random.choice(
            CANDIDATES
        )

        company_id = random.choice(
            COMPANIES
        )

        job_id = random.choice(
            JOBS
        )

        category = random.choice(
            CATEGORIES
        )

        location = random.choice(
            LOCATIONS
        )

        session_id = (
            f"SESSION_{application_counter:05d}"
        )

        started_at = (
            current_day
            + timedelta(
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59),
            )
        )

        add_event(
            "application_started",
            started_at,
            candidate_id,
            company_id,
            job_id,
            application_id,
            category,
            location,
            session_id,
        )

        # ~88% reach submitted
        if random.random() < 0.88:

            submitted_at = (
                started_at
                + timedelta(
                    minutes=random.randint(5, 90)
                )
            )

            add_event(
                "application_submitted",
                submitted_at,
                candidate_id,
                company_id,
                job_id,
                application_id,
                category,
                location,
                session_id,
                {
                    "submission_type": "standard",
                },
            )

            # ~78% get reviewed
            if random.random() < 0.78:

                reviewed_at = (
                    submitted_at
                    + timedelta(
                        hours=random.randint(2, 72)
                    )
                )

                add_event(
                    "application_reviewed",
                    reviewed_at,
                    candidate_id,
                    company_id,
                    job_id,
                    application_id,
                    category,
                    location,
                    session_id,
                    {
                        "review_status": "reviewed",
                    },
                )

                # ~48% shortlisted
                if random.random() < 0.48:

                    shortlisted_at = (
                        reviewed_at
                        + timedelta(
                            hours=random.randint(1, 48)
                        )
                    )

                    add_event(
                        "application_shortlisted",
                        shortlisted_at,
                        candidate_id,
                        company_id,
                        job_id,
                        application_id,
                        category,
                        location,
                        session_id,
                        {
                            "shortlist_stage": "shortlisted",
                        },
                    )

                    # ~62% reach next step
                    if random.random() < 0.62:

                        next_step_at = (
                            shortlisted_at
                            + timedelta(
                                hours=random.randint(2, 72)
                            )
                        )

                        add_event(
                            "application_next_step",
                            next_step_at,
                            candidate_id,
                            company_id,
                            job_id,
                            application_id,
                            category,
                            location,
                            session_id,
                            {
                                "next_step_type": "interview",
                            },
                        )

                        # ~52% selected
                        if random.random() < 0.52:

                            selected_at = (
                                next_step_at
                                + timedelta(
                                    hours=random.randint(4, 96)
                                )
                            )

                            add_event(
                                "application_selected",
                                selected_at,
                                candidate_id,
                                company_id,
                                job_id,
                                application_id,
                                category,
                                location,
                                session_id,
                                {
                                    "selection_type": "selected",
                                },
                            )

                            # ~70% successful outcome
                            if random.random() < 0.70:

                                outcome_at = (
                                    selected_at
                                    + timedelta(
                                        hours=random.randint(
                                            4,
                                            96,
                                        )
                                    )
                                )

                                add_event(
                                    "application_outcome_recorded",
                                    outcome_at,
                                    candidate_id,
                                    company_id,
                                    job_id,
                                    application_id,
                                    category,
                                    location,
                                    session_id,
                                    {
                                        "outcome_id": (
                                            f"OUT{application_counter:05d}"
                                        ),
                                        "outcome_type": "successful",
                                        "outcome_status": "success",
                                    },
                                )

        application_counter += 1


events_df = pd.DataFrame(events)

events_df["event_timestamp"] = pd.to_datetime(
    events_df["event_timestamp"]
)

events_df = events_df.sort_values(
    [
        "event_timestamp",
        "event_id",
    ]
).reset_index(drop=True)

events_df.to_csv(
    EVENTS_FILE,
    index=False,
)


# ============================================================
# VALIDATION
# ============================================================

validation = {
    "total_events": int(
        len(events_df)
    ),
    "invalid_event_names": int(
        (~events_df["event_name"]
         .isin(APPROVED_EVENTS)).sum()
    ),
    "duplicate_event_ids": int(
        events_df["event_id"]
        .duplicated()
        .sum()
    ),
    "missing_event_ids": int(
        events_df["event_id"]
        .isna()
        .sum()
    ),
    "missing_application_ids": int(
        events_df["application_id"]
        .isna()
        .sum()
    ),
    "missing_candidate_ids": int(
        events_df["candidate_id"]
        .isna()
        .sum()
    ),
    "missing_company_ids": int(
        events_df["company_id"]
        .isna()
        .sum()
    ),
    "invalid_timestamps": int(
        events_df["event_timestamp"]
        .isna()
        .sum()
    ),
}


# ============================================================
# FUNNEL RELATIONSHIP VALIDATION
# ============================================================

def applications_for(
    event_name: str,
) -> set[str]:

    return set(
        events_df.loc[
            events_df["event_name"]
            == event_name,
            "application_id",
        ]
    )


started_ids = applications_for(
    "application_started"
)

submitted_ids = applications_for(
    "application_submitted"
)

reviewed_ids = applications_for(
    "application_reviewed"
)

shortlisted_ids = applications_for(
    "application_shortlisted"
)

next_step_ids = applications_for(
    "application_next_step"
)

selected_ids = applications_for(
    "application_selected"
)


validation["submitted_without_start"] = len(
    submitted_ids - started_ids
)

validation["reviewed_without_submission"] = len(
    reviewed_ids - submitted_ids
)

validation["shortlisted_without_review"] = len(
    shortlisted_ids - reviewed_ids
)

validation["next_step_without_shortlist"] = len(
    next_step_ids - shortlisted_ids
)

validation["selected_without_next_step"] = len(
    selected_ids - next_step_ids
)

outcome_application_ids = applications_for(
    "application_outcome_recorded"
)

validation["outcome_without_selection"] = len(
    outcome_application_ids - selected_ids
)


validation["validation_passed"] = all(
    value == 0
    for key, value in validation.items()
    if key != "total_events"
    and key != "validation_passed"
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
# FUNNEL COUNTS
# ============================================================

started = len(started_ids)
submitted = len(submitted_ids)
reviewed = len(reviewed_ids)
shortlisted = len(shortlisted_ids)
next_steps = len(next_step_ids)
selected = len(selected_ids)
outcomes = len(outcome_application_ids)


def conversion(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:
        return 0.0

    return (
        numerator /
        denominator *
        100
    )


submission_rate = conversion(
    submitted,
    started,
)

review_rate = conversion(
    reviewed,
    submitted,
)

shortlist_rate = conversion(
    shortlisted,
    reviewed,
)

next_step_rate = conversion(
    next_steps,
    shortlisted,
)

selection_rate = conversion(
    selected,
    next_steps,
)

outcome_rate = conversion(
    outcomes,
    selected,
)

overall_conversion = conversion(
    outcomes,
    submitted,
)


# ============================================================
# DAILY SUMMARY
# ============================================================

daily = (
    events_df.assign(
        date=events_df[
            "event_timestamp"
        ].dt.strftime("%Y-%m-%d")
    )
    .groupby(
        [
            "date",
            "event_name",
        ]
    )
    .size()
    .unstack(
        fill_value=0
    )
    .reset_index()
)

for event_name in APPROVED_EVENTS:

    if event_name not in daily.columns:
        daily[event_name] = 0


daily = daily[
    [
        "date",
        "application_started",
        "application_submitted",
        "application_reviewed",
        "application_shortlisted",
        "application_next_step",
        "application_selected",
        "application_outcome_recorded",
    ]
]

daily.to_csv(
    SUMMARY_FILE,
    index=False,
)


# ============================================================
# BUILD HTML
# ============================================================

daily_data = daily.to_dict(
    orient="records"
)


stages = [
    ("Applications Started", started),
    ("Applications Submitted", submitted),
    ("Applications Reviewed", reviewed),
    ("Applications Shortlisted", shortlisted),
    ("Next Step", next_steps),
    ("Selected", selected),
    ("Successful Outcomes", outcomes),
]


stage_html = ""

for label, value in stages:

    width = (
        value / max(started, 1)
    ) * 100

    stage_html += f"""
    <div class="stage">

        <div class="stage-header">
            <span>{label}</span>
            <span>{value}</span>
        </div>

        <div class="bar">
            <div
                class="fill"
                style="width:{width:.1f}%"
            ></div>
        </div>

    </div>
    """


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
PlaceMux — Application Funnel View
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
    font-size: 36px;
    margin-bottom: 5px;
}}

.subtitle {{
    color: #6b7280;
    margin-bottom: 28px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);
    gap: 16px;
}}

.card {{
    background: white;
    padding: 22px;
    border-radius: 14px;
    box-shadow:
        0 3px 12px rgba(0,0,0,.07);
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
        0 3px 12px rgba(0,0,0,.07);
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

.funnel {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.stage {{
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
}}

.stage-header {{
    display: flex;
    justify-content: space-between;
    font-weight: 700;
}}

.bar {{
    height: 14px;
    background: #e5e7eb;
    margin-top: 8px;
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

canvas {{
    width: 100%;
    height: 300px;
}}

.metric-grid {{
    display: grid;
    grid-template-columns:
        repeat(3, 1fr);
    gap: 12px;
}}

.metric {{
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
}}

@media (max-width: 900px) {{

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
Application Funnel View
</h1>

<div class="subtitle">
PlaceMux Phase 2 — Applications & Shortlisting ·
Synthetic Demonstration Dataset
</div>


<!-- ===================================================== -->
<!-- KPIs -->
<!-- ===================================================== -->

<div class="grid">

<div class="card">
<h3>Applications Started</h3>
<div class="value">{started}</div>
</div>

<div class="card">
<h3>Applications Submitted</h3>
<div class="value">{submitted}</div>
</div>

<div class="card">
<h3>Applications Reviewed</h3>
<div class="value">{reviewed}</div>
</div>

<div class="card">
<h3>Applications Shortlisted</h3>
<div class="value">{shortlisted}</div>
</div>

<div class="card">
<h3>Next Steps</h3>
<div class="value">{next_steps}</div>
</div>

<div class="card">
<h3>Selected</h3>
<div class="value">{selected}</div>
</div>

<div class="card">
<h3>Successful Outcomes</h3>
<div class="value">{outcomes}</div>
</div>

<div class="card">
<h3>Overall Conversion</h3>
<div class="value">{overall_conversion:.1f}%</div>
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

Validation Status:

<span class="
status
{"pass" if validation["validation_passed"] else "fail"}
">

{"PASS" if validation["validation_passed"] else "FAIL"}

</span>

</p>


<div class="metric-grid">

<div class="metric">
<strong>Total Events</strong>
<br>
{validation["total_events"]}
</div>

<div class="metric">
<strong>Duplicate Event IDs</strong>
<br>
{validation["duplicate_event_ids"]}
</div>

<div class="metric">
<strong>Missing Application IDs</strong>
<br>
{validation["missing_application_ids"]}
</div>

<div class="metric">
<strong>Missing Candidate IDs</strong>
<br>
{validation["missing_candidate_ids"]}
</div>

<div class="metric">
<strong>Missing Company IDs</strong>
<br>
{validation["missing_company_ids"]}
</div>

<div class="metric">
<strong>Broken Funnel Links</strong>
<br>
{
    validation["submitted_without_start"]
    + validation["reviewed_without_submission"]
    + validation["shortlisted_without_review"]
    + validation["next_step_without_shortlist"]
    + validation["selected_without_next_step"]
    + validation["outcome_without_selection"]
}
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- FUNNEL -->
<!-- ===================================================== -->

<div class="section">

<h2>
Application Funnel
</h2>

<div class="funnel">

{stage_html}

</div>

</div>


<!-- ===================================================== -->
<!-- CONVERSIONS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Stage Conversion Rates
</h2>

<table>

<thead>

<tr>
<th>Stage</th>
<th>Conversion Rate</th>
</tr>

</thead>

<tbody>

<tr>
<td>Started → Submitted</td>
<td>{submission_rate:.1f}%</td>
</tr>

<tr>
<td>Submitted → Reviewed</td>
<td>{review_rate:.1f}%</td>
</tr>

<tr>
<td>Reviewed → Shortlisted</td>
<td>{shortlist_rate:.1f}%</td>
</tr>

<tr>
<td>Shortlisted → Next Step</td>
<td>{next_step_rate:.1f}%</td>
</tr>

<tr>
<td>Next Step → Selected</td>
<td>{selection_rate:.1f}%</td>
</tr>

<tr>
<td>Selected → Outcome</td>
<td>{outcome_rate:.1f}%</td>
</tr>

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- TREND -->
<!-- ===================================================== -->

<div class="section">

<h2>
Applications Over Time
</h2>

<canvas id="trendChart"></canvas>

</div>


<!-- ===================================================== -->
<!-- DEFINITIONS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Source & Definitions
</h2>

<p>
<strong>Source:</strong>
Synthetic application and shortlisting event stream created specifically
for the Day 24 demonstration.
</p>

<p>
<strong>Applications Started:</strong>
Distinct applications with a valid
<code>application_started</code>
event.
</p>

<p>
<strong>Applications Submitted:</strong>
Distinct applications with a valid
<code>application_submitted</code>
event.
</p>

<p>
<strong>Applications Shortlisted:</strong>
Distinct applications with a valid
<code>application_shortlisted</code>
event.
</p>

<p>
<strong>Successful Outcomes:</strong>
Distinct applications with a valid
<code>application_outcome_recorded</code>
event.
</p>

</div>


</div>


<script>

const data =
{json.dumps(daily_data, default=str)};

const canvas =
document.getElementById(
    "trendChart"
);

const ctx =
canvas.getContext("2d");


function drawChart() {{

    const width =
        canvas.clientWidth || 1100;

    const height = 300;

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
            ...data.map(
                row =>
                    Number(
                        row.application_started
                    )
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


    // Started applications

    ctx.beginPath();

    data.forEach(
        (row, index) => {{

            const px = x(index);

            const py = y(
                Number(
                    row.application_started
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


    // Submitted applications

    ctx.beginPath();

    data.forEach(
        (row, index) => {{

            const px = x(index);

            const py = y(
                Number(
                    row.application_submitted
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
# TERMINAL OUTPUT
# ============================================================

print("=" * 60)
print("DAY 24 — APPLICATION FUNNEL DEMO")
print("=" * 60)

print(
    f"Total events          : {len(events_df):,}"
)

print(
    f"Applications started  : {started:,}"
)

print(
    f"Applications submitted: {submitted:,}"
)

print(
    f"Applications reviewed : {reviewed:,}"
)

print(
    f"Applications shortlisted: {shortlisted:,}"
)

print(
    f"Next steps            : {next_steps:,}"
)

print(
    f"Selected              : {selected:,}"
)

print(
    f"Successful outcomes   : {outcomes:,}"
)

print(
    f"Overall conversion    : {overall_conversion:.1f}%"
)

print()
print("VALIDATION")
print("-" * 60)

print(
    f"Duplicate event IDs   : "
    f"{validation['duplicate_event_ids']}"
)

print(
    f"Missing event IDs     : "
    f"{validation['missing_event_ids']}"
)

print(
    f"Missing application IDs: "
    f"{validation['missing_application_ids']}"
)

print(
    f"Missing candidate IDs : "
    f"{validation['missing_candidate_ids']}"
)

print(
    f"Missing company IDs   : "
    f"{validation['missing_company_ids']}"
)

print(
    f"Submitted without start: "
    f"{validation['submitted_without_start']}"
)

print(
    f"Reviewed without submit: "
    f"{validation['reviewed_without_submission']}"
)

print(
    f"Shortlisted without review: "
    f"{validation['shortlisted_without_review']}"
)

print(
    f"Next step without shortlist: "
    f"{validation['next_step_without_shortlist']}"
)

print(
    f"Selected without next step: "
    f"{validation['selected_without_next_step']}"
)

print(
    f"Outcome without selection: "
    f"{validation['outcome_without_selection']}"
)

print(
    f"Validation status     : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 60)

print(EVENTS_FILE)
print(SUMMARY_FILE)
print(VALIDATION_FILE)
print(HTML_FILE)