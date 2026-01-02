# STCI Data Operations Best Practices

**Document ID:** 010
**Category:** DR (Documentation & Reference)
**Type:** SOPS (Standard Operating Procedures)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01

---

## Overview

This document establishes best practices for STCI data operations: collection, verification, monitoring, and incident response. These practices ensure data quality, reliability, and auditability.

---

## 1. Data Collection Practices

### 1.1 Collection Schedule

| Frequency | Scope | Purpose |
|-----------|-------|---------|
| Daily (00:00 UTC) | OpenRouter API | Primary data collection |
| Weekly (Sunday) | Manual verification | Spot-check key models |
| Monthly (1st) | Full audit | Cross-reference all sources |
| Ad-hoc | Announced price changes | Immediate update |

### 1.2 Collection Protocol

**Pre-Collection:**
1. Check source health (API reachable)
2. Verify last collection timestamp
3. Confirm no active incidents

**Collection:**
1. Fetch data from source
2. Log raw response (for debugging)
3. Validate against schema
4. Normalize to observation format
5. Apply validation rules
6. Store with provenance metadata

**Post-Collection:**
1. Verify observation count
2. Run anomaly detection
3. Log collection metrics
4. Alert on failures

### 1.3 Idempotency

Collections must be idempotent:
- Same source + date = same observations
- Use deterministic observation IDs
- Overwrite if re-collecting (not append)

---

## 2. Verification Practices

### 2.1 Automated Verification

| Check | Frequency | Action on Failure |
|-------|-----------|-------------------|
| Schema validation | Every collection | Reject observation |
| Rate sanity (<$100/1M input) | Every collection | Flag, include with warning |
| Model ID mapping exists | Every collection | Skip unknown models |
| Source reachable | Pre-collection | Retry 3x, then alert |

### 2.2 Manual Verification

**Monthly Spot-Check Protocol:**

1. Select 5 key models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, etc.)
2. Visit each provider's pricing page directly
3. Compare published price to STCI observation
4. Document any discrepancies
5. Update source profile if needed

**Verification Log Format:**
```markdown
## Verification Log: YYYY-MM-DD

### GPT-4o
- Provider URL: https://openai.com/pricing
- Provider Input Rate: $2.50/1M
- STCI Observation: $2.50/1M
- Status: ✅ MATCH

### Claude 3.5 Sonnet
- Provider URL: https://anthropic.com/pricing
- Provider Input Rate: $3.00/1M
- STCI Observation: $3.00/1M
- Status: ✅ MATCH
```

### 2.3 Cross-Reference Verification

When multiple sources available:
1. Collect from all sources
2. Compare rates for same model
3. Flag discrepancies >10%
4. Use primary source (T1) if discrepancy
5. Document deviation in observation notes

---

## 3. Anomaly Detection

### 3.1 Price Change Detection

| Change Magnitude | Classification | Action |
|------------------|----------------|--------|
| <5% | Normal | Log only |
| 5-20% | Notable | Log + review next day |
| 20-50% | Significant | Alert + manual verification |
| >50% | Anomaly | Alert + hold until verified |

### 3.2 Staleness Detection

| Staleness Period | Classification | Action |
|------------------|----------------|--------|
| <24 hours | Current | Normal operation |
| 24-48 hours | Warning | Log warning |
| 48-72 hours | Stale | Alert, investigate |
| >72 hours | Critical | Escalate, consider carry-forward |

### 3.3 Model Lifecycle Events

Detect and log:
- New model appears in source
- Model disappears from source
- Model ID changes
- Model capability tier change

---

## 4. Incident Response

### 4.1 Incident Classification

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 | Index cannot be computed | <1 hour | API completely down |
| P2 | Data quality degraded | <4 hours | >20% models missing |
| P3 | Minor issue | <24 hours | Single model stale |
| P4 | Informational | Best effort | Schema warning |

### 4.2 Response Procedures

**P1 - Critical:**
1. Acknowledge within 15 minutes
2. Attempt fallback data source
3. If >7 days since last valid data: suspend index publication
4. Post incident notice
5. Post-incident review required

**P2 - High:**
1. Acknowledge within 1 hour
2. Investigate root cause
3. Apply carry-forward if appropriate
4. Document in daily log

**P3/P4 - Medium/Low:**
1. Log issue
2. Address in next business day
3. Update relevant documentation

### 4.3 Carry-Forward Rule

When current data unavailable:
1. Use most recent valid observation
2. Maximum carry-forward: 7 days
3. Mark observation with `carried_forward: true`
4. After 7 days: exclude model from index

---

## 5. Audit Trail Requirements

### 5.1 What to Log

| Event | Required Fields |
|-------|-----------------|
| Collection start | timestamp, source_id, run_id |
| Collection end | timestamp, observation_count, duration, status |
| Validation failure | timestamp, observation_id, rule_violated, raw_data |
| Anomaly detected | timestamp, model_id, anomaly_type, value, expected |
| Index computed | timestamp, date, hash, methodology_version |
| Manual verification | timestamp, model_id, provider_value, stci_value, status |

### 5.2 Log Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Raw API responses | 30 days | Object storage |
| Observations | Indefinite | Database |
| Collection logs | 90 days | Log aggregator |
| Verification logs | Indefinite | 000-docs/ |
| Index outputs | Indefinite | Database + archive |

### 5.3 Audit Support

Enable third-party verification:
- Publish observations used for each index
- Include methodology version in output
- Provide verification hash
- Document recomputation steps

---

## 6. Operational Checklists

### 6.1 Daily Operations

```
[ ] Verify previous day's collection completed
[ ] Check for P1/P2 alerts
[ ] Review anomaly log
[ ] Confirm index published
[ ] Note any manual interventions
```

### 6.2 Weekly Operations

```
[ ] Review all alerts from past week
[ ] Check source health status
[ ] Verify carry-forward usage (should be rare)
[ ] Spot-check 2-3 random observations
[ ] Update operational log
```

### 6.3 Monthly Operations

```
[ ] Complete full verification (5+ key models)
[ ] Review and update source profiles
[ ] Check for new models to add
[ ] Review methodology for updates
[ ] Archive old logs per retention policy
[ ] Update documentation if needed
```

---

## 7. Monitoring Dashboard (Planned)

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Collection success rate | >99% | <95% |
| Observations per day | ~400 | <350 or >450 |
| Average collection time | <60s | >300s |
| Anomalies per week | <5 | >10 |
| Index publication time | <00:30 UTC | >01:00 UTC |
| API latency (p95) | <200ms | >500ms |

---

## References

- 005-DR-SOPS-recompute-runbook.md
- 007-RL-RSRC-data-strategy-research.md
- 008-PM-RISK-legal-source-risks.md
- 009-DR-TMPL-source-profile.md

---

*STCI — Standard Token Cost Index*
*Data Ops Version: 1.0.0*
