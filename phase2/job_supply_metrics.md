# Job Supply Metrics

## Purpose

This document defines the measurement framework for tracking job supply in the PlaceMux marketplace.

The Day 22 task focuses on job-supply instrumentation. The metrics below are designed to answer:

- How many jobs are being posted?
- How many postings successfully enter the marketplace?
- How much active job supply is available?
- How is job supply changing over time?
- Which sellers are contributing job supply?

These are proposed analytical definitions for Phase 2 instrumentation and should be validated against the production implementation when job data becomes available.

---

## 1. Jobs Posted

### Definition

Number of distinct jobs for which the seller completes the job-post creation flow during the selected period.

### Calculation

```text
Jobs Posted = COUNT(DISTINCT job_id)