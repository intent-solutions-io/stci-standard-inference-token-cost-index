# STCI Source Universe Research Plan

**Document ID:** 006
**Category:** RL (Research & Learning)
**Type:** RSRC (Research)
**Status:** DRAFT
**Owner:** STCI Project Team
**Created:** 2026-01-01

---

## Purpose

This document inventories the **source universe** for STCI pricing data: all known LLM providers and aggregators with published pricing that could be included in the index.

---

## 1. Source Categories

### 1.1 Direct Providers (T1 Sources)

Organizations that offer their own models via API with published pricing.

### 1.2 Cloud Marketplaces (T2 Sources)

Cloud providers offering third-party models with distinct pricing.

### 1.3 Aggregators (T3 Sources)

Services that route requests to multiple providers with unified pricing.

### 1.4 Community Sources (T4 Sources)

User-reported pricing, forums, comparison sites.

---

## 2. Provider Inventory

### 2.1 Tier 1: Major Direct Providers

| Provider | Priority | Pricing URL | Update Frequency | Models |
|----------|----------|-------------|------------------|--------|
| OpenAI | P0 | openai.com/pricing | Ad-hoc | GPT-4o, GPT-4o-mini, o1, o1-mini |
| Anthropic | P0 | anthropic.com/pricing | Ad-hoc | Claude 3.5 Sonnet, Haiku, Opus |
| Google (Vertex) | P0 | cloud.google.com/vertex-ai/pricing | Ad-hoc | Gemini 1.5 Pro, Flash |
| Google (AI Studio) | P0 | ai.google.dev/pricing | Ad-hoc | Gemini 1.5 Pro, Flash |
| Mistral | P1 | mistral.ai/pricing | Ad-hoc | Mistral Large, Small, Nemo |
| Cohere | P1 | cohere.com/pricing | Ad-hoc | Command R, Command R+ |
| DeepSeek | P1 | platform.deepseek.com/pricing | Ad-hoc | DeepSeek V3, V2.5 |

### 2.2 Tier 2: Cloud Marketplaces

| Provider | Priority | Pricing URL | Notes |
|----------|----------|-------------|-------|
| AWS Bedrock | P0 | aws.amazon.com/bedrock/pricing | Multiple models, regional pricing |
| Azure OpenAI | P0 | azure.microsoft.com/pricing/details/cognitive-services/openai-service | OpenAI models with Azure markup |
| GCP Vertex | P0 | (same as Google above) | Unified with Vertex AI |

### 2.3 Tier 3: Aggregators

| Aggregator | Priority | Pricing URL | Notes |
|------------|----------|-------------|-------|
| OpenRouter | P1 | openrouter.ai/models | Large model catalog, unified pricing |
| Together AI | P1 | together.ai/pricing | Focus on open-weight models |
| Fireworks AI | P1 | fireworks.ai/pricing | Fast inference, open-weight focus |
| Replicate | P2 | replicate.com/pricing | Pay-per-second, complex pricing |
| Groq | P2 | groq.com/pricing | Fast inference, limited models |
| Perplexity | P2 | perplexity.ai/pro | Bundled subscription model |
| Anyscale | P2 | anyscale.com/endpoints | Open-weight hosting |

### 2.4 Tier 4: Community Sources

| Source | Use Case |
|--------|----------|
| LLMAP.io | Aggregated comparison data |
| Artificial Analysis | Benchmark + pricing data |
| Reddit r/LocalLLaMA | Community-reported prices |
| GitHub pricing repos | Historical tracking |

---

## 3. Prioritization Matrix

### 3.1 Priority Criteria

| Factor | Weight | Description |
|--------|--------|-------------|
| Market share | 40% | Estimated % of LLM API traffic |
| Data quality | 30% | Pricing clarity, update consistency |
| Model importance | 20% | Flagship/frontier models |
| Ease of collection | 10% | Scraping complexity |

### 3.2 MVP Priority (P0 Sources)

