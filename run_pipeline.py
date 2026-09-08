import argparse
from pathlib import Path

from pipeline.config import PipelineConfig
from pipeline.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Day 19 analytical market-basket pipeline."
    )

    parser.add_argument(
        "--source",
        default="data/online_retail/Online Retail.xlsx",
        help="Path to the Excel transaction dataset.",
    )

    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for pipeline outputs.",
    )

    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for pipeline logs.",
    )

    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional inclusive start date, e.g. 2010-12-01.",
    )

    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional inclusive end date, e.g. 2011-06-30.",
    )

    parser.add_argument(
        "--min-support",
        type=float,
        default=0.02,
        help="Minimum itemset support.",
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.30,
        help="Minimum rule confidence.",
    )

    parser.add_argument(
        "--min-lift",
        type=float,
        default=1.20,
        help="Minimum rule lift.",
    )

    parser.add_argument(
        "--max-itemset-length",
        type=int,
        default=3,
        help="Maximum itemset size mined by Apriori.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = PipelineConfig(
        source_path=Path(args.source),
        output_dir=Path(args.output_dir),
        log_dir=Path(args.log_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        max_itemset_length=args.max_itemset_length,
    )

    summary = run_pipeline(config)

    print("\nPipeline completed successfully.")
    print("Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()