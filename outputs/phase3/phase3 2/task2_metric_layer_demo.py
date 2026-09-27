from __future__ import annotations

import argparse
import json
from pathlib import Path

from metric_semantic_layer import build_outputs
from build_task2_dashboard import build as build_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(description="PlaceMux Phase 3 Task 2 semantic metric layer demo")
    parser.add_argument("--source", required=True, help="Path to the real external proxy source XLSX")
    parser.add_argument("--out", default="phase3/task2_outputs")
    args = parser.parse_args()

    out = Path(args.out)
    result = build_outputs(args.source, str(out))
    dashboard = Path("phase3/task2_dashboard.html")
    build_dashboard(
        out / "semantic_metrics_snapshot.json",
        out / "data_quality_checks.json",
        out / "semantic_layer_validation.json",
        dashboard,
    )
    print(json.dumps(result["validation"], indent=2))
    print(f"Dashboard: {dashboard}")


if __name__ == "__main__":
    main()
