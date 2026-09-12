from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
CONTROL_FILE = BASE / "reporting_governance_controls.csv"
OUTPUT = BASE / "reporting_governance_validation.json"

ALLOWED_STATUS = {"CHECKED", "PENDING", "BLOCKED"}


def main() -> None:
    df = pd.read_csv(CONTROL_FILE)

    required_cols = {
        "control_id",
        "domain",
        "control_name",
        "required",
        "evidence",
        "status",
    }
    missing_cols = sorted(required_cols - set(df.columns))
    duplicate_ids = int(df["control_id"].duplicated().sum()) if "control_id" in df.columns else 0
    invalid_status = int((~df["status"].isin(ALLOWED_STATUS)).sum()) if "status" in df.columns else 0
    missing_evidence = int(df["evidence"].fillna("").astype(str).str.strip().eq("").sum()) if "evidence" in df.columns else 0
    unchecked_required = int(((df["required"] == "yes") & (df["status"] != "CHECKED")).sum()) if {"required", "status"}.issubset(df.columns) else 0

    checks = {
        "missing_columns": missing_cols,
        "duplicate_control_ids": duplicate_ids,
        "invalid_status_values": invalid_status,
        "missing_evidence": missing_evidence,
        "unchecked_required_controls": unchecked_required,
    }
    validation_pass = not any([
        missing_cols,
        duplicate_ids,
        invalid_status,
        missing_evidence,
        unchecked_required,
    ])

    result = {
        "controls": int(len(df)),
        "checked_controls": int((df["status"] == "CHECKED").sum()),
        "validation_status": "PASS" if validation_pass else "FAIL",
        "checks": checks,
        "scope_note": "Documentation/control-catalog validation only; not a production legal or security certification.",
    }

    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
