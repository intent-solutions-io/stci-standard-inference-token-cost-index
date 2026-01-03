# Release Report: STCI v0.1.0

**Date:** 2026-01-02
**Version:** 0.1.0
**Type:** Initial Release

---

## Executive Summary

First public release of STCI (Standard Token Cost Index), a vendor-neutral price index for LLM tokens. This release delivers a complete MVP with data collection, index computation, and API serving capabilities.

---

## Release Metrics

| Metric | Value |
|--------|-------|
| Version | 0.1.0 |
| Commits | 14 |
| Contributors | 1 |
| Files Changed | 37 |
| Lines Added | +3,557 |
| Lines Removed | -102 |
| Test Coverage | 48 tests passing |

---

## Version Bump Decision

**Bump Level:** MINOR (0.1.0)

**Justification:**
- Initial development release following semver conventions
- Complete MVP functionality implemented
- All quality gates passed
- No prior releases to compare against

---

## Changes Summary

### Features (7)
- `51eb4fd` Implement working OpenRouter collector pipeline
- `9665d55` Implement working STCI indexer pipeline
- `e97420f` Implement working STCI API serving real data
- `7eccc00` Add daily cron automation for pipeline
- `1266e0d` Add Docker support for API and pipeline
- `794b5f9` Add GitHub Actions workflows
- `e9fe561` Add GCP Cloud Run deployment with WIF

### Documentation (3)
- `55c7108` Add ADR for OpenRouter as primary data source
- `7655892` Add data pipeline architecture ADR and storage directories
- `553740d` Add CLAUDE.md for Claude Code guidance

### Infrastructure (3)
- `9e85a48` Add unit tests for all services
- `9ac3b99` Keep collected data private, open-source code only
- `41e0739` Initial scaffold: STCI - Standard Token Cost Index

### Maintenance (1)
- `9ba940b` Update AAR to reflect 12 docs including OpenRouter ADR

---

## Quality Gates Status

| Gate | Status | Details |
|------|--------|---------|
| Tests | PASS | 48/48 passed |
| Working Tree | PASS | Clean |
| Branch | PASS | main |
| Remote Sync | PASS | Up to date |

---

## Files Updated

| File | Type | Description |
|------|------|-------------|
| VERSION | CREATE | Version file (0.1.0) |
| CHANGELOG.md | CREATE | Release changelog |
| README.md | UPDATE | Fixed URLs, updated roadmap, added badges |
| 000-docs/015-RL-REPT-stci-release-v0.1.0.md | CREATE | This release report |

---

## Artifacts Generated

- Git tag: `v0.1.0`
- GitHub Release: `v0.1.0`
- Docker image: `stci-api:0.1.0`

---

## Rollback Procedure

If this release needs to be rolled back:

```bash
# 1. Delete remote tag
git push origin --delete v0.1.0

# 2. Delete local tag
git tag -d v0.1.0

# 3. Revert release commit
git revert HEAD
git push origin main

# 4. Delete GitHub Release (if created)
gh release delete v0.1.0 --yes
```

---

## Post-Release Checklist

- [x] VERSION file created
- [x] CHANGELOG.md created
- [x] README.md updated with correct version and URLs
- [x] Release report generated
- [ ] Git tag created
- [ ] Pushed to origin
- [ ] GitHub Release created

---

**Generated:** 2026-01-02T21:00:00-06:00
**System:** Universal Release Engineering (Claude Code)

intent solutions io — confidential IP
Contact: jeremy@intentsolutions.io
