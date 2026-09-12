import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
REG = BASE / "launch_kpi_registry.csv"
OUT = BASE / "metrics_governance_validation.json"
RESULTS = BASE / "launch_kpi_governance_results.csv"

REQUIRED = ["metric_id","metric_name","status","owner","reviewer","refresh_sla_hours","source","version","critical"]
VALID_STATUS = {"CERTIFIED","STALE","DEGRADED","BLOCKED","DEPRECATED"}


def main():
    df = pd.read_csv(REG)
    checks = {}
    checks["missing_columns"] = sorted(set(REQUIRED) - set(df.columns))
    checks["duplicate_metric_ids"] = int(df["metric_id"].duplicated().sum()) if "metric_id" in df else -1
    checks["duplicate_metric_names"] = int(df["metric_name"].duplicated().sum()) if "metric_name" in df else -1
    checks["invalid_status_values"] = int((~df["status"].isin(VALID_STATUS)).sum()) if "status" in df else -1
    checks["missing_owner"] = int(df["owner"].isna().sum()) if "owner" in df else -1
    checks["missing_reviewer"] = int(df["reviewer"].isna().sum()) if "reviewer" in df else -1
    checks["missing_source"] = int(df["source"].isna().sum()) if "source" in df else -1
    checks["missing_version"] = int(df["version"].isna().sum()) if "version" in df else -1
    checks["invalid_refresh_sla"] = int((pd.to_numeric(df["refresh_sla_hours"], errors="coerce") <= 0).sum()) if "refresh_sla_hours" in df else -1
    checks["critical_not_certified"] = int(((df["critical"] == True) & (df["status"] != "CERTIFIED")).sum()) if {"critical","status"}.issubset(df.columns) else -1
    checks["deprecated_launch_candidates"] = int((df["status"] == "DEPRECATED").sum()) if "status" in df else -1

    result = df.copy()
    result["launch_eligible"] = (result["status"] == "CERTIFIED") & (result["status"] != "DEPRECATED")
    result.to_csv(RESULTS, index=False)

    blocking = (
        checks["missing_columns"]
        or checks["duplicate_metric_ids"] != 0
        or checks["duplicate_metric_names"] != 0
        or checks["invalid_status_values"] != 0
        or checks["missing_owner"] != 0
        or checks["missing_reviewer"] != 0
        or checks["missing_source"] != 0
        or checks["missing_version"] != 0
        or checks["invalid_refresh_sla"] != 0
        or checks["critical_not_certified"] != 0
    )

    payload = {
        "metrics": int(len(df)),
        "certified_metrics": int((df["status"] == "CERTIFIED").sum()),
        "degraded_metrics": int((df["status"] == "DEGRADED").sum()),
        "deprecated_metrics": int((df["status"] == "DEPRECATED").sum()),
        "launch_ready_metrics": int(result["launch_eligible"].sum()),
        "validation_status": "FAIL" if blocking else "PASS",
        "checks": checks,
        "scope_note": "Synthetic governance registry validation only; not a production KPI certification."
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
