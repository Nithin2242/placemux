
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILE = (
    BASE_DIR /
    "payment_events_demo.csv"
)

METRICS_FILE = (
    BASE_DIR /
    "arpu_cohort_metrics_demo.csv"
)

COHORT_FILE = (
    BASE_DIR /
    "cohort_revenue_demo.csv"
)

CUSTOMER_FILE = (
    BASE_DIR /
    "customer_revenue_demo.csv"
)

VALIDATION_FILE = (
    BASE_DIR /
    "arpu_cohort_validation.json"
)

HTML_FILE = (
    BASE_DIR /
    "arpu_cohort_dashboard.html"
)


APPROVED_EVENTS = {
    "payment_initiated",
    "payment_authorized",
    "payment_failed",
    "payment_captured",
    "revenue_recognized",
    "payment_refunded",
    "payment_chargeback",
}


# ============================================================
# LOAD DATA
# ============================================================

if not SOURCE_FILE.exists():

    raise FileNotFoundError(
        "Day 26 source file not found:\n"
        f"{SOURCE_FILE}\n\n"
        "Run first:\n"
        "python phase2/revenue_metrics_demo.py"
    )


df = pd.read_csv(
    SOURCE_FILE
)


df["event_timestamp"] = pd.to_datetime(
    df["event_timestamp"],
    errors="coerce",
)


# ============================================================
# BASIC VALIDATION
# ============================================================

validation = {

    "total_events":
        int(len(df)),

    "duplicate_event_ids":
        int(
            df["event_id"]
            .duplicated()
            .sum()
        ),

    "missing_event_ids":
        int(
            df["event_id"]
            .isna()
            .sum()
        ),

    "missing_payment_ids":
        int(
            df["payment_id"]
            .isna()
            .sum()
        ),

    "missing_company_ids":
        int(
            df["company_id"]
            .isna()
            .sum()
        ),

    "invalid_event_names":
        int(
            (
                ~df[
                    "event_name"
                ].isin(
                    APPROVED_EVENTS
                )
            ).sum()
        ),

    "invalid_timestamps":
        int(
            df[
                "event_timestamp"
            ].isna()
            .sum()
        ),
}


# ============================================================
# EVENT TABLES
# ============================================================

captured = df[
    df["event_name"]
    == "payment_captured"
].copy()


recognized = df[
    df["event_name"]
    == "revenue_recognized"
].copy()


refunded = df[
    df["event_name"]
    == "payment_refunded"
].copy()


initiated = df[
    df["event_name"]
    == "payment_initiated"
].copy()


failed = df[
    df["event_name"]
    == "payment_failed"
].copy()


# ============================================================
# PAYMENT RELATIONSHIP VALIDATION
# ============================================================

initiated_ids = set(
    initiated[
        "payment_id"
    ].dropna()
)

captured_ids = set(
    captured[
        "payment_id"
    ].dropna()
)

recognized_ids = set(
    recognized[
        "payment_id"
    ].dropna()
)

refunded_ids = set(
    refunded[
        "payment_id"
    ].dropna()
)


validation[
    "captured_without_initiated"
] = len(
    captured_ids
    - initiated_ids
)


validation[
    "revenue_without_capture"
] = len(
    recognized_ids
    - captured_ids
)


validation[
    "refund_without_capture"
] = len(
    refunded_ids
    - captured_ids
)


# ============================================================
# FIRST PAID DATE
# ============================================================

first_paid = (
    captured
    .groupby(
        "company_id"
    )[
        "event_timestamp"
    ]
    .min()
    .rename(
        "first_paid_date"
    )
    .reset_index()
)


