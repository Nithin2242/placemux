import logging

import pandas as pd


def clean_transactions(
    df: pd.DataFrame,
    logger: logging.Logger,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    logger.info("Starting transaction cleaning.")

    cleaned = df.copy()

    # Identify cancellation invoices.
    cleaned["is_cancellation"] = (
        cleaned["InvoiceNo"].astype(str).str.startswith("C")
    )

    # Optional date filtering.
    if start_date is not None:
        start = pd.Timestamp(start_date)
        cleaned = cleaned[
            cleaned["InvoiceDate"] >= start
        ]

    if end_date is not None:
        end = pd.Timestamp(end_date) + pd.Timedelta(days=1)
        cleaned = cleaned[
            cleaned["InvoiceDate"] < end
        ]

    # Remove invalid/non-purchase rows.
    cleaned = cleaned[
        (~cleaned["is_cancellation"])
        & (cleaned["Quantity"] > 0)
        & (cleaned["UnitPrice"] > 0)
        & cleaned["StockCode"].notna()
        & cleaned["Description"].notna()
    ].copy()

    # Standardise product descriptions.
    cleaned["Description"] = (
        cleaned["Description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    cleaned["TotalAmount"] = (
        cleaned["Quantity"] * cleaned["UnitPrice"]
    )

    cleaned = cleaned.drop(columns=["is_cancellation"])

    logger.info(
        "Cleaning complete: %d valid purchase rows remain.",
        len(cleaned),
    )

    return cleaned