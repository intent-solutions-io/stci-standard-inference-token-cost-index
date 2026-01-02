# ADR: Data Pipeline Architecture

**Document ID:** 013
**Category:** AT (Architecture & Technical)
**Type:** ADEC (Architecture Decision)
**Status:** PROPOSED
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Phase:** 0 (Foundation)

---

## Context

STCI collects LLM pricing data daily, computes indices, and serves them via API. We need to decide:

1. Where raw observations are stored
2. Where computed indices are stored
3. How data flows between stages
4. What format/technology for storage

### Requirements

| Requirement | Priority |
|-------------|----------|
| Deterministic recomputation from raw data | P0 |
| Audit trail (what data produced what index) | P0 |
| Low operational cost for MVP | P0 |
| Query historical indices by date | P1 |
| Query observations by date/model | P1 |
| Support 1000+ observations/day | P2 |
| Real-time updates | P3 (not MVP) |

---

## Decision

**File-based storage with Git versioning for MVP, designed for future migration to BigQuery.**

```
data/
├── raw/                     # Raw API responses (immutable)
│   └── {source}/{date}.json
├── observations/            # Normalized observations (immutable)
│   └── {date}.jsonl
├── indices/                 # Computed indices (immutable)
│   └── {date}.json
└── fixtures/                # Test data
    └── *.json
```

---

## Data Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STCI DATA PIPELINE                           │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  SOURCE  │────▶│ COLLECT  │────▶│  INDEX   │────▶│  SERVE   │
  │          │     │          │     │          │     │          │
  │OpenRouter│     │Normalize │     │ Compute  │     │   API    │
  │   API    │     │ Validate │     │  STCI    │     │  + CDN   │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                │                │                │
       ▼                ▼                ▼                ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │   RAW    │     │   OBS    │     │  INDEX   │     │  CACHE   │
  │ STORAGE  │     │ STORAGE  │     │ STORAGE  │     │ (in-mem) │
  │          │     │          │     │          │     │          │
  │data/raw/ │     │data/obs/ │     │data/idx/ │     │ Optional │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Stage 1: Collection (Daily @ 00:00 UTC)

```python
# Pseudocode: services/collector/pipeline.py

def collect(target_date: date) -> Path:
    """Fetch and store raw data from all sources."""

    # 1. Fetch from OpenRouter
    raw_response = openrouter_source.fetch_raw()

    # 2. Store raw response (immutable archive)
    raw_path = f"data/raw/openrouter/{target_date}.json"
    write_json(raw_path, raw_response)

    # 3. Normalize to observations
    observations = openrouter_source.normalize(raw_response)

    # 4. Validate each observation against schema
    for obs in observations:
        validate(obs, "schemas/observation.schema.json")

    # 5. Store observations (JSONL for append-friendliness)
    obs_path = f"data/observations/{target_date}.jsonl"
    write_jsonl(obs_path, observations)

    return obs_path
```

**Output**: `data/observations/2026-01-01.jsonl`

```jsonl
{"observation_id":"obs-2026-01-01-openrouter-gpt-4o","model_id":"openai/gpt-4o","input_rate":2.50,...}
{"observation_id":"obs-2026-01-01-openrouter-claude-3-5-sonnet","model_id":"anthropic/claude-3.5-sonnet","input_rate":3.00,...}
```

### Stage 2: Indexing (Daily @ 00:30 UTC)

```python
# Pseudocode: services/indexer/pipeline.py

def compute_index(target_date: date) -> Path:
    """Compute STCI indices from observations."""

    # 1. Load observations for date
    obs_path = f"data/observations/{target_date}.jsonl"
    observations = read_jsonl(obs_path)

    # 2. Load methodology config
    methodology = load_yaml("data/fixtures/methodology.yaml")

    # 3. Compute indices
    indexer = Indexer(methodology)
    result = indexer.compute(observations, target_date)

    # 4. Add verification hash
    result["verification_hash"] = compute_hash(observations, methodology)

    # 5. Validate output
    validate(result, "schemas/stci_daily.schema.json")

    # 6. Store index
    idx_path = f"data/indices/{target_date}.json"
    write_json(idx_path, result)

    return idx_path
```

**Output**: `data/indices/2026-01-01.json`

```json
{
  "index_date": "2026-01-01",
  "indices": {
    "STCI-ALL": {"value": 4.25, "model_count": 412},
    "STCI-FRONTIER": {"value": 8.50, "model_count": 12},
    "STCI-EFFICIENT": {"value": 0.85, "model_count": 45}
  },
  "verification_hash": "sha256:abc123...",
  "methodology_version": "1.0.0"
}
```

### Stage 3: Serving (Always-on API)

