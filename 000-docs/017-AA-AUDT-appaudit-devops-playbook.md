# Inference Price Index (STCI): Operator-Grade System Analysis & Operations Guide

*For: DevOps Engineer*
*Generated: 2026-01-04*
*System Version: v0.1.0-14-g996a94a*

---

## Table of Contents
1. Executive Summary
2. Operator & Customer Journey
3. System Architecture Overview
4. Directory Deep-Dive
5. Automation & Agent Surfaces
6. Operational Reference
7. Security, Compliance & Access
8. Cost & Performance
9. Development Workflow
10. Dependencies & Supply Chain
11. Integration with Existing Documentation
12. Current State Assessment
13. Quick Reference
14. Recommendations Roadmap

---

## 1. Executive Summary

### Business Purpose

The **Inference Price Index (STCI)** is a vendor-neutral, public price index for LLM tokens - analogous to LIBOR for interest rates or VIX for volatility. It aggregates published pricing from major model providers (OpenAI, Anthropic, Google) and aggregators (OpenRouter), normalizes data into a canonical schema, and computes daily reference rates with full provenance.

**Core Value Proposition:**
- Transparent, reproducible benchmark for LLM pricing
- Enterprise-grade auditability for cost estimation and contract negotiation
- Historical price tracking across 323+ models from 4 data sources
- Read-only API at https://inferencepriceindex.com

The system is currently in production (v0.1.0) with daily automated data collection running successfully. The platform serves as a trusted source of truth for LLM token pricing - critical for enterprises, researchers, and developers performing cost analysis.

**Immediate Strengths:**
- Fully automated daily pipeline collecting from OpenRouter API + 3 official pricing configs
- 43 automated tests with comprehensive coverage across collector, indexer, and API
- Firebase Hosting + Functions architecture with Firestore backend
- Workload Identity Federation (WIF) for secure GitHub Actions authentication

**Known Risks:**
- Firebase deployment workflow has intermittent failures (non-blocking)
- Single Firestore document storing 300+ observations may hit size limits at scale
- No monitoring/alerting infrastructure beyond GitHub Actions status

### Operational Status Matrix

| Environment | Status | Uptime Target | Current Uptime | Release Cadence | Active Users |
|-------------|--------|---------------|----------------|-----------------|--------------|
| Production  | Live   | 99.5%         | 100% (7 days)  | On merge to main | API consumers |
| Staging     | N/A    | N/A           | N/A            | N/A             | N/A          |
| Development | Local  | N/A           | N/A            | Continuous      | 1 developer  |

### Technology Stack Summary

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.12 | Core services |
| Framework | Firebase Functions | Python 3.12 | API serving |
| Database | Firestore | - | Document storage |
| Cloud Platform | Google Cloud | - | Hosting, Functions |
| CI/CD | GitHub Actions | - | Tests, deploy, daily pipeline |
| Hosting | Firebase Hosting | - | Static assets |
| Authentication | Workload Identity Federation | - | Keyless GCP auth |

---

## 2. Operator & Customer Journey

### Primary Personas

- **API Consumers**: Developers and enterprises querying pricing data programmatically
- **Data Analysts**: Researchers analyzing LLM pricing trends
- **Operators**: DevOps/SRE managing the daily pipeline and infrastructure
- **Contributors**: Developers adding new data sources or features

### End-to-End Journey Map

```
Data Collection → Index Computation → Firestore Storage → API Serving → Consumer
     ↓                   ↓                  ↓                ↓
GitHub Actions     Python Indexer      Firebase        Firebase Functions
(00:30 UTC)        (deterministic)     (persistent)    (read-only API)
```

**Critical Touchpoints:**
1. **Daily Pipeline (00:30 UTC)**: Collects from 4 sources, computes indices, uploads to Firestore
2. **Validation Workflow (00:45 UTC)**: Validates model matching, catches data quality issues
3. **API Access**: https://inferencepriceindex.com/v1/index/latest
4. **Compare Page**: https://inferencepriceindex.com/compare.html

### SLA Commitments

| Metric | Target | Current | Owner |
|--------|--------|---------|-------|
| Data Freshness | Daily by 01:00 UTC | Met | Pipeline |
| API Availability | 99.5% | 100% | Firebase |
| API Response Time | < 500ms | ~100ms | Firebase Functions |
| Model Coverage | 300+ models | 323 models | Collector |

---

## 3. System Architecture Overview

### Technology Stack (Detailed)

