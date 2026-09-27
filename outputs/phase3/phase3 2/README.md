# PlaceMux Phase 3 - Task 2
## Observability Deep-Dive, SLOs & Error Budgets

### Goal
Build one semantic/metric layer, data-quality tests with alerts, and a published metric dictionary.

### Data note
The task brief requires real production data but does not supply a PlaceMux production export. This implementation therefore uses the real UCI Online Retail dataset already present in the project as an explicit external-data proxy. It must not be described as PlaceMux production telemetry.

### Run

```bash
python phase3/metric_semantic_layer.py --source "data/online_retail/Online Retail.xlsx" --out phase3/task2_outputs
python phase3/build_task2_dashboard.py --snapshot phase3/task2_outputs/semantic_metrics_snapshot.json --dq phase3/task2_outputs/data_quality_checks.json --validation phase3/task2_outputs/semantic_layer_validation.json --out phase3/task2_dashboard.html
```

### Demo surfaces

- `task2_dashboard.html` - semantic layer, KPI parity, quality status and failure-path evidence.
- `metric_dictionary.csv` - published machine-readable metric registry.
- `semantic_monthly_metrics.csv` - governed monthly aggregates.
- `semantic_layer_validation.json` - validation and parity checks.
- `failure_path_test.json` - intentional mismatch test.

### Key design rule

All consumer surfaces read the same semantic values and metric IDs. New dashboards should not recreate formulas independently.
