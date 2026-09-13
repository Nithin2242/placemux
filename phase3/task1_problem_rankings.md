# Phase 3 Task 1 - Ranked Problem List

The ranking is based on affected raw source rows. Issue classes can overlap, so the percentages should not be summed.

1. **Customer traceability gap - P0.** Missing CustomerID affects 135,080 raw rows (24.9%). Decision: protect customer attribution and retention reporting by separating guest activity from known-customer analytics.
2. **Transaction-state contamination - P0.** Cancellation invoice lines affect 9,288 raw rows (1.7%). Decision: keep cancellations/returns out of sales KPIs and reconcile them in a separate return-value control.
3. **Invalid quantity states - P1.** Quantity <= 0 affects 10,624 raw rows (2.0%). Decision: validate transaction state before commercial publication.
4. **Invalid price states - P1.** UnitPrice <= 0 affects 2,517 raw rows (0.5%). Decision: add a price-quality gate and quarantine non-positive-price records.

Because missing CustomerID is the dominant row-level issue, the first decision is attribution quality rather than another dashboard. The next P0 is transaction semantics: cancellation and negative-quantity records require explicit state handling so revenue cannot be silently distorted.