| Layer | Technology | Version | Source of Truth | Purpose | Owner |
|-------|------------|---------|-----------------|---------|-------|
| Frontend/UI | Static HTML/CSS/JS | - | `public/` | Landing, docs, compare pages | - |
| Backend/API | Firebase Functions | Python 3.12 | `functions/main.py` | REST API endpoints | - |
| Database | Firestore | - | Collections: indices, observations, methodology | Document storage | - |
| Data Collection | Python | 3.12 | `services/collector/` | Multi-source price collection | - |
| Index Computation | Python | 3.12 | `services/indexer/` | Deterministic index calculation | - |
| Infrastructure | Firebase + GCP | - | `firebase.json`, workflows | Hosting, Functions, Firestore | - |
| Observability | GitHub Actions | - | `.github/workflows/` | Pipeline logs, test results | - |

### Environment Matrix

| Environment | Purpose | Hosting | Data Source | Release Cadence | IaC Source |
|-------------|---------|---------|-------------|-----------------|------------|
| local | Development | localhost:8000 | Fixtures or API | Manual | docker-compose.yml |
| prod | Live service | Firebase | Firestore | On main merge | firebase.json |

### Cloud & Platform Services

| Service | Purpose | Environment | Key Config | Cost/Limits |
|---------|---------|-------------|------------|-------------|
| Firebase Hosting | Static site | prod | `public/` directory | Free tier |
| Firebase Functions | API | prod | Python 3.12, 512MB | Pay per invocation |
| Firestore | Database | prod | 3 collections | Pay per read/write |
| GitHub Actions | CI/CD | all | 5 workflows | 2000 min/month free |
| Workload Identity | Auth | prod | Pool: github-pool | Free |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Daily Pipeline  │  │ Tests Workflow  │  │ Deploy Workflows (2)   │  │
│  │ (00:30 UTC)     │  │ (PR/Push)       │  │ Cloud Run + Firebase   │  │
│  └────────┬────────┘  └─────────────────┘  └─────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────┐
│           Data Sources                     │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │ OpenRouter   │  │ Direct Sources   │   │
│  │ API (300+)   │  │ YAML configs (23)│   │
│  └──────┬───────┘  └────────┬─────────┘   │
└─────────┴───────────────────┴─────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Collection Pipeline                               │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────────┐ │
│  │ Collector  │→ │ Drift    │→ │ Dedup      │→ │ Store observations   │ │
│  │ (sources)  │  │ Detection│  │ (prefer    │  │ (JSONL)              │ │
│  │            │  │          │  │  official) │  │                      │ │
│  └────────────┘  └──────────┘  └────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Indexer Pipeline                                  │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │
│  │ Load observations  │→ │ Compute indices    │→ │ Generate hash      │ │
│  │ + methodology      │  │ (ALL/FRONTIER/     │  │ (deterministic)    │ │
│  │                    │  │  EFFICIENT/OPEN)   │  │                    │ │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Firestore                                        │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ indices/{date}│  │ observations/{d} │  │ methodology/current        │ │
│  │ (daily)       │  │ (daily, 300+)    │  │ (singleton)                │ │
│  └──────────────┘  └──────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Firebase Functions + Hosting                          │
│  ┌─────────────────────────────────────┐  ┌────────────────────────────┐│
│  │ functions/main.py (API)             │  │ public/                    ││
│  │ /v1/index/latest                    │  │ index.html (landing)       ││
│  │ /v1/index/{date}                    │  │ docs.html (API docs)       ││
│  │ /v1/observations/{date}             │  │ compare.html (comparison)  ││
│  │ /v1/methodology                     │  │ styles.css, app.js         ││
│  └─────────────────────────────────────┘  └────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
            https://inferencepriceindex.com
