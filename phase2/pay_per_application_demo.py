
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

EVENTS_FILE = (
    BASE_DIR /
    "pay_per_application_events_demo.csv"
)

BASELINE_FILE = (
    BASE_DIR /
    "pay_per_application_baseline.csv"
)

VALIDATION_FILE = (
    BASE_DIR /
    "pay_per_application_validation.json"
)

HTML_FILE = (
    BASE_DIR /
    "pay_per_application_view.html"
)

RANDOM_SEED = 42

START_DATE = datetime(
    2026,
    8,
    1,
)

DAYS = 30

APPLICATIONS_PER_DAY = 24


CANDIDATES = [
    f"CAN{n:03d}"
    for n in range(1, 101)
]

COMPANIES = [
    f"CMP{n:03d}"
    for n in range(1, 41)
]

JOBS = [
    f"JOB{n:03d}"
    for n in range(1, 81)
]


APPROVED_EVENTS = {
    "application_started",
    "application_submitted",
    "application_eligible",
    "payment_initiated",
    "payment_captured",
    "payment_failed",
    "payment_refunded",
    "revenue_recognized",
}


CURRENCY = "INR"


# ============================================================
# EVENT GENERATOR
# ============================================================

random.seed(
    RANDOM_SEED
)

events = []

event_counter = 1
application_counter = 1
payment_counter = 1


def add_event(
    event_name: str,
    timestamp: datetime,
    application_id: str,
    candidate_id: str,
    company_id: str,
    job_id: str,
    extra: dict | None = None,
) -> None:

    global event_counter

    row = {
        "event_id":
            f"PAE{event_counter:06d}",

        "event_name":
            event_name,

        "event_timestamp":
            timestamp.isoformat(),

        "application_id":
            application_id,

        "candidate_id":
            candidate_id,

        "company_id":
            company_id,

        "job_id":
            job_id,

        "event_version":
            "1.0",
    }

    if extra:
        row.update(extra)

    events.append(
        row
    )

    event_counter += 1


# ============================================================
# GENERATE APPLICATION + PAYMENT JOURNEY
# ============================================================

