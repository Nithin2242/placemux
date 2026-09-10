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

EVENTS_FILE = BASE_DIR / "payment_events_demo.csv"
METRICS_FILE = BASE_DIR / "revenue_metrics_demo.csv"
VALIDATION_FILE = BASE_DIR / "payment_validation_demo.json"

RANDOM_SEED = 42

START_DATE = datetime(2026, 8, 1)
DAYS = 30

COMPANIES = [
    f"CMP{n:03d}"
    for n in range(1, 31)
]

SELLERS = [
    f"SEL{n:03d}"
    for n in range(1, 21)
]

GATEWAYS = [
    "DemoPay",
    "DemoGateway",
]

CURRENCY = "INR"

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
# EVENT GENERATOR
# ============================================================

random.seed(RANDOM_SEED)

events = []

event_counter = 1
payment_counter = 1


def add_event(
    event_name: str,
    timestamp: datetime,
    payment_id: str,
    company_id: str,
    seller_id: str,
    order_id: str,
    gateway: str,
    amount: float,
    extra: dict | None = None,
) -> None:

    global event_counter

    row = {
        "event_id": f"PE{event_counter:06d}",
        "event_name": event_name,
        "event_timestamp": timestamp.isoformat(),
        "payment_id": payment_id,
        "company_id": company_id,
        "seller_id": seller_id,
        "order_id": order_id,
        "amount": round(float(amount), 2),
        "currency": CURRENCY,
        "gateway": gateway,
        "event_version": "1.0",
    }

    if extra:
        row.update(extra)

    events.append(row)

    event_counter += 1


# ============================================================
# GENERATE PAYMENTS
# ============================================================

for day_offset in range(DAYS):

    current_day = START_DATE + timedelta(
        days=day_offset
    )

    weekday = current_day.weekday()

    payments_today = (
        random.randint(22, 32)
        if weekday < 5
        else random.randint(12, 20)
    )

    for _ in range(payments_today):

        payment_id = (
            f"PAY{payment_counter:05d}"
        )

        order_id = (
            f"ORD{payment_counter:05d}"
        )

        company_id = random.choice(
            COMPANIES
        )

        seller_id = random.choice(
            SELLERS
        )

        gateway = random.choice(
            GATEWAYS
        )

        amount = round(
            random.uniform(
                1500,
                25000,
            ),
            2,
        )

        initiated_at = (
            current_day
            + timedelta(
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59),
            )
        )

        add_event(
            "payment_initiated",
            initiated_at,
            payment_id,
            company_id,
            seller_id,
            order_id,
            gateway,
            amount,
            {
                "payment_method": random.choice(
                    [
                        "card",
                        "upi",
                        "netbanking",
                    ]
                )
            },
        )

        # ----------------------------------------------------
        # PAYMENT FAILURE BRANCH
        # ----------------------------------------------------

        # Around 8% fail before authorization.
        if random.random() < 0.08:

            failed_at = (
                initiated_at
                + timedelta(
                    seconds=random.randint(10, 90)
                )
            )

            add_event(
                "payment_failed",
                failed_at,
                payment_id,
                company_id,
                seller_id,
                order_id,
                gateway,
                amount,
                {
                    "failure_code": random.choice(
                        [
                            "DECLINED",
                            "TIMEOUT",
                            "INSUFFICIENT_FUNDS",
                        ]
                    ),
                    "failure_reason": "demo_failure",
                },
            )

            payment_counter += 1
            continue

        # ----------------------------------------------------
        # AUTHORIZATION
        # ----------------------------------------------------

        authorized_at = (
            initiated_at
            + timedelta(
                seconds=random.randint(5, 60)
            )
        )

        add_event(
            "payment_authorized",
            authorized_at,
            payment_id,
            company_id,
            seller_id,
            order_id,
            gateway,
            amount,
            {
                "gateway_transaction_id":
                    f"GTX{payment_counter:06d}"
            },
        )

        # ----------------------------------------------------
        # CAPTURE
        # ----------------------------------------------------

        captured_at = (
            authorized_at
            + timedelta(
                seconds=random.randint(5, 120)
            )
        )

        add_event(
            "payment_captured",
            captured_at,
            payment_id,
            company_id,
            seller_id,
            order_id,
            gateway,
            amount,
            {
                "captured_amount": amount,
                "gateway_transaction_id":
                    f"GTX{payment_counter:06d}"
            },
        )

        # ----------------------------------------------------
        # REVENUE RECOGNITION
        # ----------------------------------------------------

        # Demonstration platform fee = 8%.
        platform_fee = round(
            amount * 0.08,
            2,
        )

        recognized_at = (
            captured_at
            + timedelta(
                minutes=random.randint(1, 120)
            )
        )

        add_event(
            "revenue_recognized",
            recognized_at,
            payment_id,
            company_id,
            seller_id,
            order_id,
            gateway,
            platform_fee,
            {
                "revenue_id":
                    f"REV{payment_counter:05d}",
                "recognized_amount":
                    platform_fee,
                "revenue_type":
                    "platform_fee",
            },
        )

        # ----------------------------------------------------
        # REFUND
        # ----------------------------------------------------

        if random.random() < 0.10:

            refund_amount = round(
                amount
                * random.uniform(
                    0.25,
                    1.0,
                ),
                2,
            )

            refund_at = (
                recognized_at
                + timedelta(
                    days=random.randint(1, 5)
                )
            )

            add_event(
                "payment_refunded",
                refund_at,
                payment_id,
                company_id,
                seller_id,
                order_id,
                gateway,
                refund_amount,
                {
                    "refund_id":
                        f"REF{payment_counter:05d}",
                    "refund_amount":
                        refund_amount,
                    "refund_reason":
                        random.choice(
                            [
                                "customer_request",
                                "order_cancelled",
                                "service_issue",
                            ]
                        ),
                },
            )

        # ----------------------------------------------------
        # CHARGEBACK
        # ----------------------------------------------------

        if random.random() < 0.03:

            chargeback_amount = round(
                amount
                * random.uniform(
                    0.25,
                    1.0,
                ),
                2,
            )

            chargeback_at = (
                recognized_at
                + timedelta(
                    days=random.randint(2, 12)
                )
            )

            add_event(
                "payment_chargeback",
                chargeback_at,
                payment_id,
                company_id,
                seller_id,
                order_id,
                gateway,
                chargeback_amount,
                {
                    "chargeback_id":
                        f"CB{payment_counter:05d}",
                    "chargeback_amount":
                        chargeback_amount,
                    "chargeback_reason":
                        random.choice(
                            [
                                "customer_dispute",
                                "fraud_claim",
                                "duplicate_payment",
                            ]
                        ),
                },
            )

        payment_counter += 1


