from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


# ============================================================
# DAY 30 — MONETIZATION INTEGRATION & REVENUE DASHBOARD
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# INPUT FILES
# ============================================================

PAYMENT_SOURCE = (
    BASE_DIR /
    "payment_events_demo.csv"
)

APPLICATION_SOURCE = (
    BASE_DIR /
    "pay_per_application_events_demo.csv"
)


# ============================================================
# OUTPUT FILES
# ============================================================

METRICS_OUTPUT = (
    BASE_DIR /
    "revenue_dashboard_metrics_demo.csv"
)

COHORT_OUTPUT = (
    BASE_DIR /
    "revenue_dashboard_cohort.csv"
)

VALIDATION_OUTPUT = (
    BASE_DIR /
    "revenue_dashboard_validation.json"
)

HTML_OUTPUT = (
    BASE_DIR /
    "revenue_dashboard.html"
)


# ============================================================
# APPROVED EVENTS
# ============================================================

APPROVED_PAYMENT_EVENTS = {
    "payment_initiated",
    "payment_authorized",
    "payment_failed",
    "payment_captured",
    "revenue_recognized",
    "payment_refunded",
    "payment_chargeback",
}


APPROVED_APPLICATION_EVENTS = {
    "application_started",
    "application_submitted",
    "application_eligible",
    "payment_initiated",
    "payment_captured",
    "payment_failed",
    "payment_refunded",
    "revenue_recognized",
}


# ============================================================
# HELPERS
# ============================================================

def pct(
    numerator: float,
    denominator: float,
) -> float:
    """Return percentage safely."""

    if denominator == 0:
        return 0.0

    return (
        float(numerator)
        /
        float(denominator)
        *
        100
    )


def money(
    value: float,
) -> float:
    """Round monetary values to two decimals."""

    return round(
        float(value),
        2,
    )


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    """Fail clearly when required columns are absent."""

    missing = (
        required_columns
        -
        set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{sorted(missing)}"
        )


# ============================================================
# CHECK SOURCE FILES
# ============================================================

if not PAYMENT_SOURCE.exists():

    raise FileNotFoundError(
        f"""
Payment source not found:

{PAYMENT_SOURCE}

Run Day 26 first:

python phase2/revenue_metrics_demo.py
""".strip()
    )


if not APPLICATION_SOURCE.exists():

    raise FileNotFoundError(
        f"""
Application source not found:

{APPLICATION_SOURCE}

Run Day 27 first:

python phase2/pay_per_application_demo.py
""".strip()
    )


# ============================================================
# LOAD PAYMENT DATA
# ============================================================

payment_events = pd.read_csv(
    PAYMENT_SOURCE
)


require_columns(
    payment_events,
    {
        "event_id",
        "event_name",
        "event_timestamp",
        "payment_id",
        "company_id",
        "amount",
    },
    "Payment source",
)


payment_events[
    "event_timestamp"
] = pd.to_datetime(
    payment_events[
        "event_timestamp"
    ],
    errors="coerce",
)


payment_events[
    "amount"
] = pd.to_numeric(
    payment_events[
        "amount"
    ],
    errors="coerce",
)


# ============================================================
# LOAD APPLICATION DATA
# ============================================================

application_events = pd.read_csv(
    APPLICATION_SOURCE
)


require_columns(
    application_events,
    {
        "event_id",
        "event_name",
        "event_timestamp",
        "application_id",
    },
    "Application source",
)


application_events[
    "event_timestamp"
] = pd.to_datetime(
    application_events[
        "event_timestamp"
    ],
    errors="coerce",
)


# ============================================================
# PAYMENT EVENT TABLES
# ============================================================

payment_initiated_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_initiated"
    ]
    .copy()
)


payment_authorized_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_authorized"
    ]
    .copy()
)


payment_failed_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_failed"
    ]
    .copy()
)


payment_captured_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_captured"
    ]
    .copy()
)


revenue_recognized_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "revenue_recognized"
    ]
    .copy()
)


payment_refunded_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_refunded"
    ]
    .copy()
)


payment_chargeback_events = (
    payment_events[
        payment_events[
            "event_name"
        ]
        == "payment_chargeback"
    ]
    .copy()
)


# ============================================================
# APPLICATION EVENT TABLES
# ============================================================

application_started_events = (
    application_events[
        application_events[
            "event_name"
        ]
        == "application_started"
    ]
    .copy()
)


application_submitted_events = (
    application_events[
        application_events[
            "event_name"
        ]
        == "application_submitted"
    ]
    .copy()
)


application_eligible_events = (
    application_events[
        application_events[
            "event_name"
        ]
        == "application_eligible"
    ]
    .copy()
)


application_payment_initiated_events = (
    application_events[
        application_events[
            "event_name"
        ]
        == "payment_initiated"
    ]
    .copy()
)


application_payment_captured_events = (
    application_events[
        application_events[
            "event_name"
        ]
        == "payment_captured"
    ]
    .copy()
)


# ============================================================
# PAYMENT COUNTS
# ============================================================

payment_attempt_count = (
    payment_initiated_events[
        "payment_id"
    ]
    .dropna()
    .nunique()
)


successful_payment_count = (
    payment_captured_events[
        "payment_id"
    ]
    .dropna()
    .nunique()
)


failed_payment_count = (
    payment_failed_events[
        "payment_id"
    ]
    .dropna()
    .nunique()
)


