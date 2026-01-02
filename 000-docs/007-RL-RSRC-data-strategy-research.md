# STCI Data Strategy Research Findings

**Document ID:** 007
**Category:** RL (Research & Learning)
**Type:** RSRC (Research)
**Status:** FINAL
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Research Date:** 2026-01-01

---

## Executive Summary

This document captures critical research findings that inform STCI's data sourcing strategy. The research reveals that:

1. **Direct provider scraping is legally risky** - Major providers (OpenAI, etc.) explicitly prohibit automated data extraction in their ToS
2. **Aggregator APIs provide a viable alternative** - OpenRouter offers a public API with 400+ models and claims no markup from provider prices
3. **The market is crowded with comparison tools** - But none operate as a true INDEX with historical series and deterministic methodology
4. **LIBOR methodology provides a blueprint** - Waterfall approach, trimmed means, and transparency are key

---

## 1. Legal Constraints on Provider Scraping

### OpenAI Terms of Service

> "You may not... use any automated or programmatic method to extract data or output from the Services, including scraping, web harvesting, or web data extraction."

**Source:** [OpenAI Service Terms](https://openai.com/policies/service-terms/)

**Implication:** Scraping OpenAI's pricing page violates their ToS. Similar restrictions likely exist for other major providers.

### Risk Assessment

| Provider | Likely ToS Status | Risk Level |
|----------|------------------|------------|
| OpenAI | Explicit prohibition | High |
| Anthropic | Needs review | Medium-High |
| Google | Needs review | Medium |
| AWS | Likely prohibited | Medium-High |
| Azure | Likely prohibited | Medium-High |

### Conclusion

**Direct scraping is NOT a viable primary data source strategy.**

---

## 2. Aggregator APIs - The Viable Alternative

### OpenRouter API

**Endpoint:** `GET https://openrouter.ai/api/v1/models`

**Key Findings:**
- Returns 400+ models with pricing data
- Claims "no markup" - pricing matches provider websites
- JSON format with structured `pricing` object
- robots.txt explicitly allows `/api/` access
- No authentication required for models endpoint

**Pricing Data Structure:**
```json
{
  "id": "openai/gpt-4o",
  "name": "GPT-4o",
  "pricing": {
    "prompt": "0.0000025",    // USD per token
    "completion": "0.00001",   // USD per token
    "request": "0",
    "image": "0.007225"
  }
}
```

**Source:** [OpenRouter Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)

### Other Aggregators Reviewed

| Aggregator | Public API | Coverage | Notes |
|------------|-----------|----------|-------|
| OpenRouter | Yes (free) | 400+ models | Primary candidate |
| PricePerToken | No (uses OpenRouter data) | — | Derived source |
| LLMPriceCheck | No public API | — | UI only |
| Helicone | Needs research | 300+ | May have API |

### Recommendation

**OpenRouter API as primary data source** with periodic manual verification against provider pricing pages.

---

## 3. Existing Competitors

### Comparison/Calculator Tools

| Tool | URL | Differentiation |
|------|-----|-----------------|
| LLM Price Check | llmpricecheck.com | Calculator, no historical |
| Price Per Token | pricepertoken.com | Uses OpenRouter, no index |
| Helicone Calculator | helicone.ai/llm-cost | Cost estimation, no index |
| BinaryVerseAI | binaryverseai.com | Comparison, no index |
| AIMultiple | research.aimultiple.com/llm-pricing | Research, not automated |

**Source:** [AIMultiple LLM Pricing](https://research.aimultiple.com/llm-pricing/), [LLM Price Check](https://llmpricecheck.com/)

### Gap Analysis

| Capability | Competitors | STCI |
|------------|------------|------|
| Price comparison | ✅ Many | ✅ |
| Cost calculator | ✅ Many | ✅ |
| Historical time series | ❌ None found | ✅ DIFFERENTIATOR |
| Sub-indices (Frontier/Efficient/Open) | ❌ None | ✅ DIFFERENTIATOR |
| Deterministic recomputation | ❌ None | ✅ DIFFERENTIATOR |
| Published methodology | ❌ None | ✅ DIFFERENTIATOR |
| Aggregator-agnostic | ❌ Most use single source | ✅ DIFFERENTIATOR |

### STCI Differentiation Strategy

STCI is not another comparison tool. It's an **INDEX** (like LIBOR, CPI, or VIX):

1. **Reference rate** - Not just comparison, but a published benchmark
2. **Historical series** - Track price changes over time
3. **Sub-indices** - Segment by capability tier (Frontier, Efficient, Open)
4. **Methodology transparency** - Published, auditable, reproducible
5. **Determinism** - Same inputs always produce same outputs

---

## 4. LIBOR Methodology Lessons

### ICE LIBOR Structure

The LIBOR (London Interbank Offered Rate) methodology provides a blueprint:

**Source:** [ICE Benchmark Administration](https://www.ice.com/IBA), [ICE LIBOR Methodology](https://www.ice.com/publicdocs/USD_LIBOR_Methodology.pdf)

### Waterfall Approach

| Level | Data Source | Priority |
|-------|-------------|----------|
| 1 | Eligible transactions (highest quality) | Preferred |
| 2 | Transaction-derived data (adjusted) | Fallback |
| 3 | Expert judgment (market observations) | Last resort |

**STCI Application:**

| Level | STCI Data Source | Priority |
|-------|-----------------|----------|
| 1 | Aggregator APIs (OpenRouter) | Preferred |
| 2 | Manual verification fixtures | Fallback |
| 3 | Cross-reference other aggregators | Validation |

### Trimmed Mean

LIBOR uses trimmed arithmetic mean - remove highest and lowest 25%, average the rest.

**STCI Application:** Consider trimming outliers in sub-indices, especially when cross-referencing multiple sources.

### Regulatory Framework

LIBOR was administered by ICE Benchmark Administration under FCA regulation, with:
- Majority independent oversight board
- Published control framework
- Conflict of interest management
- Audit trail requirements

**STCI Application:** While not regulated, adopt similar transparency principles:
- Published methodology
- Versioned schemas
- Verification hashes
- Recomputation instructions

---

## 5. Revised Data Strategy

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                          │
├─────────────────────────────────────────────────────────────┤
│  Level 1: OpenRouter API         (automated, daily)        │
│  Level 2: Manual Verification    (monthly, key models)     │
│  Level 3: Cross-Reference        (anomaly detection)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    NORMALIZATION                            │
├─────────────────────────────────────────────────────────────┤
│  - Convert to USD/1M tokens                                 │
│  - Map model IDs to canonical names                         │
│  - Add provenance metadata                                  │
│  - Validate against schema                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    INDEX COMPUTATION                        │
├─────────────────────────────────────────────────────────────┤
│  - Apply basket filters (Frontier/Efficient/Open)          │
│  - Calculate weighted averages                              │
│  - Compute dispersion metrics                               │
│  - Generate verification hash                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PUBLICATION                              │
├─────────────────────────────────────────────────────────────┤
│  - Store observations + index values                        │
│  - Expose via read-only API                                 │
│  - Enable historical queries                                │
│  - Support recomputation verification                       │
└─────────────────────────────────────────────────────────────┘
```

### Source Tier Redefinition

| Tier | Source Type | Confidence | Example |
|------|-------------|------------|---------|
| T1 | Aggregator APIs (no ToS risk) | High | OpenRouter |
| T2 | Manual verification | High | Spot-checks |
| T3 | Cross-reference | Medium | Multiple aggregators |
| T4 | Community/historical | Lower | Archived data |

### Key Changes from Original Plan

| Original Assumption | Research Finding | Revised Approach |
|--------------------|--------------------|------------------|
| Scrape provider pages | ToS prohibits | Use aggregator APIs |
| Multiple sources equally viable | OpenRouter is most accessible | OpenRouter as primary |
| Competition is minimal | Many comparison tools exist | Differentiate as INDEX |
| Novel problem | Solved pattern (LIBOR) | Apply financial index methodology |

---

## 6. Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Can we scrape provider pages? | No - ToS violations |
| What's our primary data source? | OpenRouter API |
| How do we differentiate? | INDEX approach, not comparison |
| What methodology to follow? | LIBOR-inspired waterfall + transparency |

---

## 7. Remaining Open Questions

- [ ] OpenRouter API rate limits and ToS?
- [ ] Verification frequency for manual spot-checks?
- [ ] How to handle OpenRouter outages/errors?
- [ ] Historical data availability before STCI launch?

---

## References

- [OpenAI Terms of Service](https://openai.com/policies/service-terms/)
- [OpenRouter Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)
- [ICE Benchmark Administration](https://www.ice.com/IBA)
- [ICE LIBOR Methodology PDF](https://www.ice.com/publicdocs/USD_LIBOR_Methodology.pdf)
- [LLM Price Check](https://llmpricecheck.com/)
- [Price Per Token](https://pricepertoken.com/)
- [AIMultiple LLM Pricing](https://research.aimultiple.com/llm-pricing/)

---

*STCI — Standard Token Cost Index*
*Research Status: COMPLETE*
