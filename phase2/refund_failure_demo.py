
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILE = BASE_DIR / "payment_events_demo.csv"

OUTPUT_METRICS = (
    BASE_DIR /
    "refund_failure_metrics_demo.csv"
)

OUTPUT_FAILURES = (
    BASE_DIR /
    "payment_failure_analysis.csv"
)

OUTPUT_REFUNDS = (
    BASE_DIR /
    "refund_analysis.csv"
)

OUTPUT_RECONCILIATION = (
    BASE_DIR /
    "payment_reconciliation_demo.json"
)

OUTPUT_HTML = (
    BASE_DIR /
    "refund_failure_dashboard.html"
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
# LOAD SOURCE DATA
# ============================================================

if not SOURCE_FILE.exists():

    raise FileNotFoundError(
        f"Source file not found:\n{SOURCE_FILE}\n\n"
        "Run the Day 26 payment demo first:\n"
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
    "total_events": int(len(df)),

    "duplicate_event_ids": int(
        df["event_id"]
        .duplicated()
        .sum()
    ),

    "missing_event_ids": int(
        df["event_id"]
        .isna()
        .sum()
    ),

    "missing_payment_ids": int(
        df["payment_id"]
        .isna()
        .sum()
    ),

    "invalid_event_names": int(
        (
            ~df["event_name"]
            .isin(APPROVED_EVENTS)
        ).sum()
    ),

    "invalid_timestamps": int(
        df["event_timestamp"]
        .isna()
        .sum()
    ),
}


# ============================================================
# PAYMENT EVENT TABLES
# ============================================================

initiated = df[
    df["event_name"]
    == "payment_initiated"
].copy()

authorized = df[
    df["event_name"]
    == "payment_authorized"
].copy()

failed = df[
    df["event_name"]
    == "payment_failed"
].copy()

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

chargebacks = df[
    df["event_name"]
    == "payment_chargeback"
].copy()


# ============================================================
# LIFECYCLE VALIDATION
# ============================================================

initiated_ids = set(
    initiated["payment_id"]
)

authorized_ids = set(
    authorized["payment_id"]
)

captured_ids = set(
    captured["payment_id"]
)

failed_ids = set(
    failed["payment_id"]
)

refunded_ids = set(
    refunded["payment_id"]
)

chargeback_ids = set(
    chargebacks["payment_id"]
)

recognized_ids = set(
    recognized["payment_id"]
)


validation[
    "authorized_without_initiated"
] = len(
    authorized_ids
    - initiated_ids
)

validation[
    "captured_without_authorized"
] = len(
    captured_ids
    - authorized_ids
)

validation[
    "captured_without_initiated"
] = len(
    captured_ids
    - initiated_ids
)

validation[
    "failed_without_initiated"
] = len(
    failed_ids
    - initiated_ids
)

validation[
    "refund_without_capture"
] = len(
    refunded_ids
    - captured_ids
)

validation[
    "chargeback_without_capture"
] = len(
    chargeback_ids
    - captured_ids
)

validation[
    "revenue_without_capture"
] = len(
    recognized_ids
    - captured_ids
)


# ============================================================
# MONEY DATA
# ============================================================

gross_payment_volume = float(
    captured["amount"].sum()
)

refund_amount = float(
    refunded["amount"].sum()
)

chargeback_amount = float(
    chargebacks["amount"].sum()
)

recognized_revenue = float(
    recognized["amount"].sum()
)


# ============================================================
# CORE COUNTS
# ============================================================

payment_attempts = initiated[
    "payment_id"
].nunique()

failed_payments = failed[
    "payment_id"
].nunique()

successful_payments = captured[
    "payment_id"
].nunique()

refunded_payments = refunded[
    "payment_id"
].nunique()

refund_count = len(
    refunded
)

chargeback_transactions = (
    chargebacks[
        "payment_id"
    ].nunique()
)


# ============================================================
# REFUND CLASSIFICATION
# ============================================================

captured_amount_by_payment = (
    captured
    .groupby("payment_id")[
        "amount"
    ]
    .sum()
)

refund_amount_by_payment = (
    refunded
    .groupby("payment_id")[
        "amount"
    ]
    .sum()
)

refund_comparison = pd.DataFrame({
    "captured_amount":
        captured_amount_by_payment,

    "refund_amount":
        refund_amount_by_payment,
}).fillna(0)


refund_comparison = (
    refund_comparison[
        refund_comparison[
            "refund_amount"
        ] > 0
    ]
    .copy()
)


refund_comparison[
    "refund_type"
] = refund_comparison.apply(
    lambda row:
        "full_refund"
        if abs(
            row["refund_amount"]
            - row["captured_amount"]
        ) < 0.01
        else "partial_refund",
    axis=1,
)


full_refunds = int(
    (
        refund_comparison[
            "refund_type"
        ]
        == "full_refund"
    ).sum()
)

partial_refunds = int(
    (
        refund_comparison[
            "refund_type"
        ]
        == "partial_refund"
    ).sum()
)


refund_comparison.reset_index(
    inplace=True
)

refund_comparison.to_csv(
    OUTPUT_REFUNDS,
    index=False,
)


# ============================================================
# RATES
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


payment_failure_rate = pct(
    failed_payments,
    payment_attempts,
)

payment_success_rate = pct(
    successful_payments,
    payment_attempts,
)

refund_transaction_rate = pct(
    refunded_payments,
    successful_payments,
)

refund_value_rate = pct(
    refund_amount,
    gross_payment_volume,
)

full_refund_rate = pct(
    full_refunds,
    refunded_payments,
)

partial_refund_rate = pct(
    partial_refunds,
    refunded_payments,
)

chargeback_rate = pct(
    chargeback_amount,
    gross_payment_volume,
)

refund_to_revenue = pct(
    refund_amount,
    recognized_revenue,
)

chargeback_to_revenue = pct(
    chargeback_amount,
    recognized_revenue,
)


# ============================================================
# FAILURE ANALYSIS
# ============================================================

if len(failed) > 0:

    failure_analysis = (
        failed
        .groupby(
            [
                "gateway",
                "failure_code",
                "failure_reason",
            ]
        )
        .agg(
            failed_payments=(
                "payment_id",
                "nunique",
            ),
            failure_amount=(
                "amount",
                "sum",
            ),
        )
        .reset_index()
        .sort_values(
            "failed_payments",
            ascending=False,
        )
    )

else:

    failure_analysis = pd.DataFrame(
        columns=[
            "gateway",
            "failure_code",
            "failure_reason",
            "failed_payments",
            "failure_amount",
        ]
    )


failure_analysis.to_csv(
    OUTPUT_FAILURES,
    index=False,
)


# ============================================================
# RECONCILIATION
# ============================================================

net_retained_payment_value = (
    gross_payment_volume
    - refund_amount
    - chargeback_amount
)

expected_retained_value = (
    gross_payment_volume
    - refund_amount
    - chargeback_amount
)

reconciliation_gap = (
    net_retained_payment_value
    - expected_retained_value
)


# Money-control check
monetary_adjustment_not_exceeding_capture = (
    refund_amount
    + chargeback_amount
    <= gross_payment_volume
    + 0.01
)


validation[
    "refund_plus_chargeback_exceeds_capture"
] = int(
    not monetary_adjustment_not_exceeding_capture
)

validation[
    "reconciliation_gap"
] = round(
    reconciliation_gap,
    2,
)


validation[
    "validation_passed"
] = all(
    value == 0
    for key, value in validation.items()
    if key not in {
        "total_events",
        "validation_passed",
    }
)


with open(
    OUTPUT_RECONCILIATION,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        {
            "gross_payment_volume":
                round(
                    gross_payment_volume,
                    2,
                ),

            "refund_amount":
                round(
                    refund_amount,
                    2,
                ),

            "chargeback_amount":
                round(
                    chargeback_amount,
                    2,
                ),

            "net_retained_payment_value":
                round(
                    net_retained_payment_value,
                    2,
                ),

            "reconciliation_gap":
                round(
                    reconciliation_gap,
                    2,
                ),

            "validation":
                validation,
        },
        file,
        indent=2,
    )


# ============================================================
# METRICS OUTPUT
# ============================================================

metrics = [
    (
        "Payment Attempts",
        payment_attempts,
        "count",
    ),
    (
        "Failed Payments",
        failed_payments,
        "count",
    ),
    (
        "Successful Payments",
        successful_payments,
        "count",
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
        "Payment Success Rate",
        round(
            payment_success_rate,
            2,
        ),
        "%",
    ),
    (
        "Refunded Payments",
        refunded_payments,
        "count",
    ),
    (
        "Refund Count",
        refund_count,
        "count",
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
        "Refund Transaction Rate",
        round(
            refund_transaction_rate,
            2,
        ),
        "%",
    ),
    (
        "Refund Value Rate",
        round(
            refund_value_rate,
            2,
        ),
        "%",
    ),
    (
        "Full Refunds",
        full_refunds,
        "count",
    ),
    (
        "Partial Refunds",
        partial_refunds,
        "count",
    ),
    (
        "Full Refund Rate",
        round(
            full_refund_rate,
            2,
        ),
        "%",
    ),
    (
        "Partial Refund Rate",
        round(
            partial_refund_rate,
            2,
        ),
        "%",
    ),
    (
        "Chargeback Transactions",
        chargeback_transactions,
        "count",
    ),
    (
        "Chargeback Amount",
        round(
            chargeback_amount,
            2,
        ),
        "INR",
    ),
    (
        "Chargeback Value Rate",
        round(
            chargeback_rate,
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
        "Net Retained Payment Value",
        round(
            net_retained_payment_value,
            2,
        ),
        "INR",
    ),
    (
        "Retention Rate",
        round(
            pct(
                net_retained_payment_value,
                gross_payment_volume,
            ),
            2,
        ),
        "%",
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
        "Refund-to-Revenue Ratio",
        round(
            refund_to_revenue,
            2,
        ),
        "%",
    ),
    (
        "Chargeback-to-Revenue Ratio",
        round(
            chargeback_to_revenue,
            2,
        ),
        "%",
    ),
    (
        "Reconciliation Gap",
        round(
            reconciliation_gap,
            2,
        ),
        "INR",
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
    OUTPUT_METRICS,
    index=False,
)


# ============================================================
# DAILY TREND
# ============================================================

df["date"] = (
    df["event_timestamp"]
    .dt.strftime("%Y-%m-%d")
)

failed_daily = (
    failed.assign(
        date=failed[
            "event_timestamp"
        ].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")
    .size()
    .rename("failed_payments")
)

refund_daily = (
    refunded.assign(
        date=refunded[
            "event_timestamp"
        ].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")[
        "amount"
    ]
    .sum()
    .rename("refund_amount")
)

chargeback_daily = (
    chargebacks.assign(
        date=chargebacks[
            "event_timestamp"
        ].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")[
        "amount"
    ]
    .sum()
    .rename("chargeback_amount")
)

captured_daily = (
    captured.assign(
        date=captured[
            "event_timestamp"
        ].dt.strftime(
            "%Y-%m-%d"
        )
    )
    .groupby("date")[
        "amount"
    ]
    .sum()
    .rename("gross_payment_volume")
)

trend = pd.concat(
    [
        failed_daily,
        refund_daily,
        chargeback_daily,
        captured_daily,
    ],
    axis=1,
).fillna(0)

trend = (
    trend
    .reset_index()
    .sort_values("date")
)

trend_json = trend.to_json(
    orient="records"
)


# ============================================================
# HEALTH STATUS
# ============================================================

if reconciliation_gap != 0:

    health_status = "RISK"

elif payment_failure_rate >= 10:

    health_status = "WATCH"

elif refund_value_rate >= 5:

    health_status = "WATCH"

elif chargeback_rate >= 2:

    health_status = "WATCH"

else:

    health_status = "HEALTHY"


# ============================================================
# HTML DASHBOARD
# ============================================================

status_class = (
    "healthy"
    if health_status == "HEALTHY"
    else "watch"
    if health_status == "WATCH"
    else "risk"
)

validation_class = (
    "pass"
    if validation["validation_passed"]
    else "fail"
)


failure_rows = ""

for _, row in failure_analysis.iterrows():

    failure_rows += f"""
    <tr>
        <td>{row["gateway"]}</td>
        <td>{row["failure_code"]}</td>
        <td>{row["failure_reason"]}</td>
        <td>{int(row["failed_payments"])}</td>
        <td>INR {float(row["failure_amount"]):,.2f}</td>
    </tr>
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
PlaceMux — Refund & Failure Dashboard
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

.pass {{
    background: #dcfce7;
    color: #166534;
}}

.fail {{
    background: #fee2e2;
    color: #991b1b;
}}

.validation {{
    display: inline-block;
    padding: 7px 13px;
    border-radius: 20px;
    font-weight: 700;
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

.note {{
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.5;
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

code {{
    background: #f1f5f9;
    padding: 3px 6px;
    border-radius: 5px;
}}

canvas {{
    width: 100%;
    height: 320px;
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
Refund & Failure Dashboard
</h1>

<div class="subtitle">

PlaceMux Phase 2 — Task 8 ·
Receipts, Refunds & Reconciliation ·
Synthetic Demonstration Data

</div>


<!-- ===================================================== -->
<!-- HEALTH -->
<!-- ===================================================== -->

<div class="section">

<h2>
Payment Health
</h2>

<p>

Current status:

<span class="status {status_class}">
{health_status}
</span>

</p>

<p class="note">

Health status is a rules-based demonstration signal.
Production thresholds should be calibrated from validated historical
payment performance.

</p>

</div>


<!-- ===================================================== -->
<!-- PAYMENT KPIS -->
<!-- ===================================================== -->

<div class="grid">

<div class="card">

<h3>
Payment Attempts
</h3>

<div class="value">
{payment_attempts}
</div>

</div>


<div class="card">

<h3>
Failed Payments
</h3>

<div class="value">
{failed_payments}
</div>

</div>


<div class="card">

<h3>
Payment Failure Rate
</h3>

<div class="value">
{payment_failure_rate:.1f}%
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
Refunded Payments
</h3>

<div class="value">
{refunded_payments}
</div>

</div>


<div class="card">

<h3>
Refund Amount
</h3>

<div class="value">
INR {refund_amount:,.0f}
</div>

</div>


<div class="card">

<h3>
Chargebacks
</h3>

<div class="value">
{chargeback_transactions}
</div>

</div>


<div class="card">

<h3>
Chargeback Amount
</h3>

<div class="value">
INR {chargeback_amount:,.0f}
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- REFUNDS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Refund Analytics
</h2>

<div class="metric-grid">

<div class="metric">
<strong>Refund Count</strong>
<br>
{refund_count}
</div>

<div class="metric">
<strong>Refund Transaction Rate</strong>
<br>
{refund_transaction_rate:.1f}%
</div>

<div class="metric">
<strong>Refund Value Rate</strong>
<br>
{refund_value_rate:.1f}%
</div>

<div class="metric">
<strong>Full Refunds</strong>
<br>
{full_refunds}
</div>

<div class="metric">
<strong>Partial Refunds</strong>
<br>
{partial_refunds}
</div>

<div class="metric">
<strong>Partial Refund Rate</strong>
<br>
{partial_refund_rate:.1f}%
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- RECONCILIATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Payment Reconciliation
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
Refund Amount
</strong>

<br>

INR {refund_amount:,.2f}

</div>


<div class="metric">

<strong>
Chargeback Amount
</strong>

<br>

INR {chargeback_amount:,.2f}

</div>


<div class="metric">

<strong>
Net Retained Value
</strong>

<br>

INR {net_retained_payment_value:,.2f}

</div>


<div class="metric">

<strong>
Retention Rate
</strong>

<br>

{
    pct(
        net_retained_payment_value,
        gross_payment_volume
    )
:.1f}%

</div>


<div class="metric">

<strong>
Reconciliation Gap
</strong>

<br>

INR {reconciliation_gap:,.2f}

</div>

</div>

</div>


<!-- ===================================================== -->
<!-- FAILURE ANALYSIS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Payment Failure Analysis
</h2>

<table>

<thead>

<tr>

<th>Gateway</th>
<th>Failure Code</th>
<th>Reason</th>
<th>Count</th>
<th>Failure Amount</th>

</tr>

</thead>

<tbody>

{failure_rows}

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- TREND -->
<!-- ===================================================== -->

<div class="section">

<h2>
Payment Issues Over Time
</h2>

<canvas id="trendChart"></canvas>

</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Validation
</h2>

<p>

Validation status:

<span class="
validation
{validation_class}
">

{
    "PASS"
    if validation["validation_passed"]
    else "FAIL"
}

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
<strong>Missing Payment IDs</strong>
<br>
{validation["missing_payment_ids"]}
</div>

<div class="metric">
<strong>Invalid Event Names</strong>
<br>
{validation["invalid_event_names"]}
</div>

<div class="metric">
<strong>Lifecycle Errors</strong>
<br>
{
    validation["authorized_without_initiated"]
    + validation["captured_without_authorized"]
    + validation["failed_without_initiated"]
    + validation["refund_without_capture"]
    + validation["chargeback_without_capture"]
    + validation["revenue_without_capture"]
}
</div>

<div class="metric">
<strong>Reconciliation Gap</strong>
<br>
INR {reconciliation_gap:,.2f}
</div>

</div>

</div>


<!-- ===================================================== -->
<!-- SOURCE -->
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
Source type:
</strong>

Synthetic payment event stream generated for the Day 26 revenue
metrics demonstration and reused here for refund/failure analytics.

</p>

<p>

<strong>
Refund Amount:
</strong>

Sum of amounts on
<code>payment_refunded</code>
events.

</p>

<p>

<strong>
Net Retained Payment Value:
</strong>

Gross Payment Volume minus refunds and chargebacks.

</p>

<p>

<strong>
Reconciliation Gap:
</strong>

Calculated retained value minus expected retained value.
A clean demonstration produces zero.

</p>

</div>


</div>


<script>

const trendData =
{trend_json};

const canvas =
document.getElementById(
    "trendChart"
);

const ctx =
canvas.getContext(
    "2d"
);


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
            ...trendData.flatMap(
                row => [
                    Number(
                        row.failed_payments
                    ),
                    Number(
                        row.refund_amount
                    ) / 1000,
                    Number(
                        row.chargeback_amount
                    ) / 1000,
                    Number(
                        row.gross_payment_volume
                    ) / 1000
                ]
            )
        );


    function x(index) {{

        return padding
            + index
            * chartWidth
            / Math.max(
                trendData.length - 1,
                1
            );

    }}


    function y(value) {{

        return height
            - padding
            - (
                value /
                Math.max(
                    maxValue,
                    1
                )
            )
            * chartHeight;

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
        key,
        divisor
    ) {{

        ctx.beginPath();

        trendData.forEach(
            (row, index) => {{

                const value =
                    Number(
                        row[key]
                    )
                    / divisor;

                const px =
                    x(index);

                const py =
                    y(value);


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
        "failed_payments",
        1
    );

    drawSeries(
        "refund_amount",
        1000
    );

    drawSeries(
        "chargeback_amount",
        1000
    );

    drawSeries(
        "gross_payment_volume",
        1000
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
print("DAY 28 — REFUND & FAILURE ANALYTICS")
print("=" * 65)

print(
    f"Source events             : "
    f"{len(df):,}"
)

print(
    f"Payment attempts          : "
    f"{payment_attempts:,}"
)

print(
    f"Failed payments           : "
    f"{failed_payments:,}"
)

print(
    f"Successful payments       : "
    f"{successful_payments:,}"
)

print(
    f"Payment failure rate      : "
    f"{payment_failure_rate:.2f}%"
)

print(
    f"Refunded payments         : "
    f"{refunded_payments:,}"
)

print(
    f"Refund count              : "
    f"{refund_count:,}"
)

print(
    f"Refund amount             : "
    f"INR {refund_amount:,.2f}"
)

print(
    f"Refund value rate         : "
    f"{refund_value_rate:.2f}%"
)

print(
    f"Full refunds              : "
    f"{full_refunds:,}"
)

print(
    f"Partial refunds           : "
    f"{partial_refunds:,}"
)

print(
    f"Chargeback transactions   : "
    f"{chargeback_transactions:,}"
)

print(
    f"Chargeback amount         : "
    f"INR {chargeback_amount:,.2f}"
)

print(
    f"Chargeback value rate     : "
    f"{chargeback_rate:.2f}%"
)

print(
    f"Gross payment volume      : "
    f"INR {gross_payment_volume:,.2f}"
)

print(
    f"Net retained value        : "
    f"INR {net_retained_payment_value:,.2f}"
)

print(
    f"Retention rate            : "
    f"{pct(net_retained_payment_value, gross_payment_volume):.2f}%"
)

print(
    f"Reconciliation gap        : "
    f"INR {reconciliation_gap:,.2f}"
)

print(
    f"Health status             : "
    f"{health_status}"
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
    f"Missing payment IDs       : "
    f"{validation['missing_payment_ids']}"
)

print(
    f"Invalid event names       : "
    f"{validation['invalid_event_names']}"
)

print(
    f"Authorization errors     : "
    f"{validation['authorized_without_initiated']}"
)

print(
    f"Capture errors            : "
    f"{validation['captured_without_authorized']}"
)

print(
    f"Failure lifecycle errors  : "
    f"{validation['failed_without_initiated']}"
)

print(
    f"Refund lifecycle errors   : "
    f"{validation['refund_without_capture']}"
)

print(
    f"Chargeback lifecycle errs : "
    f"{validation['chargeback_without_capture']}"
)

print(
    f"Revenue lifecycle errors  : "
    f"{validation['revenue_without_capture']}"
)

print(
    f"Validation status         : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 65)

print(OUTPUT_METRICS)
print(OUTPUT_FAILURES)
print(OUTPUT_REFUNDS)
print(OUTPUT_RECONCILIATION)
print(OUTPUT_HTML)