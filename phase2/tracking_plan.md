# Marketplace Event Tracking Plan

## Purpose

This tracking plan extends the marketplace event model so that buyer demand,
seller supply, marketplace engagement and successful outcomes can be measured.

The Day 21 brief requires marketplace events to be added to the tracking plan.
The specific event names below are proposed implementation definitions for that
purpose.

---

# Event Naming Convention

Use:

`<object>_<action>`

Examples:

- `search_performed`
- `listing_viewed`
- `seller_contacted`

Event names should remain stable once released.

---

# Marketplace Events

| Event | Actor | Required properties | Purpose |
|---|---|---|---|
| `search_performed` | Buyer | search_id, query, timestamp, user_id/session_id | Measure marketplace demand and discovery |
| `search_result_viewed` | Buyer | search_id, listing_id, position, timestamp | Measure listing discovery |
| `listing_viewed` | Buyer | listing_id, seller_id, category, timestamp, user_id/session_id | Measure listing interest |
| `listing_saved` | Buyer | listing_id, seller_id, timestamp, user_id | Measure stronger buyer intent |
| `seller_contacted` | Buyer | listing_id, seller_id, contact_id, timestamp, user_id | Measure buyer-to-seller connection |
| `application_started` | Buyer | listing_id, seller_id, application_id, timestamp, user_id | Measure application intent |
| `application_submitted` | Buyer | listing_id, seller_id, application_id, timestamp, user_id | Measure completed buyer action |
| `seller_listing_created` | Seller | listing_id, seller_id, category, timestamp | Measure new supply |
| `seller_listing_published` | Seller | listing_id, seller_id, category, timestamp | Measure available supply |
| `seller_listing_paused` | Seller | listing_id, seller_id, reason, timestamp | Track supply availability |
| `seller_listing_closed` | Seller | listing_id, seller_id, reason, timestamp | Track supply removal |
| `seller_response_sent` | Seller | listing_id, seller_id, contact_id, timestamp | Measure seller responsiveness |
| `match_created` | Marketplace | match_id, listing_id, buyer_id, seller_id, timestamp | Measure successful buyer-seller matching |
| `outcome_recorded` | Marketplace | outcome_id, match_id, outcome_type, timestamp | Measure final marketplace success |

---

# Common Event Properties

Every marketplace event should include a common envelope where available.

| Property | Description |
|---|---|
| `event_id` | Unique identifier for the event |
| `event_name` | Stable event name |
| `event_timestamp` | Event time in UTC |
| `user_id` | User identifier where applicable |
| `session_id` | Session identifier where applicable |
| `buyer_id` | Buyer identifier where applicable |
| `seller_id` | Seller identifier where applicable |
| `listing_id` | Listing identifier where applicable |
| `category` | Marketplace category |
| `platform` | Web / iOS / Android / other platform |
| `source` | Traffic or acquisition source where available |
| `event_version` | Version of the event schema |

---

# Event Quality Rules

## Required

Every event should have:

- Stable event name
- Event ID
- Timestamp
- Actor/user identifier where applicable
- Relevant marketplace object ID
- Event version

## Validation

Before production use, validate:

1. Event volume is plausible.
2. Event timestamps are valid.
3. IDs are populated where required.
4. Duplicate event IDs are investigated.
5. Event sequences are logically possible.
6. Events are emitted consistently across supported platforms.

---

# Recommended Funnel Sequence

The marketplace journey can be represented as:

Search
→ Listing View
→ Save / Contact
→ Application Started
→ Application Submitted
→ Seller Response
→ Match
→ Successful Outcome

Not every marketplace journey must follow every step. Events should therefore
be analysed as a set of measurable transitions rather than assuming every user
must pass through every stage.

---

# Ownership

| Area | Responsibility |
|---|---|
| Product | Define business meaning of events |
| Engineering | Implement event instrumentation |
| Data / Analytics | Validate event quality and metric calculations |
| QA | Test event firing and payloads |
| Marketplace Operations | Validate business interpretation |

## Versioning

Changes to event names, required properties or semantic meaning should create a
new `event_version`.

Existing event definitions should not be silently repurposed.

## Status

This is the proposed Phase 2 marketplace tracking plan created to satisfy the
Day 21 requirement to add marketplace events to the tracking plan.