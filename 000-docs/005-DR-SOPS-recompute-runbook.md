# STCI Recompute Runbook

**Document ID:** 005
**Category:** OD (Operations & Deployment)
**Type:** SOPS (Standard Operating Procedures)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01

---

## Purpose

This runbook describes how to **deterministically recompute** STCI index values for any historical date. Recomputation is used for:

1. **Verification:** Third-party validation of published values
2. **Backfill:** Computing historical values for dates before automation
3. **Audit:** Investigating discrepancies or data quality issues
4. **Recovery:** Regenerating values after data corrections

---

## Prerequisites

- [ ] Python 3.11+ installed
- [ ] STCI repository cloned
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Access to observation data for target date(s)

---

## 1. Recompute Single Date

### Step 1: Prepare Observations

Ensure observations for the target date are available:

```bash
# Check for observations file
ls data/observations/YYYY-MM-DD.json

# Or fetch from observation store
python -m services.collector.fetch --date 2026-01-01 --output data/observations/
```

### Step 2: Run Indexer

```bash
python -m services.indexer.compute \
  --date 2026-01-01 \
  --observations data/observations/2026-01-01.json \
  --methodology data/fixtures/methodology.yaml \
  --output data/indices/2026-01-01.json
```

### Step 3: Verify Output

```bash
# Compare with published value (if exists)
python -m scripts.verify_index \
  --computed data/indices/2026-01-01.json \
  --published https://api.stci.io/v1/index/2026-01-01
```

**Expected output:**
```
Date: 2026-01-01
Computed STCI-ALL: 6.27
Published STCI-ALL: 6.27
Status: MATCH ✓
Verification Hash: a1b2c3d4e5f6...
```

---

## 2. Recompute Date Range (Backfill)

### Step 1: Define Range

```bash
# Set date range
START_DATE="2025-10-01"
END_DATE="2026-01-01"
```

### Step 2: Batch Recompute

```bash
python -m services.indexer.backfill \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --observations-dir data/observations/ \
  --methodology data/fixtures/methodology.yaml \
  --output-dir data/indices/ \
  --parallel 4
```

### Step 3: Generate Report

```bash
python -m scripts.backfill_report \
  --indices-dir data/indices/ \
  --start-date $START_DATE \
  --end-date $END_DATE
```

**Sample report:**
```
Backfill Report: 2025-10-01 to 2026-01-01
=========================================
Total dates: 93
Successful: 91
Failed: 2
  - 2025-11-15: INSUFFICIENT_DATA (3/12 observations)
  - 2025-12-25: MISSING_OBSERVATIONS (no file)
```

---

## 3. Investigate Discrepancy

When computed value differs from published:

### Step 1: Collect Evidence

```bash
# Download published observations
curl -o /tmp/published_obs.json \
  "https://api.stci.io/v1/observations/2026-01-01"

# Download published index
curl -o /tmp/published_idx.json \
  "https://api.stci.io/v1/index/2026-01-01"
```

### Step 2: Compare Observations

```bash
python -m scripts.diff_observations \
  --local data/observations/2026-01-01.json \
  --published /tmp/published_obs.json
```

### Step 3: Identify Root Cause

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Different observation count | Missing/extra observations | Sync observations |
| Same observations, different rate | Rounding difference | Check methodology version |
| Methodology mismatch | Version skew | Use matching methodology |
| Hash mismatch | Computation bug | Report issue |

### Step 4: Document Finding

Create issue in Beads:
```bash
bd create --title "Index discrepancy 2026-01-01" \
  --label "data-quality" \
  --description "Computed: 6.28, Published: 6.27. Root cause: ..."
```

---

## 4. Emergency Correction

When published data is found to be incorrect:

### Step 1: Assess Impact

- Which dates affected?
- Magnitude of error?
- Downstream consumers notified?

### Step 2: Generate Corrections

```bash
python -m services.indexer.compute \
  --date 2026-01-01 \
  --observations data/observations/2026-01-01-corrected.json \
  --methodology data/fixtures/methodology.yaml \
  --output data/indices/2026-01-01-corrected.json
```

### Step 3: Publish Correction

```bash
# Create correction record
python -m scripts.create_correction \
  --date 2026-01-01 \
  --old-value 6.27 \
  --new-value 6.28 \
  --reason "Observation obs-2026-01-01-openai-gpt4o had incorrect rate"
```

### Step 4: Notify Consumers

- Update API with corrected value
- Publish correction notice
- Update changelog

---

## 5. Verification Checklist

After any recompute:

- [ ] Output file exists and is valid JSON
- [ ] All expected indices present (STCI-ALL, sub-indices)
- [ ] Verification hash computed and stored
- [ ] Model count matches expected basket size
- [ ] Rates are within reasonable bounds
- [ ] Dispersion metrics computed
- [ ] Methodology version recorded

---

## 6. Troubleshooting

### Error: "No observations found"

```bash
# Check observation file exists
ls -la data/observations/2026-01-01.json

# Check file is valid JSON
python -c "import json; json.load(open('data/observations/2026-01-01.json'))"
```

### Error: "Methodology file not found"

```bash
# Check methodology file
ls -la data/fixtures/methodology.yaml

# Validate YAML
python -c "import yaml; yaml.safe_load(open('data/fixtures/methodology.yaml'))"
```

### Error: "Insufficient observations"

```bash
# Check observation count
python -c "import json; obs = json.load(open('data/observations/2026-01-01.json')); print(f'Count: {len(obs)}')"

# Minimum required: 50% of basket
```

### Error: "Hash mismatch"

```bash
# Recompute with verbose logging
python -m services.indexer.compute \
  --date 2026-01-01 \
  --verbose \
  --debug-rounding
```

---

## 7. Automation

### Daily Verification Cron

```bash
# Add to crontab
0 1 * * * /path/to/stci/scripts/daily_verify.sh
```

### daily_verify.sh
```bash
#!/bin/bash
DATE=$(date -d "yesterday" +%Y-%m-%d)
python -m scripts.verify_index \
  --date $DATE \
  --alert-on-mismatch
```

---

## References

- 003-AT-SPEC-observation-schema.md
- 004-AT-SPEC-stci-methodology.md
- services/indexer/README.md

---

*STCI — Standard Token Cost Index*
*Runbook Version: 1.0.0*
