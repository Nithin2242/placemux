# Marketplace Data Model

## Purpose

This document describes the minimum logical entities required to support the
marketplace liquidity metrics and tracking plan.

---

# Core Entities

## 1. Buyer

Represents the demand-side marketplace participant.

Key fields:

- `buyer_id`
- `created_at`
- `status`
- `location`
- `profile_type`

---

## 2. Seller

Represents the supply-side marketplace participant.

Key fields:

- `seller_id`
- `created_at`
- `status`
- `seller_type`
- `location`

---

## 3. Listing

Represents an item/opportunity made available by a seller.

Key fields:

- `listing_id`
- `seller_id`
- `category`
- `status`
- `created_at`
- `published_at`
- `closed_at`

Relationship:

`Seller 1 → many Listings`

---

## 4. Marketplace Event

Represents a measurable user or system action.

Key fields:

- `event_id`
- `event_name`
- `event_timestamp`
- `event_version`
- `buyer_id`
- `seller_id`
- `listing_id`
- `session_id`
- `platform`

Relationship:

`Buyer / Seller / Listing → many Events`

---

## 5. Contact

Represents a buyer-to-seller connection attempt.

Key fields:

- `contact_id`
- `buyer_id`
- `seller_id`
- `listing_id`
- `created_at`
- `first_response_at`
- `status`

Relationships:

`Buyer 1 → many Contacts`

`Seller 1 → many Contacts`

`Listing 1 → many Contacts`

---

## 6. Application

Represents a formal buyer action following marketplace engagement.

Key fields:

- `application_id`
- `buyer_id`
- `seller_id`
- `listing_id`
- `created_at`
- `submitted_at`
- `status`

---

## 7. Match

Represents a successful buyer-seller connection.

Key fields:

- `match_id`
- `buyer_id`
- `seller_id`
- `listing_id`
- `created_at`
- `status`

---

## 8. Outcome

Represents the final business-defined successful marketplace result.

Key fields:

- `outcome_id`
- `match_id`
- `outcome_type`
- `created_at`
- `status`

---

# Logical Relationship

```text
Buyer
  │
  ├─────────────── Marketplace Events
  │
  ├─────────────── Contact
  │                     │
  │                     ▼
  │                  Application
  │                     │
  │                     ▼
  └────────────────── Match
                        │
                        ▼
                     Outcome


Seller
  │
  ├─────────────── Marketplace Events
  │
  └─────────────── Listing
                         │
                         ├── Marketplace Events
                         ├── Contact
                         ├── Application
                         ├── Match
                         └── Outcome