for day_offset in range(DAYS):

    current_day = (
        START_DATE
        + timedelta(
            days=day_offset
        )
    )

    for _ in range(
        APPLICATIONS_PER_DAY
    ):

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

        started_at = (
            current_day
            + timedelta(
                hours=random.randint(
                    8,
                    18,
                ),
                minutes=random.randint(
                    0,
                    59,
                ),
            )
        )

        # ----------------------------------------------------
        # APPLICATION START
        # ----------------------------------------------------

        add_event(
            "application_started",
            started_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
        )


        # ~88% submit
        submitted = (
            random.random()
            < 0.88
        )

        if not submitted:

            application_counter += 1

            continue


        submitted_at = (
            started_at
            + timedelta(
                minutes=random.randint(
                    5,
                    90,
                )
            )
        )

        add_event(
            "application_submitted",
            submitted_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
        )


        # ----------------------------------------------------
        # ELIGIBILITY
        # ----------------------------------------------------

        # ~82% of submitted applications become eligible
        eligible = (
            random.random()
            < 0.82
        )

        if not eligible:

            application_counter += 1

            continue


        eligible_at = (
            submitted_at
            + timedelta(
                hours=random.randint(
                    1,
                    24,
                )
            )
        )

        add_event(
            "application_eligible",
            eligible_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
            {
                "eligibility_status":
                    "eligible",

                "eligibility_reason":
                    "meets_demo_rules",
            },
        )


        # ----------------------------------------------------
        # PAYMENT INITIATION
        # ----------------------------------------------------

        # ~90% eligible applications attempt payment
        payment_started = (
            random.random()
            < 0.90
        )

        if not payment_started:

            application_counter += 1

            continue


        payment_id = (
            f"PAY{payment_counter:05d}"
        )

        amount = round(
            random.uniform(
                250,
                1500,
            ),
            2,
        )

        payment_initiated_at = (
            eligible_at
            + timedelta(
                minutes=random.randint(
                    1,
                    30,
                )
            )
        )

        add_event(
            "payment_initiated",
            payment_initiated_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
            {
                "payment_id":
                    payment_id,

                "amount":
                    amount,

                "currency":
                    CURRENCY,

                "payment_method":
                    random.choice(
                        [
                            "upi",
                            "card",
                            "netbanking",
                        ]
                    ),

                "gateway":
                    "PayPerAppDemo",
            },
        )


        # ----------------------------------------------------
        # PAYMENT RESULT
        # ----------------------------------------------------

        payment_successful = (
            random.random()
            < 0.94
        )

        if not payment_successful:

            failed_at = (
                payment_initiated_at
                + timedelta(
                    seconds=random.randint(
                        5,
                        120,
                    )
                )
            )

            add_event(
                "payment_failed",
                failed_at,
                application_id,
                candidate_id,
                company_id,
                job_id,
                {
                    "payment_id":
                        payment_id,

                    "amount":
                        amount,

                    "currency":
                        CURRENCY,

                    "failure_code":
                        random.choice(
                            [
                                "DECLINED",
                                "TIMEOUT",
                                "INSUFFICIENT_FUNDS",
                            ]
                        ),

                    "failure_reason":
                        "demo_payment_failure",
                },
            )

            payment_counter += 1
            application_counter += 1

            continue


        captured_at = (
            payment_initiated_at
            + timedelta(
                seconds=random.randint(
                    5,
                    120,
                )
            )
        )

        gateway_transaction_id = (
            f"GTX{payment_counter:06d}"
        )

        add_event(
            "payment_captured",
            captured_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
            {
                "payment_id":
                    payment_id,

                "gateway_transaction_id":
                    gateway_transaction_id,

                "captured_amount":
                    amount,

                "amount":
                    amount,

                "currency":
                    CURRENCY,

                "gateway":
                    "PayPerAppDemo",
            },
        )


        # ----------------------------------------------------
        # REVENUE RECOGNITION
        # ----------------------------------------------------

        revenue = round(
            amount * 0.08,
            2,
        )

        recognized_at = (
            captured_at
            + timedelta(
                minutes=random.randint(
                    1,
                    60,
                )
            )
        )

        add_event(
            "revenue_recognized",
            recognized_at,
            application_id,
            candidate_id,
            company_id,
            job_id,
            {
                "payment_id":
                    payment_id,

                "revenue_id":
                    f"REV{payment_counter:05d}",

                "recognized_amount":
                    revenue,

                "amount":
                    revenue,

                "currency":
                    CURRENCY,

                "revenue_type":
                    "pay_per_application_fee",
            },
        )


        # ----------------------------------------------------
        # OPTIONAL REFUND
        # ----------------------------------------------------

        if random.random() < 0.06:

            refund_amount = round(
                amount *
                random.uniform(
                    0.25,
                    1.0,
                ),
                2,
            )

            refund_at = (
                recognized_at
                + timedelta(
                    days=random.randint(
                        1,
                        5,
                    )
                )
            )

            add_event(
                "payment_refunded",
                refund_at,
                application_id,
                candidate_id,
                company_id,
                job_id,
                {
                    "payment_id":
                        payment_id,

                    "refund_id":
                        f"REF{payment_counter:05d}",

                    "refund_amount":
                        refund_amount,

                    "amount":
                        refund_amount,

                    "currency":
                        CURRENCY,

                    "refund_reason":
                        "demo_refund",
                },
            )


        payment_counter += 1

        application_counter += 1


events_df = pd.DataFrame(
    events
)

events_df[
    "event_timestamp"
] = pd.to_datetime(
    events_df[
        "event_timestamp"
    ]
)

events_df = events_df.sort_values(
    [
        "application_id",
        "event_timestamp",
        "event_id",
    ]
).reset_index(
    drop=True
)


events_df.to_csv(
    EVENTS_FILE,
    index=False,
)


# ============================================================
# VALIDATION
# ============================================================

validation = {
    "total_events":
        int(len(events_df)),

    "duplicate_event_ids":
        int(
            events_df[
                "event_id"
            ].duplicated().sum()
        ),

    "missing_event_ids":
        int(
            events_df[
                "event_id"
            ].isna().sum()
        ),

    "missing_application_ids":
        int(
            events_df[
                "application_id"
            ].isna().sum()
        ),

    "invalid_event_names":
        int(
            (
                ~events_df[
                    "event_name"
                ].isin(
                    APPROVED_EVENTS
                )
            ).sum()
        ),

    "invalid_timestamps":
        int(
            events_df[
                "event_timestamp"
            ].isna().sum()
        ),
}


