# Task 2 - Published Metric Dictionary

## Purpose

This dictionary is the single semantic contract for the analytics layer. Each metric has one business definition, formula, grain, source fields, owner, refresh SLA, and decision use.

## Core metrics

| ID | Metric | Grain | Formula | Decision | Owner | SLA |
|---|---|---|---|---|---|---|
| m001 | Raw Transaction Lines | transaction-line | COUNT(rows) | Detect source-volume breaks | Data Engineering | Daily |
| m002 | Valid Purchase Lines | transaction-line | COUNT(rows meeting sale-quality rules) | Define trusted analytical population | Analytics | Daily |
| m003 | Net Revenue Proxy | transaction-line | SUM(Quantity × UnitPrice) | Track commercial value | Analytics | Daily |
| m004 | Identified Customers | customer | COUNT(DISTINCT CustomerID) | Assess customer reporting coverage | Analytics | Daily |
| m005 | Repeat Customer Rate | customer | repeat customers / identified customers | Assess repeat activity | Analytics | Daily |
| m006 | CustomerID Null Rate | transaction-line | missing CustomerID / raw rows | Gate customer-level reporting | Data Engineering | Daily |
| m007 | Cancellation Rate | transaction-line | cancellation rows / raw rows | Detect transaction-state contamination | Finance Analytics | Daily |
| m008 | Invalid Quantity Rate | transaction-line | Quantity <= 0 rows / raw rows | Trigger quantity-quality investigation | Data Engineering | Daily |
| m009 | Invalid Price Rate | transaction-line | UnitPrice <= 0 rows / raw rows | Trigger numeric-quality investigation | Data Engineering | Daily |
| m010 | Customer Revenue Share | customer | top-decile revenue / total identified-customer revenue | Assess concentration risk | Analytics | Weekly |

## Governance rule

Two people asking the same question should use this dictionary and receive the same value. Derived dashboards and ad-hoc analysis must read the same semantic definitions rather than recreating formulas independently.
