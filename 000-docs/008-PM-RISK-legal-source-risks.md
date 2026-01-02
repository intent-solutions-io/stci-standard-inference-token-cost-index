# STCI Legal & Source Risk Register

**Document ID:** 008
**Category:** PM (Project Management)
**Type:** RISK (Risk Register)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01

---

## Overview

This register documents legal, operational, and data quality risks related to STCI data sourcing and publication. Each risk includes assessment, mitigation, and monitoring approach.

---

## Risk Assessment Framework

### Probability Scale
- **1 - Very Low:** <5% chance
- **2 - Low:** 5-25% chance
- **3 - Medium:** 25-50% chance
- **4 - High:** 50-75% chance
- **5 - Very High:** >75% chance

### Impact Scale
- **1 - Minimal:** Minor inconvenience
- **2 - Minor:** Limited functionality impact
- **3 - Moderate:** Significant feature degradation
- **4 - Major:** Core functionality blocked
- **5 - Critical:** Project viability threatened

**Risk Score = Probability × Impact**

---

## 1. Legal & Terms of Service Risks

### RISK-L01: Direct Provider Scraping Violation

**Category:** Legal
**Probability:** 5 (if attempted)
**Impact:** 5 (cease & desist, legal action)
**Risk Score:** 25 (CRITICAL)

**Description:**
Scraping provider pricing pages (OpenAI, Anthropic, etc.) violates explicit Terms of Service prohibitions on automated data extraction.

**Evidence:**
OpenAI ToS: "You may not... use any automated or programmatic method to extract data or output from the Services, including scraping, web harvesting, or web data extraction."

**Mitigation:**
- **AVOID:** Do not scrape provider websites directly
- Use aggregator APIs (OpenRouter) as primary source
- Manual verification only for spot-checks

**Status:** MITIGATED (by design)

---

### RISK-L02: Aggregator API ToS Violation

**Category:** Legal
**Probability:** 2
**Impact:** 4
**Risk Score:** 8 (MEDIUM)

**Description:**
OpenRouter or other aggregator APIs may have ToS restrictions on data reuse, redistribution, or commercial use.

**Mitigation:**
- [ ] Review OpenRouter ToS for data redistribution rights
- [ ] Consider reaching out for explicit permission
- [ ] Attribute data source clearly
- [ ] Maintain fallback to manual data collection

**Owner:** Legal review before public launch

---

### RISK-L03: Pricing Data Intellectual Property

**Category:** Legal
**Probability:** 2
**Impact:** 3
**Risk Score:** 6 (LOW-MEDIUM)

**Description:**
Providers may claim pricing data as proprietary intellectual property.

**Mitigation:**
- Prices are factual data, generally not copyrightable
- Provide clear attribution
- Do not claim data ownership
- Focus on index value (derived work)

---

## 2. Data Source Risks

### RISK-D01: OpenRouter API Unavailability

**Category:** Operational
**Probability:** 3
**Impact:** 4
**Risk Score:** 12 (HIGH)

**Description:**
OpenRouter API becomes unavailable (outage, rate limiting, discontinuation, ToS change).

**Mitigation:**
- Cache recent observations locally
- Implement 7-day carry-forward rule
- Develop fallback to manual collection
- Monitor for alternative aggregator APIs
- Maximum acceptable outage: 7 days

**Trigger:** If API fails for 3+ consecutive days, escalate

---

### RISK-D02: OpenRouter Data Accuracy

**Category:** Data Quality
**Probability:** 2
**Impact:** 3
**Risk Score:** 6 (LOW-MEDIUM)

**Description:**
OpenRouter claims "no markup" but data may lag or contain errors compared to actual provider pricing.

**Mitigation:**
- Monthly manual verification of key models (GPT-4o, Claude, Gemini)
- Anomaly detection for price changes >20%
- Document discrepancies in observation metadata
- Cross-reference with other sources when available

---

### RISK-D03: Model Coverage Gaps

**Category:** Data Quality
**Probability:** 3
**Impact:** 2
**Risk Score:** 6 (LOW-MEDIUM)

**Description:**
New models released by providers may not appear in OpenRouter immediately, creating coverage gaps.