```

---

## 4. Directory Deep-Dive

### Project Structure Analysis

```
stci/
├── .beads/                      # Issue tracking (beads system)
│   ├── config.yaml              # Beads configuration
│   └── beads.left.jsonl         # Active issues
├── .github/workflows/           # CI/CD pipelines
│   ├── daily-pipeline.yml       # Daily collection (00:30 UTC)
│   ├── deploy-firebase.yml      # Firebase deployment
│   ├── deploy.yml               # Cloud Run deployment
│   ├── tests.yml                # Test suite (Python 3.11, 3.12)
│   └── validate-comparison.yml  # Data validation (00:45 UTC)
├── 000-docs/                    # Documentation (16 docs)
│   ├── 001-PP-PROD-stci-prd.md  # Product requirements
│   ├── 004-DR-STND-stci-methodology.md  # Index methodology
│   ├── 005-DR-SOPS-recompute-runbook.md # Recompute procedures
│   └── ...
├── data/
│   ├── fixtures/                # Test data + pricing configs
│   │   ├── openai_pricing.yaml  # 7 models
│   │   ├── anthropic_pricing.yaml # 8 models
│   │   ├── google_pricing.yaml  # 8 models
│   │   └── methodology.yaml     # Basket definitions
│   ├── indices/                 # Daily index JSON files
│   ├── observations/            # Daily observations JSONL
│   └── raw/                     # Raw API responses
├── functions/                   # Firebase Functions
│   ├── main.py                  # API endpoints (111 lines)
│   ├── requirements.txt         # firebase-functions, firebase-admin
│   └── lib/                     # Vendored dependencies
├── public/                      # Static hosting
│   ├── index.html               # Landing page
│   ├── docs.html                # API documentation
│   ├── compare.html             # Price comparison tool
│   ├── styles.css               # CSS (8386 bytes)
│   └── app.js                   # Client-side JS
├── schemas/                     # JSON schemas
│   ├── observation.schema.json  # Observation validation
│   └── stci_daily.schema.json   # Daily index validation
├── services/
│   ├── collector/               # Data collection
│   │   ├── pipeline.py          # Main pipeline (463 lines)
│   │   ├── sources.py           # OpenRouter + Fixture sources
│   │   ├── drift.py             # Price drift detection
│   │   └── direct_sources/      # Official pricing sources
│   │       ├── openai_source.py
│   │       ├── anthropic_source.py
│   │       └── google_source.py
│   ├── indexer/                 # Index computation
│   │   ├── pipeline.py          # Indexer pipeline
│   │   └── indexer.py           # Core computation logic
│   └── api/                     # Local API server
│       └── main.py              # FastAPI server (dev only)
├── tests/                       # Test suite (43 tests)
│   ├── conftest.py              # Fixtures (181 lines)
│   ├── test_collector.py        # Collector tests
│   ├── test_indexer.py          # Indexer tests
│   ├── test_api.py              # API tests
│   └── test_comparison.py       # Normalization tests (13 tests)
├── docker-compose.yml           # Local development
├── firebase.json                # Firebase configuration
├── firestore.rules              # Firestore security rules
├── requirements.txt             # Python dependencies
└── README.md                    # Project overview
```

### Detailed Directory Analysis

#### services/collector/

**Purpose**: Multi-source price data collection with drift detection

**Key Files**:
- `pipeline.py:83-136` - Single-source collection workflow
- `pipeline.py:138-236` - Multi-source with drift detection (`run_multi`)
- `sources.py` - OpenRouter API and fixture sources
- `drift.py:65-153` - Cross-source price comparison
- `direct_sources/` - Official pricing from YAML configs

**Patterns**:
- Source abstraction via `BaseSource` class
- Deduplication prefers official sources over aggregators
- Drift detection compares same-type sources only

**Entry Points**:
```bash
python -m services.collector.pipeline --multi --date 2026-01-03
```

#### services/indexer/

**Purpose**: Deterministic index computation from observations

**Key Files**:
- `indexer.py` - Core computation (blended rates, dispersion)
- `pipeline.py` - Orchestration and output

**Key Algorithm** (indexer.py):
- Blended rate = (input_rate + output_rate) / 2 (equal weight)
- Dispersion = standard deviation of rates
- Verification hash = SHA256 of sorted observation IDs

#### functions/

**Purpose**: Firebase Functions API serving Firestore data

**Key Files**:
- `main.py:16-39` - Request routing
- `main.py:42-98` - Endpoint handlers

**Endpoints**:
| Path | Handler | Firestore Collection |
|------|---------|---------------------|
| `/health` | `handle_health` | - |
| `/v1/index/latest` | `handle_index_latest` | indices |
| `/v1/index/{date}` | `handle_index_date` | indices |
| `/v1/indices` | `handle_indices_list` | indices |
| `/v1/observations/{date}` | `handle_observations` | observations |
| `/v1/methodology` | `handle_methodology` | methodology |

#### tests/

**Framework**: pytest with fixtures
**Coverage**: 43 tests across 4 modules

**Categories**:
- `test_collector.py` - Source fetching, normalization
- `test_indexer.py` - Index computation, hashing
- `test_api.py` - Endpoint responses, CORS
- `test_comparison.py` - Model ID normalization (critical for matching)

**CI Integration**: Runs on Python 3.11 and 3.12 via `tests.yml`

---

## 5. Automation & Agent Surfaces

### GitHub Actions Workflows

| Workflow | Trigger | Purpose | Status |
|----------|---------|---------|--------|
| `daily-pipeline.yml` | cron 00:30 UTC, manual | Collect + index + Firestore upload | Active |
| `validate-comparison.yml` | cron 00:45 UTC, manual | Validate model matching | Active |
| `tests.yml` | push, PR | Run test suite | Active |
| `deploy-firebase.yml` | push main, manual | Deploy to Firebase | Active |
| `deploy.yml` | push main, manual | Deploy to Cloud Run | Active |

### Beads Issue Tracking

**Location**: `.beads/`
**Config**: `config.yaml` with sync branch `beads-sync`
**Usage**: `bd list`, `bd create`, `bd update`

---

## 6. Operational Reference

### Deployment Workflows

#### Local Development

1. **Prerequisites**:
   - Python 3.11+ (`python --version`)
   - pip (`pip --version`)
   - Git
   - Optional: Docker, Firebase CLI

2. **Environment Setup**:
```bash
# Clone repository
git clone https://github.com/intent-solutions-io/stci-standard-inference-token-cost-index.git
cd stci-standard-inference-token-cost-index

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Service Startup**:
```bash
# Run tests
pytest tests/ -v

# Run collector with fixtures
python -m services.collector.pipeline --fixtures

# Run indexer
python -m services.indexer.pipeline --date 2026-01-03

# Start local API
python -m services.api.main
# → http://localhost:8000
```

