---
name: stci-dataops
description: Research and onboard new data sources for STCI, producing source profiles, collector stubs, and validation rules
---

# STCI Data Operations Skill

## Purpose

This skill assists with researching, evaluating, and onboarding new data sources for the STCI (Standard Token Cost Index). Given a provider or aggregator, it produces structured outputs ready for implementation.

## Capabilities

1. **Source Research**: Analyze a pricing source (provider page, aggregator API) and extract key characteristics
2. **Legal Assessment**: Review ToS, robots.txt, and rate limits for compliance
3. **Source Profile**: Generate a complete source profile following the template
4. **Collector Stub**: Produce a Python collector module for the source
5. **Validation Rules**: Define source-specific validation and anomaly detection

## Invocation

Use this skill when you need to:
- Add a new LLM provider to STCI
- Evaluate an aggregator API for data sourcing
- Create a source profile for a pricing endpoint
- Generate collector code for a new source

## Workflow

### Step 1: Source Identification

Given a source URL or name, gather:
- Source type (provider, aggregator, community)
- API endpoint (if available)
- Pricing page URL
- Data format (JSON, HTML, etc.)

### Step 2: Legal Review

Check and document:
- [ ] robots.txt allows access to target endpoints
- [ ] ToS permits automated data access
- [ ] ToS permits data redistribution
- [ ] Rate limits and API quotas
- [ ] Authentication requirements

**Decision Matrix:**

| Condition | Action |
|-----------|--------|
| API explicitly public + no ToS restrictions | Proceed to T1/T2 source |
| API available but ToS unclear | Request legal review before production |
| Scraping required + ToS prohibits | Do NOT proceed - use alternative |
| Manual collection only viable | Proceed as T4 source with caveats |

### Step 3: Data Structure Analysis

For API sources:
```bash
# Fetch sample data
curl -s [API_URL] | head -100

# Analyze structure
# - Identify model ID field
# - Identify pricing fields (input, output, per-request)
# - Identify metadata fields (context window, etc.)
# - Note rate units (per-token, per-1K, per-1M)
```

For HTML sources:
```bash
# Check page structure
# - Identify pricing table elements
# - Note update indicators (timestamps, version)
# - Assess scraping complexity
```

### Step 4: Generate Source Profile

Output a completed source profile using template:
`000-docs/009-DR-TMPL-source-profile.md`

Required sections:
1. Source Identification
2. Legal & Compliance
3. Data Availability
4. Pricing Data Structure
5. Collection Strategy
6. Normalization Mapping
7. Validation Rules
8. Monitoring & Alerting
9. Source Acceptance Checklist

### Step 5: Generate Collector Stub

Produce a Python module following this pattern:

```python
# services/collector/sources/{source_id}.py

from .base import BaseSource

class {SourceName}Source(BaseSource):
    """
    {Source description}
    See: {Source URL}
    """

    API_URL = "{api_url}"

    @property
    def source_id(self) -> str:
        return "{source_id}"

    @property
    def source_tier(self) -> str:
        return "{tier}"  # T1, T2, T3, or T4

    def fetch(self, target_date: date) -> List[dict]:
        # Implementation
        pass
```

### Step 6: Define Validation Rules

Specify source-specific rules:

```yaml
validation:
  required_fields:
    - model_id
    - input_rate
    - output_rate

  rate_bounds:
    input_max: 100.0  # USD per 1M
    output_max: 500.0

  model_id_pattern: "^[a-z0-9-]+/[a-z0-9.-]+$"

  cross_reference:
    enabled: true
    tolerance: 0.10  # 10% tolerance
    reference_source: "openrouter"
```

### Step 7: Generate Test Fixtures

Create test data for the source:

```json
// data/fixtures/{source_id}_sample.json
[
  {
    "observation_id": "obs-2026-01-01-{source_id}-{model}",
    "provider": "{provider}",
    ...
  }
]
```

## Output Checklist

After running this skill, you should have:

- [ ] Source profile document (`000-docs/0XX-DR-REFF-{source_id}-profile.md`)
- [ ] Collector module (`services/collector/sources/{source_id}.py`)
- [ ] Test fixtures (`data/fixtures/{source_id}_sample.json`)
- [ ] Validation config update (`data/fixtures/methodology.yaml`)
- [ ] Beads task for implementation tracking

## Example: Onboarding OpenRouter

### Input
```
Source: OpenRouter
URL: https://openrouter.ai
API: https://openrouter.ai/api/v1/models
```

### Research Output

**Legal Assessment:**
- robots.txt: Allows /api/
- ToS: Public API, no explicit redistribution restriction found
- Rate limits: Standard API limits apply
- Auth: None required for models endpoint
- Risk: LOW

**Data Structure:**
```json
{
  "data": [
    {
      "id": "openai/gpt-4o",
      "name": "GPT-4o",
      "pricing": {
        "prompt": "0.0000025",
        "completion": "0.00001"
      }
    }
  ]
}
```

**Normalization:**
- `id` → `model_id`
- `pricing.prompt` × 1M → `input_rate_usd_per_1m`
- `pricing.completion` × 1M → `output_rate_usd_per_1m`

**Source Tier:** T1 (public API, high confidence)

## Related Documents

- 007-RL-RSRC-data-strategy-research.md
- 008-PM-RISK-legal-source-risks.md
- 009-DR-TMPL-source-profile.md
- 010-DR-SOPS-data-ops-practices.md

---

*STCI Data Operations Skill*
*Version: 1.0.0*
