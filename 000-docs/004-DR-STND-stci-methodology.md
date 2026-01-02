# STCI Methodology Specification

**Document ID:** 004
**Category:** AT (Architecture & Technical)
**Type:** SPEC (Specification)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Methodology Version:** 1.0.0

---

## Overview

This specification defines the methodology for computing STCI (Standard Token Cost Index) daily reference rates. The methodology is designed to be:

1. **Transparent:** All rules are publicly documented
2. **Reproducible:** Same inputs always produce same outputs
3. **Auditable:** Full provenance trail for every computation

---

## 1. Index Definitions

### 1.1 Primary Index

**STCI-ALL**
- Includes all eligible models across all providers
- Weighted equally within capability tiers
- Published daily at 00:00 UTC

### 1.2 Sub-Indices

| Index | Basket | Description |
|-------|--------|-------------|
| STCI-FRONTIER | Frontier-class models | GPT-4o, Claude 3.5, Gemini 1.5 Pro, etc. |
| STCI-EFFICIENT | High-efficiency models | GPT-4o-mini, Claude 3.5 Haiku, Gemini Flash |
| STCI-OPEN | Open-weight models | Llama 3.x, Mistral, Mixtral, Qwen |

---

## 2. Basket Definition

### 2.1 Eligibility Criteria

A model is eligible for STCI inclusion if:

1. **Published pricing:** T1 or T2 source tier required
2. **API availability:** Publicly accessible API endpoint
3. **Market presence:** Active provider with reasonable uptime
4. **Data completeness:** Both input and output rates available

### 2.2 Capability Tier Classification

| Tier | Criteria | Examples |
|------|----------|----------|
| Frontier | Flagship model, highest capability | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro |
| Efficient | Optimized for cost/speed | GPT-4o-mini, Claude 3.5 Haiku, Gemini 1.5 Flash |
| Open | Open-weight models | Llama 3.1 405B, Mistral Large, Qwen2.5 72B |

### 2.3 Initial Basket (v1.0.0)

**Frontier Tier:**
- openai/gpt-4o
- anthropic/claude-3-5-sonnet
- google/gemini-1.5-pro
- mistral/mistral-large-latest

**Efficient Tier:**
- openai/gpt-4o-mini
- anthropic/claude-3-5-haiku
- google/gemini-1.5-flash
- mistral/mistral-small-latest

**Open Tier:**
- meta/llama-3.1-405b
- meta/llama-3.1-70b
- mistral/mixtral-8x22b
- qwen/qwen2.5-72b

---

## 3. Weighting Methodology

### 3.1 MVP Weighting (v1.0.0)

**Equal weight within capability tiers:**
- Each model in a tier receives weight = 1 / (number of models in tier)
- STCI-ALL: Equal weight across all eligible models

**Rationale:** Usage data not available for MVP. Equal weight is transparent and neutral.

### 3.2 Future Weighting (v2.0.0+)

**Usage-weighted:**
- Weight based on estimated market share
- Sources: API traffic estimates, public usage data
- Updated quarterly

---

## 4. Aggregation Rules

### 4.1 Rate Computation

For each index:

```
Input Rate = Σ(weight_i × input_rate_i) for all models i in basket
Output Rate = Σ(weight_i × output_rate_i) for all models i in basket
Blended Rate = (Input Rate + Output Ratio × Output Rate) / (1 + Output Ratio)
```

Where:
- `Output Ratio` = 3.0 (configurable, represents typical output:input token ratio)

### 4.2 Dispersion Metrics

**Standard Deviation:**
```
σ_input = sqrt(Σ(weight_i × (input_rate_i - Input Rate)²))
σ_output = sqrt(Σ(weight_i × (output_rate_i - Output Rate)²))
```

**Dispersion Index:**
- Low dispersion (<0.2): Market convergence
- Medium dispersion (0.2-0.5): Normal variation
- High dispersion (>0.5): Price divergence

---

## 5. Edge Case Handling

### 5.1 Missing Data

**Single observation missing:**
- Carry forward previous day's rate
- Maximum carry-forward: 7 days
- After 7 days: Model removed from basket

**Multiple observations missing:**
- If <50% of basket has data: Index not published
- Flag: "INSUFFICIENT_DATA"

### 5.2 Price Changes

**Intra-day price change:**
- Use end-of-day (23:59 UTC) price
- Note price change in observations

**Announced future price:**
- Use current effective price
- Track upcoming changes in metadata

### 5.3 Model Changes

**New model addition:**
- Added at next rebalancing window (monthly)
- Not included until 7 days of stable data

**Model removal/deprecation:**
- Removed immediately on deprecation announcement
- Weight redistributed to remaining models

**Model rename:**
- Treat as same model if pricing unchanged
- Update model_id mapping

---

## 6. Rebalancing

### 6.1 Schedule

- **Monthly:** First trading day of each month
- **Ad-hoc:** Provider exits or major pricing structure changes

### 6.2 Process

1. Review basket eligibility
2. Update capability tier classifications
3. Recalculate weights
4. Publish rebalancing announcement (7 days prior)
5. Apply new basket at rebalancing date

---

## 7. Publication Schedule

### 7.1 Daily Publication

- **Calculation time:** 00:00 UTC
- **Publication time:** 00:15 UTC
- **Data window:** Previous 24 hours observations

### 7.2 Historical Backfill

- Backfill uses same methodology
- Clearly labeled as backfilled data
- Source observations documented

---

## 8. Determinism Requirements

### 8.1 Reproducibility

Given:
- Date D
- Observation set O for date D
- Methodology version M

Result: Identical index values every time

### 8.2 Rounding Rules

- All rates: 6 decimal places (e.g., 2.500000)
- Weights: 8 decimal places
- Final output: 2 decimal places (e.g., 2.50)

### 8.3 Computation Order

1. Sort observations by observation_id (lexicographic)
2. Apply eligibility filters
3. Calculate weights
4. Compute aggregates
5. Round final output

---

## 9. Methodology Configuration

### 9.1 Configuration File

Location: `data/fixtures/methodology.yaml`

```yaml
methodology_version: "1.0.0"
output_ratio: 3.0
carry_forward_max_days: 7
min_basket_coverage: 0.5
decimal_places:
  rates: 6
  weights: 8
  output: 2
baskets:
  STCI-FRONTIER:
    - openai/gpt-4o
    - anthropic/claude-3-5-sonnet
    - google/gemini-1.5-pro
    - mistral/mistral-large-latest
  STCI-EFFICIENT:
    - openai/gpt-4o-mini
    - anthropic/claude-3-5-haiku
    - google/gemini-1.5-flash
    - mistral/mistral-small-latest
weighting:
  type: equal
rebalancing:
  schedule: monthly
  day: 1
```

---

## 10. Verification

### 10.1 Self-Verification

- Indexer produces verification hash
- Hash = SHA256(sorted observations + methodology version)
- Stored with each daily output

### 10.2 Third-Party Verification

Anyone can:
1. Obtain observations for date D
2. Obtain methodology version M
3. Run indexer
4. Compare output to published value

---

## References

- 001-PP-PROD-stci-prd.md
- 003-AT-SPEC-observation-schema.md
- 005-OD-SOPS-recompute-runbook.md

---

*STCI — Standard Token Cost Index*
*Methodology Version: 1.0.0*
