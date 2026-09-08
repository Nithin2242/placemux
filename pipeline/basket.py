import logging

import pandas as pd


def build_basket_matrix(
    transactions: pd.DataFrame,
    logger: logging.Logger,
) -> pd.DataFrame:
    logger.info("Building invoice-level basket matrix.")

    basket_matrix = (
        transactions
        .groupby(["InvoiceNo", "Description"])["Quantity"]
        .sum()
        .unstack(fill_value=0)
    )

    # Convert quantities into binary item presence.
    basket_matrix = (basket_matrix > 0)

    logger.info(
        "Basket matrix created: %d baskets x %d products.",
        basket_matrix.shape[0],
        basket_matrix.shape[1],
    )

    return basket_matrix