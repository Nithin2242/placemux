# Phase 3 Task 4 — Submission Answer

I built a reproducible horizontal-scale planning workflow on the real UCI Online Retail transaction workbook. Because the supplied brief requires real production data but no PlaceMux production traffic dataset was provided, the workbook is explicitly treated as an external transaction-demand proxy rather than PlaceMux traffic.

The workflow constructs monthly invoice demand, compares a seasonal-naive baseline with a Holt-Winters seasonal model using rolling backtests, selects the lower-MAE model, forecasts the next six months, and translates the forecast into 2x, 5x and 10x capacity and normalized cost scenarios.

Peak capacity is planned using a documented peak factor and a 90% utilization guardrail. An intentional failure-path rehearsal identifies when the guardrail is breached and explicitly marks excess load for degradation rather than silently overcommitting resources.

The main limitation is that invoices are not HTTP requests or application sessions, and normalized capacity/cost units are not cloud-provider SKUs. Therefore these results are a real-data forecasting and capacity-planning demonstration, not a claim about PlaceMux production traffic. A production version should replace the proxy with actual traffic and infrastructure telemetry while retaining the same rolling-backtest and scenario framework.
