# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STCI (Standard Token Cost Index) is a vendor-neutral price index for LLM tokens. It collects pricing data from model providers, normalizes it to a canonical schema, and computes daily reference rates with full provenance.

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest                           # All tests
pytest tests/test_collector.py   # Single module
pytest -k "test_fetch"           # By pattern

# Verify repository structure
./scripts/verify_repo.sh

# Collection pipeline (fetch pricing data)
python -m services.collector.pipeline                    # Live from OpenRouter
python -m services.collector.pipeline --fixtures         # Use fixture data
python -m services.collector.pipeline --date 2026-01-01  # Specific date
python -m services.collector.pipeline --dry-run          # No file writes

# Indexing pipeline (compute indices)
python -m services.indexer.pipeline                      # Today's index
python -m services.indexer.pipeline --date 2026-01-01    # Specific date

# API server
python -m services.api.main                              # Default port 8000
python -m services.api.main --port 9000

# Docker
docker compose up api           # Run API server
docker compose run pipeline     # Run collector + indexer
```

## Architecture

```
stci/
├── services/
│   ├── collector/          # Data collection from sources
│   │   ├── sources.py      # BaseSource, OpenRouterSource, FixtureSource
│   │   ├── collector.py    # Collector class with waterfall fallback
│   │   └── pipeline.py     # Full collection workflow: fetch → store → validate
│   ├── indexer/            # Index computation
│   │   ├── indexer.py      # Indexer class, compute_index()
│   │   └── pipeline.py     # Full indexing workflow: load → compute → store
│   ├── api/                # Read-only HTTP API (stdlib, no framework)
│   │   └── main.py         # STCIHandler, endpoints: /health, /v1/index/*
│   └── storage/            # Storage backends (GCS, local)
├── schemas/                # JSON Schema definitions
│   ├── observation.schema.json   # Pricing observation format
│   └── stci_daily.schema.json    # Daily index output format
├── data/
│   ├── fixtures/           # Test data and methodology config
│   │   ├── observations.sample.json
│   │   └── methodology.yaml
│   ├── raw/                # Immutable raw API responses
│   ├── observations/       # Normalized observations (JSONL by date)
│   └── indices/            # Computed indices (JSON by date)
└── 000-docs/               # Documentation (6767 naming convention)
```

## Data Flow

```
OpenRouter API → raw/{date}.json → observations/{date}.jsonl → indices/{date}.json → API
     ↓                                      ↓
 sources.py                           indexer.py
```

1. **Collector** fetches from sources (OpenRouter is primary, fixtures are fallback)
2. **Raw storage** preserves original API responses for audit
3. **Observations** are normalized to canonical schema (JSONL format)
4. **Indexer** computes weighted averages per methodology
5. **API** serves computed indices read-only

## Key Concepts

**Observation**: Single pricing data point with provenance
- `input_rate_usd_per_1m`, `output_rate_usd_per_1m`: Normalized rates
- `source_tier`: T1 (official) through T4 (community)
- `observation_id` format: `obs-{date}-{provider}-{model}`

**Index**: Aggregated reference rate (STCI-ALL, STCI-FRONTIER, STCI-EFFICIENT, STCI-OPEN)
- `blended_rate`: Assumes 3:1 output:input ratio (configurable in methodology.yaml)
- `verification_hash`: SHA256 for deterministic verification

**Methodology** (`data/fixtures/methodology.yaml`):
- Defines index baskets, weighting, and thresholds
- Equal weighting for MVP, usage-weighted planned

## Testing

Tests use `pytest` with fixtures in `tests/conftest.py`. Key fixtures:
- `sample_observations`: Pre-built observation list
- `sample_openrouter_response`: Mock API response
- `temp_data_dir`: Temporary data directory with sample files
- `target_date`: Standard test date (2026-01-01)

Uses `responses` library to mock HTTP requests to OpenRouter API.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check with data availability |
| `GET /v1/index/latest` | Most recent index |
| `GET /v1/index/{date}` | Index for specific date |
| `GET /v1/indices` | List all available dates |
| `GET /v1/observations/{date}` | Raw observations |
| `GET /v1/methodology` | Current methodology config |

## Documentation Convention

Documents in `000-docs/` follow 6767 naming: `NNN-CC-ABCD-description.md`
- NNN: Sequence number
- CC: Category (PP=Product, AT=Architecture, DR=Design, etc.)
- ABCD: Type code (PROD, ADEC, STND, SOPS, etc.)