**Mitigation:**
- Accept 48-72 hour lag for new model inclusion
- Monitor provider announcements
- Manual addition for critical new models
- Document coverage policy in methodology

---

### RISK-D04: Pricing Format Changes

**Category:** Technical
**Probability:** 2
**Impact:** 3
**Risk Score:** 6 (LOW-MEDIUM)

**Description:**
OpenRouter API schema or pricing format changes, breaking collector.

**Mitigation:**
- Version API responses in observations
- Schema validation with clear error reporting
- Monitor OpenRouter changelog/docs
- Alert on schema validation failures

---

## 3. Index Integrity Risks

### RISK-I01: Calculation Error

**Category:** Technical
**Probability:** 2
**Impact:** 5
**Risk Score:** 10 (HIGH)

**Description:**
Bug in index computation produces incorrect values.

**Mitigation:**
- Unit tests with fixed fixtures (golden tests)
- Verification hash on each computation
- Third-party recomputation capability
- Correction procedure documented

---

### RISK-I02: Historical Data Restatement

**Category:** Reputational
**Probability:** 3
**Impact:** 3
**Risk Score:** 9 (MEDIUM)

**Description:**
Need to restate historical index values due to data corrections or methodology changes.

**Mitigation:**
- Document restatement policy
- Maintain observation history for audit
- Publish correction notices
- Version methodology clearly

---

### RISK-I03: Index Manipulation

**Category:** Integrity
**Probability:** 1
**Impact:** 5
**Risk Score:** 5 (LOW)

**Description:**
Bad actor attempts to manipulate STCI values.

**Mitigation:**
- Deterministic computation from public sources
- Third-party verification possible
- No external submissions in MVP
- Transparent methodology

---

## 4. Operational Risks

### RISK-O01: Single Maintainer Risk

**Category:** Operational
**Probability:** 3
**Impact:** 3
**Risk Score:** 9 (MEDIUM)

**Description:**
Single person maintaining STCI creates bus factor risk.

**Mitigation:**
- Comprehensive documentation
- Automated daily runs
- Open source code
- Clear runbooks

---

### RISK-O02: Infrastructure Failure

**Category:** Operational
**Probability:** 2
**Impact:** 3
**Risk Score:** 6 (LOW-MEDIUM)

**Description:**
API infrastructure fails, preventing index publication.

**Mitigation:**
- Static site fallback (JSON files)
- Multiple deployment options
- Monitoring and alerting
- 99.5% uptime target (allows ~1.8 days/year downtime)

---

## Risk Summary Matrix

| Risk ID | Description | Score | Status |
|---------|-------------|-------|--------|
| RISK-L01 | Provider scraping violation | 25 | MITIGATED |
| RISK-D01 | OpenRouter unavailability | 12 | OPEN |
| RISK-I01 | Calculation error | 10 | OPEN |
| RISK-O01 | Single maintainer | 9 | OPEN |
| RISK-I02 | Historical restatement | 9 | OPEN |
| RISK-L02 | Aggregator ToS | 8 | NEEDS REVIEW |
| RISK-D02 | Data accuracy | 6 | OPEN |
| RISK-D03 | Coverage gaps | 6 | OPEN |
| RISK-D04 | Format changes | 6 | OPEN |
| RISK-O02 | Infrastructure failure | 6 | OPEN |
| RISK-L03 | Pricing IP claims | 6 | LOW PRIORITY |
| RISK-I03 | Index manipulation | 5 | LOW PRIORITY |

---

## Action Items

| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P0 | Review OpenRouter ToS for data reuse rights | Legal | Before launch |
| P1 | Implement 7-day carry-forward for outages | Engineering | v0.1.0 |
| P1 | Create golden test fixtures | Engineering | v0.1.0 |
| P1 | Document correction/restatement policy | Product | v0.1.0 |
| P2 | Set up monitoring for OpenRouter API | DevOps | v0.2.0 |
| P2 | Identify backup aggregator sources | Research | v0.2.0 |

---

## References

- 007-RL-RSRC-data-strategy-research.md
- 004-DR-STND-stci-methodology.md

---

*STCI — Standard Token Cost Index*
*Risk Register Version: 1.0.0*
