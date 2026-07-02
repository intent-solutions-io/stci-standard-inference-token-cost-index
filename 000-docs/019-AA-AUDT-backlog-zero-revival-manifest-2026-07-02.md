# Backlog Zero — Revival Manifest: STCI

**Campaign:** Backlog Zero, Wave 0 (dormant-repo settle)
**Date:** 2026-07-02
**Repo:** `stci` (remote `jeremylongshore/stci-standard-inference-token-cost-index`)
**Runner:** backlog-zero mutation-runner (db triage from `.beads/issues.jsonl` snapshot, verified against the repo)
**End-state:** 8 open beads settled → only the revival epic remains open. No needs-human beads were required.

---

## Revival epic

**`stci-5ob` — Revive or archive STCI: settle the dormant backlog and decide the project's future** (P2, labels `backlog-zero,revival`)

The dormant backlog was pure done-but-open drift: the project actually shipped v0.1.0 through
v0.5.0 and ran its daily pipeline from 2026-01 to 2026-03-06, but the beads were never closed.
The one live decision — resume daily collection (cron deliberately disabled in commit `1ecec83`
to stop burning Actions minutes) vs archive — is captured in the revival epic.

## Settled beads

| Bead | Title | Disposition | Evidence (one line) |
|---|---|---|---|
| stci-9b1 | STCI — Index + API MVP (epic) | Closed — done-but-open drift | Shipped as v0.1.0 (tag + `000-docs/015-RL-REPT-stci-release-v0.1.0.md`); `services/{collector,indexer,api}/`, `schemas/*.json`, tests all in-tree; all 8 children closed |
| stci-9b1.8 | v0.1.0 release checklist | Closed — done-but-open drift | Tag `v0.1.0` exists (repo tagged through `v0.5.0`), `VERSION` = 0.1.0, `CHANGELOG.md`, release report `000-docs/015` (48 tests passing) |
| stci-q9l | STCI — Data Sourcing, Verification, Automation (epic) | Closed — all children settled | q9l.1–3 closed earlier against docs 006/008/009; q9l.4–7 drift-closed today; q9l.8 obsolete; pipeline ran daily 2026-01 → 2026-03-06 |
| stci-q9l.4 | Data collection strategy | Closed — done-but-open drift | `000-docs/010-DR-SOPS-data-ops-practices.md` §1 (schedule, protocol, idempotency), `000-docs/007` §5, ADR `000-docs/012`; implemented in `services/collector/` + `daily-pipeline.yml` |
| stci-q9l.5 | Verification strategy | Closed — done-but-open drift | `000-docs/010` §2 verification + §3 anomaly detection + §4 incident response; recompute runbook `000-docs/005`; `verification_hash` in `schemas/stci_daily.schema.json` |
| stci-q9l.6 | Automation plan | Closed — done-but-open drift | ADR `000-docs/013` (pipeline architecture), `000-docs/010` §7 (monitoring), `.github/workflows/daily-pipeline.yml` ran daily (e.g. commit `27cc28b`); cron disabled deliberately (`1ecec83`) |
| stci-q9l.7 | QA/test harness plan | Closed — done-but-open drift | `tests/test_{collector,indexer,api,comparison}.py` + `tests/conftest.py`, golden fixtures `data/fixtures/`, CI invariants in `ci.yml` (schema validation, business rules, Playwright, Lighthouse) + `tests.yml` |
| stci-q9l.8 | Execution roadmap | Closed — obsolete (overtaken by events) | Bead targeted go/no-go for the FIRST public publish; v0.1.0 published 2026-01-02, then v0.2.0–v0.5.0 + daily publishes through 2026-03-06 |

## In-flight residue (left alone)

- **Dirty working tree (pre-existing, NOT committed):** `package.json` (modified), `package-lock.json` (modified), `screenshot-audit.js` (untracked).
- **Beads-DB recovery residue:** local main carries an unpushed `bd init` commit (`e24d591`) that diverged from origin/main; the local dolt backend was broken (server mode pointing at an empty data dir) and was repaired to embedded mode during this settle (`.beads/metadata.json` `dolt_mode: server → embedded`, local-only change). `bd bootstrap`'s failed restore deleted `.beads/issues.jsonl` mid-recovery; it was restored from git, verified byte-identical to the pre-run snapshot, and re-imported (18 issues) before any writes.
- **Local branch:** `feat/install-audit-harness-baseline` (its remote counterpart merged as PR #6).
- **Remote branches:** `feat/email-notification`, `fix/enterprise-csv-upload` (stale, no open PRs).
- **Open PRs:** none.
- **CI:** all cron schedules deliberately disabled (`1ecec83`, "stop burning Actions minutes").

## Needs-human digest

None. The single genuine decision — resume the daily pipeline vs archive the project — is the
revival epic's charter (`stci-5ob`), not a separate needs-human bead.