# ============================================================
# APPLICATION RELATIONSHIP CHECKS
# ============================================================

def application_ids_for(
    event_name: str,
) -> set[str]:

    return set(
        events_df.loc[
            events_df[
                "event_name"
            ]
            == event_name,
            "application_id",
        ]
    )


started_ids = application_ids_for(
    "application_started"
)

submitted_ids = application_ids_for(
    "application_submitted"
)

eligible_ids = application_ids_for(
    "application_eligible"
)

payment_initiated_ids = application_ids_for(
    "payment_initiated"
)

payment_captured_ids = application_ids_for(
    "payment_captured"
)

payment_failed_ids = application_ids_for(
    "payment_failed"
)

revenue_ids = application_ids_for(
    "revenue_recognized"
)

refund_ids = application_ids_for(
    "payment_refunded"
)


validation[
    "submitted_without_start"
] = len(
    submitted_ids
    - started_ids
)

validation[
    "eligible_without_submission"
] = len(
    eligible_ids
    - submitted_ids
)

validation[
    "payment_without_eligible"
] = len(
    payment_initiated_ids
    - eligible_ids
)

validation[
    "captured_without_initiated"
] = len(
    payment_captured_ids
    - payment_initiated_ids
)

validation[
    "failed_without_initiated"
] = len(
    payment_failed_ids
    - payment_initiated_ids
)

validation[
    "revenue_without_capture"
] = len(
    revenue_ids
    - payment_captured_ids
)

validation[
    "refund_without_capture"
] = len(
    refund_ids
    - payment_captured_ids
)


# ============================================================
# PAYMENT ID CHECKS
# ============================================================

initiated_payment_ids = set(
    events_df.loc[
        events_df[
            "event_name"
        ]
        == "payment_initiated",
        "payment_id",
    ]
)

captured_payment_ids = set(
    events_df.loc[
        events_df[
            "event_name"
        ]
        == "payment_captured",
        "payment_id",
    ]
)

failed_payment_ids = set(
    events_df.loc[
        events_df[
            "event_name"
        ]
        == "payment_failed",
        "payment_id",
    ]
)


validation[
    "captured_payment_without_initiated"
] = len(
    captured_payment_ids
    - initiated_payment_ids
)

validation[
    "failed_payment_without_initiated"
] = len(
    failed_payment_ids
    - initiated_payment_ids
)


validation[
    "validation_passed"
] = all(
    value == 0
    for key, value
    in validation.items()
    if key != "total_events"
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

applications_started = len(
    started_ids
)

applications_submitted = len(
    submitted_ids
)

eligible_applications = len(
    eligible_ids
)

payment_initiated = len(
    payment_initiated_ids
)

payment_captured = len(
    payment_captured_ids
)

payment_failed = len(
    payment_failed_ids
)

paid_applications = len(
    payment_captured_ids
)


# ============================================================
# MONEY METRICS
# ============================================================

captured_rows = events_df[
    events_df[
        "event_name"
    ]
    == "payment_captured"
]

revenue_rows = events_df[
    events_df[
        "event_name"
    ]
    == "revenue_recognized"
]

refund_rows = events_df[
    events_df[
        "event_name"
    ]
    == "payment_refunded"
]


gross_payment_volume = (
    captured_rows[
        "captured_amount"
    ].sum()
)

recognized_revenue = (
    revenue_rows[
        "recognized_amount"
    ].sum()
)

refund_amount = (
    refund_rows[
        "refund_amount"
    ].sum()
)

net_revenue = (
    recognized_revenue
    - refund_amount
)


# ============================================================
# RATE FUNCTION
# ============================================================

def pct(
    numerator: float,
    denominator: float,
) -> float:

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100
    )


submission_rate = pct(
    applications_submitted,
    applications_started,
)

eligibility_rate = pct(
    eligible_applications,
    applications_submitted,
)

