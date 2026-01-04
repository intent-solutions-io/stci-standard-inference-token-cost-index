# Changelog

All notable changes to STCI (Standard Token Cost Index) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-04

### Added

- **Pricing Intelligence Center** (`/intelligence.html`) - comprehensive LLM pricing analysis tool:
  - Historical pricing timeline with 19 curated events from major providers
  - Price velocity chart powered by Chart.js with linear/log scale toggle
  - Multiplicative savings calculator (quick, advanced, and contract benchmark modes)
  - Live market snapshot from daily index API
  - Evidence-backed data with source links and confidence levels
  - Cost optimization features explainer (caching, batching, routing)
  - Methodology and verification documentation
  - Email subscription form with honeypot protection

- **Testing Infrastructure**:
  - Playwright smoke test suite with 19 tests covering all major features
  - GitHub Actions CI pipeline with three jobs:
    - Data validation (JSON Schema + business rules)
    - E2E tests (Playwright)
    - Lighthouse audits with score thresholds

- **Build-Time Validation**:
  - JSON Schema validation for pricing events data
  - Business rules validation (duplicate IDs, severity rubric, HTTPS sources)
  - JSON-LD generation for SEO structured data

- **Legal Pages**:
  - Privacy policy (`/privacy.html`)
  - Terms of service (`/terms.html`)

### Changed

- Improved accessibility score from 84 to 97:
  - Fixed color contrast on hero stat labels
  - Corrected heading hierarchy (h4 → h3)
  - Added form labels and ARIA attributes
  - Added main landmark element

- Enhanced landing page UI/UX with better spacing and tier explanations

### Fixed

- Firestore initialization for Firebase Functions
- Python venv creation for Firebase Functions deployment
- Landing page comparison spacing and data loading
- Production URL in deploy summary

### Security

- All source URLs require HTTPS for high-confidence events
- Honeypot field for bot protection on subscription form
- CSP-ready with vendored dependencies (no CDN)

## [0.1.0] - 2026-01-02

### Added

- **OpenRouter Collector Pipeline**: Fetches LLM pricing data from OpenRouter API with automatic rate normalization to USD/1M tokens
- **Indexer Pipeline**: Computes daily reference rates for STCI-ALL, STCI-FRONTIER, STCI-EFFICIENT, and STCI-OPEN indices
- **Read-only HTTP API**: Serves index data, observations, and methodology via REST endpoints
- **JSON Schema Validation**: Canonical schemas for observations (`observation.schema.json`) and daily indices (`stci_daily.schema.json`)
- **Docker Support**: Multi-stage Dockerfile for API server and pipeline execution
- **GCP Cloud Run Deployment**: GitHub Actions workflow with Workload Identity Federation
- **Daily Automation**: Cron-based pipeline execution with systemd timer support
- **Comprehensive Test Suite**: 48 unit tests covering collector, indexer, and API services
- **CLAUDE.md**: Claude Code guidance for development workflows

### Infrastructure

- GitHub Actions workflows for CI (tests), CD (deployment), and daily pipeline
- Docker Compose for local development
- Storage backends for local filesystem and Google Cloud Storage

### Documentation

- Product Requirements Document (PRD)
- Architecture Decision Records (ADRs) for index-first strategy, OpenRouter integration, data pipeline, and licensing
- Observation schema specification
- STCI methodology specification
- Recompute runbook for deterministic verification

---

*STCI — Making LLM pricing transparent, reproducible, and trustworthy.*

[0.2.0]: https://github.com/intent-solutions-io/stci-standard-inference-token-cost-index/releases/tag/v0.2.0
[0.1.0]: https://github.com/intent-solutions-io/stci-standard-inference-token-cost-index/releases/tag/v0.1.0
