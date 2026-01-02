# ADR: OpenRouter as Primary Data Source

**Document ID:** 012
**Category:** AT (Architecture & Technical)
**Type:** ADEC (Architecture Decision)
**Status:** ACCEPTED
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Phase:** 0 (Foundation)

---

## Context

STCI requires reliable, legal access to LLM pricing data across multiple providers. The challenge: how do we collect pricing data from 20+ LLM providers without violating Terms of Service or creating unsustainable maintenance burden?

### Constraints

1. **Legal Compliance**: Must not violate provider ToS
2. **Data Quality**: Pricing must be accurate and timely
3. **Coverage**: Need broad model coverage (400+ models)
4. **Sustainability**: Collection method must be maintainable long-term
5. **Cost**: Minimize operational costs for data collection

### Research Findings

**Direct Provider Scraping (Not Viable)**:
- OpenAI ToS Section 2(c): "You may not... scrape... any Service"
- Anthropic, Google, Mistral have similar restrictions
- High maintenance burden (each provider's page structure differs)
- ToS changes could make approach illegal overnight

**Existing Comparison Sites**:
- LLMPriceCheck.com, PricePerToken.com, Helicone - all exist
- Unknown data freshness and methodology
- No API access for programmatic consumption
- Scraping these sites has same ToS issues

**OpenRouter API**:
- Public API at `https://openrouter.ai/api/v1/models`
- 400+ models from all major providers
- No authentication required for models endpoint
- Claims "no markup" from provider prices
- JSON format, well-structured
- Rate limits are reasonable for daily collection

---

## Decision

**Use OpenRouter API as the Tier-1 (primary) data source for STCI.**

OpenRouter provides:
- Single API endpoint for multi-provider pricing
- Legal access (public API, no ToS prohibition found)
- Structured JSON output
- Comprehensive model coverage
- Daily collection feasibility

---

## Alternatives Considered

### Alternative 1: Direct Provider Scraping

**Rejected**: Violates ToS for most major providers. OpenAI explicitly prohibits scraping. Creates legal risk and unsustainable maintenance.

### Alternative 2: Community-Sourced Data

**Deferred as Tier-4**: GitHub repos like `BerriAI/litellm` maintain pricing. Useful for cross-validation but not primary source (staleness risk, no SLA).

### Alternative 3: Manual Collection

**Deferred as Fallback**: Manual data entry from pricing pages. High labor cost, not scalable. Reserved for emergency validation only.

### Alternative 4: Partnership with Providers

**Future Consideration**: Direct data feeds from providers would be ideal but requires business development effort. Not viable for MVP.

### Alternative 5: Scrape Comparison Sites

**Rejected**: Same ToS issues as direct scraping. Unknown data quality. Single point of failure if site changes.

---

## Consequences

### Positive

1. **Legal Clarity**: OpenRouter API is public and intended for programmatic access
2. **Single Integration**: One API covers 400+ models vs. 20+ provider integrations
3. **Structured Data**: JSON format matches our observation schema
4. **Low Maintenance**: API contract is more stable than HTML scraping
5. **Fast MVP**: Can build working collector immediately

### Negative

1. **Single Source Dependency**: If OpenRouter changes or fails, STCI is impacted
2. **Pricing Accuracy Trust**: We trust OpenRouter's claim of "no markup"
3. **Coverage Gaps**: Only models available through OpenRouter are indexed
4. **ToS Uncertainty**: Should verify redistribution rights before public launch

### Mitigations

| Risk | Mitigation |
|------|------------|
| OpenRouter unavailable | 7-day carry-forward policy; fallback to fixtures |
| Pricing accuracy | Cross-reference with Tier-2/3 sources; anomaly detection |
| ToS uncertainty | Formal legal review before public launch |
| Coverage gaps | Add direct provider sources as Tier-2 where legally viable |

---

## Implementation

### Source Tier Assignment

| Tier | Source | Purpose |
|------|--------|---------|
| T1 | OpenRouter API | Primary daily collection |
| T2 | Provider APIs (where legal) | Cross-validation |
| T3 | Community datasets | Historical backfill |
| T4 | Manual collection | Emergency validation |

### Collector Architecture

```python
# services/collector/sources/openrouter.py
class OpenRouterSource(BaseSource):
    API_URL = "https://openrouter.ai/api/v1/models"

    def fetch(self, target_date: date) -> List[dict]:
        response = requests.get(self.API_URL)
        # Transform to STCI observation format
        # Apply validation rules
        # Return normalized observations
```

### Validation Strategy

1. **Schema Validation**: All observations must pass `observation.schema.json`
2. **Rate Bounds**: Flag prices outside expected ranges ($0.01 - $500/1M tokens)
3. **Cross-Reference**: Compare T1 data against T2/T3 when available
4. **Anomaly Detection**: Alert on >20% price changes day-over-day

---

## Review Triggers

This decision should be revisited if:

1. OpenRouter changes ToS to prohibit data redistribution
2. OpenRouter API becomes unreliable (>3 outages per month)
3. OpenRouter pricing accuracy is found to be compromised
4. Direct provider APIs become legally accessible
5. A superior aggregator emerges with better coverage/accuracy

---

## References

- [OpenRouter API Documentation](https://openrouter.ai/docs/api-reference)
- [OpenRouter Models Endpoint](https://openrouter.ai/api/v1/models)
- [STCI Data Strategy Research](007-RL-RSRC-data-strategy-research.md)
- [Legal Source Risks](008-PM-RISK-legal-source-risks.md)
- [OpenAI Terms of Service](https://openai.com/policies/service-terms/)

---

## Decision Record

| Date | Author | Decision |
|------|--------|----------|
| 2026-01-01 | STCI Team | ACCEPTED - OpenRouter as T1 source |

---

*STCI — Standard Token Cost Index*
*Architecture Decision Record*
