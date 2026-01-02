# STCI Observation Schema Specification

**Document ID:** 003
**Category:** AT (Architecture & Technical)
**Type:** SPEC (Specification)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01
**Schema Version:** 1.0.0

---

## Overview

This specification defines the canonical schema for **pricing observations** collected by STCI. An observation represents a single pricing data point for a specific model at a specific time.

---

## 1. Observation Schema

### 1.1 Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `observation_id` | string | Yes | Unique identifier (format: `obs-{date}-{provider}-{model}`) |
| `schema_version` | string | Yes | Schema version (semver) |
| `provider` | string | Yes | Provider identifier (lowercase, no spaces) |
| `model_id` | string | Yes | Provider's model identifier |
| `model_display_name` | string | Yes | Human-readable model name |
| `input_rate_usd_per_1m` | number | Yes | USD per 1 million input tokens |
| `output_rate_usd_per_1m` | number | Yes | USD per 1 million output tokens |
| `effective_date` | string (date) | Yes | Date pricing is effective (ISO 8601) |
| `collected_at` | string (datetime) | Yes | Collection timestamp (ISO 8601 UTC) |
| `source_url` | string (uri) | Yes | Source URL for pricing |
| `source_tier` | string (enum) | Yes | Data quality tier (T1-T4) |
| `currency` | string | Yes | Currency code (must be "USD") |

### 1.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `context_window` | integer | Maximum context window (tokens) |
| `max_output_tokens` | integer | Maximum output tokens per request |
| `batch_rate_input` | number | Batch API input rate (if different) |
| `batch_rate_output` | number | Batch API output rate (if different) |
| `cached_rate_input` | number | Cached/prompt-caching input rate |
| `free_tier_tokens` | integer | Free tier allocation per month |
| `rate_limit_rpm` | integer | Requests per minute limit |
| `rate_limit_tpm` | integer | Tokens per minute limit |
| `notes` | string | Additional notes |
| `collector_id` | string | Collector module that produced this observation |
| `raw_data` | object | Original unparsed data (for debugging) |

### 1.3 Provenance Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_method` | string (enum) | Yes | How data was collected |
| `confidence_level` | string (enum) | No | Data confidence (high/medium/low) |
| `verified_at` | string (datetime) | No | Manual verification timestamp |
| `verified_by` | string | No | Verifier identifier |

---

## 2. Enumerations

### 2.1 Source Tier (`source_tier`)

| Value | Description | Confidence |
|-------|-------------|------------|
| `T1` | Official provider pricing page | Highest |
| `T2` | Official provider API | High |
| `T3` | Aggregator pricing (verified) | Medium |
| `T4` | Community-reported | Lower |

### 2.2 Collection Method (`collection_method`)

| Value | Description |
|-------|-------------|
| `manual` | Human data entry |
| `scrape` | Automated web scraping |
| `api` | Provider API call |
| `aggregator_api` | Aggregator API call |
| `fixture` | Test fixture data |

### 2.3 Confidence Level (`confidence_level`)

| Value | Criteria |
|-------|----------|
| `high` | Direct from provider, verified |
| `medium` | Aggregator or unverified |
| `low` | Community-reported or stale |

---

## 3. Provider Identifiers

Standard provider IDs (lowercase, no spaces):

| Provider ID | Display Name |
|-------------|--------------|
| `openai` | OpenAI |
| `anthropic` | Anthropic |
| `google` | Google (Vertex AI) |
| `google-aistudio` | Google AI Studio |
| `aws-bedrock` | AWS Bedrock |
| `azure-openai` | Azure OpenAI |
| `cohere` | Cohere |
| `mistral` | Mistral AI |
| `fireworks` | Fireworks AI |
| `together` | Together AI |
| `replicate` | Replicate |
| `groq` | Groq |
| `deepseek` | DeepSeek |
| `perplexity` | Perplexity AI |

---

## 4. Validation Rules

### 4.1 Required Field Validation
- All required fields must be present
- `observation_id` must be unique
- `schema_version` must be valid semver

### 4.2 Rate Validation
- `input_rate_usd_per_1m` >= 0
- `output_rate_usd_per_1m` >= 0
- Rates should be reasonable (flag if >$100/1M tokens)

### 4.3 Date Validation
- `effective_date` <= `collected_at`
- `effective_date` <= today
- `collected_at` must be valid ISO 8601 UTC

### 4.4 Source Validation
- `source_url` must be valid URI
- `source_tier` must match collection method appropriateness

---

## 5. Example Observations

### 5.1 T1 Provider Observation
```json
{
  "observation_id": "obs-2026-01-01-openai-gpt4o",
  "schema_version": "1.0.0",
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
  "collection_method": "manual",
  "confidence_level": "high",
  "context_window": 128000,
  "max_output_tokens": 16384
}
```

### 5.2 T3 Aggregator Observation
```json
{
  "observation_id": "obs-2026-01-01-openrouter-claude35sonnet",
  "schema_version": "1.0.0",
  "provider": "openrouter",
  "model_id": "anthropic/claude-3.5-sonnet",
  "model_display_name": "Claude 3.5 Sonnet (via OpenRouter)",
  "input_rate_usd_per_1m": 3.00,
  "output_rate_usd_per_1m": 15.00,
  "effective_date": "2026-01-01",
  "collected_at": "2026-01-01T14:30:00Z",
  "source_url": "https://openrouter.ai/models",
  "source_tier": "T3",
  "currency": "USD",
  "collection_method": "scrape",
  "confidence_level": "medium",
  "notes": "Aggregator rate includes OpenRouter margin"
}
```

---

## 6. Schema Evolution

### 6.1 Versioning
- Schema uses semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes (field removal, type change)
- MINOR: Backward-compatible additions (new optional fields)
- PATCH: Documentation or validation rule updates

### 6.2 Migration Policy
- All observations include `schema_version`
- Readers must handle older schema versions
- Migration scripts provided for major version changes

---

## 7. JSON Schema Reference

See: `schemas/observation.schema.json`

---

## References

- 001-PP-PROD-stci-prd.md
- 004-AT-SPEC-stci-methodology.md
- schemas/observation.schema.json

---

*STCI — Standard Token Cost Index*
*Schema Version: 1.0.0*