```python
# Pseudocode: services/api/main.py

# On startup: load recent indices into memory
INDEX_CACHE = {}

def load_index(date: str) -> dict:
    if date in INDEX_CACHE:
        return INDEX_CACHE[date]

    idx_path = f"data/indices/{date}.json"
    if not exists(idx_path):
        raise HTTPException(404, f"No index for {date}")

    INDEX_CACHE[date] = read_json(idx_path)
    return INDEX_CACHE[date]

@app.get("/v1/index/{date}")
def get_index(date: str):
    return load_index(date)

@app.get("/v1/index/latest")
def get_latest():
    latest_date = get_latest_index_date()
    return load_index(latest_date)
```

---

## Storage Format Decisions

### Why JSONL for Observations?

| Format | Pros | Cons |
|--------|------|------|
| JSON array | Simple, one file | Can't append, must rewrite |
| JSONL | Append-friendly, streamable | Multiple lines |
| SQLite | Queryable, indexed | Binary, harder to diff |
| Parquet | Compressed, columnar | Overkill for MVP |

**Decision**: JSONL for observations (append-friendly, human-readable, git-diffable)

### Why JSON for Indices?

Daily index is a single document (~1KB). JSON is:
- Human-readable
- Git-diffable
- Easy to serve directly
- Schema-validatable

### Why Git for Versioning?

- **Audit Trail**: Every change tracked with commit hash
- **Rollback**: Easy revert if bad data published
- **Reproducibility**: Clone repo, run indexer, get same results
- **Cost**: Free (no database infra for MVP)

---

## Directory Structure (Expanded)

```
stci/
├── data/
│   ├── raw/                          # Immutable API responses
│   │   └── openrouter/
│   │       ├── 2026-01-01.json       # Raw response
│   │       ├── 2026-01-02.json
│   │       └── ...
│   ├── observations/                 # Normalized observations
│   │   ├── 2026-01-01.jsonl          # ~400 lines (one per model)
│   │   ├── 2026-01-02.jsonl
│   │   └── ...
│   ├── indices/                      # Computed indices
│   │   ├── 2026-01-01.json           # ~1KB
│   │   ├── 2026-01-02.json
│   │   └── ...
│   └── fixtures/                     # Test data (checked in)
│       ├── observations.sample.json
│       └── methodology.yaml
├── services/
│   ├── collector/                    # Stage 1
│   ├── indexer/                      # Stage 2
│   └── api/                          # Stage 3
└── schemas/
    ├── observation.schema.json
    └── stci_daily.schema.json
```

---

## Automation (Cron/Scheduler)

```bash
# /etc/cron.d/stci (or GitHub Actions workflow)

# Collect at 00:00 UTC daily
0 0 * * * cd /app && python -m services.collector.pipeline

# Index at 00:30 UTC daily (after collection completes)
30 0 * * * cd /app && python -m services.indexer.pipeline

# Optional: Push to git at 01:00 UTC
0 1 * * * cd /app && git add data/ && git commit -m "Daily update $(date +%Y-%m-%d)" && git push
```

---

## Future: Migration to BigQuery

When scale requires it:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Collector   │────▶│   BigQuery   │────▶│   API/CDN    │
│              │     │              │     │              │
│  Cloud Run   │     │ observations │     │  Cloud Run   │
│  (scheduled) │     │ indices      │     │  + Fastly    │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Migration path**:
1. Keep file-based as source of truth
2. Add BigQuery sync as write-through
3. Switch API to read from BigQuery
4. Eventually deprecate file storage (or keep as backup)

**BigQuery tables** (future):

```sql
-- stci.observations
CREATE TABLE observations (
  observation_id STRING,
  observation_date DATE,
  source_id STRING,
  model_id STRING,
  provider STRING,
  input_rate_usd_per_1m FLOAT64,
  output_rate_usd_per_1m FLOAT64,
  collected_at TIMESTAMP
)
PARTITION BY observation_date;

-- stci.indices
CREATE TABLE indices (
  index_date DATE,
  index_name STRING,  -- STCI-ALL, STCI-FRONTIER, STCI-EFFICIENT
  value FLOAT64,
  model_count INT64,
  verification_hash STRING,
  computed_at TIMESTAMP
)
PARTITION BY index_date;
```

---

## Consequences

### Positive

1. **Zero infrastructure cost** for MVP (files + git)
2. **Full audit trail** via git history
3. **Deterministic** - clone and recompute anytime
4. **Human-readable** - debug by reading files
5. **Clear migration path** to BigQuery when needed

### Negative

1. **No real-time queries** - must load files
2. **Git repo size** grows (~500KB/year at current scale)
3. **No concurrent writes** - single collector process assumed

### Mitigations

| Risk | Mitigation |
|------|------------|
| Repo size | Use git-lfs for data/ if exceeds 1GB |
| Query performance | Pre-compute common queries, cache in API |
| Concurrent writes | Use file locking; single scheduled job |

---

## Review Triggers

Revisit this decision if:

1. Data volume exceeds 10,000 observations/day
2. Query latency requirements drop below 100ms
3. Multiple concurrent collectors needed
4. Real-time index updates required

---

*STCI — Standard Token Cost Index*
*Architecture Decision Record*