1. **OpenAI** - Market leader, clear pricing page
2. **Anthropic** - Major competitor, clear pricing
3. **Google (Vertex/AI Studio)** - Growing share, two pricing pages
4. **AWS Bedrock** - Enterprise market, API-accessible pricing
5. **Azure OpenAI** - Enterprise market, structured pricing

### 3.3 Phase 2 Priority (P1 Sources)

6. **Mistral** - Growing European provider
7. **Cohere** - Enterprise focus
8. **OpenRouter** - Aggregator with comprehensive catalog
9. **Together AI** - Open-weight leader
10. **Fireworks AI** - Performance-focused

---

## 4. Source Characteristics

### 4.1 Pricing Page Analysis

| Provider | Format | Machine-Readable | Rate Limits | Update Notice |
|----------|--------|------------------|-------------|---------------|
| OpenAI | HTML table | No | No | No |
| Anthropic | HTML table | No | No | No |
| Google | HTML + JSON | Partial | Yes | No |
| AWS | HTML + API | Yes (API) | No | No |
| Azure | HTML + calculator | Partial | No | No |
| OpenRouter | JSON API | Yes | Yes | Yes |

### 4.2 Pricing Structures

| Provider | Input/Output Split | Batch Pricing | Caching | Tiers |
|----------|-------------------|---------------|---------|-------|
| OpenAI | Yes | Yes | Yes (prompt caching) | No |
| Anthropic | Yes | Yes | Yes | No |
| Google | Yes | No | Yes | No |
| AWS | Yes | No | No | No |
| OpenRouter | Yes | No | No | No |

---

## 5. Data Collection Strategy

### 5.1 T1 Collection (Provider Pages)

**Method:** Web scraping with fallback to manual
**Frequency:** Daily check, update on change
**Validation:** Cross-reference with API responses

### 5.2 T2 Collection (Cloud APIs)

**Method:** Provider pricing APIs where available
**Frequency:** Daily
**Validation:** Compare to web pricing pages

### 5.3 T3 Collection (Aggregators)

**Method:** Aggregator APIs (e.g., OpenRouter /models endpoint)
**Frequency:** Hourly (aggregators update frequently)
**Validation:** Cross-reference with direct provider

---

## 6. Gap Analysis

### 6.1 Missing from MVP

| Gap | Impact | Mitigation |
|-----|--------|------------|
| Chinese providers (Alibaba, Baidu) | Low (Western focus) | Phase 3 addition |
| Self-hosted open weights | Medium | Community tier data |
| Per-request pricing models | Low | Out of scope |

### 6.2 Data Quality Gaps

| Issue | Affected Providers | Mitigation |
|-------|-------------------|------------|
| Regional pricing variations | AWS, Azure, GCP | Default to US pricing |
| Volume discounts | Most enterprise | Use published list price |
| Currency variations | Non-US providers | Convert to USD |

---

## 7. Research Tasks

### 7.1 Immediate (Week 1)

- [ ] Catalog all P0 provider pricing URLs
- [ ] Document pricing page structure for each P0
- [ ] Identify machine-readable data sources
- [ ] Create source profile template

### 7.2 Short-term (Week 2-4)

- [ ] Build collector stubs for P0 sources
- [ ] Validate cross-source consistency
- [ ] Document change detection approach
- [ ] Create monitoring dashboard

### 7.3 Medium-term (Month 2-3)

- [ ] Add P1 sources
- [ ] Implement historical backfill
- [ ] Automate daily collection
- [ ] Build anomaly detection

---

## 8. Open Questions

- [ ] How to handle regional pricing (Bedrock has region-specific rates)?
- [ ] Include batch/async pricing as separate observations?
- [ ] How to weight aggregator pricing vs direct?
- [ ] Include volume discount tiers?

---

## References

- 001-PP-PROD-stci-prd.md
- 009-DR-TMPL-source-profile-template.md

---

*STCI — Standard Token Cost Index*
*Research Status: IN PROGRESS*
