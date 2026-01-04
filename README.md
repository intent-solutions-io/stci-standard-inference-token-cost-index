# STCI — Standard Token Cost Index

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index/releases)
[![Tests](https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index/actions/workflows/tests.yml/badge.svg)](https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A public, vendor-neutral price index for LLM tokens.**

STCI provides a transparent, reproducible reference rate for large language model token pricing, analogous to market indices like LIBOR or VIX. It aggregates published pricing from major model providers and aggregators, normalizes the data into a canonical schema, and computes daily reference rates with full provenance.

---

## The Problem

Token pricing in the LLM ecosystem is fragmented:

- **Dozens of providers**: OpenAI, Anthropic, Google, AWS Bedrock, Azure OpenAI, Cohere, Mistral, Fireworks, Together, Replicate, Groq, and growing
- **No standard format**: Pricing is published as $/1K tokens, $/1M tokens, per-minute, per-character, or blended rates
- **No historical record**: Prices change without notice; there's no "price tape" to track over time
- **No neutral benchmark**: Users can't easily answer "what's the market rate for frontier-class models today?"

Enterprises, researchers, and developers need a **trusted, auditable source of truth** for LLM token pricing—for cost estimation, budgeting, contract negotiation, and market analysis.

---

## What STCI Provides

### 1. Normalized Observations
Every pricing data point is captured as a **canonical observation** with:
- Provider and model identifiers
- Input token rate (USD per 1M tokens)
- Output token rate (USD per 1M tokens)
- Effective date and timestamp
- Source URL and provenance metadata
- Collection method and confidence level

### 2. Daily Reference Rates
STCI computes a **daily index value** (and sub-indices) using a transparent methodology:
- **STCI-ALL**: Weighted average across all tracked models
- **STCI-FRONTIER**: Frontier-class models only (GPT-4o, Claude 3.5, Gemini 1.5 Pro, etc.)
- **STCI-EFFICIENT**: High-efficiency models (GPT-4o-mini, Claude 3.5 Haiku, Gemini Flash, etc.)
- **STCI-OPEN**: Open-weight models (Llama, Mistral, Mixtral, etc.)

Each sub-index has:
- Defined basket composition
- Transparent weighting methodology
- Documented inclusion/exclusion criteria
- Rebalancing schedule

### 3. Deterministic Recomputation
Given a date and the observation set for that date, STCI produces **identical results every time**. This enables:
- Independent verification by third parties
- Backtesting and historical analysis
- Audit compliance for enterprise users

### 4. Read-Only API
A simple API exposes:
- Latest index values
- Historical time series
- Raw observations (with provenance)
- Methodology documentation

---

## Data Sourcing Tiers

STCI uses a tiered approach to data quality:

| Tier | Source Type | Confidence | Example |
|------|-------------|------------|---------|
| T1 | Official pricing pages (provider-published) | Highest | openai.com/pricing |
| T2 | Official APIs returning pricing | High | Bedrock pricing API |
| T3 | Aggregator pricing (verified) | Medium | OpenRouter, LLMAP.io |
| T4 | Community-reported (cross-validated) | Lower | User submissions |

MVP focuses on T1 and T2 sources only.

---

## Repository Structure

```
stci/
├── 000-docs/                 # All documentation (flat, 6767 naming)
│   ├── 001-PP-PROD-stci-prd.md            # Product Requirements
│   ├── 002-AT-ADEC-index-first-strategy.md # Architecture Decision
│   ├── 003-AT-SPEC-observation-schema.md   # Observation Schema Spec
│   ├── 004-AT-SPEC-stci-methodology.md     # Index Methodology Spec
│   ├── 005-OD-SOPS-recompute-runbook.md    # Deterministic Recompute
│   └── ...                                 # Additional docs
├── schemas/                  # Canonical JSON schemas
│   ├── observation.schema.json
│   └── stci_daily.schema.json
├── data/                     # Sample data and fixtures
│   └── fixtures/
│       ├── observations.sample.json
│       └── methodology.sample.yaml
├── services/                 # Application services
│   ├── collector/            # Price data collection
│   ├── indexer/              # Index computation
│   └── api/                  # Read-only API
├── scripts/                  # Utilities and verification
│   └── verify_repo.sh
├── skills/                   # Claude Code skills
│   └── stci-dataops/
│       └── SKILL.md
├── infra/                    # Infrastructure placeholders
├── .beads/                   # Beads issue tracking
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## Core Concepts

### Observation
A single pricing data point for a specific model at a specific time:

```json
{
  "observation_id": "obs-2026-01-01-openai-gpt4o",
  "provider": "openai",
  "model_id": "gpt-4o",
  "model_display_name": "GPT-4o",
  "input_rate_usd_per_1m": 2.50,
  "output_rate_usd_per_1m": 10.00,
  "effective_date": "2026-01-01",
  "collected_at": "2026-01-01T12:00:00Z",
  "source_url": "https://openai.com/pricing",
  "source_tier": "T1",
  "currency": "USD",
  "schema_version": "1.0.0"
}
```

### Daily Index Output
Aggregated reference rate for a given date:

```json
{
  "date": "2026-01-01",
  "indices": {
    "STCI-ALL": {
      "input_rate": 3.42,
      "output_rate": 12.87,
      "blended_rate": 6.27,
      "model_count": 24,
      "dispersion": 0.42
    },
    "STCI-FRONTIER": {
      "input_rate": 4.85,
      "output_rate": 15.20,
      "blended_rate": 8.22,
      "model_count": 8
    }
  },
  "methodology_version": "1.0.0",
  "computed_at": "2026-01-01T23:59:00Z"
}
```

---

## Methodology Overview

### Basket Definition
Each sub-index has a defined basket of models based on:
- **Capability tier**: Frontier, efficient, open-weight
- **Market presence**: Minimum usage threshold
- **Data availability**: Must have T1/T2 pricing

### Weighting
Default weighting for MVP:
- **Equal weight** within capability tiers
- Future: Usage-weighted based on market share data

### Aggregation
- **Input rate**: Weighted average of USD/1M input tokens
- **Output rate**: Weighted average of USD/1M output tokens
- **Blended rate**: Assumes 3:1 output-to-input ratio (configurable)
- **Dispersion**: Standard deviation to indicate price spread

### Edge Cases
- **Missing data**: Carry forward previous day's rate (max 7 days)
- **Price changes**: Use end-of-day price
- **Model additions**: Next rebalancing window
- **Model removals**: Same business day

---

## Quickstart

```bash
# Clone the repository
git clone https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index.git
cd stci-standard-llm-token-cost-index

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run verification
./scripts/verify_repo.sh

# Run tests
pytest

# Run collection pipeline (from fixtures)
python -m services.collector.pipeline --fixtures

# Run indexing pipeline
python -m services.indexer.pipeline --date 2026-01-02

# Start API (development)
python -m services.api.main
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/index/latest` | GET | Latest STCI values |
| `/v1/index/{date}` | GET | Index for specific date |
| `/v1/indices` | GET | List all available dates |
| `/v1/observations/{date}` | GET | Raw observations for date |
| `/v1/methodology` | GET | Current methodology config |

---

## Trust Model

STCI is designed as a **reference rate product**. Trust is the moat:

1. **Transparency**: All methodology is documented and public
2. **Reproducibility**: Anyone can verify index values
3. **Provenance**: Every observation has source metadata
4. **Auditability**: Full history of changes and computations
5. **Neutrality**: No financial stake in any provider

---

## Roadmap

### v0.1.0 (Current)
- [x] Schema definitions (observation, daily index)
- [x] OpenRouter collector pipeline
- [x] Indexer with STCI-ALL, STCI-FRONTIER, STCI-EFFICIENT, STCI-OPEN
- [x] Read-only API server
- [x] Firebase Hosting + Functions deployment
- [x] GitHub Actions CI/CD
- [x] Comprehensive test suite

### v0.2.0
- [ ] Additional T1/T2 collectors (direct provider APIs)
- [ ] Historical backfill tooling
- [ ] Rate change alerts

### v0.3.0
- [ ] Dashboard UI
- [ ] Public API with authentication
- [ ] Webhook notifications

### Future
- [ ] Usage-weighted indices
- [ ] Enterprise data feeds
- [ ] Multi-currency support

---

## Contributing

See documentation in `000-docs/` for:
- Contribution guidelines
- Source acceptance criteria
- Data quality requirements

---

## License

MIT License. See [LICENSE](./LICENSE).

---

## Contact

- Repository: [github.com/intent-solutions-io/stci-standard-llm-token-cost-index](https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index)
- Issues: Use GitHub Issues or Beads (`bd create`)

---

*STCI — Making LLM pricing transparent, reproducible, and trustworthy.*
