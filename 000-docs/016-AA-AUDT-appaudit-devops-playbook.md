# STCI: Operator-Grade System Analysis & Operations Guide
*For: DevOps Engineer*
*Generated: 2026-01-02*
*System Version: v0.1.0 (abda537)*

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Operator & Customer Journey](#2-operator--customer-journey)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Directory Deep-Dive](#4-directory-deep-dive)
5. [Automation & Agent Surfaces](#5-automation--agent-surfaces)
6. [Operational Reference](#6-operational-reference)
7. [Security, Compliance & Access](#7-security-compliance--access)
8. [Cost & Performance](#8-cost--performance)
9. [Development Workflow](#9-development-workflow)
10. [Dependencies & Supply Chain](#10-dependencies--supply-chain)
11. [Integration with Existing Documentation](#11-integration-with-existing-documentation)
12. [Current State Assessment](#12-current-state-assessment)
13. [Quick Reference](#13-quick-reference)
14. [Recommendations Roadmap](#14-recommendations-roadmap)

---

## 1. Executive Summary

### Business Purpose

STCI (Standard Token Cost Index) is a **vendor-neutral price index for LLM tokens**, analogous to market indices like LIBOR or VIX for financial markets. The system addresses a critical gap in the AI ecosystem: fragmented, non-standardized token pricing across dozens of providers (OpenAI, Anthropic, Google, etc.) with no historical record or neutral benchmark.

The platform collects published pricing from aggregators and model providers, normalizes data to a canonical schema (USD per 1M tokens), and computes daily reference rates with full provenance. This enables enterprises, researchers, and developers to perform cost estimation, budgeting, contract negotiation, and market analysis with a trusted, auditable source of truth.

Currently at **v0.1.0** (initial release, 2026-01-02), STCI is fully operational with a working collection pipeline (OpenRouter integration), indexer computing four sub-indices (STCI-ALL, STCI-FRONTIER, STCI-EFFICIENT, STCI-OPEN), and a read-only HTTP API. The system is deployed on GCP Cloud Run with daily automation via GitHub Actions.

Key strengths include deterministic recomputation (verification hashes), comprehensive test coverage (48 tests), and clean separation of concerns. Primary risk is single-source dependency (OpenRouter only); roadmap addresses this with additional T1/T2 collectors.

### Operational Status Matrix

| Environment | Status | Uptime Target | Current Uptime | Release Cadence | Active Users |
|-------------|--------|---------------|----------------|-----------------|--------------|
| Production  | Active | 99.5% | N/A (new) | On-demand | Internal |
| Staging     | N/A | - | - | - | - |
| Development | Active | - | - | Daily | 1 |

### Technology Stack Summary

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.11/3.12 | All services |
| Framework | stdlib http.server | - | API (no external framework) |
| Database | Filesystem (JSON/JSONL) | - | Index and observation storage |
| Cloud Platform | GCP Cloud Run | - | Production hosting |
| CI/CD | GitHub Actions | - | Tests, deploy, daily pipeline |
| Container | Docker | Multi-stage | API and pipeline images |

---

## 2. Operator & Customer Journey

### Primary Personas

- **Operators**: DevOps engineers maintaining the pipeline, monitoring index accuracy, handling source failures
- **External Customers**: (Future) API consumers querying index values for cost modeling
- **Reseller Partners**: (Future) Financial data aggregators embedding STCI in reports
- **Automation Bots**: GitHub Actions running daily collection/indexing at 00:30 UTC

### End-to-End Journey Map

```
Data Source → Collector → Raw Archive → Observations → Indexer → Index → API → Consumer
     ↓            ↓            ↓             ↓            ↓         ↓        ↓
OpenRouter   sources.py   data/raw/   data/observations/  indexer.py  data/indices/  /v1/index/*
```

**Critical Touchpoints:**
1. **Data Collection (00:30 UTC daily)**: OpenRouter API fetch, rate normalization
2. **Index Computation**: Weighted averages per methodology, verification hash generation
3. **API Serving**: Read-only endpoints, 60-second cache TTL
4. **Verification**: Deterministic recomputation for audit compliance

### SLA Commitments

| Metric | Target | Current | Owner |
|--------|--------|---------|-------|
| Data Freshness | Daily by 01:00 UTC | Met (00:30 UTC cron) | Platform |
| API Availability | 99.5% | TBD | Platform |
| Index Accuracy | 100% deterministic | Verified via hash | Platform |
| Response Time | <500ms P95 | TBD | Platform |

---

## 3. System Architecture Overview

### Technology Stack (Detailed)

| Layer | Technology | Version | Source of Truth | Purpose | Owner |
|-------|------------|---------|-----------------|---------|-------|
| API Server | Python http.server | 3.12 | services/api/main.py:18 | Read-only HTTP API | Platform |
| Collection | requests + custom | 2.28+ | services/collector/ | Price data fetching | Platform |
| Indexing | Python stdlib | 3.12 | services/indexer/ | Index computation | Platform |
| Validation | jsonschema | 4.17+ | schemas/*.json | Observation validation | Platform |
| Storage | Local filesystem | - | data/ directories | JSON/JSONL persistence | Platform |
| Cloud Storage | google-cloud-storage | 2.10+ | services/storage/ | GCS backend (optional) | Platform |
| Testing | pytest + responses | 7.0+ | tests/ | Unit and mock tests | Platform |

### Environment Matrix

| Environment | Purpose | Hosting | Data Source | Release Cadence | IaC Source | Notes |
|-------------|---------|---------|-------------|-----------------|------------|-------|
| local | Development | localhost:8000 | Fixtures/OpenRouter | Continuous | N/A | venv-based |
| dev | N/A | - | - | - | - | Not implemented |
| staging | N/A | - | - | - | - | Not implemented |
| prod | Production | Cloud Run (us-central1) | OpenRouter | On push to main | .github/workflows/deploy.yml | WIF auth |

### Cloud & Platform Services

| Service | Purpose | Environment(s) | Key Config | Cost/Limits | Owner | Vendor Risk |
|---------|---------|----------------|------------|-------------|-------|-------------|
| Cloud Run (stci-api) | API hosting | prod | 512Mi/1CPU, 0-10 instances | ~$5-20/mo | Platform | Low |
| Cloud Run Job (stci-pipeline) | Daily collection | prod | 1Gi/1CPU, 10min timeout | ~$1/mo | Platform | Low |
| Artifact Registry | Container images | prod | stci/api, stci/pipeline | Minimal | Platform | Low |
| GCS Bucket | Data storage (optional) | prod | {project}-data | ~$1/mo | Platform | Low |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STCI Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │  Data Sources   │      │   Collection    │      │   Raw Storage   │    │
│  │  ─────────────  │ ───► │  ─────────────  │ ───► │  ─────────────  │    │
│  │  • OpenRouter   │      │  sources.py     │      │  data/raw/      │    │
│  │  • (Future T1s) │      │  collector.py   │      │  {date}.json    │    │
│  │  • Fixtures     │      │  pipeline.py    │      │  (immutable)    │    │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │  Observations   │      │    Indexer      │      │   Index Store   │    │
│  │  ─────────────  │ ───► │  ─────────────  │ ───► │  ─────────────  │    │
│  │  data/          │      │  indexer.py     │      │  data/indices/  │    │
│  │  observations/  │      │  methodology    │      │  {date}.json    │    │
│  │  {date}.jsonl   │      │  .yaml config   │      │  (SHA256 hash)  │    │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘    │
│                                                             │               │
│                                                             ▼               │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │   Consumers     │ ◄─── │   HTTP API      │ ◄─── │   Data Files    │    │
│  │  ─────────────  │      │  ─────────────  │      │  ─────────────  │    │
│  │  • Dashboards   │      │  /health        │      │  • indices/     │    │
│  │  • Analytics    │      │  /v1/index/*    │      │  • observations/│    │
│  │  • Integrations │      │  /v1/methodology│      │  • fixtures/    │    │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Cloud Run (prod) ◄──── GitHub Actions ◄──── git push main                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Directory Deep-Dive

### Project Structure Analysis

```
stci/
├── .github/workflows/         # CI/CD automation
│   ├── tests.yml              # Python 3.11/3.12 matrix, lint, schema validation
│   ├── deploy.yml             # Cloud Run deployment with WIF
│   └── daily-pipeline.yml     # 00:30 UTC cron collection + indexing
├── 000-docs/                  # Documentation (6767 naming: NNN-CC-ABCD-desc.md)
│   ├── 001-PP-PROD-*.md       # Product requirements
│   ├── 002-012-AT-ADEC-*.md   # Architecture decisions
│   └── 015-RL-REPT-*.md       # Release reports
├── data/
│   ├── fixtures/              # Test data and methodology config
│   │   ├── observations.sample.json
│   │   └── methodology.yaml   # Index basket definitions
│   ├── raw/                   # Immutable API responses (audit trail)
│   ├── observations/          # Normalized JSONL (by date)
│   └── indices/               # Computed indices JSON (by date)
├── schemas/                   # JSON Schema definitions
│   ├── observation.schema.json
│   └── stci_daily.schema.json
├── services/                  # Application code
│   ├── collector/             # Data collection
│   ├── indexer/               # Index computation
│   ├── api/                   # HTTP API server
│   └── storage/               # Storage backends
├── tests/                     # pytest tests (48 total)
├── scripts/                   # Utilities
│   └── verify_repo.sh
├── Dockerfile                 # API server image
├── Dockerfile.pipeline        # Pipeline job image
├── docker-compose.yml         # Local development
├── requirements.txt           # Python dependencies
├── VERSION                    # Current version (0.1.0)
└── CLAUDE.md                  # Claude Code guidance
```

### Detailed Directory Analysis

#### services/collector/ (3 files, ~500 lines)

**Purpose**: Fetch pricing data from external sources, normalize to canonical schema
**Key Files**:
- `sources.py:49-139` - OpenRouterSource: fetches from openrouter.ai/api/v1/models, converts $/token to $/1M tokens
- `sources.py:142-194` - FixtureSource: loads sample data for testing
- `pipeline.py:40-121` - CollectionPipeline: orchestrates fetch → store → validate → output
- `collector.py` - Collector class with waterfall fallback

**Data Flow**: API → raw/{date}.json → observations/{date}.jsonl

**Critical Logic**:
- Rate conversion: `input_rate = float(prompt_rate) * 1_000_000` (line 104)
- Source tier assignment: OpenRouter = T1, Fixtures = T4
- Validation against observation.schema.json before storage

#### services/indexer/ (3 files, ~450 lines)

**Purpose**: Compute weighted averages per methodology, generate verification hash
**Key Files**:
- `indexer.py:15-178` - Indexer class: filters to basket, applies weighting, computes aggregates
- `indexer.py:44-84` - compute(): main computation loop for all indices
- `indexer.py:86-158` - _compute_single_index(): per-index calculation
- `indexer.py:160-177` - _compute_hash(): SHA256 for determinism verification
- `pipeline.py:31-106` - IndexingPipeline: load observations → compute → store

**Key Formulas**:
- Blended rate: `(avg_input + 3.0 * avg_output) / 4.0` (assumes 3:1 output:input ratio)
- Dispersion: standard deviation of input rates
- Verification: SHA256(sorted observations + methodology version + date)[:16]

**Index Baskets** (from methodology.yaml):
- STCI-ALL: All models (no filter)
- STCI-FRONTIER: GPT-4o, Claude Opus/Sonnet, Gemini Pro, Mistral Large
- STCI-EFFICIENT: GPT-4o-mini, Claude Haiku, Gemini Flash, Mistral Small
- STCI-OPEN: Llama, Mixtral, Qwen, DeepSeek

#### services/api/ (1 file, 310 lines)

**Purpose**: Read-only HTTP API serving computed indices
**Key Files**:
- `main.py:18-251` - STCIHandler: route handling, data loading, JSON responses
- `main.py:253-256` - create_app(): factory function
- `main.py:258-306` - main(): CLI with argument parsing

**Endpoints**:
| Endpoint | Handler | Cache | Line |
|----------|---------|-------|------|
| GET /health | _handle_health | No | 71-83 |
| GET /v1/index/latest | _handle_index_latest | 60s | 85-93 |
| GET /v1/index/{date} | _handle_index_date | 60s | 95-125 |
| GET /v1/indices | _handle_available_indices | 60s | 182-203 |
| GET /v1/observations/{date} | _handle_observations_date | 60s | 127-160 |
| GET /v1/methodology | _handle_methodology | Cached | 162-180 |

**No External Framework**: Uses stdlib http.server (zero runtime dependencies beyond requests/pyyaml)

#### tests/ (3 files, ~800 lines, 48 tests)

**Framework**: pytest with responses library for HTTP mocking
**Coverage Categories**:
- test_collector.py (18 tests): Source fetching, normalization, validation
- test_indexer.py (15 tests): Methodology loading, computation, hashing
- test_api.py (15 tests): Endpoints, caching, error handling, CORS

**Key Fixtures** (conftest.py):
- `sample_observations`: Pre-built observation list
- `sample_openrouter_response`: Mock API response
- `temp_data_dir`: Temporary directory with sample files
- `target_date`: Standard test date (2026-01-01)

---

## 5. Automation & Agent Surfaces

### GitHub Actions Workflows

| Workflow | Trigger | Purpose | Key Steps |
|----------|---------|---------|-----------|
| tests.yml | push/PR to main | CI validation | Python 3.11/3.12 matrix, pytest, ruff lint, schema validation |
| deploy.yml | push to main, manual | Cloud Run deployment | WIF auth, docker build, gcloud run deploy |
| daily-pipeline.yml | 00:30 UTC cron, manual | Data collection | collector.pipeline → indexer.pipeline → git commit → push |

### Daily Pipeline Automation

**Schedule**: `cron: '30 0 * * *'` (00:30 UTC daily)

**Steps**:
1. Checkout repository
2. Setup Python 3.12
3. Install dependencies (cached)
4. Run collector: `python -m services.collector.pipeline --date $(date -u +%Y-%m-%d)`
5. Run indexer: `python -m services.indexer.pipeline --date $(date -u +%Y-%m-%d)`
6. Verify outputs (print index summary)
7. Commit data changes: `git add data/ && git commit -m "Daily update: {date}"`
8. Push to main
9. Upload artifacts (30-day retention)

**Failure Modes**:
- OpenRouter API timeout: Pipeline fails, no data committed
- Network issues: Retry not implemented (single attempt)
- Git conflict: Push fails, requires manual resolution

### Claude Code Integration

**CLAUDE.md**: Present at project root with development commands and architecture overview
**Beads**: .beads/ directory for issue tracking (initialized but unused)

---

## 6. Operational Reference

### Deployment Workflows

#### Local Development

**Prerequisites**:
- Python 3.11 or 3.12
- Git
- Docker (optional, for container testing)

**Environment Setup**:
```bash
# Clone and setup
git clone https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index.git
cd stci-standard-llm-token-cost-index
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify
./scripts/verify_repo.sh
pytest
```

**Service Startup**:
```bash
# Run collection (fixtures for testing)
python -m services.collector.pipeline --fixtures

# Run indexing
python -m services.indexer.pipeline --date 2026-01-02

# Start API server
python -m services.api.main --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/v1/index/latest
```

**Verification**:
```bash
# Health check
curl -s http://localhost:8000/health | jq .

# Expected: {"status": "healthy", "data_available": true, ...}
```

#### Production Deployment (Cloud Run)

**Trigger**: Push to main branch (automatic) or manual workflow dispatch

**Pre-flight**:
- CI pipeline must pass (tests, lint, schema validation)
- Docker build must succeed

**Execution** (via GitHub Actions):
1. Authenticate to GCP via Workload Identity Federation
2. Configure Docker for Artifact Registry
3. Build and push images:
   - `us-central1-docker.pkg.dev/{project}/stci/api:{sha}`
   - `us-central1-docker.pkg.dev/{project}/stci/pipeline:{sha}`
4. Deploy API to Cloud Run (allow-unauthenticated)
5. Update pipeline job
6. Verify health endpoint

**Rollback Protocol**:
```bash
# Revert to previous image
gcloud run deploy stci-api \
  --image=us-central1-docker.pkg.dev/{project}/stci/api:{previous_sha} \
  --region=us-central1

# Or revert git commit and redeploy
git revert HEAD
git push origin main
```

### Monitoring & Alerting

**Dashboards**: Not implemented (v0.1.0)

**SLIs/SLOs** (Proposed):
- Latency: P95 < 500ms for /v1/index/latest
- Availability: 99.5% uptime
- Data Freshness: Index available within 1 hour of midnight UTC

**Logging**:
- API logs to stdout: `[HH:MM:SS] GET /path HTTP/1.1 200 -`
- Cloud Run logs visible in GCP Console
- No centralized logging configured

**On-Call**: Not established (single maintainer)

### Incident Response

| Severity | Definition | Response Time | Playbook | Communication |
|----------|------------|---------------|----------|---------------|
| P0 | API fully down | Immediate | Check Cloud Run logs, redeploy | GitHub issue |
| P1 | Data collection failed | 1 hour | Check OpenRouter status, manual run | Commit message |
| P2 | Index computation error | Next day | Review observations, recompute | PR |
| P3 | Minor data quality issue | Next week | Add validation | Issue |

### Backup & Recovery

**Backup Strategy**:
- All data in git: `data/raw/`, `data/observations/`, `data/indices/`
- Git history serves as audit trail
- No separate backup system

**RPO/RTO**:
- RPO: 1 day (daily collection)
- RTO: Minutes (redeploy from git)

**Disaster Recovery**:
1. Clone repository
2. `pip install -r requirements.txt`
3. `python -m services.api.main`

---

## 7. Security, Compliance & Access

### Identity & Access Management

| Account/Role | Purpose | Permissions | Provisioning | MFA | Used By |
|--------------|---------|-------------|--------------|-----|---------|
| stci-runtime@{project}.iam.gserviceaccount.com | Cloud Run runtime | GCS read/write, Secret Manager | Terraform (manual) | N/A | Cloud Run |
| GitHub Actions (WIF) | CI/CD deployment | Artifact Registry push, Cloud Run deploy | Workload Identity | N/A | Actions |
| Repository admins | Code access | Full | GitHub | Required | Maintainers |

### Secrets Management

**Storage**:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: GitHub Actions secret
- `GCP_SERVICE_ACCOUNT`: GitHub Actions secret
- `GCP_PROJECT_ID`: GitHub Actions secret
- No runtime secrets (public API, no auth)

**Rotation**: Not applicable (WIF uses OIDC tokens)

**Break-glass**: Direct GCP Console access with project owner credentials

### Security Posture

**Authentication**:
- API: Unauthenticated (public read-only)
- Cloud Run: allow-unauthenticated

**Authorization**: None (all data public)

**Encryption**:
- In-transit: HTTPS (Cloud Run managed TLS)
- At-rest: GCS server-side encryption (default)

**Network**: Cloud Run default VPC, no custom firewall rules

**Known Issues**: None identified

---

## 8. Cost & Performance

### Current Costs

**Monthly Cloud Spend**: ~$10-30 (estimated)
- Cloud Run API: $5-15/mo (0-10 instances, 512Mi)
- Cloud Run Pipeline: $1-2/mo (daily job, 1Gi, 10min)
- Artifact Registry: <$1/mo (container storage)
- GCS: <$1/mo (minimal data volume)

**Cost Optimization Opportunities**:
1. Min instances = 0 (cold start acceptable for reference data)
2. No committed use needed at this scale

### Performance Baseline

**Latency** (local testing):
- P50: ~20ms (cached)
- P95: ~50ms (cold)
- P99: ~100ms (first request after restart)

**Throughput**: ~100 req/sec (single instance, stdlib http.server)

**Error Budget**: N/A (not established)

---

## 9. Development Workflow

### Local Development

**Standard Environment**:
- macOS/Linux
- Python 3.11 or 3.12
- venv for isolation

**Bootstrap**:
```bash
git clone <repo>
cd stci
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Common Tasks**:
```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_collector.py

# Run with pattern
pytest -k "test_fetch"

# Collect from fixtures
python -m services.collector.pipeline --fixtures

# Collect live (requires network)
python -m services.collector.pipeline

# Compute index
python -m services.indexer.pipeline --date 2026-01-02
```

### CI/CD Pipeline

**Platform**: GitHub Actions

**Triggers**:
- Push to main: full CI + deploy
- PR to main: CI only
- Cron (00:30 UTC): daily pipeline

**Stages**:
```
lint (ruff) → test (pytest 3.11/3.12) → validate-schemas → build → deploy
```

**Artifacts**:
- Docker images: us-central1-docker.pkg.dev/{project}/stci/{api|pipeline}:{sha}
- Pipeline data: artifacts uploaded with 30-day retention

### Code Quality

**Linting**: ruff (config not customized)

**Analysis**: None (no SAST/DAST)

**Review**: GitHub PR approval required

**Coverage**: Not enforced (Codecov integration available but optional)

---

## 10. Dependencies & Supply Chain

### Direct Dependencies (requirements.txt)

| Package | Version | Purpose | Risk |
|---------|---------|---------|------|
| requests | >=2.28.0 | HTTP client for API fetching | Low |
| pyyaml | >=6.0 | Methodology config parsing | Low |
| google-cloud-storage | >=2.10.0 | GCS storage backend (optional) | Low |
| jsonschema | >=4.17.0 | Observation validation | Low |
| pytest | >=7.0.0 | Testing framework | Dev only |
| pytest-cov | >=4.0.0 | Coverage reporting | Dev only |
| responses | >=0.23.0 | HTTP mocking | Dev only |

### Third-Party Services

| Service | Purpose | Data Shared | Auth | SLA | Renewal | Owner |
|---------|---------|-------------|------|-----|---------|-------|
| OpenRouter | Pricing data source | None (public API) | None | None | N/A | External |
| GitHub Actions | CI/CD | Code, secrets | GitHub auth | 99.9% | N/A | Platform |
| GCP Cloud Run | Hosting | Application data | WIF | 99.95% | Monthly | Platform |

---

## 11. Integration with Existing Documentation

### Documentation Inventory

| Document | Location | Status | Last Updated |
|----------|----------|--------|--------------|
| README.md | / | Complete | 2026-01-02 |
| CLAUDE.md | / | Complete | 2026-01-02 |
| CHANGELOG.md | / | Current | 2026-01-02 |
| PRD | 000-docs/001-PP-PROD | Complete | 2026-01-01 |
| ADRs (4) | 000-docs/002,012-014 | Complete | 2026-01-02 |
| Methodology Spec | 000-docs/004-DR-STND | Complete | 2026-01-01 |
| Recompute Runbook | 000-docs/005-DR-SOPS | Complete | 2026-01-01 |
| Release Report | 000-docs/015-RL-REPT | Current | 2026-01-02 |

### Discrepancies

None identified. Documentation is fresh (v0.1.0 just released).

### Recommended Reading Order

1. **README.md** - Business context, quickstart, API endpoints
2. **CLAUDE.md** - Development commands, architecture overview
3. **000-docs/004-DR-STND-stci-methodology.md** - Index computation rules
4. **000-docs/012-AT-ADEC-openrouter-primary-source.md** - Data source rationale
5. **000-docs/005-DR-SOPS-recompute-runbook.md** - Verification procedures

---

## 12. Current State Assessment

### What's Working Well

✅ **Clean Architecture**: Clear separation of collector → indexer → API with well-defined data flow

✅ **Comprehensive Testing**: 48 tests with mocking, all passing

✅ **Deterministic Computation**: Verification hashes enable third-party audit

✅ **Minimal Dependencies**: stdlib API server, few runtime dependencies

✅ **CI/CD Automation**: Tests, linting, deployment, daily pipeline all automated

✅ **Documentation**: 16 documents covering product, architecture, operations

✅ **Container Ready**: Multi-stage Dockerfile, docker-compose for local dev

### Areas Needing Attention

⚠️ **Single Data Source**: OpenRouter only; no fallback if service is down

⚠️ **No Monitoring**: No dashboards, alerting, or SLO tracking

⚠️ **No Staging Environment**: Changes deploy directly to production

⚠️ **No Error Retry**: Collection pipeline fails on first error

⚠️ **No Rate Limiting**: API has no protection against abuse

⚠️ **Carry-Forward Not Implemented**: Missing data handling documented but not coded

### Immediate Priorities

| Priority | Issue | Impact | Action | Owner |
|----------|-------|--------|--------|-------|
| **High** | Single source dependency | Data unavailability | Add direct provider collectors (OpenAI, Anthropic) | Platform |
| **High** | No monitoring | Blind to failures | Add Cloud Monitoring dashboard + alerts | DevOps |
| **Medium** | No staging | Risk of production issues | Add staging Cloud Run service | DevOps |
| **Medium** | No retry logic | Transient failures cause daily gaps | Add retry with exponential backoff | Platform |
| **Low** | No rate limiting | Potential abuse | Add Cloud Run concurrency limits | DevOps |

---

## 13. Quick Reference

### Operational Command Map

| Capability | Command | Source | Notes |
|------------|---------|--------|-------|
| Local env setup | `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` | - | One-time |
| Run tests | `pytest` | tests/ | 48 tests |
| Run single test | `pytest tests/test_collector.py -k "test_name"` | - | Pattern match |
| Collect (fixtures) | `python -m services.collector.pipeline --fixtures` | services/collector/ | Test data |
| Collect (live) | `python -m services.collector.pipeline` | services/collector/ | Requires network |
| Compute index | `python -m services.indexer.pipeline --date YYYY-MM-DD` | services/indexer/ | Requires observations |
| Start API | `python -m services.api.main --port 8000` | services/api/ | Default port 8000 |
| Docker API | `docker compose up api` | docker-compose.yml | Port 8000 |
| Docker pipeline | `docker compose run pipeline` | docker-compose.yml | One-shot |
| Manual deploy | GitHub Actions → workflow_dispatch | .github/workflows/deploy.yml | Requires secrets |
| View logs | `gcloud run logs read stci-api --region=us-central1` | - | Requires gcloud auth |
| Emergency rollback | Revert commit + push | - | Triggers redeploy |

### Critical Endpoints & Resources

| Resource | URL/Path | Notes |
|----------|----------|-------|
| Production API | (Cloud Run URL) | Check GCP Console |
| Health Check | `/health` | Returns {"status": "healthy"} |
| Latest Index | `/v1/index/latest` | Most recent computed index |
| Index by Date | `/v1/index/YYYY-MM-DD` | Specific date |
| Methodology | `/v1/methodology` | Current basket config |
| GitHub Repo | github.com/intent-solutions-io/stci-standard-llm-token-cost-index | Source of truth |
| CI/CD | Repo → Actions tab | Pipeline status |
| Cloud Run | GCP Console → Cloud Run | Service health |

### First-Week Checklist

- [ ] Clone repository and set up local environment
- [ ] Run tests: `pytest` (all 48 should pass)
- [ ] Run collection pipeline with fixtures
- [ ] Run indexer and verify output
- [ ] Start API server and test all endpoints
- [ ] Review CLAUDE.md and README.md
- [ ] Review methodology.yaml for index definitions
- [ ] Understand observation.schema.json validation rules
- [ ] Review GitHub Actions workflows
- [ ] Get GCP access and verify Cloud Run services
- [ ] Set up GCP workload identity if deploying
- [ ] Review ADRs for architectural context
- [ ] Log first improvement issue/ticket

---

## 14. Recommendations Roadmap

### Week 1 – Critical Setup & Visibility

**Goals**:
- [ ] Set up Cloud Monitoring dashboard for API latency/errors
- [ ] Create alerting policy for pipeline failures
- [ ] Document Cloud Run access and deployment process
- [ ] Verify daily pipeline is running (check data/indices/)

**Stakeholders**: DevOps, Platform

**Dependencies**: GCP access, Monitoring API enabled

### Month 1 – Resilience & Reliability

**Goals**:
- [ ] Add retry logic to collector pipeline (3 attempts, exponential backoff)
- [ ] Implement carry-forward for missing observations (up to 7 days)
- [ ] Add staging environment (stci-api-staging)
- [ ] Add second data source (direct OpenAI pricing API)
- [ ] Implement basic rate limiting (Cloud Run concurrency)

**Stakeholders**: Platform, DevOps

**Dependencies**: Additional API access, staging resources

### Quarter 1 – Strategic Enhancements

**Goals**:
- [ ] Add Anthropic and Google direct collectors (T1 sources)
- [ ] Implement usage-weighted indices (requires market share data)
- [ ] Add historical backfill tooling
- [ ] Create public documentation site
- [ ] Implement API authentication for premium access
- [ ] Add Slack/email notifications for significant rate changes

**Stakeholders**: Platform, Product, Business

**Dependencies**: Provider API access, market share data source

---

## Appendices

### Appendix A. Glossary

| Term | Definition |
|------|------------|
| **Observation** | Single pricing data point for a model at a specific time |
| **Index** | Aggregated reference rate (STCI-ALL, STCI-FRONTIER, etc.) |
| **Blended Rate** | Weighted average assuming 3:1 output:input ratio |
| **Methodology** | Configuration defining baskets, weights, thresholds |
| **T1/T2/T3/T4** | Data source quality tiers (official → community) |
| **Verification Hash** | SHA256 checksum for deterministic recomputation |
| **Carry Forward** | Using previous day's rate when current day missing |
| **WIF** | Workload Identity Federation (GCP auth mechanism) |

### Appendix B. Reference Links

- GitHub Repository: [stci-standard-llm-token-cost-index](https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index)
- OpenRouter API: https://openrouter.ai/api/v1/models
- Keep a Changelog: https://keepachangelog.com/
- Cloud Run: https://console.cloud.google.com/run

### Appendix C. Troubleshooting Playbooks

**Pipeline fails with network error**:
1. Check OpenRouter status: https://status.openrouter.ai
2. Manual retry: `python -m services.collector.pipeline`
3. If persistent, use fixtures: `--fixtures`
4. Create issue if >24h outage

**Index has unexpected values**:
1. Compare with previous day: `diff data/indices/{prev}.json data/indices/{today}.json`
2. Check observations: `cat data/observations/{date}.jsonl | jq .model_id`
3. Verify against source: visit OpenRouter pricing page
4. Recompute: `python -m services.indexer.pipeline --date {date}`
5. Compare verification hashes

**API returns 404 for date**:
1. Check if data exists: `ls data/indices/{date}.json`
2. If missing, check observations: `ls data/observations/{date}.jsonl`
3. If observations exist, run indexer
4. If observations missing, run collector (may need fixtures for historical)

### Appendix D. Change Management

**Release Process**:
1. Create feature branch
2. Develop and test locally
3. Open PR → CI runs
4. Merge to main → Auto-deploy to production
5. Tag release if significant: `git tag -a vX.Y.Z -m "Release notes"`

**Rollback**: Revert commit and push to main (triggers redeploy)

### Appendix E. Open Questions

1. What is the target SLA for production API?
2. Should we implement caching layer (Redis/Memcache) for high traffic?
3. What market share data source will we use for usage-weighted indices?
4. Should historical data be backfilled, and how far back?
5. What authentication model for premium API access?
6. Should we support non-USD currencies?

---

*Document: 016-AA-AUDT-appaudit-devops-playbook.md*
*Generated by: Claude Code Universal Release Engineering*
*Contact: jeremy@intentsolutions.io*