refunded_payment_count = (
    payment_refunded_events[
        "payment_id"
    ]
    .dropna()
    .nunique()
)


chargeback_payment_count = (
    payment_chargeback_events[
        "payment_id"
    ]
    .dropna()
    .nunique()
)


# ============================================================
# PAYMENT VALUE METRICS
# ============================================================

gross_payment_volume = money(
    payment_captured_events[
        "amount"
    ]
    .fillna(0)
    .sum()
)


recognized_revenue = money(
    revenue_recognized_events[
        "amount"
    ]
    .fillna(0)
    .sum()
)


refund_amount = money(
    payment_refunded_events[
        "amount"
    ]
    .fillna(0)
    .sum()
)


chargeback_amount = money(
    payment_chargeback_events[
        "amount"
    ]
    .fillna(0)
    .sum()
)


net_revenue = money(
    recognized_revenue
    -
    refund_amount
    -
    chargeback_amount
)


net_retained_payment_value = money(
    gross_payment_volume
    -
    refund_amount
    -
    chargeback_amount
)


revenue_margin = pct(
    net_revenue,
    gross_payment_volume,
)


payment_failure_rate = pct(
    failed_payment_count,
    payment_attempt_count,
)


payment_success_rate = pct(
    successful_payment_count,
    payment_attempt_count,
)


refund_value_rate = pct(
    refund_amount,
    gross_payment_volume,
)


chargeback_value_rate = pct(
    chargeback_amount,
    gross_payment_volume,
)


retention_rate = pct(
    net_retained_payment_value,
    gross_payment_volume,
)


# ============================================================
# CUSTOMER / ARPU
# ============================================================

paying_company_count = (
    payment_captured_events[
        "company_id"
    ]
    .dropna()
    .nunique()
)


arpu = (
    recognized_revenue
    /
    paying_company_count
    if paying_company_count
    else 0.0
)


net_arpu = (
    net_revenue
    /
    paying_company_count
    if paying_company_count
    else 0.0
)


revenue_per_payment = (
    recognized_revenue
    /
    successful_payment_count
    if successful_payment_count
    else 0.0
)


company_payment_counts = (
    payment_captured_events
    .dropna(
        subset=[
            "company_id",
            "payment_id",
        ]
    )
    .groupby(
        "company_id"
    )[
        "payment_id"
    ]
    .nunique()
)


repeat_paying_company_count = int(
    (
        company_payment_counts
        > 1
    ).sum()
)


repeat_payer_rate = pct(
    repeat_paying_company_count,
    paying_company_count,
)


# ============================================================
# FIRST-PAID COHORT
# ============================================================