payment_initiation_rate = pct(
    payment_initiated,
    eligible_applications,
)

payment_capture_rate = pct(
    payment_captured,
    payment_initiated,
)

paid_application_conversion = pct(
    paid_applications,
    eligible_applications,
)

application_to_payment = pct(
    paid_applications,
    applications_submitted,
)

started_to_paid = pct(
    paid_applications,
    applications_started,
)

payment_failure_rate = pct(
    payment_failed,
    payment_initiated,
)

refund_rate = pct(
    refund_amount,
    gross_payment_volume,
)

revenue_per_paid_application = (
    recognized_revenue
    / paid_applications
    if paid_applications
    else 0.0
)


# ============================================================
# BASELINE OUTPUT
# ============================================================

baseline = pd.DataFrame(
    [
        (
            "Applications Started",
            applications_started,
            "count",
        ),
        (
            "Applications Submitted",
            applications_submitted,
            "count",
        ),
        (
            "Submission Rate",
            round(
                submission_rate,
                2,
            ),
            "%",
        ),
        (
            "Eligible Applications",
            eligible_applications,
            "count",
        ),
        (
            "Eligibility Rate",
            round(
                eligibility_rate,
                2,
            ),
            "%",
        ),
        (
            "Payment Initiated",
            payment_initiated,
            "count",
        ),
        (
            "Payment Initiation Rate",
            round(
                payment_initiation_rate,
                2,
            ),
            "%",
        ),
        (
            "Payment Captured",
            payment_captured,
            "count",
        ),
        (
            "Payment Capture Rate",
            round(
                payment_capture_rate,
                2,
            ),
            "%",
        ),
        (
            "Paid Applications",
            paid_applications,
            "count",
        ),
        (
            "Paid Application Conversion",
            round(
                paid_application_conversion,
                2,
            ),
            "%",
        ),
        (
            "Application-to-Payment Conversion",
            round(
                application_to_payment,
                2,
            ),
            "%",
        ),
        (
            "Started-to-Paid Conversion",
            round(
                started_to_paid,
                2,
            ),
            "%",
        ),
        (
            "Payment Failure Rate",
            round(
                payment_failure_rate,
                2,
            ),
            "%",
        ),
        (
            "Gross Payment Volume",
            round(
                gross_payment_volume,
                2,
            ),
            "INR",
        ),
        (
            "Recognized Revenue",
            round(
                recognized_revenue,
                2,
            ),
            "INR",
        ),
        (
            "Refund Amount",
            round(
                refund_amount,
                2,
            ),
            "INR",
        ),
        (
            "Net Revenue",
            round(
                net_revenue,
                2,
            ),
            "INR",
        ),
        (
            "Revenue per Paid Application",
            round(
                revenue_per_paid_application,
                2,
            ),
            "INR",
        ),
        (
            "Refund Rate",
            round(
                refund_rate,
                2,
            ),
            "%",
        ),
    ],
    columns=[
        "metric",
        "value",
        "unit",
    ],
)


baseline.to_csv(
    BASELINE_FILE,
    index=False,
)


# ============================================================
# HTML DASHBOARD
# ============================================================

stages = [
    (
        "Applications Started",
        applications_started,
    ),
    (
        "Applications Submitted",
        applications_submitted,
    ),
    (
        "Eligible Applications",
        eligible_applications,
    ),
    (
        "Payment Initiated",
        payment_initiated,
    ),
    (
        "Payment Captured",
        payment_captured,
    ),
    (
        "Paid Applications",
        paid_applications,
    ),
]


stage_html = ""

