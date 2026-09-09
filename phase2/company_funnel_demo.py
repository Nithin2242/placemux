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

EVENTS_FILE = BASE_DIR / "company_funnel_events_demo.csv"
SUMMARY_FILE = BASE_DIR / "company_funnel_summary.csv"
VALIDATION_FILE = BASE_DIR / "company_funnel_validation.json"
HTML_FILE = BASE_DIR / "company_funnel_view.html"

RANDOM_SEED = 42

START_DATE = datetime(2026, 8, 1)
DAYS = 30

COMPANIES = [
    f"C{n:03d}"
    for n in range(1, 41)
]

SEARCH_CATEGORIES = [
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
    "search_performed",
    "search_result_viewed",
    "listing_viewed",
    "company_contact_started",
    "engagement_started",
    "match_created",
    "outcome_recorded",
}


# ============================================================
# GENERATE SYNTHETIC COMPANY FUNNEL
# ============================================================

random.seed(RANDOM_SEED)

events = []

event_counter = 1


def add_event(
    event_name: str,
    timestamp: datetime,
    company_id: str,
    search_id: str,
    session_id: str,
    category: str,
    location: str,
    extra: dict | None = None,
) -> None:

    global event_counter

    row = {
        "event_id": f"E{event_counter:06d}",
        "event_name": event_name,
        "event_timestamp": timestamp.isoformat(),
        "company_id": company_id,
        "search_id": search_id,
        "session_id": session_id,
        "search_category": category,
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


search_counter = 1
listing_counter = 1
contact_counter = 1
engagement_counter = 1
match_counter = 1
outcome_counter = 1


for day_offset in range(DAYS):

    day = START_DATE + timedelta(days=day_offset)

    weekday = day.weekday()

    searches_today = (
        random.randint(15, 22)
        if weekday < 5
        else random.randint(9, 15)
    )

    for _ in range(searches_today):

        company_id = random.choice(COMPANIES)

        search_id = f"SEARCH_{search_counter:05d}"

        session_id = f"SESSION_{search_counter:05d}"

        category = random.choice(SEARCH_CATEGORIES)

        location = random.choice(LOCATIONS)

        search_time = day + timedelta(
            hours=random.randint(8, 18),
            minutes=random.randint(0, 59),
        )

        add_event(
            "search_performed",
            search_time,
            company_id,
            search_id,
            session_id,
            category,
            location,
        )

        # Result discovery: ~90%
        if random.random() < 0.90:

            result_view_id = (
                f"RESULT_{search_counter:05d}"
            )

            result_time = search_time + timedelta(
                seconds=random.randint(10, 180)
            )

            add_event(
                "search_result_viewed",
                result_time,
                company_id,
                search_id,
                session_id,
                category,
                location,
                {
                    "result_view_id": result_view_id,
                    "result_count": random.randint(5, 30),
                },
            )

            # Listing view: ~70% of result views
            if random.random() < 0.70:

                listing_id = (
                    f"LISTING_{listing_counter:05d}"
                )

                listing_time = result_time + timedelta(
                    seconds=random.randint(10, 240)
                )

                add_event(
                    "listing_viewed",
                    listing_time,
                    company_id,
                    search_id,
                    session_id,
                    category,
                    location,
                    {
                        "listing_id": listing_id,
                        "position": random.randint(1, 10),
                    },
                )

                # Contact: ~45%
                if random.random() < 0.45:

                    contact_id = (
                        f"CONTACT_{contact_counter:05d}"
                    )

                    contact_time = listing_time + timedelta(
                        minutes=random.randint(1, 60)
                    )

                    add_event(
                        "company_contact_started",
                        contact_time,
                        company_id,
                        search_id,
                        session_id,
                        category,
                        location,
                        {
                            "listing_id": listing_id,
                            "contact_id": contact_id,
                            "contact_channel": random.choice(
                                [
                                    "message",
                                    "email",
                                    "phone",
                                ]
                            ),
                        },
                    )

                    # Engagement: ~60%
                    if random.random() < 0.60:

                        engagement_id = (
                            f"ENGAGE_{engagement_counter:05d}"
                        )

                        engagement_time = (
                            contact_time
                            + timedelta(
                                hours=random.randint(1, 24)
                            )
                        )

                        add_event(
                            "engagement_started",
                            engagement_time,
                            company_id,
                            search_id,
                            session_id,
                            category,
                            location,
                            {
                                "listing_id": listing_id,
                                "engagement_id": engagement_id,
                                "engagement_type": "application",
                            },
                        )

                        # Match: ~55%
                        if random.random() < 0.55:

                            match_id = (
                                f"MATCH_{match_counter:05d}"
                            )

                            match_time = (
                                engagement_time
                                + timedelta(
                                    hours=random.randint(2, 48)
                                )
                            )

                            add_event(
                                "match_created",
                                match_time,
                                company_id,
                                search_id,
                                session_id,
                                category,
                                location,
                                {
                                    "listing_id": listing_id,
                                    "engagement_id": engagement_id,
                                    "match_id": match_id,
                                    "match_type": "company_candidate",
                                },
                            )

                            # Successful outcome: ~65%
                            if random.random() < 0.65:

                                outcome_id = (
                                    f"OUTCOME_{outcome_counter:05d}"
                                )

                                outcome_time = (
                                    match_time
                                    + timedelta(
                                        hours=random.randint(
                                            2,
                                            72,
                                        )
                                    )
                                )

                                add_event(
                                    "outcome_recorded",
                                    outcome_time,
                                    company_id,
                                    search_id,
                                    session_id,
                                    category,
                                    location,
                                    {
                                        "listing_id": listing_id,
                                        "match_id": match_id,
                                        "outcome_id": outcome_id,
                                        "outcome_type": "successful",
                                        "outcome_status": "success",
                                    },
                                )

                                outcome_counter += 1

                            match_counter += 1

                        engagement_counter += 1

                    contact_counter += 1

                listing_counter += 1

        search_counter += 1


events_df = pd.DataFrame(events)

events_df["event_timestamp"] = pd.to_datetime(
    events_df["event_timestamp"]
)

events_df = events_df.sort_values(
    ["event_timestamp", "event_id"]
).reset_index(drop=True)

events_df.to_csv(
    EVENTS_FILE,
    index=False,
)


# ============================================================
# VALIDATION
# ============================================================

validation = {}

validation["total_events"] = int(
    len(events_df)
)

validation["invalid_event_names"] = int(
    (~events_df["event_name"].isin(APPROVED_EVENTS))
    .sum()
)

validation["duplicate_event_ids"] = int(
    events_df["event_id"].duplicated().sum()
)

validation["missing_event_ids"] = int(
    events_df["event_id"].isna().sum()
)

validation["missing_company_ids"] = int(
    events_df["company_id"].isna().sum()
)

validation["invalid_timestamps"] = int(
    events_df["event_timestamp"].isna().sum()
)


# ============================================================
# RELATIONSHIP VALIDATION
# ============================================================

search_ids = set(
    events_df.loc[
        events_df["event_name"] == "search_performed",
        "search_id",
    ]
)

result_events = events_df[
    events_df["event_name"] == "search_result_viewed"
]

listing_events = events_df[
    events_df["event_name"] == "listing_viewed"
]

engagement_events = events_df[
    events_df["event_name"] == "engagement_started"
]

match_events = events_df[
    events_df["event_name"] == "match_created"
]

outcome_events = events_df[
    events_df["event_name"] == "outcome_recorded"
]


validation["results_without_search"] = int(
    (~result_events["search_id"].isin(search_ids))
    .sum()
)


listing_search_ids = set(
    events_df.loc[
        events_df["event_name"] == "search_result_viewed",
        "search_id",
    ]
)

validation["listings_without_discovery"] = int(
    (~listing_events["search_id"].isin(listing_search_ids))
    .sum()
)


engagement_ids = set(
    events_df.loc[
        events_df["event_name"] == "company_contact_started",
        "listing_id",
    ]
)

validation["engagement_without_contact"] = int(
    (~engagement_events["listing_id"].isin(engagement_ids))
    .sum()
)


match_engagement_ids = set(
    events_df.loc[
        events_df["event_name"] == "engagement_started",
        "engagement_id",
    ]
)

validation["matches_without_engagement"] = int(
    (~match_events["engagement_id"]
     .isin(match_engagement_ids))
    .sum()
)


match_ids = set(
    events_df.loc[
        events_df["event_name"] == "match_created",
        "match_id",
    ]
)

validation["outcomes_without_match"] = int(
    (~outcome_events["match_id"]
     .isin(match_ids))
    .sum()
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

searches = events_df[
    events_df["event_name"]
    == "search_performed"
]["search_id"].nunique()

result_views = events_df[
    events_df["event_name"]
    == "search_result_viewed"
].shape[0]

listing_views = events_df[
    events_df["event_name"]
    == "listing_viewed"
].shape[0]

contacts = events_df[
    events_df["event_name"]
    == "company_contact_started"
].shape[0]

engagements = events_df[
    events_df["event_name"]
    == "engagement_started"
].shape[0]

matches = events_df[
    events_df["event_name"]
    == "match_created"
].shape[0]

outcomes = events_df[
    events_df["event_name"]
    == "outcome_recorded"
].shape[0]


def rate(
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


discovery_rate = rate(
    result_views,
    searches,
)

detail_view_rate = rate(
    listing_views,
    result_views,
)

contact_rate = rate(
    contacts,
    listing_views,
)

engagement_rate = rate(
    engagements,
    contacts,
)

match_rate = rate(
    matches,
    engagements,
)

outcome_rate = rate(
    outcomes,
    matches,
)

overall_conversion = rate(
    outcomes,
    searches,
)


# ============================================================
# DAILY TREND
# ============================================================

event_counts = (
    events_df
    .assign(
        date=events_df[
            "event_timestamp"
        ].dt.strftime("%Y-%m-%d")
    )
    .groupby(
        ["date", "event_name"]
    )
    .size()
    .unstack(
        fill_value=0
    )
    .reset_index()
)

for column in APPROVED_EVENTS:

    if column not in event_counts.columns:
        event_counts[column] = 0


event_counts = event_counts[
    [
        "date",
        "search_performed",
        "search_result_viewed",
        "listing_viewed",
        "company_contact_started",
        "engagement_started",
        "match_created",
        "outcome_recorded",
    ]
]

event_counts.to_csv(
    SUMMARY_FILE,
    index=False,
)


# ============================================================
# HTML DASHBOARD
# ============================================================

daily_data = event_counts.to_dict(
    orient="records"
)


stage_data = [
    {
        "stage": "Searches",
        "value": searches,
    },
    {
        "stage": "Result Views",
        "value": result_views,
    },
    {
        "stage": "Listing Views",
        "value": listing_views,
    },
    {
        "stage": "Contacts",
        "value": contacts,
    },
    {
        "stage": "Engagements",
        "value": engagements,
    },
    {
        "stage": "Matches",
        "value": matches,
    },
    {
        "stage": "Outcomes",
        "value": outcomes,
    },
]


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
PlaceMux — Company Funnel View
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
    padding: 15px;
    background: #f8fafc;
    border-radius: 10px;
}}

.stage-header {{
    display: flex;
    justify-content: space-between;
    font-weight: 700;
}}

.bar {{
    margin-top: 8px;
    height: 14px;
    background: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}}

.fill {{
    height: 100%;
    background: #64748b;
}}

.metric-row {{
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);
    gap: 15px;
}}

