# Architecture Decision: Index-First Strategy (Not Exchange)

**Document ID:** 002
**ADR Number:** ADR-001
**Category:** AT (Architecture & Technical)
**Type:** ADEC (Architecture Decision)
**Status:** ACCEPTED
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Decision Date:** 2026-01-01

---

## Decision Summary

### Executive Summary
**Decision:** Build STCI as a **read-only price index** (reference rate) rather than a trading exchange or marketplace.

**Impact:** Dramatically simplifies MVP scope; focuses on data quality and methodology transparency rather than transaction infrastructure.

### Decision Statement
> We will **build a price index product** (observation → normalization → aggregation → publication) **in order to** establish STCI as a trusted reference rate **accepting that** we forgo near-term monetization opportunities from transaction fees.

---

## Context & Problem Statement

### Business Context
- LLM token pricing lacks a neutral benchmark
- Enterprises need reference rates for procurement
- Market infrastructure is immature

**Alternatives considered:**
1. Build an exchange (order matching, settlement)
2. Build an aggregator (route requests to cheapest provider)
3. Build a pure index (reference rate publication only)

### Technical Context
- Exchange requires: order book, matching engine, settlement, custody, compliance
- Aggregator requires: API routing, billing, provider relationships
- Index requires: data collection, normalization, computation, publication

### Problem Statement
**Core Problem:** The market needs price transparency before it needs transaction infrastructure.

**Success Criteria:**
- Metric 1: Daily index publication with documented methodology
- Metric 2: Independent verification possible
- Metric 3: Industry adoption as reference rate

---

## Decision Drivers

### Technical Drivers
| Driver | Weight | Rationale |
|--------|--------|-----------|
| Simplicity | High | Index has 10x fewer components than exchange |
| Time to market | High | MVP in weeks vs months |
| Data quality | High | Can focus entirely on accuracy |
| Determinism | Medium | Essential for trust |

### Business Drivers
| Driver | Weight | Rationale |
|--------|--------|-----------|
| Trust | High | Index must be neutral to be trusted |
| Cost | High | No transaction infrastructure to maintain |
| Risk | High | No financial custody = no regulatory burden |

---

## Considered Alternatives

### Option 1: Price Index (CHOSEN)
**Description:** Collect, normalize, and publish reference rates only.

**Pros:**
- Simplest architecture
- Fastest to market
- Clear trust model (no financial stake)
- Foundation for future exchange if needed

**Cons:**
- No direct transaction revenue
- Requires separate monetization strategy

**Risk Assessment:**
- Technical Risk: Low
- Implementation Risk: Low
- Operational Risk: Low

### Option 2: Token Exchange
**Description:** Build order book and matching engine for token transactions.

**Pros:**
- Transaction fee revenue
- Higher market impact

**Cons:**
- Complex infrastructure
- Regulatory requirements
- Custody liability
- 6-12 month build time

**Why Rejected:** Premature. Market needs price discovery before transaction infrastructure.

### Option 3: Routing Aggregator
**Description:** Route API requests to cheapest provider.

**Pros:**
- Margin capture
- Immediate utility

**Cons:**
- Provider relationship dependencies
- Quality/latency tradeoffs
- Competitive with existing aggregators

**Why Rejected:** Competes with existing players; not differentiated.

---

## Decision

**Chosen Option:** Price Index (Option 1)

**Rationale:**
1. **Trust first:** A neutral index establishes credibility before commercial layers
2. **Speed:** Ship useful data immediately rather than wait for exchange infrastructure
3. **Foundation:** Index is prerequisite for any future exchange or derivatives
4. **Risk:** No custody or settlement risk

---

## Consequences

### Positive
- Rapid MVP delivery
- Clear value proposition
- Minimal operational burden
- Foundation for future expansion

### Negative
- No transaction revenue in v1
- Must develop separate monetization (data licensing, enterprise API)

### Neutral
- Positions STCI as infrastructure rather than competitor

---

## Implementation Notes

### What This Means for Architecture
- No order book, matching engine, or settlement
- No user accounts or authentication (MVP)
- No billing or payment processing
- Focus: Data pipeline and computation

### Migration Path to Exchange (If Ever)
1. Build index (this decision)
2. Establish market trust
3. Add authenticated enterprise tier
4. Consider exchange features based on demand

---

## Related Decisions

- ADR-002 (future): Monetization strategy
- ADR-003 (future): Provider API access approach

---

## References

- 001-PP-PROD-stci-prd.md
- 004-AT-SPEC-stci-methodology.md

---

*STCI — Standard Token Cost Index*
*ADR Status: ACCEPTED*