4. **Docker Alternative**:
```bash
docker compose up api
# → http://localhost:8000
```

#### Production Deployment

**Pre-deployment Checklist**:
- [ ] All tests pass (`tests.yml` green)
- [ ] No lint errors (ruff check)
- [ ] Schemas validated
- [ ] Local testing complete

**Deployment Triggers**:
- Push to `main` → Automatic deploy
- Manual: `gh workflow run deploy-firebase.yml`

**Rollback**:
```bash
# Revert to previous commit
git revert HEAD
git push

# Or deploy specific commit
gh workflow run deploy-firebase.yml --ref <commit>
```

### Monitoring & Alerting

**Current State**: Limited to GitHub Actions status

**Dashboards**:
- GitHub Actions: https://github.com/intent-solutions-io/stci-standard-inference-token-cost-index/actions
- Firebase Console: https://console.firebase.google.com/project/stci-production

**Key Metrics to Monitor**:
- Daily pipeline success (00:30 UTC)
- Validation workflow success (00:45 UTC)
- Observation count (should be 300+)
- Overlapping models in comparison (should be 5+)

### Incident Response

| Severity | Definition | Response | Playbook |
|----------|------------|----------|----------|
| P0 | API down | Immediate | Check Firebase Functions logs |
| P1 | Daily pipeline failed | Within 1 hour | Re-run manually, check API keys |
| P2 | Validation failed | Next day | Check model matching logic |
| P3 | Missing single source | Next cycle | Investigate source-specific issue |

### Backup & Recovery

**Data Persistence**:
- Git repository contains all historical data in `data/` directory
- Firestore stores current/recent data
- Raw API responses archived in `data/raw/`

**Recovery Procedure**:
```bash
# Recompute from stored observations
python -m services.indexer.pipeline --date YYYY-MM-DD

# Re-upload to Firestore (from daily-pipeline.yml)
python -c "
from google.cloud import firestore
import json
db = firestore.Client(project='stci-production')
with open('data/indices/YYYY-MM-DD.json') as f:
    db.collection('indices').document('YYYY-MM-DD').set(json.load(f))
"
```

---

## 7. Security, Compliance & Access

### Identity & Access Management

| Account/Role | Purpose | Permissions | Provisioning |
|--------------|---------|-------------|--------------|
| `github-actions@stci-production.iam.gserviceaccount.com` | CI/CD | Firestore write, Cloud Run deploy | WIF |
| `stci-runtime@stci-production.iam.gserviceaccount.com` | Cloud Run | Firestore read/write | IAM |

### Secrets Management

**GitHub Secrets**:
- `OPENROUTER_API_KEY` - API access for data collection
- `GCP_WORKLOAD_IDENTITY_PROVIDER` - WIF provider path
- `GCP_SERVICE_ACCOUNT` - Service account email
- `GCP_PROJECT_ID` - GCP project ID

**Rotation**: Manual, no automated rotation

### Security Posture

**Authentication**: None required for read-only API (public data)