first_paid_by_company = (
    payment_captured_events
    .dropna(
        subset=[
            "company_id",
            "event_timestamp",
        ]
    )
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


first_paid_by_company[
    "cohort"
] = (
    first_paid_by_company[
        "first_paid_date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


# ============================================================
# COMPANY REVENUE
# ============================================================

company_revenue = (
    revenue_recognized_events
    .dropna(
        subset=[
            "company_id",
        ]
    )
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


company_refunds = (
    payment_refunded_events
    .dropna(
        subset=[
            "company_id",
        ]
    )
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


company_chargebacks = (
    payment_chargeback_events
    .dropna(
        subset=[
            "company_id",
        ]
    )
    .groupby(
        "company_id"
    )[
        "amount"
    ]
    .sum()
    .rename(
        "chargeback_amount"
    )
    .reset_index()
)


company_successful_payments = (
    payment_captured_events
    .dropna(
        subset=[
            "company_id",
            "payment_id",
        ]
    )
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


customer_revenue = (
    first_paid_by_company
    .merge(
        company_revenue,
        on="company_id",
        how="left",
    )
    .merge(
        company_refunds,
        on="company_id",
        how="left",
    )
    .merge(
        company_chargebacks,
        on="company_id",
        how="left",
    )
    .merge(
        company_successful_payments,
        on="company_id",
        how="left",
    )
)


for numeric_column in [
    "recognized_revenue",
    "refund_amount",
    "chargeback_amount",
    "successful_payments",
]:

    customer_revenue[
        numeric_column
    ] = pd.to_numeric(
        customer_revenue[
            numeric_column
        ],
        errors="coerce",
    ).fillna(0)


customer_revenue[
    "net_revenue"
] = (
    customer_revenue[
        "recognized_revenue"
    ]
    -
    customer_revenue[
        "refund_amount"
    ]
    -
    customer_revenue[
        "chargeback_amount"
    ]
)


# ============================================================
# COHORT REVENUE
# ============================================================

cohort_revenue = (
    customer_revenue
    .groupby(
        "cohort"
    )
    .agg(
        customers=(
            "company_id",
            "nunique",
        ),

        revenue=(
            "recognized_revenue",
            "sum",
        ),

        refunds=(
            "refund_amount",
            "sum",
        ),

        chargebacks=(
            "chargeback_amount",
            "sum",
        ),

        net_revenue=(
            "net_revenue",
            "sum",
        ),

        successful_payments=(
            "successful_payments",
            "sum",
        ),
    )
    .reset_index()
    .sort_values(
        "cohort"
    )
)


cohort_revenue[
    "arpu"
] = (
    cohort_revenue[
        "revenue"
    ]
    /
    cohort_revenue[
        "customers"
    ]
    .replace(
        0,
        pd.NA,
    )
)


cohort_revenue[
    "arpu"
] = (
    cohort_revenue[
        "arpu"
    ]
    .fillna(0)
)


cohort_revenue[
    "revenue_share"
] = (
    cohort_revenue[
        "revenue"
    ]
    /
    recognized_revenue
    *
    100
    if recognized_revenue
    else 0
)


cohort_revenue[
    "net_arpu"
] = (
    cohort_revenue[
        "net_revenue"
    ]
    /
    cohort_revenue[
        "customers"
    ]
    .replace(
        0,
        pd.NA,
    )
)


cohort_revenue[
    "net_arpu"
] = (
    cohort_revenue[
        "net_arpu"
    ]
    .fillna(0)
)


cohort_revenue.to_csv(
    COHORT_OUTPUT,
    index=False,
)


# ============================================================
# APPLICATION CONVERSION
# ============================================================

applications_started_count = (
    application_started_events[
        "application_id"
    ]
    .dropna()
    .nunique()
)


applications_submitted_count = (
    application_submitted_events[
        "application_id"
    ]
    .dropna()
    .nunique()
)


eligible_application_count = (
    application_eligible_events[
        "application_id"
    ]
    .dropna()
    .nunique()
)


application_payment_initiated_count = (
    application_payment_initiated_events[
        "application_id"
    ]
    .dropna()
    .nunique()
)


application_payment_captured_count = (
    application_payment_captured_events[
        "application_id"
    ]
    .dropna()
    .nunique()
)


paid_application_count = (
    application_payment_captured_count
)


application_submission_rate = pct(
    applications_submitted_count,
    applications_started_count,
)


application_eligibility_rate = pct(
    eligible_application_count,
    applications_submitted_count,
)


application_payment_initiation_rate = pct(
    application_payment_initiated_count,
    eligible_application_count,
)


application_payment_capture_rate = pct(
    application_payment_captured_count,
    application_payment_initiated_count,
)


application_to_payment_rate = pct(
    paid_application_count,
    applications_submitted_count,
)


started_to_paid_rate = pct(
    paid_application_count,
    applications_started_count,
)


# ============================================================
# PAYMENT LIFECYCLE VALIDATION
# ============================================================

payment_initiated_ids = set(
    payment_initiated_events[
        "payment_id"
    ]
    .dropna()
)


payment_captured_ids = set(
    payment_captured_events[
        "payment_id"
    ]
    .dropna()
)


payment_failed_ids = set(
    payment_failed_events[
        "payment_id"
    ]
    .dropna()
)


payment_refunded_ids = set(
    payment_refunded_events[
        "payment_id"
    ]
    .dropna()
)


payment_chargeback_ids = set(
    payment_chargeback_events[
        "payment_id"
    ]
    .dropna()
)


recognized_payment_ids = set(
    revenue_recognized_events[
        "payment_id"
    ]
    .dropna()
)


# ============================================================
# APPLICATION LIFECYCLE VALIDATION
# ============================================================

application_started_ids = set(
    application_started_events[
        "application_id"
    ]
    .dropna()
)


application_submitted_ids = set(
    application_submitted_events[
        "application_id"
    ]
    .dropna()
)


application_eligible_ids = set(
    application_eligible_events[
        "application_id"
    ]
    .dropna()
)


application_payment_initiated_ids = set(
    application_payment_initiated_events[
        "application_id"
    ]
    .dropna()
)


application_payment_captured_ids = set(
    application_payment_captured_events[
        "application_id"
    ]
    .dropna()
)


# ============================================================
# VALIDATION DICTIONARY
# ============================================================

validation = {

    "payment_total_events":
        int(
            len(
                payment_events
            )
        ),

    "application_total_events":
        int(
            len(
                application_events
            )
        ),

    "payment_duplicate_event_ids":
        int(
            payment_events[
                "event_id"
            ]
            .duplicated()
            .sum()
        ),

    "application_duplicate_event_ids":
        int(
            application_events[
                "event_id"
            ]
            .duplicated()
            .sum()
        ),

    "payment_missing_payment_ids":
        int(
            payment_events[
                "payment_id"
            ]
            .isna()
            .sum()
        ),

    "payment_missing_company_ids":
        int(
            payment_events[
                "company_id"
            ]
            .isna()
            .sum()
        ),

    "application_missing_application_ids":
        int(
            application_events[
                "application_id"
            ]
            .isna()
            .sum()
        ),

    "payment_invalid_event_names":
        int(
            (
                ~payment_events[
                    "event_name"
                ]
                .isin(
                    APPROVED_PAYMENT_EVENTS
                )
            )
            .sum()
        ),

    "application_invalid_event_names":
        int(
            (
                ~application_events[
                    "event_name"
                ]
                .isin(
                    APPROVED_APPLICATION_EVENTS
                )
            )
            .sum()
        ),

    "payment_invalid_timestamps":
        int(
            payment_events[
                "event_timestamp"
            ]
            .isna()
            .sum()
        ),

    "application_invalid_timestamps":
        int(
            application_events[
                "event_timestamp"
            ]
            .isna()
            .sum()
        ),
}


# ============================================================
# PAYMENT LIFECYCLE ERRORS
# ============================================================

validation[
    "captured_without_initiated"
] = len(
    payment_captured_ids
    -
    payment_initiated_ids
)


validation[
    "failed_without_initiated"
] = len(
    payment_failed_ids
    -
    payment_initiated_ids
)


validation[
    "refund_without_capture"
] = len(
    payment_refunded_ids
    -
    payment_captured_ids
)


validation[
    "chargeback_without_capture"
] = len(
    payment_chargeback_ids
    -
    payment_captured_ids
)


validation[
    "revenue_without_capture"
] = len(
    recognized_payment_ids
    -
    payment_captured_ids
)


# ============================================================
# APPLICATION LIFECYCLE ERRORS
# ============================================================

validation[
    "application_submitted_without_start"
] = len(
    application_submitted_ids
    -
    application_started_ids
)


validation[
    "application_eligible_without_submission"
] = len(
    application_eligible_ids
    -
    application_submitted_ids
)


validation[
    "application_payment_without_eligible"
] = len(
    application_payment_initiated_ids
    -
    application_eligible_ids
)


validation[
    "application_capture_without_payment"
] = len(
    application_payment_captured_ids
    -
    application_payment_initiated_ids
)


# ============================================================
# COHORT RECONCILIATION
# ============================================================

cohort_customer_gap = (
    int(
        cohort_revenue[
            "customers"
        ]
        .sum()
    )
    -
    paying_company_count
)


cohort_revenue_gap = money(
    cohort_revenue[
        "revenue"
    ]
    .sum()
    -
    recognized_revenue
)


cohort_refund_gap = money(
    cohort_revenue[
        "refunds"
    ]
    .sum()
    -
    refund_amount
)


cohort_chargeback_gap = money(
    cohort_revenue[
        "chargebacks"
    ]
    .sum()
    -
    chargeback_amount
)


validation[
    "cohort_customer_gap"
] = cohort_customer_gap


validation[
    "cohort_revenue_gap"
] = cohort_revenue_gap


validation[
    "cohort_refund_gap"
] = cohort_refund_gap


validation[
    "cohort_chargeback_gap"
] = cohort_chargeback_gap


# ============================================================
# VALUE RECONCILIATION
# ============================================================

expected_retained_value = money(
    gross_payment_volume
    -
    refund_amount
    -
    chargeback_amount
)


calculated_retained_value = money(
    net_retained_payment_value
)


reconciliation_gap = money(
    calculated_retained_value
    -
    expected_retained_value
)


validation[
    "reconciliation_gap"
] = reconciliation_gap


validation[
    "refund_plus_chargeback_exceeds_gpv"
] = int(
    (
        refund_amount
        +
        chargeback_amount
    )
    >
    gross_payment_volume
    +
    0.01
)


# ============================================================
# OVERALL VALIDATION
# ============================================================

validation_exclusions = {
    "payment_total_events",
    "application_total_events",
}


validation_passed = all(
    value == 0
    for key, value
    in validation.items()
    if key not in validation_exclusions
)


validation[
    "validation_passed"
] = bool(
    validation_passed
)


# ============================================================
# WRITE VALIDATION JSON
# ============================================================

with open(
    VALIDATION_OUTPUT,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        validation,
        file,
        indent=2,
    )


# ============================================================
# HEALTH STATUS
# ============================================================

if not validation_passed:

    health_status = "RISK"

elif (
    payment_failure_rate >= 10
    or
    refund_value_rate >= 5
    or
    chargeback_value_rate >= 2
):

    health_status = "WATCH"

else:

    health_status = "HEALTHY"


# ============================================================
# METRICS OUTPUT
# ============================================================

metrics = [

    (
        "Gross Payment Volume",
        money(gross_payment_volume),
        "INR",
        "Total captured payment value",
    ),

    (
        "Recognized Revenue",
        money(recognized_revenue),
        "INR",
        "Sum of revenue_recognized amounts",
    ),

    (
        "Refund Amount",
        money(refund_amount),
        "INR",
        "Sum of payment_refunded amounts",
    ),

    (
        "Chargeback Amount",
        money(chargeback_amount),
        "INR",
        "Sum of payment_chargeback amounts",
    ),

    (
        "Net Revenue",
        money(net_revenue),
        "INR",
        "Recognized revenue - refunds - chargebacks",
    ),

    (
        "Revenue Margin",
        round(
            revenue_margin,
            2,
        ),
        "%",
        "Net revenue / gross payment volume",
    ),

    (
        "Payment Attempts",
        payment_attempt_count,
        "count",
        "Distinct initiated payments",
    ),

    (
        "Successful Payments",
        successful_payment_count,
        "count",
        "Distinct captured payments",
    ),

    (
        "Failed Payments",
        failed_payment_count,
        "count",
        "Distinct failed payments",
    ),

    (
        "Payment Failure Rate",
        round(
            payment_failure_rate,
            2,
        ),
        "%",
        "Failed payments / attempts",
    ),

    (
        "Payment Success Rate",
        round(
            payment_success_rate,
            2,
        ),
        "%",
        "Successful payments / attempts",
    ),

    (
        "Refunded Payments",
        refunded_payment_count,
        "count",
        "Distinct refunded payments",
    ),

    (
        "Refund Value Rate",
        round(
            refund_value_rate,
            2,
        ),
        "%",
        "Refund amount / GPV",
    ),

    (
        "Chargeback Transactions",
        chargeback_payment_count,
        "count",
        "Distinct chargeback payments",
    ),

    (
        "Chargeback Value Rate",
        round(
            chargeback_value_rate,
            2,
        ),
        "%",
        "Chargeback amount / GPV",
    ),

    (
        "Net Retained Payment Value",
        money(
            net_retained_payment_value
        ),
        "INR",
        "GPV - refunds - chargebacks",
    ),

    (
        "Retention Rate",
        round(
            retention_rate,
            2,
        ),
        "%",
        "Net retained value / GPV",
    ),

    (
        "Paying Companies",
        paying_company_count,
        "count",
        "Distinct companies with captured payments",
    ),

    (
        "ARPU",
        money(arpu),
        "INR",
        "Recognized revenue / paying companies",
    ),

    (
        "Net ARPU",
        money(net_arpu),
        "INR",
        "Net revenue / paying companies",
    ),

    (
        "Revenue per Payment",
        money(
            revenue_per_payment
        ),
        "INR",
        "Recognized revenue / successful payments",
    ),

    (
        "Repeat Paying Companies",
        repeat_paying_company_count,
        "count",
        "Companies with more than one successful payment",
    ),

    (
        "Repeat Payer Rate",
        round(
            repeat_payer_rate,
            2,
        ),
        "%",
        "Repeat payers / paying companies",
    ),

    (
        "Applications Started",
        applications_started_count,
        "count",
        "Day 27 application stream",
    ),

    (
        "Applications Submitted",
        applications_submitted_count,
        "count",
        "Day 27 application stream",
    ),

    (
        "Eligible Applications",
        eligible_application_count,
        "count",
        "Day 27 application stream",
    ),

    (
        "Paid Applications",
        paid_application_count,
        "count",
        "Day 27 application stream",
    ),

    (
        "Application-to-Payment",
        round(
            application_to_payment_rate,
            2,
        ),
        "%",
        "Paid / submitted applications",
    ),

    (
        "Started-to-Paid",
        round(
            started_to_paid_rate,
            2,
        ),
        "%",
        "Paid / started applications",
    ),

    (
        "Reconciliation Gap",
        money(
            reconciliation_gap
        ),
        "INR",
        "Calculated retained value - expected retained value",
    ),

]


metrics_df = pd.DataFrame(
    metrics,
    columns=[
        "metric",
        "value",
        "unit",
        "definition",
    ],
)


metrics_df.to_csv(
    METRICS_OUTPUT,
    index=False,
)


# ============================================================
# COHORT HTML ROWS
# ============================================================

cohort_rows_html = ""

for _, row in cohort_revenue.iterrows():

    cohort_rows_html += f"""
    <tr>

        <td>
            {row["cohort"]}
        </td>

        <td>
            {int(row["customers"])}
        </td>

        <td>
            INR {row["revenue"]:,.2f}
        </td>

        <td>
            INR {row["refunds"]:,.2f}
        </td>

        <td>
            INR {row["chargebacks"]:,.2f}
        </td>

        <td>
            INR {row["net_revenue"]:,.2f}
        </td>

        <td>
            INR {row["arpu"]:,.2f}
        </td>

        <td>
            {row["revenue_share"]:.1f}%
        </td>

    </tr>
    """


# ============================================================
# FUNNEL STAGES
# ============================================================

funnel_stages = [
    (
        "Applications Started",
        applications_started_count,
    ),
    (
        "Applications Submitted",
        applications_submitted_count,
    ),
    (
        "Eligible Applications",
        eligible_application_count,
    ),
    (
        "Payment Initiated",
        application_payment_initiated_count,
    ),
    (
        "Payment Captured",
        application_payment_captured_count,
    ),
    (
        "Paid Applications",
        paid_application_count,
    ),
]


funnel_html = ""

for name, value in funnel_stages:

    width = (
        value
        /
        max(
            applications_started_count,
            1,
        )
        *
        100
    )

    funnel_html += f"""
    <div class="stage">

        <div class="stage-header">

            <span>
                {name}
            </span>

            <span>
                {value}
            </span>

        </div>

        <div class="bar">

            <div
                class="fill"
                style="
                    width:{width:.1f}%;
                "
            ></div>

        </div>

    </div>
    """


# ============================================================
# VALIDATION ERRORS
# ============================================================

payment_lifecycle_errors = (
    validation[
        "captured_without_initiated"
    ]
    +
    validation[
        "failed_without_initiated"
    ]
    +
    validation[
        "refund_without_capture"
    ]
    +
    validation[
        "chargeback_without_capture"
    ]
    +
    validation[
        "revenue_without_capture"
    ]
)


application_lifecycle_errors = (
    validation[
        "application_submitted_without_start"
    ]
    +
    validation[
        "application_eligible_without_submission"
    ]
    +
    validation[
        "application_payment_without_eligible"
    ]
    +
    validation[
        "application_capture_without_payment"
    ]
)


invalid_event_count = (
    validation[
        "payment_invalid_event_names"
    ]
    +
    validation[
        "application_invalid_event_names"
    ]
)


# ============================================================
# HTML DASHBOARD
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
PlaceMux — Monetization & Revenue Dashboard
</title>


<style>

* {{
    box-sizing: border-box;
}}


body {{

    margin: 0;

    background:
        #f5f7fa;

    color:
        #1f2937;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}}


.container {{

    max-width:
        1320px;

    margin:
        auto;

    padding:
        30px;
}}


h1 {{

    font-size:
        38px;

    margin:
        0 0 6px;
}}


h2 {{

    font-size:
        24px;

    margin-top:
        0;
}}


.subtitle {{

    color:
        #64748b;

    margin-bottom:
        28px;
}}


.grid {{

    display:
        grid;

    grid-template-columns:
        repeat(
            4,
            1fr
        );

    gap:
        15px;
}}


.card {{

    background:
        white;

    border-radius:
        14px;

    padding:
        20px;

    box-shadow:
        0 3px 12px
        rgba(
            0,
            0,
            0,
            .07
        );
}}


.label {{

    font-size:
        13px;

    color:
        #64748b;

    font-weight:
        600;
}}


.value {{

    font-size:
        28px;

    font-weight:
        700;

    margin-top:
        8px;
}}


.section {{

    background:
        white;

    border-radius:
        14px;

    margin-top:
        22px;

    padding:
        24px;

    box-shadow:
        0 3px 12px
        rgba(
            0,
            0,
            0,
            .07
        );
}}


.status {{

    display:
        inline-block;

    padding:
        8px 15px;

    border-radius:
        20px;

    font-weight:
        700;
}}


.healthy {{

    background:
        #dcfce7;

    color:
        #166534;
}}


.watch {{

    background:
        #fef3c7;

    color:
        #92400e;
}}


.risk {{

    background:
        #fee2e2;

    color:
        #991b1b;
}}


.metric-grid {{

    display:
        grid;

    grid-template-columns:
        repeat(
            3,
            1fr
        );

    gap:
        14px;
}}


.metric-box {{

    background:
        #f8fafc;

    border-radius:
        10px;

    padding:
        16px;
}}


.metric-label {{

    color:
        #64748b;

    font-size:
        13px;

    font-weight:
        600;
}}


.metric-value {{

    font-size:
        20px;

    font-weight:
        700;

    margin-top:
        7px;
}}


.funnel {{

    display:
        flex;

    flex-direction:
        column;

    gap:
        11px;
}}


.stage {{

    background:
        #f8fafc;

    padding:
        14px;

    border-radius:
        10px;
}}


.stage-header {{

    display:
        flex;

    justify-content:
        space-between;

    font-weight:
        700;
}}


.bar {{

    height:
        14px;

    margin-top:
        8px;

    background:
        #e5e7eb;

    border-radius:
        10px;

    overflow:
        hidden;
}}


.fill {{

    height:
        100%;

    background:
        #64748b;
}}


table {{

    width:
        100%;

    border-collapse:
        collapse;
}}


th,
td {{

    padding:
        11px;

    text-align:
        left;

    border-bottom:
        1px solid
        #e5e7eb;
}}


th {{

    color:
        #64748b;
}}


.note {{

    background:
        #f8fafc;

    border-radius:
        10px;

    padding:
        15px;

    line-height:
        1.55;
}}


.code {{

    background:
        #f1f5f9;

    padding:
        4px 7px;

    border-radius:
        5px;

    font-family:
        monospace;
}}


@media (
    max-width:
    950px
) {{

    .grid {{

        grid-template-columns:
            repeat(
                2,
                1fr
            );
    }}

    .metric-grid {{

        grid-template-columns:
            repeat(
                2,
                1fr
            );
    }}

}}


@media (
    max-width:
    600px
) {{

    .container {{

        padding:
            16px;
    }}

    .grid,
    .metric-grid {{

        grid-template-columns:
            1fr;
    }}

    h1 {{

        font-size:
            29px;
    }}

}}

</style>

</head>


<body>


<div class="container">


<!-- ===================================================== -->
<!-- HEADER -->
<!-- ===================================================== -->

<h1>
Monetization & Revenue Dashboard
</h1>


<div class="subtitle">

PlaceMux Phase 2 —
Task 10 · Monetization Integration & Revenue Dashboard ·
Synthetic Demonstration Data

</div>


<!-- ===================================================== -->
<!-- REVENUE HEALTH -->
<!-- ===================================================== -->

<div class="section">

<h2>
Revenue Health
</h2>


<p>

Current status:

<span class="
    status
    {health_status.lower()}
">

{health_status}

</span>

</p>


<div class="note">

The dashboard integrates validated analytical layers from
Days 26–29.

Day 26 provides the payment and revenue source.
Day 27 provides the Pay-per-Application conversion stream.
Day 28 provides payment-health and reconciliation logic.
Day 29 provides company-level ARPU and cohort analysis.

Revenue from the separate synthetic streams is intentionally not
added together.

</div>

</div>


<!-- ===================================================== -->
<!-- REVENUE KPIS -->
<!-- ===================================================== -->

<div class="grid">


<div class="card">

<div class="label">
Gross Payment Volume
</div>

<div class="value">
INR {gross_payment_volume:,.2f}
</div>

</div>


<div class="card">

<div class="label">
Recognized Revenue
</div>

<div class="value">
INR {recognized_revenue:,.2f}
</div>

</div>


<div class="card">

<div class="label">
Refund Amount
</div>

<div class="value">
INR {refund_amount:,.2f}
</div>

</div>


<div class="card">

<div class="label">
Chargeback Amount
</div>

<div class="value">
INR {chargeback_amount:,.2f}
</div>

</div>


<div class="card">

<div class="label">
Net Revenue
</div>

<div class="value">
INR {net_revenue:,.2f}
</div>

</div>


<div class="card">

<div class="label">
Revenue Margin
</div>

<div class="value">
{revenue_margin:.2f}%
</div>

</div>


<div class="card">

<div class="label">
Paying Companies
</div>

<div class="value">
{paying_company_count}
</div>

</div>


<div class="card">

<div class="label">
ARPU
</div>

<div class="value">
INR {arpu:,.2f}
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


<div class="metric-box">

<div class="metric-label">
Net ARPU
</div>

<div class="metric-value">
INR {net_arpu:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Revenue / Payment
</div>

<div class="metric-value">
INR {revenue_per_payment:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Successful Payments
</div>

<div class="metric-value">
{successful_payment_count}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Repeat Paying Companies
</div>

<div class="metric-value">
{repeat_paying_company_count}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Repeat Payer Rate
</div>

<div class="metric-value">
{repeat_payer_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Retention Rate
</div>

<div class="metric-value">
{retention_rate:.1f}%
</div>

</div>


</div>

</div>


<!-- ===================================================== -->
<!-- APPLICATION CONVERSION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Pay-per-Application Conversion
</h2>


<div class="funnel">

{funnel_html}

</div>


<div class="metric-grid">


<div class="metric-box">

<div class="metric-label">
Submission Rate
</div>

<div class="metric-value">
{application_submission_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Eligibility Rate
</div>

<div class="metric-value">
{application_eligibility_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Payment Initiation Rate
</div>

<div class="metric-value">
{application_payment_initiation_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Payment Capture Rate
</div>

<div class="metric-value">
{application_payment_capture_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Application → Payment
</div>

<div class="metric-value">
{application_to_payment_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Started → Paid
</div>

<div class="metric-value">
{started_to_paid_rate:.1f}%
</div>

</div>


</div>

</div>


<!-- ===================================================== -->
<!-- PAYMENT HEALTH -->
<!-- ===================================================== -->

<div class="section">

<h2>
Payment Health
</h2>


<div class="metric-grid">


<div class="metric-box">

<div class="metric-label">
Payment Attempts
</div>

<div class="metric-value">
{payment_attempt_count}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Successful Payments
</div>

<div class="metric-value">
{successful_payment_count}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Failed Payments
</div>

<div class="metric-value">
{failed_payment_count}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Payment Failure Rate
</div>

<div class="metric-value">
{payment_failure_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Refund Value Rate
</div>

<div class="metric-value">
{refund_value_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Chargeback Value Rate
</div>

<div class="metric-value">
{chargeback_value_rate:.1f}%
</div>

</div>


</div>

</div>


<!-- ===================================================== -->
<!-- COHORT REVENUE -->
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
Chargebacks
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

{cohort_rows_html}

</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- RECONCILIATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Revenue Reconciliation
</h2>


<div class="metric-grid">


<div class="metric-box">

<div class="metric-label">
Gross Payment Volume
</div>

<div class="metric-value">
INR {gross_payment_volume:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Refunds
</div>

<div class="metric-value">
INR {refund_amount:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Chargebacks
</div>

<div class="metric-value">
INR {chargeback_amount:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Net Retained Value
</div>

<div class="metric-value">
INR {net_retained_payment_value:,.2f}
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Retention Rate
</div>

<div class="metric-value">
{retention_rate:.1f}%
</div>

</div>


<div class="metric-box">

<div class="metric-label">
Reconciliation Gap
</div>

<div class="metric-value">
INR {reconciliation_gap:,.2f}
</div>

</div>


</div>

</div>


<!-- ===================================================== -->
<!-- VALIDATION -->
<!-- ===================================================== -->

<div class="section">

<h2>
Integrated Validation
</h2>


<p>

Validation status:

<span class="
    status
    {
        "healthy"
        if validation_passed
        else "risk"
    }
">

{
    "PASS"
    if validation_passed
    else "FAIL"
}

</span>

</p>


<table>

<thead>

<tr>

<th>
Validation Check
</th>

<th>
Result
</th>

</tr>

</thead>


<tbody>


<tr>

<td>
Payment Duplicate Event IDs
</td>

<td>
{validation["payment_duplicate_event_ids"]}
</td>

</tr>


<tr>

<td>
Application Duplicate Event IDs
</td>

<td>
{validation["application_duplicate_event_ids"]}
</td>

</tr>


<tr>

<td>
Missing Payment IDs
</td>

<td>
{validation["payment_missing_payment_ids"]}
</td>

</tr>


<tr>

<td>
Missing Company IDs
</td>

<td>
{validation["payment_missing_company_ids"]}
</td>

</tr>


<tr>

<td>
Invalid Event Names
</td>

<td>
{invalid_event_count}
</td>

</tr>


<tr>

<td>
Payment Lifecycle Errors
</td>

<td>
{payment_lifecycle_errors}
</td>

</tr>


<tr>

<td>
Application Lifecycle Errors
</td>

<td>
{application_lifecycle_errors}
</td>

</tr>


<tr>

<td>
Cohort Revenue Gap
</td>

<td>
INR {cohort_revenue_gap:,.2f}
</td>

</tr>


<tr>

<td>
Cohort Customer Gap
</td>

<td>
{cohort_customer_gap}
</td>

</tr>


<tr>

<td>
Cohort Refund Gap
</td>

<td>
INR {cohort_refund_gap:,.2f}
</td>

</tr>


<tr>

<td>
Reconciliation Gap
</td>

<td>
INR {reconciliation_gap:,.2f}
</td>

</tr>


</tbody>

</table>

</div>


<!-- ===================================================== -->
<!-- SOURCE & DEFINITIONS -->
<!-- ===================================================== -->

<div class="section">

<h2>
Source & Definitions
</h2>


<p>

<strong>
Primary revenue source:
</strong>

<span class="code">
phase2/payment_events_demo.csv
</span>

</p>


<p>

<strong>
Application conversion source:
</strong>

<span class="code">
phase2/pay_per_application_events_demo.csv
</span>

</p>


<p>

<strong>
Customer definition:
</strong>

<code>
company_id
</code>

for the payment/revenue layer.

</p>


<p>

<strong>
ARPU:
</strong>

Recognized revenue divided by distinct paying companies.

</p>


<p>

<strong>
Cohort:
</strong>

Calendar month of the company's first successful payment.

</p>


<p>

<strong>
Reproducible command:
</strong>

<code>
python phase2/revenue_dashboard_demo.py
</code>

</p>


<p class="note">

The dashboard combines separate synthetic demonstration streams.
Revenue from those streams is intentionally not summed together.
Production reporting should replace them with a governed,
authoritative event and financial data source.

</p>

</div>


</div>


</body>

</html>
"""


# ============================================================
# WRITE DASHBOARD
# ============================================================

HTML_OUTPUT.write_text(
    html,
    encoding="utf-8",
)


# ============================================================
# TERMINAL OUTPUT
# ============================================================

print("=" * 70)
print(
    "DAY 30 — MONETIZATION INTEGRATION & REVENUE DASHBOARD"
)
print("=" * 70)


print(
    f"Payment source events        : "
    f"{len(payment_events):,}"
)


print(
    f"Application source events    : "
    f"{len(application_events):,}"
)


print(
    f"Gross payment volume         : "
    f"INR {gross_payment_volume:,.2f}"
)


print(
    f"Recognized revenue           : "
    f"INR {recognized_revenue:,.2f}"
)


print(
    f"Refund amount                : "
    f"INR {refund_amount:,.2f}"
)


print(
    f"Chargeback amount            : "
    f"INR {chargeback_amount:,.2f}"
)


print(
    f"Net revenue                  : "
    f"INR {net_revenue:,.2f}"
)


print(
    f"Revenue margin               : "
    f"{revenue_margin:.2f}%"
)


print(
    f"Paying companies             : "
    f"{paying_company_count}"
)


print(
    f"ARPU                         : "
    f"INR {arpu:,.2f}"
)


print(
    f"Net ARPU                     : "
    f"INR {net_arpu:,.2f}"
)


print(
    f"Revenue per payment          : "
    f"INR {revenue_per_payment:,.2f}"
)


print(
    f"Repeat payer rate            : "
    f"{repeat_payer_rate:.2f}%"
)


print(
    f"Application → Payment        : "
    f"{application_to_payment_rate:.2f}%"
)


print(
    f"Started → Paid               : "
    f"{started_to_paid_rate:.2f}%"
)


print(
    f"Payment failure rate         : "
    f"{payment_failure_rate:.2f}%"
)


print(
    f"Refund value rate            : "
    f"{refund_value_rate:.2f}%"
)


print(
    f"Chargeback value rate        : "
    f"{chargeback_value_rate:.2f}%"
)


print(
    f"Retention rate               : "
    f"{retention_rate:.2f}%"
)


print(
    f"Reconciliation gap           : "
    f"INR {reconciliation_gap:,.2f}"
)


print(
    f"Health status                : "
    f"{health_status}"
)


print()
print("VALIDATION")
print("-" * 70)


print(
    f"Payment duplicate IDs        : "
    f"{validation['payment_duplicate_event_ids']}"
)


print(
    f"Application duplicate IDs    : "
    f"{validation['application_duplicate_event_ids']}"
)


print(
    f"Missing payment IDs          : "
    f"{validation['payment_missing_payment_ids']}"
)


print(
    f"Missing company IDs          : "
    f"{validation['payment_missing_company_ids']}"
)


print(
    f"Invalid event names          : "
    f"{invalid_event_count}"
)


print(
    f"Payment lifecycle errors     : "
    f"{payment_lifecycle_errors}"
)


print(
    f"Application lifecycle errors : "
    f"{application_lifecycle_errors}"
)


print(
    f"Cohort revenue gap           : "
    f"INR {cohort_revenue_gap:,.2f}"
)


print(
    f"Cohort customer gap          : "
    f"{cohort_customer_gap}"
)


print(
    f"Cohort refund gap            : "
    f"INR {cohort_refund_gap:,.2f}"
)


print(
    f"Reconciliation gap           : "
    f"INR {reconciliation_gap:,.2f}"
)


print(
    f"Validation status            : "
    f"{'PASS' if validation_passed else 'FAIL'}"
)


print()
print("FILES CREATED")
print("-" * 70)


print(
    METRICS_OUTPUT
)


print(
    COHORT_OUTPUT
)


print(
    VALIDATION_OUTPUT
)


print(
    HTML_OUTPUT
)