.metric-box {{
    background: #f8fafc;
    border-radius: 10px;
    padding: 16px;
}}

canvas {{
    width: 100%;
    height: 300px;
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

@media (max-width: 900px) {{

    .grid {{
        grid-template-columns:
            repeat(2, 1fr);
    }}

    .metric-row {{
        grid-template-columns:
            repeat(2, 1fr);
    }}
}}

@media (max-width: 600px) {{

    .container {{
        padding: 16px;
    }}

    .grid,
    .metric-row {{
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
Company Funnel View
</h1>

<div class="subtitle">
PlaceMux Phase 2 — Search & Discovery ·
Synthetic Demonstration Dataset
</div>


<!-- KPIs -->

<div class="grid">

<div class="card">

<h3>
Searches
</h3>

<div class="value">
{searches}
</div>

</div>


<div class="card">

<h3>
Result Views
</h3>

<div class="value">
{result_views}
</div>

</div>


<div class="card">

<h3>
Listing Views
</h3>

<div class="value">
{listing_views}
</div>

</div>


<div class="card">

<h3>
Contacts
</h3>

<div class="value">
{contacts}
</div>

</div>


<div class="card">

<h3>
Engagements
</h3>

<div class="value">
{engagements}
</div>

</div>


<div class="card">

<h3>
Matches
</h3>

<div class="value">
{matches}
</div>

</div>


<div class="card">

<h3>
Successful Outcomes
</h3>

<div class="value">
{outcomes}
</div>

</div>


<div class="card">

<h3>
Overall Conversion
</h3>

<div class="value">
{overall_conversion:.1f}%
</div>

</div>

</div>


<!-- VALIDATION -->

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
<strong>Total Events</strong>
<br>
{validation["total_events"]}
</div>

<div class="metric-box">
<strong>Duplicate IDs</strong>
<br>
{validation["duplicate_event_ids"]}
</div>

<div class="metric-box">
<strong>Missing Company IDs</strong>
<br>
{validation["missing_company_ids"]}
</div>

<div class="metric-box">
<strong>Broken Funnel Links</strong>
<br>
{
    validation["results_without_search"]
    + validation["listings_without_discovery"]
    + validation["engagement_without_contact"]
    + validation["matches_without_engagement"]
    + validation["outcomes_without_match"]
}
</div>

</div>

</div>


<!-- FUNNEL -->

<div class="section">

<h2>
Company Funnel
</h2>

<div class="funnel">

{
"".join(
    f"""
    <div class="stage">

        <div class="stage-header">

            <span>
            {row["stage"]}
            </span>

            <span>
            {row["value"]}
            </span>

        </div>

        <div class="bar">

            <div
                class="fill"
                style="
                width:
                {
                    (
                        row["value"]
                        / max(searches, 1)
                        * 100
                    )
                    if searches
                    else 0
                }%;
                "
            >
            </div>

        </div>

    </div>
    """
    for row in stage_data
)
}

</div>

</div>


<!-- CONVERSIONS -->

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
<td>
Search → Result
</td>
<td>
{discovery_rate:.1f}%
</td>
</tr>

<tr>
<td>
Result → Listing
</td>
<td>
{detail_view_rate:.1f}%
</td>
</tr>

<tr>
<td>
Listing → Contact
</td>
<td>
{contact_rate:.1f}%
</td>
</tr>

<tr>
<td>
Contact → Engagement
</td>
<td>
{engagement_rate:.1f}%
</td>
</tr>

<tr>
<td>
Engagement → Match
</td>
<td>
{match_rate:.1f}%
</td>
</tr>

<tr>
<td>
Match → Outcome
</td>
<td>
{outcome_rate:.1f}%
</td>
</tr>

</tbody>

</table>

</div>


<!-- TREND -->

<div class="section">

<h2>
Search & Discovery Activity Over Time
</h2>

<canvas id="trendChart"></canvas>

</div>


<!-- DEFINITIONS -->

<div class="section">

<h2>
Source & Definitions
</h2>

<p>
<strong>Source:</strong>
Synthetic company-side Search & Discovery event stream
created specifically for the Day 23 demonstration.
</p>

<p>
<strong>Searches:</strong>
Distinct search sessions generated by companies.
</p>

<p>
<strong>Result Views:</strong>
Search-result viewing events.
</p>

<p>
<strong>Listing Views:</strong>
Individual listing/profile views.
</p>

<p>
<strong>Overall Conversion:</strong>
Successful outcomes divided by company searches.
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

    const height = 300;

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
                row =>
                    Number(
                        row.search_performed
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


    // Search line

    ctx.beginPath();

    data.forEach(
        (row, index) => {{

            const px = x(index);

            const py = y(
                Number(
                    row.search_performed
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


    // Result-view line

    ctx.beginPath();

    data.forEach(
        (row, index) => {{

            const px = x(index);

            const py = y(
                Number(
                    row.search_result_viewed
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
print("DAY 23 — COMPANY FUNNEL DEMO")
print("=" * 60)

print(
    f"Total events          : "
    f"{len(events_df):,}"
)

print(
    f"Searches              : "
    f"{searches:,}"
)

print(
    f"Result views          : "
    f"{result_views:,}"
)

print(
    f"Listing views         : "
    f"{listing_views:,}"
)

print(
    f"Contacts              : "
    f"{contacts:,}"
)

print(
    f"Engagements           : "
    f"{engagements:,}"
)

print(
    f"Matches               : "
    f"{matches:,}"
)

print(
    f"Successful outcomes   : "
    f"{outcomes:,}"
)

print(
    f"Overall conversion    : "
    f"{overall_conversion:.1f}%"
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
    f"Missing company IDs   : "
    f"{validation['missing_company_ids']}"
)

print(
    f"Invalid event names   : "
    f"{validation['invalid_event_names']}"
)

print(
    f"Results without search: "
    f"{validation['results_without_search']}"
)

print(
    f"Listings without disc.: "
    f"{validation['listings_without_discovery']}"
)

print(
    f"Engagements w/o contact: "
    f"{validation['engagement_without_contact']}"
)

print(
    f"Matches w/o engagement: "
    f"{validation['matches_without_engagement']}"
)

print(
    f"Outcomes w/o match    : "
    f"{validation['outcomes_without_match']}"
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