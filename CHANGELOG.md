# Changelog

All notable changes to STCI (Standard Token Cost Index) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index/releases/tag/v0.1.0