first_paid[
    "cohort_month"
] = (
    first_paid[
        "first_paid_date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


# ============================================================
# CUSTOMER REVENUE
# ============================================================

customer_revenue = (
    recognized
    .groupby(
        "company_id"
    )[
        "amount"
    ]
    .sum()
    .rename(
        "recognized_revenue"
    )
    .reset_index()
)


customer_refunds = (
    refunded
    .groupby(
        "company_id"
    )[
        "amount"
    ]
    .sum()
    .rename(
        "refund_amount"
    )
    .reset_index()
)


customer_payments = (
    captured
    .groupby(
        "company_id"
    )[
        "payment_id"
    ]
    .nunique()
    .rename(
        "successful_payments"
    )
    .reset_index()
)


customer = (
    first_paid
    .merge(
        customer_revenue,
        on="company_id",
        how="left",
    )
    .merge(
        customer_refunds,
        on="company_id",
        how="left",
    )
    .merge(
        customer_payments,
        on="company_id",
        how="left",
    )
    .fillna(
        {
            "recognized_revenue": 0.0,
            "refund_amount": 0.0,
            "successful_payments": 0,
        }
    )
)


customer[
    "net_revenue"
] = (
    customer[
        "recognized_revenue"
    ]
    -
    customer[
        "refund_amount"
    ]
)


customer[
    "payer_type"
] = customer[
    "successful_payments"
].apply(
    lambda value:
        "Repeat"
        if value > 1
        else "New"
)


customer.to_csv(
    CUSTOMER_FILE,
    index=False,
)


# ============================================================
# GLOBAL ARPU
# ============================================================

paying_users = (
    customer[
        "company_id"
    ]
    .nunique()
)


successful_payments = (
    captured[
        "payment_id"
    ]
    .nunique()
)


recognized_revenue = float(
    recognized[
        "amount"
    ].sum()
)


refund_amount = float(
    refunded[
        "amount"
    ].sum()
)


net_revenue = (
    recognized_revenue
    -
    refund_amount
)


arpu = (
    recognized_revenue
    /
    paying_users
    if paying_users
    else 0
)


net_arpu = (
    net_revenue
    /
    paying_users
    if paying_users
    else 0
)


revenue_per_payment = (
    recognized_revenue
    /
    successful_payments
    if successful_payments
    else 0
)


repeat_payers = int(
    (
        customer[
            "payer_type"
        ]
        == "Repeat"
    ).sum()
)


repeat_payer_rate = (
    repeat_payers
    /
    paying_users
    * 100
    if paying_users
    else 0
)


# ============================================================
# COHORT ANALYSIS
# ============================================================

cohort = (
    customer
    .groupby(
        "cohort_month"
    )
    .agg(
        cohort_customers=(
            "company_id",
            "nunique",
        ),

        cohort_revenue=(
            "recognized_revenue",
            "sum",
        ),

        cohort_refunds=(
            "refund_amount",
            "sum",
        ),

        cohort_net_revenue=(
            "net_revenue",
            "sum",
        ),

        successful_payments=(
            "successful_payments",
            "sum",
        ),
    )
    .reset_index()
)


cohort[
    "cohort_arpu"
] = (
    cohort[
        "cohort_revenue"
    ]
    /
    cohort[
        "cohort_customers"
    ]
)


cohort[
    "cohort_net_arpu"
] = (
    cohort[
        "cohort_net_revenue"
    ]
    /
    cohort[
        "cohort_customers"
    ]
)


cohort[
    "revenue_share"
] = (
    cohort[
        "cohort_revenue"
    ]
    /
    recognized_revenue
    * 100
    if recognized_revenue
    else 0
)


cohort = cohort.sort_values(
    "cohort_month"
)


cohort.to_csv(
    COHORT_FILE,
    index=False,
)


# ============================================================
# COHORT RECONCILIATION
# ============================================================

cohort_customer_gap = (
    int(
        cohort[
            "cohort_customers"
        ].sum()
    )
    -
    paying_users
)


cohort_revenue_gap = (
    float(
        cohort[
            "cohort_revenue"
        ].sum()
    )
    -
    recognized_revenue
)


cohort_refund_gap = (
    float(
        cohort[
            "cohort_refunds"
        ].sum()
    )
    -
    refund_amount
)


validation[
    "cohort_customer_gap"
] = round(
    cohort_customer_gap,
    6,
)


validation[
    "cohort_revenue_gap"
] = round(
    cohort_revenue_gap,
    6,
)


validation[
    "cohort_refund_gap"
] = round(
    cohort_refund_gap,
    6,
)


# ============================================================
# GLOBAL VALIDATION RESULT
# ============================================================

validation[
    "validation_passed"
] = all(
    value == 0
    for key, value
    in validation.items()
    if key not in {
        "total_events",
        "validation_passed",
    }
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
# METRIC OUTPUT
# ============================================================

metrics = [
    (
        "Paying Users",
        paying_users,
        "count",
    ),

    (
        "Successful Payments",
        successful_payments,
        "count",
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
        "ARPU",
        round(
            arpu,
            2,
        ),
        "INR",
    ),

    (
        "Net ARPU",
        round(
            net_arpu,
            2,
        ),
        "INR",
    ),

    (
        "Revenue per Payment",
        round(
            revenue_per_payment,
            2,
        ),
        "INR",
    ),

    (
        "Repeat Paying Users",
        repeat_payers,
        "count",
    ),

    (
        "Repeat Payer Rate",
        round(
            repeat_payer_rate,
            2,
        ),
        "%",
    ),

    (
        "Cohort Revenue Gap",
        round(
            cohort_revenue_gap,
            2,
        ),
        "INR",
    ),

    (
        "Cohort Customer Gap",
        cohort_customer_gap,
        "count",
    ),
]


metrics_df = pd.DataFrame(
    metrics,
    columns=[
        "metric",
        "value",
        "unit",
    ],
)


metrics_df.to_csv(
    METRICS_FILE,
    index=False,
)


# ============================================================
# DASHBOARD DATA
# ============================================================

cohort_records = cohort.to_dict(
    orient="records"
)


cohort_json = json.dumps(
    cohort_records,
    default=str,
)


# ============================================================
# HTML ROWS
# ============================================================

cohort_rows = ""

for _, row in cohort.iterrows():

    cohort_rows += f"""
    <tr>

        <td>
            {row["cohort_month"]}
        </td>

        <td>
            {int(row["cohort_customers"])}
        </td>

        <td>
            INR {row["cohort_revenue"]:,.2f}
        </td>

        <td>
            INR {row["cohort_refunds"]:,.2f}
        </td>

        <td>
            INR {row["cohort_net_revenue"]:,.2f}
        </td>

        <td>
            INR {row["cohort_arpu"]:,.2f}
        </td>

        <td>
            {row["revenue_share"]:.1f}%
        </td>

    </tr>
    """


# ============================================================
# HTML
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
PlaceMux — ARPU & Cohort Revenue
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
    font-size: 28px;
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

.note {{
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.5;
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

canvas {{
    width: 100%;
    height: 330px;
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
ARPU & Cohort Revenue
</h1>

<div class="subtitle">

PlaceMux Phase 2 —
Task 9 · Deepened Revenue Views ·
Synthetic Demonstration Data

</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Validation Status
</h2>

<p>

<span class="status {
    "pass"
    if validation["validation_passed"]
    else "fail"
}">

{
    "PASS"
    if validation["validation_passed"]
    else "FAIL"
}

</span>

</p>

<div class="metric-grid">

<div class="metric">

<strong>
Total Events
</strong>

<br>

{validation["total_events"]}

</div>


<div class="metric">

<strong>
Duplicate Event IDs
</strong>

<br>

{validation["duplicate_event_ids"]}

</div>


<div class="metric">

<strong>
Missing Company IDs
</strong>

<br>

{validation["missing_company_ids"]}

</div>


<div class="metric">

<strong>
Revenue Without Capture
</strong>

<br>

{validation["revenue_without_capture"]}

</div>


<div class="metric">

<strong>
Cohort Revenue Gap
</strong>

<br>

INR {cohort_revenue_gap:,.2f}

</div>


<div class="metric">

<strong>
Cohort Customer Gap
</strong>

<br>

{cohort_customer_gap}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- HEADLINE KPIS -->
<!-- ===================================================== -->

<div class="grid">


<div class="card">

<h3>
Paying Users
</h3>

<div class="value">
{paying_users}
</div>

</div>


<div class="card">

<h3>
Recognized Revenue
</h3>

<div class="value">
INR {recognized_revenue:,.0f}
</div>

</div>


<div class="card">

<h3>
Net Revenue
</h3>

<div class="value">
INR {net_revenue:,.0f}
</div>

</div>


<div class="card">

<h3>
ARPU
</h3>

<div class="value">
INR {arpu:,.2f}
</div>

</div>


<div class="card">

<h3>
Net ARPU
</h3>

<div class="value">
INR {net_arpu:,.2f}
</div>

</div>


<div class="card">

<h3>
Successful Payments
</h3>

<div class="value">
{successful_payments}
</div>

</div>


<div class="card">

<h3>
Revenue / Payment
</h3>

<div class="value">
INR {revenue_per_payment:,.2f}
</div>

</div>


<div class="card">

<h3>
Repeat Payer Rate
</h3>

<div class="value">
{repeat_payer_rate:.1f}%
</div>

</div>


</div>


<!-- ===================================================== -->
<!-- CUSTOMER MONETIZATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Customer Monetization
</h2>

<div class="metric-grid">

<div class="metric">
<strong>Paying Users</strong>
<br>
{paying_users}
</div>

<div class="metric">
<strong>Repeat Paying Users</strong>
<br>
{repeat_payers}
</div>

<div class="metric">
<strong>Repeat Payer Rate</strong>
<br>
{repeat_payer_rate:.1f}%
</div>

<div class="metric">
<strong>Recognized Revenue</strong>
<br>
INR {recognized_revenue:,.2f}
</div>

<div class="metric">
<strong>Refund Amount</strong>
<br>
INR {refund_amount:,.2f}
</div>

<div class="metric">
<strong>Net Revenue</strong>
<br>
INR {net_revenue:,.2f}
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- COHORT TABLE -->
<!-- ===================================================== -->

<div class="section">

<h2>
Cohort Revenue
</h2>

<table>

<thead>

<tr>

<th>
Cohort
</th>

<th>
Customers
</th>

<th>
Revenue
</th>

<th>
Refunds
</th>

<th>
Net Revenue
</th>

<th>
ARPU
</th>

<th>
Revenue Share
</th>

</tr>

</thead>

<tbody>

{cohort_rows}

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- COHORT CHART -->
<!-- ===================================================== -->

<div class="section">

<h2>
Cohort Revenue & ARPU
</h2>

<canvas
    id="cohortChart">
</canvas>

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

<code>
phase2/payment_events_demo.csv
</code>

</p>

<p>

<strong>
Customer:
</strong>

<code>
company_id
</code>

</p>

<p>

<strong>
Cohort:
</strong>

Calendar month of the company's first successful payment.

</p>

<p>

<strong>
ARPU:
</strong>

Recognized revenue divided by distinct paying companies.

</p>

<p>

<strong>
Net ARPU:
</strong>

Recognized revenue minus modeled refunds, divided by distinct paying
companies.

</p>

<p class="note">

The current results are synthetic demonstration metrics. The customer
definition and revenue treatment should be confirmed by the business
and finance owners before production adoption.

</p>

</div>


</div>


<script>

const cohortData =
{cohort_json};

const canvas =
document.getElementById(
    "cohortChart"
);

const ctx =
canvas.getContext(
    "2d"
);


function drawChart() {{

    const width =
        canvas.clientWidth || 1100;

    const height = 330;

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


    const padding = 50;

    const chartWidth =
        width -
        padding * 2;

    const chartHeight =
        height -
        padding * 2;


    const maxRevenue =
        Math.max(
            ...cohortData.map(
                row =>
                    Number(
                        row.cohort_revenue
                    )
            )
        );


    function x(index) {{

        return padding
            +
            index
            *
            chartWidth
            /
            Math.max(
                cohortData.length - 1,
                1
            );

    }}


    function y(value) {{

        return height -
            padding -
            value /
            Math.max(
                maxRevenue,
                1
            )
            *
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
        height -
        padding
    );

    ctx.lineTo(
        width -
        padding,
        height -
        padding
    );

    ctx.stroke();


    // Revenue line

    ctx.beginPath();

    cohortData.forEach(
        (row, index) => {{

            const px =
                x(index);

            const py =
                y(
                    Number(
                        row.cohort_revenue
                    )
                );


            if (
                index === 0
            ) {{

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

print("=" * 65)
print("DAY 29 — ARPU & COHORT REVENUE")
print("=" * 65)

print(
    f"Source events             : "
    f"{len(df):,}"
)

print(
    f"Paying users              : "
    f"{paying_users:,}"
)

print(
    f"Successful payments       : "
    f"{successful_payments:,}"
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
    f"ARPU                      : "
    f"INR {arpu:,.2f}"
)

print(
    f"Net ARPU                  : "
    f"INR {net_arpu:,.2f}"
)

print(
    f"Revenue per payment       : "
    f"INR {revenue_per_payment:,.2f}"
)

print(
    f"Repeat paying users       : "
    f"{repeat_payers:,}"
)

print(
    f"Repeat payer rate         : "
    f"{repeat_payer_rate:.2f}%"
)

print(
    f"Cohorts                   : "
    f"{len(cohort):,}"
)

print()
print("VALIDATION")
print("-" * 65)

print(
    f"Duplicate event IDs       : "
    f"{validation['duplicate_event_ids']}"
)

print(
    f"Missing payment IDs       : "
    f"{validation['missing_payment_ids']}"
)

print(
    f"Missing company IDs       : "
    f"{validation['missing_company_ids']}"
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
    f"Cohort revenue gap        : "
    f"INR {cohort_revenue_gap:,.2f}"
)

print(
    f"Cohort customer gap       : "
    f"{cohort_customer_gap}"
)

print(
    f"Validation status         : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 65)

print(METRICS_FILE)
print(COHORT_FILE)
print(CUSTOMER_FILE)
print(VALIDATION_FILE)
print(HTML_FILE)