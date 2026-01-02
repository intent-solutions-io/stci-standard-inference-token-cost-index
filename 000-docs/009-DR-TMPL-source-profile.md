# STCI Source Profile Template

**Document ID:** 009
**Category:** DR (Documentation & Reference)
**Type:** TMPL (Template)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01

---

## Purpose

This template defines the required fields and analysis for onboarding a new data source into STCI. Every source must have a completed Source Profile before production use.

---

## Source Profile: [SOURCE_NAME]

### 1. Source Identification

| Field | Value |
|-------|-------|
| **Source ID** | `[e.g., openrouter, anthropic-direct]` |
| **Source Name** | `[Human-readable name]` |
| **Source Type** | `[aggregator / provider / community]` |
| **Source Tier** | `[T1 / T2 / T3 / T4]` |
| **Source URL** | `[Primary URL]` |
| **API Endpoint** | `[If applicable]` |
| **Profile Created** | `YYYY-MM-DD` |
| **Profile Author** | `[Name]` |
| **Last Verified** | `YYYY-MM-DD` |

---

### 2. Legal & Compliance

| Field | Status | Notes |
|-------|--------|-------|
| **ToS Reviewed** | `[ ] Yes [ ] No` | |
| **robots.txt Reviewed** | `[ ] Yes [ ] No` | |
| **Automated Access Permitted** | `[ ] Yes [ ] No [ ] Unclear` | |
| **Data Redistribution Permitted** | `[ ] Yes [ ] No [ ] Unclear` | |
| **Attribution Required** | `[ ] Yes [ ] No` | Format: |
| **Rate Limits** | `[e.g., 100 req/min]` | |
| **API Key Required** | `[ ] Yes [ ] No` | |
| **Commercial Use Permitted** | `[ ] Yes [ ] No [ ] Unclear` | |

**ToS Key Excerpts:**
```
[Paste relevant ToS sections here]
```

**Legal Risk Assessment:** `[Low / Medium / High]`

**Compliance Notes:**
```
[Any additional notes on legal/compliance considerations]
```

---

### 3. Data Availability

| Field | Value |
|-------|-------|
| **Data Format** | `[JSON / HTML / CSV / Other]` |
| **Schema Stability** | `[Stable / Occasional changes / Volatile]` |
| **Historical Data Available** | `[ ] Yes [ ] No` |
| **Update Frequency** | `[Real-time / Daily / Weekly / Ad-hoc]` |
| **Update Notification** | `[API header / Changelog / None]` |

**Models Covered:**
- [ ] OpenAI (GPT-4o, GPT-4o-mini, etc.)
- [ ] Anthropic (Claude 3.5 Sonnet, Haiku, etc.)
- [ ] Google (Gemini 1.5 Pro, Flash, etc.)
- [ ] Mistral (Large, Small, etc.)
- [ ] Open-weight (Llama, Mixtral, etc.)
- [ ] Other: `[List]`

**Approximate Model Count:** `[Number]`

---

### 4. Pricing Data Structure

**Pricing Fields Available:**

| Field | Available | Format | Notes |
|-------|-----------|--------|-------|
| Input token rate | `[ ] Yes [ ] No` | `[e.g., $/token]` | |
| Output token rate | `[ ] Yes [ ] No` | `[e.g., $/token]` | |
| Request fee | `[ ] Yes [ ] No` | | |
| Image input rate | `[ ] Yes [ ] No` | | |
| Batch pricing | `[ ] Yes [ ] No` | | |
| Cached input rate | `[ ] Yes [ ] No` | | |
| Context window | `[ ] Yes [ ] No` | | |
| Rate limits | `[ ] Yes [ ] No` | | |

**Pricing Units:** `[$/token, $/1K tokens, $/1M tokens]`

**Currency:** `[USD / EUR / Other]`

**Sample Response:**
```json
{
  "example": "paste sample data structure here"
}
```

---

### 5. Collection Strategy

**Collection Method:**
- [ ] API call
- [ ] Web scraping (if permitted)
- [ ] Manual entry
- [ ] File download

**Collection Frequency:** `[Daily / Hourly / On-demand]`

**Collection Time:** `[e.g., 00:00 UTC]`

**Error Handling:**
- On timeout: `[retry / skip / alert]`
- On rate limit: `[backoff / skip / alert]`
- On schema change: `[alert / attempt parse / fail]`

**Collector Module Path:** `services/collector/sources/[source_id].py`

---

### 6. Normalization Mapping

**Model ID Mapping:**

| Source Model ID | STCI Canonical ID | Notes |
|-----------------|-------------------|-------|
| `openai/gpt-4o` | `openai/gpt-4o` | |
| `anthropic/claude-3.5-sonnet` | `anthropic/claude-3-5-sonnet` | |
| | | |

**Rate Conversion:**
```
Source: [e.g., $/token → multiply by 1,000,000 → $/1M tokens]
```

**Required Transformations:**
1. `[Transformation step 1]`
2. `[Transformation step 2]`

---

### 7. Validation Rules

**Required Fields:**
- [ ] Model ID present and mapped
- [ ] Input rate >= 0
- [ ] Output rate >= 0
- [ ] Source URL valid

**Sanity Checks:**
- [ ] Input rate < $100/1M tokens (flag if exceeded)
- [ ] Output rate < $500/1M tokens (flag if exceeded)
- [ ] Input rate <= Output rate (flag if violated)

**Cross-Reference Validation:**
- [ ] Compare to other sources (within 10% tolerance)
- [ ] Compare to previous day (flag if >50% change)

---

### 8. Monitoring & Alerting

**Health Checks:**
- [ ] API reachability (daily)
- [ ] Response schema validation (each collection)
- [ ] Data freshness check (if stale >48h, alert)

**Alert Conditions:**
| Condition | Severity | Action |
|-----------|----------|--------|
| API unreachable | P1 | Page on-call |
| Schema changed | P2 | Alert, attempt fallback |
| Price change >50% | P2 | Alert, manual review |
| Data stale >48h | P2 | Alert, check source status |

---

### 9. Source Acceptance Checklist

Before production use, verify:

- [ ] Legal review completed (ToS, robots.txt)
- [ ] Collector module implemented and tested
- [ ] Normalization mapping documented
- [ ] Validation rules implemented
- [ ] Monitoring configured
- [ ] Source profile reviewed and approved
- [ ] Test data collected successfully
- [ ] Cross-reference with known prices successful

**Approved By:** `[Name]`
**Approval Date:** `YYYY-MM-DD`

---

### 10. Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial profile created | [Name] |
| | | |

---

## Example: OpenRouter Source Profile

See: `010-DR-REFF-openrouter-profile.md` (to be created)

---

*STCI — Standard Token Cost Index*
*Template Version: 1.0.0*
