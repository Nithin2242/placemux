# Marketplace Liquidity Metrics

## Purpose

The purpose of these metrics is to define how marketplace health and liquidity
will be measured before marketplace event data starts flowing.

Liquidity should describe whether buyer demand is successfully connecting with
available seller supply.

---

## 1. Active Buyers

**Definition:** Number of unique buyers who perform at least one meaningful
marketplace action during the measurement period.

**Suggested qualifying actions:**
- Search
- View listing
- Contact seller
- Apply
- Complete a marketplace transaction

**Formula:**

Active Buyers = count(distinct buyer_id with a qualifying event)

**Grain:** Daily / weekly / monthly

**Use:** Measures the size of the active demand side of the marketplace.

---

## 2. Active Sellers

**Definition:** Number of unique sellers who have at least one active listing
or seller-side marketplace action during the measurement period.

**Formula:**

Active Sellers = count(distinct seller_id with an eligible active listing/event)

**Grain:** Daily / weekly / monthly

**Use:** Measures the size of the active supply side.

---

## 3. Active Listings

**Definition:** Number of listings that are active and available during the
measurement period.

**Formula:**

Active Listings = count(distinct listing_id with active status)

**Use:** Measures available marketplace supply.

---

## 4. Buyer-to-Seller Liquidity Ratio

**Definition:** Ratio of active buyers to active sellers during the same
measurement period.

**Formula:**

Buyer-to-Seller Ratio = Active Buyers / Active Sellers

**Interpretation:**
- Higher ratio → relatively stronger buyer demand.
- Lower ratio → relatively stronger seller supply.

The metric should always be interpreted together with the underlying buyer and
seller counts.

---

## 5. Listing View-to-Contact Rate

**Definition:** Percentage of listing viewers who subsequently contact the
seller.

**Formula:**

View-to-Contact Rate =
unique buyers contacting sellers /
unique buyers viewing listings × 100

**Use:** Measures how effectively marketplace supply converts interest into
seller contact.

---

## 6. Contact-to-Application Rate

**Definition:** Percentage of buyers who contact a seller and subsequently
submit an application.

**Formula:**

Contact-to-Application Rate =
unique buyers submitting applications /
unique buyers contacting sellers × 100

**Use:** Measures progression from initial marketplace engagement toward a
higher-intent action.

---

## 7. Application-to-Outcome Rate

**Definition:** Percentage of submitted applications that reach the defined
successful marketplace outcome.

**Formula:**

Application-to-Outcome Rate =
successful outcomes /
submitted applications × 100

**Use:** Measures downstream marketplace effectiveness.

---

## 8. Time to First Response

**Definition:** Median elapsed time between a buyer's first marketplace contact
and the seller's first response.

**Formula:**

First Response Time =
seller_first_response_timestamp -
buyer_contact_timestamp

**Recommended statistic:** Median rather than mean.

**Use:** Measures responsiveness on the supply side.

---

## 9. Match Rate

**Definition:** Percentage of active buyers who achieve the defined marketplace
match or successful connection during the measurement period.

**Formula:**

Match Rate =
buyers achieving a successful match /
active buyers × 100

**Use:** Directly measures whether marketplace demand is finding relevant supply.

---

## 10. Successful Marketplace Outcome Rate

**Definition:** Percentage of active marketplace participants who reach the
final business-defined success event.

The exact success event must be agreed by the business before implementation.

**Formula:**

Outcome Rate =
successful outcomes /
eligible marketplace participants × 100

**Use:** Provides a high-level measure of marketplace effectiveness.

---

# Metric Governance

Every metric should have:

| Field | Requirement |
|---|---|
| Metric name | Stable documented name |
| Definition | Plain-language meaning |
| Formula | Explicit calculation |
| Grain | Daily / weekly / monthly or event-level |
| Owner | Business/data owner |
| Source | Event or table source |
| Refresh | Defined reporting cadence |
| Filters | Documented exclusions/inclusions |
| Version | Definition version |

## Important interpretation rule

Liquidity metrics should be reviewed together rather than interpreted in
isolation.

For example, a high buyer-to-seller ratio can indicate strong demand, but it may
also indicate insufficient supply. The underlying Active Buyers, Active Sellers,
Active Listings, Match Rate and downstream conversion metrics should therefore
be reviewed together.

## Status

These are proposed Phase 2 marketplace metric definitions created to satisfy
the Day 21 liquidity-metric requirement. They should be reviewed with the
marketplace/business owner before production implementation.