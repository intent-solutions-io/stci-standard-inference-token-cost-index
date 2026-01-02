# STCI — Product Requirements Document (PRD)

**Document ID:** 001
**Category:** PP (Product & Planning)
**Type:** PROD (Product Requirements)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Last Updated:** 2026-01-01

---

## Executive Summary

STCI (Standard Token Cost Index) is a public, vendor-neutral price index for LLM tokens. It provides transparent, reproducible reference rates for large language model pricing, enabling enterprises, researchers, and developers to track, compare, and forecast token costs across providers.

---

## 1. Product Vision & Problem Statement

### 1.1 Vision
A trusted, auditable source of truth for LLM token pricing—the "price tape" the market needs.

### 1.2 Problem Definition

**Who hurts today:**
- Enterprise procurement teams comparing LLM costs
- Developers estimating API costs for applications
- Researchers analyzing AI market economics
- Contract negotiators needing benchmark rates

**Current pain points:**
- No standard format across providers ($/1K, $/1M, per-minute, etc.)
- No historical record of price changes
- No neutral benchmark for "market rate"
- Aggregator pricing varies from posted rates

**Why now:**
- LLM API spending is growing rapidly
- Enterprise adoption requires cost transparency
- Market is maturing and needs price discovery infrastructure

**Cost of inaction:**
- Enterprises overpay due to lack of visibility
- No accountability for pricing changes
- Market inefficiency persists

---

## 2. Objectives & Key Results (OKRs)

### 2.1 Primary Objective
Establish STCI as the trusted reference rate for LLM token pricing.

### 2.2 Key Results (MVP)

| KR | Metric | Target | Timeline |
|----|--------|--------|----------|
| KR1 | Providers tracked | 10+ major providers | v0.1.0 |
| KR2 | Index computation | Deterministic, reproducible | v0.1.0 |
| KR3 | API availability | Read-only public endpoint | v0.2.0 |
| KR4 | Historical data | 90+ days backfilled | v0.3.0 |

### 2.3 Success Criteria
- **MVP Success:** Compute daily index from 10+ providers with documented methodology
- **Product-Market Fit:** 100+ daily API consumers, external citations
- **Scale Success:** Industry adoption as reference rate

---

## 3. Users & Market Segments

### 3.1 Primary Personas

**Enterprise Procurement**
- Demographics: Large enterprises with $100K+/year LLM spend
- Goals: Optimize vendor selection, negotiate contracts
- Pain Points: No benchmark for "fair" pricing
- Success Metrics: Cost savings, contract terms

**Developer/Builder**
- Demographics: Developers building LLM-powered applications
- Goals: Estimate and budget API costs
- Pain Points: Pricing fragmentation, surprise bills
- Success Metrics: Accurate cost estimates

### 3.2 Secondary Personas
- Researchers studying AI economics
- Journalists covering AI industry
- Investors evaluating AI companies

---

## 4. Product Scope & Prioritization

### 4.1 MVP (v0.1.0) — Must Have
1. **Canonical observation schema**
   - Normalized pricing data structure
   - Provenance metadata

2. **Deterministic index computation**
   - Reproducible calculation from observations
   - Configurable methodology

3. **Fixture-based collector stub**
   - Manual data entry workflow
   - Validation rules

4. **Read-only API stubs**
   - Health check
   - Latest index
   - Historical query

5. **Documentation suite**
   - Methodology specification
   - Schema documentation
   - Runbooks

### 4.2 v0.2.0 — Should Have
- Automated T1 collectors (5+ providers)
- Daily scheduled runs
- Historical backfill

### 4.3 Future (v0.3.0+)
- Sub-indices (FRONTIER, EFFICIENT, OPEN)
- Dashboard UI
- Aggregator (T3) pricing
- Usage-weighted indices

### 4.4 Explicitly Out of Scope (MVP)
- Exchange/trading functionality
- Real-time streaming prices
- Derivative contracts
- Provider authentication/billing

---

## 5. Functional Requirements

### 5.1 Observation Ingestion
- Accept normalized observations
- Validate against schema
- Reject duplicates
- Track provenance

### 5.2 Index Computation
- Load observations for date
- Apply methodology (basket, weights)
- Compute index values
- Store results

### 5.3 API Access
- Return latest index
- Return historical values
- Return methodology documentation
- No authentication required

### 5.4 Verification
- Recompute any historical date
- Compare to stored result
- Report discrepancies

---

## 6. Non-Functional Requirements

### 6.1 Determinism
- Same inputs MUST produce identical outputs
- No floating-point inconsistencies
- Documented rounding rules

### 6.2 Transparency
- All methodology publicly documented
- Observation sources cited
- Change history maintained

### 6.3 Availability
- API uptime target: 99.5%
- Response time: <500ms for latest index
- Historical data: <2s for any date

---

## 7. Dependencies & Risks

### 7.1 Dependencies
- Provider pricing page availability
- Schema stability
- Beads for task tracking

### 7.2 Risks
- Provider ToS restrictions on scraping
- Pricing format changes
- Model naming inconsistencies

---

## 8. Success Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Data freshness | Age of latest observation | <24 hours |
| Coverage | % of major providers tracked | 80% |
| Accuracy | Delta from posted prices | <1% |
| Reproducibility | % of dates with matching recompute | 100% |

---

## References

- 002-AT-ADEC-index-first-strategy.md (Architecture Decision)
- 003-AT-SPEC-observation-schema.md (Schema Specification)
- 004-AT-SPEC-stci-methodology.md (Methodology Specification)

---

*STCI — Standard Token Cost Index*
*Document Status: DRAFT*
