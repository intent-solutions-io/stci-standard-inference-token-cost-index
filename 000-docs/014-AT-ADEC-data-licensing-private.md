# ADR: Data Licensing - Private by Default

**Document ID:** 014
**Category:** AT (Architecture & Technical)
**Type:** ADEC (Architecture Decision)
**Status:** ACCEPTED
**Owner:** STCI Project Team
**Created:** 2026-01-02
**Phase:** 0 (Foundation)

---

## Context

STCI collects pricing data from external APIs (primarily OpenRouter) and computes index values. We must decide what data is publicly accessible vs. private.

### Legal Constraints

1. **OpenRouter ToS**: Not formally reviewed for redistribution rights
2. **Provider Data**: Pricing derived from OpenAI, Anthropic, etc. - original sources prohibit scraping
3. **Transformative Use**: Computed indices may qualify as transformative, reducing legal risk

### Trust vs. Legal Risk

| Approach | Trust Level | Legal Risk |
|----------|-------------|------------|
| Fully open data | High | High |
| Indices only | Medium | Low |
| Private data | Lower | Minimal |

---

## Decision

**Keep all collected data private. Only publish computed indices via API.**

```
PUBLIC (in git repo):
├── Code (MIT License)
├── Schemas
├── Methodology documentation
├── Fixtures (synthetic test data)
└── Index values (via API only, not raw files)

PRIVATE (excluded from git):
├── data/raw/          # Raw API responses
├── data/observations/ # Normalized observations
└── data/indices/      # Computed indices (served via API)
```

---

## Rationale

1. **Legal Safety**: Until OpenRouter ToS formally reviewed, don't redistribute their data
2. **Reversible**: Easy to open-source later; hard to un-publish
3. **API Control**: Can implement rate limits, authentication, usage tracking
4. **Index Still Useful**: Users get STCI values without raw observation data
5. **Methodology Transparent**: How we compute is open; raw inputs are not

---

## What IS Public

| Asset | License | Location |
|-------|---------|----------|
| Source code | MIT | GitHub repo |
| JSON schemas | MIT | `schemas/` |
| Methodology docs | CC-BY-4.0 | `000-docs/` |
| Fixture/test data | MIT | `data/fixtures/` |
| Index values | TBD | API responses |

## What is NOT Public

| Asset | Reason | Access |
|-------|--------|--------|
| Raw API responses | ToS uncertainty | Internal only |
| Observations | Derived from raw | Internal only |
| Index files | Operational data | Via API only |

---

## API Access Model

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Public    │     │  Rate-Ltd   │     │   Private   │
│             │     │             │     │             │
│ /health     │     │ /v1/index/* │     │ Raw data    │
│ /methodology│     │             │     │ Observations│
└─────────────┘     └─────────────┘     └─────────────┘
```

**Public endpoints** (no auth):
- `GET /health`
- `GET /v1/methodology`

**Rate-limited endpoints** (no auth, but throttled):
- `GET /v1/index/latest`
- `GET /v1/index/{date}`

**Future consideration**:
- API keys for heavy users
- Paid tier for observation-level data (if legally cleared)

---

## Implementation

### .gitignore Updates

```gitignore
# Private data (not open-sourced)
data/raw/
data/observations/
data/indices/

# Keep fixtures (test data)
!data/fixtures/
```

### Data Storage

Private data stored:
- **Local development**: `data/` directory (gitignored)
- **Production**: Cloud storage (GCS bucket, private)
- **Backups**: Encrypted, private

---

## Future: Path to Open Data

If legal review clears redistribution:

1. **Phase 1**: Publish historical indices (30+ days old)
2. **Phase 2**: Publish historical observations (90+ days old)
3. **Phase 3**: Real-time observation access (API key required)

**Trigger for review**:
- Formal legal opinion on OpenRouter ToS
- OpenRouter provides explicit permission
- Alternative data sources with clear redistribution rights

---

## Consequences

### Positive

1. **Zero legal risk** from data redistribution
2. **Flexibility** to monetize data access later
3. **Control** over how data is consumed
4. **Reversible** - can always open up later

### Negative

1. **Less transparent** - users can't verify raw inputs
2. **Trust requirement** - users must trust our computation
3. **Harder to replicate** - others can't rebuild index independently

### Mitigations

| Concern | Mitigation |
|---------|------------|
| Verification | Publish verification hashes; deterministic methodology |
| Trust | Open methodology; third-party audits possible |
| Replication | Document methodology thoroughly; provide test fixtures |

---

## Review Triggers

Revisit this decision when:

1. Legal review of OpenRouter ToS completed
2. Alternative open-licensed data sources available
3. Community requests for open data reach critical mass
4. Business model requires data monetization

---

*STCI — Standard Token Cost Index*
*Architecture Decision Record*
