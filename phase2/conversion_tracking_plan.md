
---

# 2. `phase2/conversion_tracking_plan.md`

Paste:

```markdown
# Pay-per-Application Conversion Tracking Plan

## Purpose

This tracking plan defines the proposed events required to measure the
Pay-per-Application conversion baseline.

The Day 27 task requires conversion tracking to be live.

The implementation uses a shared `application_id` across application
and payment events so that exact application-level conversion can be
calculated.

---

# Event Naming Convention

Use:

```text
<object>_<action>