# Task 2 - Metric Layer Tracking Plan

## Required source fields

`InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`

## Derived semantic fields

`is_cancellation`, `customer_missing`, `quantity_invalid`, `price_invalid`, `line_total`, `is_valid_purchase`

## Metric consumption contract

All consumer surfaces should reference the same semantic field names and formulas. No dashboard-specific reimplementation of metric logic is permitted for governed KPIs.

## Freshness metadata

Production ingestion should record:

- `source_max_event_time`
- `ingested_at`
- `transformed_at`
- `published_at`
- `expected_refresh_sla`

## Lineage

Raw transaction source -> quality flags -> valid purchase semantic layer -> aggregate metrics -> dashboard / executive view / ad-hoc query.
