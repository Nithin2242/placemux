
---

# 3. `phase2/jobs_posted_view.md`

Use this:

```markdown
# Jobs Posted View

## Purpose

The Jobs Posted view is the analytical view for monitoring marketplace job supply.

The Day 22 task requires a jobs-posted view to be live and demonstrable after job-post events are validated. :contentReference[oaicite:2]{index=2}

The view should provide a simple operational picture of how much job supply is being created, published, and maintained in the marketplace.

---

# Primary Business Question

> How much job supply is entering the marketplace, how much becomes active, and how is that supply changing over time?

---

# Core KPIs

The view should contain the following headline metrics.

## KPI 1 — Jobs Posted

```text
COUNT(DISTINCT job_id)