**Authorization**: Firestore rules enforce read-only access:
```
allow read: if true;
allow write: if false;
```

**Encryption**:
- In-transit: HTTPS enforced by Firebase
- At-rest: Firestore encryption (managed)

**XSS Prevention**: Added `escapeHtml()` in compare.html (2026-01-04)

**Known Issues**:
- No rate limiting on API endpoints
- No API authentication for heavy consumers

---

## 8. Cost & Performance

### Current Costs

**Monthly Cloud Spend**: ~$0-10 (Free tier eligible)

| Service | Est. Monthly | Notes |
|---------|-------------|-------|
| Firebase Hosting | $0 | Free tier (10GB/month) |
| Firebase Functions | $0-5 | ~1000 invocations/day |
| Firestore | $0-5 | ~1000 reads/day |
| GitHub Actions | $0 | Free tier (2000 min/month) |

### Performance Baseline

**API Response Times** (Firebase Functions):
- `/v1/index/latest`: ~100ms
- `/v1/observations/{date}`: ~200ms (larger payload)

**Daily Pipeline Duration**: ~2 minutes

**Data Volumes**:
- Observations per day: ~323
- Index JSON size: ~13KB
- Observations JSONL size: ~160KB

### Optimization Opportunities

1. **Firestore Document Size** - Split observations into subcollections if >1MB
2. **CDN Caching** - Already configured (max-age=60s)
3. **Cold Start** - Consider min-instances if latency critical

---

## 9. Development Workflow

### Local Development

**Standard Environment**:
- macOS/Linux
- Python 3.11 or 3.12
- VS Code recommended

**Bootstrap**:
```bash
git clone <repo>
cd stci
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

### CI/CD Pipeline

**Platform**: GitHub Actions

**Triggers**:
| Event | Workflows |
|-------|-----------|
| Push to main | tests, deploy-firebase, deploy (Cloud Run) |
| Pull request | tests |
| Schedule 00:30 UTC | daily-pipeline |
| Schedule 00:45 UTC | validate-comparison |
| Manual | all workflows |

**Stages**: checkout → setup → install → test/build → deploy

### Code Quality

**Linting**: Ruff (configured in tests.yml)
```bash
ruff check services/ tests/
```

**Testing**:
```bash
# Full suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=services --cov-report=term
```

---

## 10. Dependencies & Supply Chain

### Direct Dependencies (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| requests | >=2.28.0 | HTTP client for API calls |
| pyyaml | >=6.0 | YAML config parsing |
| google-cloud-storage | >=2.10.0 | GCS backend (optional) |
| google-cloud-firestore | >=2.16.0 | Firestore client |
| jsonschema | >=4.17.0 | Schema validation |
| pytest | >=7.0.0 | Testing |
| pytest-cov | >=4.0.0 | Coverage reporting |
| responses | >=0.23.0 | HTTP mocking |

### Third-Party Services

| Service | Purpose | Data Shared | SLA |
|---------|---------|-------------|-----|
| OpenRouter | Model pricing | API key | Best effort |
| Firebase | Hosting, Functions, Firestore | Application data | 99.95% |
| GitHub | Source, CI/CD | Code, secrets | 99.9% |

---

## 11. Integration with Existing Documentation

### Documentation Inventory

| Document | Status | Purpose |
|----------|--------|---------|
| 001-PP-PROD-stci-prd.md | Current | Product requirements |
| 004-DR-STND-stci-methodology.md | Current | Index calculation methodology |
| 005-DR-SOPS-recompute-runbook.md | Current | Recompute procedures |
| 016-AA-AUDT-appaudit-devops-playbook.md | Superseded | Previous audit |
| README.md | Current | Project overview |

### Discrepancies

1. **Cloud Run vs Firebase**: Both deploy workflows exist; Firebase is primary
2. **API documentation**: README shows FastAPI endpoints; production uses Firebase Functions

### Recommended Reading

1. `004-DR-STND-stci-methodology.md` - Understand index computation
2. `005-DR-SOPS-recompute-runbook.md` - Recovery procedures
3. `.github/workflows/daily-pipeline.yml` - Daily automation

---

## 12. Current State Assessment

### What's Working Well

- Daily pipeline executing successfully (323 observations collected)
- 4 sub-indices computed (ALL, FRONTIER, EFFICIENT, OPEN)
- API responding with correct data
- Compare page showing 7 overlapping models
- 43 tests passing
- WIF authentication working for CI/CD
- XSS vulnerabilities fixed in compare.html

### Areas Needing Attention

- **Firebase Deploy Failures**: Intermittent failures not blocking main function
- **No Staging Environment**: Direct to production
- **Limited Monitoring**: No alerting beyond GitHub Actions
- **Firestore Scale**: Single document for 300+ observations
- **No Rate Limiting**: API vulnerable to abuse

### Immediate Priorities

1. **[Low]** Fix Firebase deploy workflow failures
   - Impact: Cleaner CI/CD status
   - Action: Debug jq parsing in hosting URL step

2. **[Medium]** Add monitoring/alerting
   - Impact: Faster incident response
   - Action: Configure Google Cloud Monitoring or Uptime checks

3. **[Low]** Document manual recovery procedures
   - Impact: Reduced recovery time
   - Action: Add runbook for common failure scenarios

---

## 13. Quick Reference

### Operational Command Map

| Capability | Command | Notes |
|------------|---------|-------|
| Run tests | `pytest tests/ -v` | Local |
| Run collector | `python -m services.collector.pipeline --multi` | Needs OPENROUTER_API_KEY |
| Run indexer | `python -m services.indexer.pipeline --date YYYY-MM-DD` | Needs observations |
| Deploy Firebase | `firebase deploy` | Needs auth |
| Trigger pipeline | `gh workflow run daily-pipeline.yml` | GitHub CLI |
| Check API health | `curl https://inferencepriceindex.com/health` | - |
| View workflow logs | `gh run view <run_id> --log` | GitHub CLI |