events_df = pd.DataFrame(events)

events_df["event_timestamp"] = pd.to_datetime(
    events_df["event_timestamp"]
)

events_df = events_df.sort_values(
    [
        "payment_id",
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
    "missing_payment_ids": int(
        events_df["payment_id"]
        .isna()
        .sum()
    ),
    "invalid_event_names": int(
        (~events_df["event_name"]
         .isin(APPROVED_EVENTS))
        .sum()
    ),
    "invalid_timestamps": int(
        events_df["event_timestamp"]
        .isna()
        .sum()
    ),
}


# ============================================================
# LIFECYCLE VALIDATION
# ============================================================

lifecycle_errors = []

for payment_id, group in events_df.groupby(
    "payment_id"
):

    names = set(
        group["event_name"]
    )

    if (
        "payment_authorized" in names
        and "payment_initiated" not in names
    ):
        lifecycle_errors.append(
            f"{payment_id}: authorized_without_initiated"
        )

    if (
        "payment_captured" in names
        and "payment_authorized" not in names
    ):
        lifecycle_errors.append(
            f"{payment_id}: captured_without_authorized"
        )

    if (
        "revenue_recognized" in names
        and "payment_captured" not in names
    ):
        lifecycle_errors.append(
            f"{payment_id}: revenue_without_capture"
        )

    if (
        "payment_refunded" in names
        and "payment_captured" not in names
    ):
        lifecycle_errors.append(
            f"{payment_id}: refund_without_capture"
        )

    if (
        "payment_chargeback" in names
        and "payment_captured" not in names
    ):
        lifecycle_errors.append(
            f"{payment_id}: chargeback_without_capture"
        )


validation[
    "lifecycle_errors"
] = len(
    lifecycle_errors
)

validation[
    "lifecycle_error_examples"
] = lifecycle_errors[:10]


validation[
    "validation_passed"
] = all(
    value == 0
    for key, value in validation.items()
    if key not in {
        "total_events",
        "validation_passed",
        "lifecycle_error_examples",
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
# CALCULATE REVENUE METRICS
# ============================================================

initiated = events_df[
    events_df["event_name"]
    == "payment_initiated"
]

captured = events_df[
    events_df["event_name"]
    == "payment_captured"
]

recognized = events_df[
    events_df["event_name"]
    == "revenue_recognized"
]

refunded = events_df[
    events_df["event_name"]
    == "payment_refunded"
]

chargebacks = events_df[
    events_df["event_name"]
    == "payment_chargeback"
]


payment_transactions = initiated[
    "payment_id"
].nunique()

successful_payments = captured[
    "payment_id"
].nunique()

gross_payment_volume = captured[
    "amount"
].sum()

gross_revenue = recognized[
    "amount"
].sum()

refund_amount = refunded[
    "amount"
].sum()

chargeback_amount = chargebacks[
    "amount"
].sum()

net_revenue = (
    gross_revenue
    - refund_amount
    - chargeback_amount
)


def ratio(
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


payment_success_rate = ratio(
    successful_payments,
    payment_transactions,
)

average_transaction_value = (
    gross_payment_volume
    / successful_payments
    if successful_payments
    else 0.0
)

platform_fee_rate = ratio(
    gross_revenue,
    gross_payment_volume,
)

revenue_per_successful_payment = (
    gross_revenue
    / successful_payments
    if successful_payments
    else 0.0
)

refund_rate = ratio(
    refund_amount,
    gross_payment_volume,
)

chargeback_rate = ratio(
    chargeback_amount,
    gross_payment_volume,
)

revenue_recognition_rate = ratio(
    gross_revenue,
    gross_payment_volume,
)

net_revenue_margin = ratio(
    net_revenue,
    gross_payment_volume,
)


# ============================================================
# METRIC OUTPUT
# ============================================================

metrics = [
    (
        "Payment Transactions",
        payment_transactions,
        "count",
    ),
    (
        "Successful Payments",
        successful_payments,
        "count",
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
        "Gross Payment Volume",
        round(
            gross_payment_volume,
            2,
        ),
        "INR",
    ),
    (
        "Gross Revenue",
        round(
            gross_revenue,
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
        "Chargeback Amount",
        round(
            chargeback_amount,
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
        "Average Transaction Value",
        round(
            average_transaction_value,
            2,
        ),
        "INR",
    ),
    (
        "Platform Fee Rate",
        round(
            platform_fee_rate,
            2,
        ),
        "%",
    ),
    (
        "Revenue per Successful Payment",
        round(
            revenue_per_successful_payment,
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
    (
        "Chargeback Rate",
        round(
            chargeback_rate,
            2,
        ),
        "%",
    ),
    (
        "Revenue Recognition Rate",
        round(
            revenue_recognition_rate,
            2,
        ),
        "%",
    ),
    (
        "Net Revenue Margin",
        round(
            net_revenue_margin,
            2,
        ),
        "%",
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
# TERMINAL OUTPUT
# ============================================================

print("=" * 65)
print("DAY 26 — REVENUE METRICS DEMO")
print("=" * 65)

print(
    f"Total events              : "
    f"{len(events_df):,}"
)

print(
    f"Payment transactions      : "
    f"{payment_transactions:,}"
)

print(
    f"Successful payments       : "
    f"{successful_payments:,}"
)

print(
    f"Payment success rate      : "
    f"{payment_success_rate:.2f}%"
)

print(
    f"Gross payment volume      : "
    f"INR {gross_payment_volume:,.2f}"
)

print(
    f"Gross revenue             : "
    f"INR {gross_revenue:,.2f}"
)

print(
    f"Refund amount             : "
    f"INR {refund_amount:,.2f}"
)

print(
    f"Chargeback amount         : "
    f"INR {chargeback_amount:,.2f}"
)

print(
    f"Net revenue               : "
    f"INR {net_revenue:,.2f}"
)

print(
    f"Average transaction value : "
    f"INR {average_transaction_value:,.2f}"
)

print(
    f"Platform fee rate         : "
    f"{platform_fee_rate:.2f}%"
)

print(
    f"Refund rate               : "
    f"{refund_rate:.2f}%"
)

print(
    f"Chargeback rate           : "
    f"{chargeback_rate:.2f}%"
)

print(
    f"Net revenue margin        : "
    f"{net_revenue_margin:.2f}%"
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
    f"Lifecycle errors          : "
    f"{validation['lifecycle_errors']}"
)

print(
    f"Validation status         : "
    f"{'PASS' if validation['validation_passed'] else 'FAIL'}"
)

print()
print("FILES CREATED")
print("-" * 65)

print(EVENTS_FILE)
print(METRICS_FILE)
print(VALIDATION_FILE)