for name, value in stages:

    width = (
        value
        / max(
            applications_started,
            1,
        )
        * 100
    )

    stage_html += f"""
    <div class="stage">

        <div class="stage-header">
            <span>{name}</span>
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
PlaceMux — Pay-per-Application Conversion
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
    color: #64748b;
    margin-bottom: 28px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);
    gap: 15px;
}}

.card {{
    background: white;
    padding: 20px;
    border-radius: 14px;
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

.section {{
    background: white;
    margin-top: 22px;
    padding: 24px;
    border-radius: 14px;
    box-shadow:
        0 3px 12px rgba(0,0,0,.07);
}}

.pass {{
    display: inline-block;
    padding: 8px 14px;
    background: #dcfce7;
    color: #166534;
    border-radius: 20px;
    font-weight: 700;
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
    height: 14px;
    margin-top: 8px;
    background: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}}

.fill {{
    height: 100%;
    background: #64748b;
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

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 11px;
    text-align: left;
    border-bottom:
        1px solid #e5e7eb;
}}

th {{
    color: #64748b;
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
        grid-template-columns:
            1fr;
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
Pay-per-Application Conversion
</h1>

<div class="subtitle">
PlaceMux Phase 2 — Task 7 ·
Conversion Baseline ·
Synthetic Demonstration Data
</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Conversion Tracking Status
</h2>

<p>

<span class="pass">
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

<strong>Invalid Event Names</strong>

<br>

{validation["invalid_event_names"]}

</div>

<div class="metric">

<strong>Broken Application Links</strong>

<br>

{
    validation["submitted_without_start"]
    + validation["eligible_without_submission"]
    + validation["payment_without_eligible"]
    + validation["captured_without_initiated"]
    + validation["failed_without_initiated"]
    + validation["revenue_without_capture"]
    + validation["refund_without_capture"]
}

</div>

<div class="metric">

<strong>Payment-ID Link Errors</strong>

<br>

{
    validation["captured_payment_without_initiated"]
    + validation["failed_payment_without_initiated"]
}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- HEADLINE KPIs -->
<!-- ===================================================== -->

<div class="grid">

<div class="card">

<h3>
Applications Started
</h3>

<div class="value">
{applications_started}
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
Eligible Applications
</h3>

<div class="value">
{eligible_applications}
</div>

</div>


<div class="card">

<h3>
Paid Applications
</h3>

<div class="value">
{paid_applications}
</div>

</div>


<div class="card">

<h3>
Payment Success Rate
</h3>

<div class="value">
{payment_capture_rate:.1f}%
</div>

</div>


<div class="card">

<h3>
Paid Application Conversion
</h3>

<div class="value">
{paid_application_conversion:.1f}%
</div>

</div>


<div class="card">

<h3>
Application → Payment
</h3>

<div class="value">
{application_to_payment:.1f}%
</div>

</div>


<div class="card">

<h3>
Started → Paid
</h3>

<div class="value">
{started_to_paid:.1f}%
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- FUNNEL -->
<!-- ===================================================== -->

<div class="section">

<h2>
Pay-per-Application Funnel
</h2>

<div class="funnel">

{stage_html}

</div>

</div>


<!-- ===================================================== -->
<!-- CONVERSION TABLE -->
<!-- ===================================================== -->

<div class="section">

<h2>
Conversion Baseline
</h2>

<table>

<thead>

<tr>
<th>Metric</th>
<th>Value</th>
</tr>

</thead>

<tbody>

<tr>
<td>Submission Rate</td>
<td>{submission_rate:.1f}%</td>
</tr>

<tr>
<td>Eligibility Rate</td>
<td>{eligibility_rate:.1f}%</td>
</tr>

<tr>
<td>Payment Initiation Rate</td>
<td>{payment_initiation_rate:.1f}%</td>
</tr>

<tr>
<td>Payment Capture Rate</td>
<td>{payment_capture_rate:.1f}%</td>
</tr>

<tr>
<td>Paid Application Conversion</td>
<td>{paid_application_conversion:.1f}%</td>
</tr>

<tr>
<td>Application-to-Payment Conversion</td>
<td>{application_to_payment:.1f}%</td>
</tr>

<tr>
<td>Started-to-Paid Conversion</td>
<td>{started_to_paid:.1f}%</td>
</tr>

<tr>
<td>Payment Failure Rate</td>
<td>{payment_failure_rate:.1f}%</td>
</tr>

<tr>
<td>Refund Rate</td>
<td>{refund_rate:.1f}%</td>
</tr>

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- REVENUE -->
<!-- ===================================================== -->

<div class="section">

<h2>
Monetization Metrics
</h2>

<div class="metric-grid">

<div class="metric">
<strong>
Gross Payment Volume
</strong>
<br>
INR {gross_payment_volume:,.2f}
</div>

<div class="metric">
<strong>
Recognized Revenue
</strong>
<br>
INR {recognized_revenue:,.2f}
</div>

<div class="metric">
<strong>
Refund Amount
</strong>
<br>
INR {refund_amount:,.2f}
</div>

<div class="metric">
<strong>
Net Revenue
</strong>
<br>
INR {net_revenue:,.2f}
</div>

<div class="metric">
<strong>
Revenue / Paid Application
</strong>
<br>
INR {revenue_per_paid_application:,.2f}
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
<strong>Source:</strong>
Synthetic linked application-and-payment event stream created
specifically for the Day 27 demonstration.
</p>

<p>
<strong>Paid Application:</strong>
An application linked through the same
<code>application_id</code>
to a successfully captured payment.
</p>

<p>
<strong>Application-to-Payment Conversion:</strong>
Paid applications divided by submitted applications.
</p>

<p>
<strong>Production recommendation:</strong>
Use a stable
<code>application_id → payment_id → gateway_transaction_id</code>
relationship for exact production cohort tracking.
</p>

</div>


</div>

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

print("=" * 65)
print("DAY 27 — PAY-PER-APPLICATION CONVERSION")
print("=" * 65)

print(
    f"Total events              : "
    f"{len(events_df):,}"
)

print(
    f"Applications started      : "
    f"{applications_started:,}"
)

print(
    f"Applications submitted    : "
    f"{applications_submitted:,}"
)

print(
    f"Eligible applications     : "
    f"{eligible_applications:,}"
)

print(
    f"Payment initiated         : "
    f"{payment_initiated:,}"
)

print(
    f"Payment captured          : "
    f"{payment_captured:,}"
)

print(
    f"Paid applications         : "
    f"{paid_applications:,}"
)

print(
    f"Submission rate           : "
    f"{submission_rate:.2f}%"
)

print(
    f"Eligibility rate          : "
    f"{eligibility_rate:.2f}%"
)

print(
    f"Payment initiation rate   : "
    f"{payment_initiation_rate:.2f}%"
)

print(
    f"Payment capture rate      : "
    f"{payment_capture_rate:.2f}%"
)

print(
    f"Paid application conversion: "
    f"{paid_application_conversion:.2f}%"
)

print(
    f"Application-to-payment    : "
    f"{application_to_payment:.2f}%"
)

print(
    f"Started-to-paid           : "
    f"{started_to_paid:.2f}%"
)

print(
    f"Payment failure rate      : "
    f"{payment_failure_rate:.2f}%"
)

print(
    f"Gross payment volume      : "
    f"INR {gross_payment_volume:,.2f}"
)

print(
    f"Recognized revenue        : "
    f"INR {recognized_revenue:,.2f}"
)

print(
    f"Refund amount             : "
    f"INR {refund_amount:,.2f}"
)

print(
    f"Net revenue               : "
    f"INR {net_revenue:,.2f}"
)

print(
    f"Revenue / paid application: "
    f"INR {revenue_per_paid_application:,.2f}"
)

print()
print("VALIDATION")
print("-" * 65)

print(
    f"Duplicate event IDs       : "
    f"{validation['duplicate_event_ids']}"
)

print(
    f"Missing event IDs         : "
    f"{validation['missing_event_ids']}"
)

print(
    f"Missing application IDs   : "
    f"{validation['missing_application_ids']}"
)

print(
    f"Invalid event names       : "
    f"{validation['invalid_event_names']}"
)

print(
    f"Submitted without start   : "
    f"{validation['submitted_without_start']}"
)

print(
    f"Eligible without submit   : "
    f"{validation['eligible_without_submission']}"
)

print(
    f"Payment without eligible  : "
    f"{validation['payment_without_eligible']}"
)

print(
    f"Captured without initiated: "
    f"{validation['captured_without_initiated']}"
)

print(
    f"Revenue without capture   : "
    f"{validation['revenue_without_capture']}"
)

print(
    f"Refund without capture    : "
    f"{validation['refund_without_capture']}"
)

print(
    f"Validation status         : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 65)

print(EVENTS_FILE)
print(BASELINE_FILE)
print(VALIDATION_FILE)
print(HTML_FILE)