### Critical Endpoints & Resources

- **Production API**: https://inferencepriceindex.com/v1/
- **Landing Page**: https://inferencepriceindex.com/
- **Compare Page**: https://inferencepriceindex.com/compare.html
- **API Docs**: https://inferencepriceindex.com/docs.html
- **GitHub Repo**: https://github.com/intent-solutions-io/stci-standard-inference-token-cost-index
- **Firebase Console**: https://console.firebase.google.com/project/stci-production

### First-Week Checklist

- [ ] Clone repository and run tests locally
- [ ] Review daily-pipeline.yml workflow
- [ ] Understand index computation methodology
- [ ] Access GitHub Actions to view pipeline runs
- [ ] Review Firestore data structure in Firebase Console
- [ ] Trigger manual workflow run
- [ ] Review validation workflow output
- [ ] Understand model normalization in test_comparison.py

---

## 14. Recommendations Roadmap

### Week 1 - Familiarization

**Goals**:
- Complete first-week checklist
- Understand data flow from collection to API
- Identify any immediate issues

### Month 1 - Stability

**Goals**:
- Fix Firebase deploy workflow intermittent failures
- Add basic uptime monitoring (Google Cloud Monitoring or external)
- Document common troubleshooting scenarios
- Review and potentially add more test coverage

### Quarter 1 - Enhancement

**Goals**:
- Implement proper staging environment
- Add alerting for pipeline failures
- Consider Firestore structure optimization for scale
- Evaluate rate limiting needs
- Add API authentication for heavy consumers

---

## Appendices

### Appendix A. Glossary

| Term | Definition |
|------|------------|
| STCI | Standard Token Cost Index |
| Observation | Single pricing data point for a model |
| Blended Rate | Average of input and output rates |
| Drift | Price discrepancy between sources |
| WIF | Workload Identity Federation |

### Appendix B. Reference Links

- [Firebase Functions Python Docs](https://firebase.google.com/docs/functions/callable)
- [Firestore Python Docs](https://cloud.google.com/firestore/docs/reference/libraries)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

### Appendix C. Troubleshooting Playbooks

**Pipeline Failed - OpenRouter API Error**:
1. Check OPENROUTER_API_KEY secret is valid
2. Test API manually: `curl https://openrouter.ai/api/v1/models`
3. Re-run workflow if transient

**No Overlapping Models in Comparison**:
1. Check normalization logic in `test_comparison.py`
2. Verify official pricing YAML files are up to date
3. Run validation workflow manually

**Firestore Write Failed**:
1. Check service account permissions
2. Verify WIF configuration
3. Check document size limits (1MB max)

### Appendix D. Change Management

**Release Process**:
1. Create PR with changes
2. Wait for tests to pass
3. Merge to main
4. Deployment automatic

**Emergency Changes**:
1. Push directly to main (for critical fixes)
2. Monitor deployment
3. Document in commit message

### Appendix E. Open Questions

1. Should we add a staging environment?
2. Is Cloud Run deployment still needed alongside Firebase?
3. What's the plan for handling >1000 models in observations?
4. Should we add API authentication?
