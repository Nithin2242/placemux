import logging

import pandas as pd


REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
}


def validate_raw_data(df: pd.DataFrame, logger: logging.Logger) -> None:
    logger.info("Validating raw dataset.")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("Input dataset is empty.")

    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        raise TypeError("InvoiceDate must be datetime-like.")

    if df["Quantity"].isna().any():
        raise ValueError("Quantity contains missing values.")

    if df["UnitPrice"].isna().any():
        raise ValueError("UnitPrice contains missing values.")

    logger.info(
        "Raw validation passed: %d rows, %d columns.",
        len(df),
        len(df.columns),
    )


def validate_clean_data(
    df: pd.DataFrame,
    logger: logging.Logger,
) -> None:
    logger.info("Validating cleaned transaction data.")

    if df.empty:
        raise ValueError("Cleaning produced zero rows.")

    if df["InvoiceNo"].astype(str).str.startswith("C").any():
        raise ValueError("Cancellation invoices remain after cleaning.")

    if (df["Quantity"] <= 0).any():
        raise ValueError("Non-positive quantities remain after cleaning.")

    if (df["UnitPrice"] <= 0).any():
        raise ValueError("Non-positive prices remain after cleaning.")

    if df["StockCode"].isna().any():
        raise ValueError("Missing StockCode values remain after cleaning.")

    if df["Description"].isna().any():
        raise ValueError("Missing descriptions remain after cleaning.")

    logger.info(
        "Clean-data validation passed: %d rows, %d invoices, %d products.",
        len(df),
        df["InvoiceNo"].nunique(),
        df["Description"].nunique(),
    )


def validate_basket_matrix(
    basket_matrix: pd.DataFrame,
    logger: logging.Logger,
) -> None:
    logger.info("Validating basket matrix.")

    if basket_matrix.empty:
        raise ValueError("Basket matrix is empty.")

    if not set(basket_matrix.dtypes.astype(str)).issubset(
        {"int64", "int32", "uint8", "bool"}
    ):
        # Keep the validation practical across pandas versions.
        numeric_values = basket_matrix.to_numpy()
        if not ((numeric_values == 0) | (numeric_values == 1)).all():
            raise ValueError(
                "Basket matrix contains values other than 0 and 1."
            )

    values = basket_matrix.to_numpy()

    if not ((values == 0) | (values == 1)).all():
        raise ValueError("Basket matrix must contain only 0 and 1.")

    logger.info(
        "Basket validation passed: %d baskets x %d products.",
        basket_matrix.shape[0],
        basket_matrix.shape[1],
    )