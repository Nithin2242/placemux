import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .basket import build_basket_matrix
from .cleaning import clean_transactions
from .config import PipelineConfig
from .analysis import (
    generate_rules,
    make_business_rules,
    mine_frequent_itemsets,
)
from .validation import (
    validate_basket_matrix,
    validate_clean_data,
    validate_raw_data,
)


def configure_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("day19_pipeline")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers when the module is reused.
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_dir / "pipeline.log",
        encoding="utf-8",
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def run_pipeline(config: PipelineConfig) -> dict:
    config.validate()

    config.output_dir.mkdir(parents=True, exist_ok=True)

    logger = configure_logging(config.log_dir)

    started_at = datetime.now(timezone.utc)

    logger.info("=" * 70)
    logger.info("DAY 19 ANALYTICAL PIPELINE START")
    logger.info("Source: %s", config.source_path)
    logger.info("Start date: %s", config.start_date)
    logger.info("End date: %s", config.end_date)
    logger.info("Min support: %.4f", config.min_support)
    logger.info("Min confidence: %.4f", config.min_confidence)
    logger.info("Min lift: %.4f", config.min_lift)
    logger.info("=" * 70)

    # ---------------------------------------------------------
    # Stage 1 — Load
    # ---------------------------------------------------------
    logger.info("STAGE 1/6 — Loading source dataset.")

    retail_df = pd.read_excel(config.source_path)

    retail_df["InvoiceDate"] = pd.to_datetime(
        retail_df["InvoiceDate"],
        errors="raise",
    )

    validate_raw_data(retail_df, logger)

    # ---------------------------------------------------------
    # Stage 2 — Clean
    # ---------------------------------------------------------
    logger.info("STAGE 2/6 — Cleaning transactions.")

    clean_df = clean_transactions(
        retail_df,
        logger,
        start_date=config.start_date,
        end_date=config.end_date,
    )

    validate_clean_data(clean_df, logger)

    # ---------------------------------------------------------
    # Stage 3 — Basket
    # ---------------------------------------------------------
    logger.info("STAGE 3/6 — Building baskets.")

    basket_matrix = build_basket_matrix(
        clean_df,
        logger,
    )

    validate_basket_matrix(
        basket_matrix,
        logger,
    )

    # ---------------------------------------------------------
    # Stage 4 — Frequent itemsets
    # ---------------------------------------------------------
    logger.info("STAGE 4/6 — Mining frequent itemsets.")

    frequent_itemsets = mine_frequent_itemsets(
        basket_matrix,
        min_support=config.min_support,
        max_itemset_length=config.max_itemset_length,
        logger=logger,
    )

    # ---------------------------------------------------------
    # Stage 5 — Rules
    # ---------------------------------------------------------
    logger.info("STAGE 5/6 — Generating and filtering rules.")

    rules = generate_rules(
        frequent_itemsets,
        min_confidence=config.min_confidence,
        min_lift=config.min_lift,
        logger=logger,
    )

    final_rules = make_business_rules(
        rules,
        logger,
        top_n=10,
    )

    # ---------------------------------------------------------
    # Stage 6 — Output
    # ---------------------------------------------------------
    logger.info("STAGE 6/6 — Writing outputs.")

    parameters = {
        "source_path": str(config.source_path),
        "start_date": config.start_date,
        "end_date": config.end_date,
        "min_support": config.min_support,
        "min_confidence": config.min_confidence,
        "min_lift": config.min_lift,
        "max_itemset_length": config.max_itemset_length,
    }

    summary = {
        "run_started_utc": started_at.isoformat(),
        "run_completed_utc": datetime.now(timezone.utc).isoformat(),
        "parameters": parameters,
        "raw_rows": len(retail_df),
        "clean_purchase_rows": len(clean_df),
        "baskets": basket_matrix.shape[0],
        "products": basket_matrix.shape[1],
        "frequent_itemsets": len(frequent_itemsets),
        "rules_after_thresholds": len(rules),
        "final_rules_reported": len(final_rules),
    }

    # Fixed output names make repeated runs idempotent.
    final_rules_path = (
        config.output_dir / "market_basket_final_rules.csv"
    )

    summary_path = (
        config.output_dir / "pipeline_summary.json"
    )

    frequent_itemsets_path = (
        config.output_dir / "frequent_itemsets.csv"
    )

    final_rules.to_csv(
        final_rules_path,
        index=False,
    )

    frequent_itemsets.assign(
        itemsets=frequent_itemsets["itemsets"].apply(
            lambda items: ", ".join(sorted(items))
        )
    ).to_csv(
        frequent_itemsets_path,
        index=False,
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            summary,
            handle,
            indent=2,
        )

    logger.info(
        "Output written: %s",
        final_rules_path,
    )

    logger.info(
        "Output written: %s",
        frequent_itemsets_path,
    )

    logger.info(
        "Output written: %s",
        summary_path,
    )

    logger.info("DAY 19 PIPELINE COMPLETE.")
    logger.info("=" * 70)

    return summary