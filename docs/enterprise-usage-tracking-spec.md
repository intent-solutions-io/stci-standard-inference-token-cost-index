# Enterprise Usage Tracking - Product Specification

**Version:** 0.1.0 (Draft)
**Date:** 2026-01-05
**Author:** Intent Solutions IO
**Status:** Research Complete, Awaiting Approval

---

## Executive Summary

Build a secure platform that allows enterprises to connect their LLM provider accounts and receive:
1. Real-time visibility into their effective token rates
2. Comparison against market benchmarks (STCI indices)
3. Optimization recommendations
4. Negotiation leverage for contract renewals

**Unique Value Proposition:** No other pricing site offers personalized enterprise rate benchmarking with actual usage data.

---

## Problem Statement

### Enterprise Pain Points

1. **Opaque Pricing:** Enterprises negotiate custom rates but don't know if they got a good deal
2. **No Benchmarks:** No way to compare their rates against market or peers
3. **Contract Renewals:** No data to support renegotiation leverage
4. **Usage Visibility:** Fragmented views across providers, no unified dashboard
5. **Optimization Gaps:** Don't know if they're using caching/batching optimally

### Market Opportunity

- Enterprise LLM API spend: $10B+ annually (2025)
- Average enterprise discount: 20-40% off rack rates
- Contract lengths: 12-36 months
- Renewal negotiation happens with zero market data

---

## Solution Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE USAGE DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Connected Providers: [OpenAI ✓] [Anthropic ✓] [Google ○]              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  YOUR EFFECTIVE RATE                                             │   │
│  │                                                                   │   │
│  │  $4.82 /1M tokens (blended)                                      │   │
│  │                                                                   │   │
│  │  vs STCI-FRONTIER: $9.18/1M                                      │   │
│  │  YOUR DISCOUNT: 47% below market rack rate                       │   │
│  │                                                                   │   │
│  │  ████████████████████░░░░░░░░░░  Better than 68% of enterprises  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │  THIS MONTH          │  │  OPTIMIZATION        │                    │
│  │                      │  │                      │                    │
│  │  Spend: $47,823      │  │  Cache Hit Rate: 34% │                    │
│  │  Tokens: 892M in     │  │  Batch Usage: 12%    │                    │
│  │          234M out    │  │                      │                    │
│  │                      │  │  Potential Savings:  │                    │
│  │  Trend: ↓ 8% MoM     │  │  $8,400/mo if 50%    │                    │
│  └──────────────────────┘  └──────────────────────┘                    │
│                                                                         │
│  [Export Report]  [Schedule Monthly Email]  [Share with Team]          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                       │
│                     (inferencepriceindex.com)                           │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Dashboard  │  │  Connect    │  │  Reports    │  │  Settings   │   │
│  │  View       │  │  Providers  │  │  Export     │  │  Keys       │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                        │
│                   (Firebase Functions / Cloud Run)                       │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  /connect   │  │  /usage     │  │  /benchmark │  │  /reports   │   │
│  │  OAuth/Keys │  │  Sync Data  │  │  Compare    │  │  Generate   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                          │
│                                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐                       │
│  │  Firestore          │  │  Secret Manager     │                       │
│  │                     │  │                     │                       │
│  │  - enterprises/     │  │  - API keys         │                       │
│  │  - usage_snapshots/ │  │  - Encrypted        │                       │
│  │  - benchmarks/      │  │  - Rotatable        │                       │
│  └─────────────────────┘  └─────────────────────┘                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PROVIDER INTEGRATIONS                                  │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  OpenAI     │  │  Anthropic  │  │  Google     │                      │
│  │  Usage API  │  │  Admin API  │  │  Cloud Mon. │                      │
│  │             │  │             │  │             │                      │
│  │  /v1/org/   │  │  /v1/org/   │  │  metrics    │                      │
│  │  usage/*    │  │  usage_*    │  │  explorer   │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Enterprise connects provider (provides Admin API key)
           │
           ▼
2. Key encrypted and stored in Secret Manager
           │
           ▼
3. Scheduled job fetches usage data (daily)
           │
           ▼
4. Data normalized to common schema
           │
           ▼
5. Metrics computed (effective rate, cache %, etc.)
           │
           ▼
6. Compared against STCI indices and anonymous benchmarks
           │
           ▼
7. Dashboard updated, alerts sent if thresholds crossed
```

---

## Data Schema

### Enterprise Document

```typescript
// Firestore: enterprises/{enterprise_id}
interface Enterprise {
  id: string;
  name: string;
  created_at: Timestamp;
  updated_at: Timestamp;

  // Connected providers
  providers: {
    openai?: {
      connected: boolean;
      key_id: string;  // Reference to Secret Manager
      last_sync: Timestamp;
      org_id?: string;
    };
    anthropic?: {
      connected: boolean;
      key_id: string;
      last_sync: Timestamp;
      org_id?: string;
    };
    google?: {
      connected: boolean;
      project_id: string;
      service_account_key_id: string;
      last_sync: Timestamp;
    };
  };

  // Preferences
  settings: {
    sync_frequency: 'daily' | 'hourly';
    email_reports: boolean;
    report_recipients: string[];
    share_anonymous_benchmarks: boolean;  // Opt-in for percentile
  };

  // Access control
  members: {
    [user_id: string]: {
      email: string;
      role: 'admin' | 'viewer';
      added_at: Timestamp;
    };
  };
}
```

### Usage Snapshot Document

```typescript
// Firestore: enterprises/{enterprise_id}/usage_snapshots/{date}
interface UsageSnapshot {
  date: string;  // YYYY-MM-DD
  created_at: Timestamp;

  // Aggregated metrics
  totals: {
    input_tokens: number;
    output_tokens: number;
    cached_tokens: number;
    total_cost_usd: number;
    request_count: number;
  };

  // Computed rates
  rates: {
    effective_input_rate: number;   // $/1M tokens
    effective_output_rate: number;
    effective_blended_rate: number; // 3:1 weighted
  };

  // Comparison to market
  benchmark: {
    stci_frontier_rate: number;
    discount_vs_market: number;     // Percentage
    percentile_rank?: number;       // If opted in
  };

  // Optimization metrics
  optimization: {
    cache_hit_rate: number;
    batch_percentage: number;
    potential_savings_usd: number;
  };

  // Breakdown by provider
  by_provider: {
    [provider: string]: {
      input_tokens: number;
      output_tokens: number;
      cached_tokens: number;
      cost_usd: number;
      models_used: string[];
    };
  };

  // Breakdown by model
  by_model: {
    [model: string]: {
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
    };
  };
}
```

### Anonymous Benchmark Document

```typescript
// Firestore: benchmarks/{month}
// Aggregated from enterprises with share_anonymous_benchmarks: true
interface MonthlyBenchmark {
  month: string;  // YYYY-MM
  created_at: Timestamp;

  // Percentile distribution of effective rates
  percentiles: {
    p10: number;  // Top 10% get this rate or better
    p25: number;
    p50: number;  // Median
    p75: number;
    p90: number;
  };

  // Aggregate stats
  stats: {
    enterprise_count: number;  // How many contributed
    total_tokens_tracked: number;
    avg_discount_vs_rack: number;
  };

  // By industry (future)
  by_industry?: {
    [industry: string]: {
      count: number;
      p50_rate: number;
    };
  };
}
```

---

## API Endpoints

### Provider Connection

```
POST /api/v1/enterprise/connect/openai
Content-Type: application/json
Authorization: Bearer {user_jwt}

{
  "admin_api_key": "sk-admin-..."
}

Response:
{
  "success": true,
  "org_id": "org-xxx",
  "org_name": "Acme Corp",
  "key_id": "key_xxx",  // Our reference, not the actual key
  "permissions": ["usage:read", "costs:read"]
}
```

```
POST /api/v1/enterprise/connect/anthropic
Content-Type: application/json
Authorization: Bearer {user_jwt}

{
  "admin_api_key": "sk-ant-admin-..."
}

Response:
{
  "success": true,
  "org_id": "org_xxx",
  "org_name": "Acme Corp",
  "key_id": "key_xxx"
}
```

### Usage Data

```
GET /api/v1/enterprise/usage?start=2026-01-01&end=2026-01-31
Authorization: Bearer {user_jwt}

Response:
{
  "period": {
    "start": "2026-01-01",
    "end": "2026-01-31"
  },
  "totals": {
    "input_tokens": 892000000,
    "output_tokens": 234000000,
    "cached_tokens": 156000000,
    "total_cost_usd": 47823.45,
    "request_count": 1247832
  },
  "effective_rates": {
    "input": 3.42,
    "output": 12.18,
    "blended": 4.82
  },
  "benchmark": {
    "stci_frontier_blended": 9.18,
    "your_discount": 0.475,
    "percentile_rank": 68
  },
  "by_provider": [...],
  "by_day": [...],
  "by_model": [...]
}
```

### Benchmarks

```
GET /api/v1/benchmarks/current
Authorization: Bearer {user_jwt}

Response:
{
  "month": "2026-01",
  "enterprise_count": 47,
  "percentiles": {
    "p10": 3.20,
    "p25": 4.50,
    "p50": 6.80,
    "p75": 8.90,
    "p90": 11.20
  },
  "your_position": {
    "rate": 4.82,
    "percentile": 68,
    "better_than": "68% of enterprises"
  }
}
```

---

## Security Requirements

### API Key Handling

1. **Encryption at Rest**
   - All API keys stored in Google Secret Manager
   - Never stored in Firestore or logs
   - Encrypted with Google-managed keys (or customer-managed for enterprise tier)

2. **Encryption in Transit**
   - All API calls over HTTPS
   - TLS 1.3 required

3. **Access Control**
   - Keys only accessed by backend service account
   - No client-side access to keys
   - Audit logging for all key access

4. **Key Rotation**
   - Support for key rotation without disconnecting
   - Alert when key fails (expired/revoked)

### Data Privacy

1. **Benchmark Anonymization**
   - Aggregated data only (no individual enterprise data shared)
   - Minimum 10 enterprises per benchmark bucket
   - k-anonymity compliance

2. **Data Retention**
   - Usage snapshots: 24 months
   - Raw API responses: 7 days (for debugging)
   - Deleted on account closure

3. **Compliance**
   - SOC 2 Type II (roadmap)
   - GDPR compliant (data deletion on request)

---

## Provider Integration Details

### OpenAI Integration

```python
# services/providers/openai_usage.py

import httpx
from datetime import datetime, timedelta

class OpenAIUsageClient:
    BASE_URL = "https://api.openai.com/v1/organization"

    def __init__(self, admin_key: str):
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {admin_key}",
                "Content-Type": "application/json"
            }
        )

    async def get_completions_usage(
        self,
        start_time: datetime,
        end_time: datetime,
        bucket_width: str = "1d",
        group_by: list[str] = ["model"]
    ) -> dict:
        """Fetch completions usage data."""
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "bucket_width": bucket_width,
            "group_by": group_by
        }

        response = await self.client.get(
            f"{self.BASE_URL}/usage/completions",
            params=params
        )
        return response.json()

    async def get_costs(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> dict:
        """Fetch cost breakdown."""
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "bucket_width": "1d"
        }

        response = await self.client.get(
            f"{self.BASE_URL}/costs",
            params=params
        )
        return response.json()

    async def fetch_all_usage(self, date: str) -> NormalizedUsage:
        """Fetch and normalize all usage for a date."""
        start = datetime.fromisoformat(f"{date}T00:00:00Z")
        end = start + timedelta(days=1)

        # Fetch in parallel
        completions, embeddings, costs = await asyncio.gather(
            self.get_completions_usage(start, end),
            self.get_embeddings_usage(start, end),
            self.get_costs(start, end)
        )

        return self._normalize(completions, embeddings, costs)
```

### Anthropic Integration

```python
# services/providers/anthropic_usage.py

class AnthropicUsageClient:
    BASE_URL = "https://api.anthropic.com/v1/organizations"

    def __init__(self, admin_key: str):
        self.client = httpx.Client(
            headers={
                "x-api-key": admin_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
        )

    async def get_usage_report(
        self,
        starting_at: datetime,
        ending_at: datetime,
        bucket_width: str = "1d",
        group_by: list[str] = ["model"]
    ) -> dict:
        """Fetch usage report."""
        params = {
            "starting_at": starting_at.isoformat() + "Z",
            "ending_at": ending_at.isoformat() + "Z",
            "bucket_width": bucket_width,
            "group_by[]": group_by
        }

        response = await self.client.get(
            f"{self.BASE_URL}/usage_report/messages",
            params=params
        )
        return response.json()

    async def get_cost_report(
        self,
        starting_at: datetime,
        ending_at: datetime
    ) -> dict:
        """Fetch cost report."""
        params = {
            "starting_at": starting_at.isoformat() + "Z",
            "ending_at": ending_at.isoformat() + "Z"
        }

        response = await self.client.get(
            f"{self.BASE_URL}/cost_report",
            params=params
        )
        return response.json()
```

### Normalized Usage Schema

```python
# services/providers/schema.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class NormalizedUsage:
    """Common schema for usage data across providers."""

    provider: str  # "openai", "anthropic", "google"
    date: str      # YYYY-MM-DD

    # Token counts
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    cache_creation_tokens: int = 0

    # Costs
    total_cost_usd: float

    # Breakdown by model
    by_model: dict[str, ModelUsage]

    # Raw response (for debugging)
    raw_response: Optional[dict] = None

@dataclass
class ModelUsage:
    model_id: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
```

---

## Sync Scheduler

```python
# services/sync/scheduler.py

from google.cloud import scheduler_v1
from google.cloud import tasks_v2

class UsageSyncScheduler:
    """Schedule daily usage syncs for all enterprises."""

    def __init__(self):
        self.scheduler = scheduler_v1.CloudSchedulerClient()
        self.tasks = tasks_v2.CloudTasksClient()

    async def create_daily_job(self, enterprise_id: str):
        """Create a daily sync job for an enterprise."""
        job = {
            "name": f"projects/{PROJECT}/locations/{LOCATION}/jobs/sync-{enterprise_id}",
            "schedule": "0 2 * * *",  # 2 AM UTC daily
            "time_zone": "UTC",
            "http_target": {
                "uri": f"{API_URL}/internal/sync/{enterprise_id}",
                "http_method": "POST",
                "oidc_token": {
                    "service_account_email": SERVICE_ACCOUNT
                }
            }
        }

        self.scheduler.create_job(parent=PARENT, job=job)

    async def trigger_sync(self, enterprise_id: str, date: str):
        """Manually trigger a sync for a specific date."""
        task = {
            "http_request": {
                "http_method": "POST",
                "url": f"{API_URL}/internal/sync/{enterprise_id}",
                "body": json.dumps({"date": date}).encode(),
                "headers": {"Content-Type": "application/json"}
            }
        }

        self.tasks.create_task(parent=QUEUE, task=task)
```

---

## UI Components

### Connect Provider Flow

```
Step 1: Select Provider
┌─────────────────────────────────────────────────────────────────┐
│  Connect Your LLM Provider                                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   OpenAI    │  │  Anthropic  │  │   Google    │              │
│  │     ○       │  │     ○       │  │     ○       │              │
│  │  [Connect]  │  │  [Connect]  │  │  [Connect]  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘

Step 2: Enter API Key
┌─────────────────────────────────────────────────────────────────┐
│  Connect OpenAI                                                  │
│                                                                  │
│  Enter your Admin API Key:                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ sk-admin-xxxxxxxxxxxxxxxxxxxx                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ℹ️ We only read usage data. Your key is encrypted and never    │
│     stored in plain text. [Learn more about security]           │
│                                                                  │
│  How to get an Admin API Key:                                   │
│  1. Go to platform.openai.com/settings/organization             │
│  2. Navigate to API Keys → Admin Keys                           │
│  3. Create a new key with "Usage Read" permissions              │
│                                                                  │
│  [Cancel]                                    [Connect Provider]  │
└─────────────────────────────────────────────────────────────────┘

Step 3: Confirm Connection
┌─────────────────────────────────────────────────────────────────┐
│  ✓ Connected Successfully                                       │
│                                                                  │
│  Organization: Acme Corp                                         │
│  Permissions: Usage Read, Costs Read                            │
│                                                                  │
│  We're now syncing your usage data. This may take a few minutes.│
│                                                                  │
│  [View Dashboard]                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Dashboard Components

```
┌─────────────────────────────────────────────────────────────────┐
│  Effective Rate Card                                             │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  YOUR RATE           MARKET RATE          YOUR SAVINGS          │
│  $4.82/1M            $9.18/1M             47%                   │
│  ████████░░          ██████████████░░     below market          │
│                                                                  │
│  [i] Based on 892M tokens processed this month                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Percentile Ranking (anonymous benchmark)                        │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  Your rate is better than 68% of enterprises                    │
│                                                                  │
│  ░░░░░░░░░░░░░░░░░░░░████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  p10    p25    p50    YOU    p75    p90                         │
│  $3.20  $4.50  $6.80  $4.82  $8.90  $11.20                      │
│                                                                  │
│  [i] Based on 47 enterprises sharing anonymous data              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Optimization Opportunities                                      │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  ⚡ Cache Hit Rate: 34%                                          │
│     Increase to 50% → Save $2,800/mo                            │
│     [How to improve caching]                                     │
│                                                                  │
│  📦 Batch Usage: 12%                                             │
│     Increase to 30% → Save $5,600/mo                            │
│     [Learn about batch API]                                      │
│                                                                  │
│  🔄 Model Mix Optimization                                       │
│     Switch 40% of GPT-4 calls to GPT-4o-mini → Save $8,200/mo   │
│     [View model analysis]                                        │
│                                                                  │
│  TOTAL POTENTIAL SAVINGS: $16,600/mo                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

| Task | Priority | Effort |
|------|----------|--------|
| Firestore schema setup | P0 | 1 day |
| Secret Manager integration | P0 | 1 day |
| OpenAI usage client | P0 | 2 days |
| Anthropic usage client | P0 | 2 days |
| Data normalization layer | P0 | 1 day |
| Basic sync scheduler | P0 | 1 day |

**Deliverable:** Backend can connect to providers and fetch usage data.

### Phase 2: Core Dashboard (Week 2-3)

| Task | Priority | Effort |
|------|----------|--------|
| Provider connection UI | P0 | 2 days |
| Effective rate calculation | P0 | 1 day |
| Dashboard layout | P0 | 2 days |
| Usage charts (by day, model) | P1 | 2 days |
| STCI comparison | P0 | 1 day |

**Deliverable:** Enterprises can connect and see their effective rates.

### Phase 3: Benchmarking (Week 3-4)

| Task | Priority | Effort |
|------|----------|--------|
| Anonymous data aggregation | P1 | 2 days |
| Percentile calculation | P1 | 1 day |
| Benchmark UI component | P1 | 1 day |
| Opt-in flow | P1 | 1 day |

**Deliverable:** Enterprises can see how they rank against peers.

### Phase 4: Optimization (Week 4-5)

| Task | Priority | Effort |
|------|----------|--------|
| Cache efficiency analysis | P2 | 2 days |
| Batch usage analysis | P2 | 1 day |
| Model mix recommendations | P2 | 2 days |
| Savings calculator | P2 | 1 day |

**Deliverable:** Enterprises get actionable optimization recommendations.

### Phase 5: Polish (Week 5-6)

| Task | Priority | Effort |
|------|----------|--------|
| Email reports | P2 | 2 days |
| Export (PDF/CSV) | P2 | 1 day |
| Multi-user access | P2 | 2 days |
| Mobile responsive | P1 | 1 day |
| Documentation | P1 | 1 day |

**Deliverable:** Production-ready enterprise dashboard.

---

## Success Metrics

| Metric | Target (90 days) |
|--------|------------------|
| Enterprises connected | 25 |
| Monthly active users | 100 |
| Tokens tracked | 10B+ |
| Benchmark opt-in rate | 60% |
| NPS score | >50 |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Provider API changes | Medium | High | Abstract provider layer, version pin |
| Key security breach | Low | Critical | Secret Manager, audit logs, alerts |
| Low adoption | Medium | High | Free tier, case studies, outreach |
| Rate limiting | Medium | Medium | Backoff, caching, batch requests |
| Data accuracy disputes | Low | Medium | Show raw data, audit trail |

---

## Open Questions

1. **Pricing model?**
   - Free tier (1 provider, 30 days history)?
   - Pro tier ($X/month for all providers, 12 months)?
   - Enterprise tier (custom, on-prem deployment)?

2. **Google Vertex integration?**
   - More complex (GCP IAM)
   - Different auth model (service account)
   - Worth the effort for MVP?

3. **Historical data import?**
   - How far back can we pull? (OpenAI: 90 days, Anthropic: ?)
   - One-time backfill on connection?

4. **Multi-org support?**
   - Enterprises with multiple OpenAI orgs?
   - Consolidated view vs separate?

---

## Appendix: API Response Examples

### OpenAI Usage Response

```json
{
  "object": "page",
  "data": [
    {
      "start_time": 1704067200,
      "end_time": 1704153600,
      "results": [
        {
          "object": "bucket",
          "model": "gpt-4o",
          "input_tokens": 15234567,
          "output_tokens": 4523456,
          "num_model_requests": 45678,
          "project_id": "proj_xxx"
        }
      ]
    }
  ],
  "has_more": false
}
```

### Anthropic Usage Response

```json
{
  "data": [
    {
      "bucket_start_time": "2026-01-01T00:00:00Z",
      "bucket_end_time": "2026-01-02T00:00:00Z",
      "model": "claude-sonnet-4-5-20250929",
      "input_tokens": 8923456,
      "output_tokens": 2345678,
      "cached_input_tokens": 1234567,
      "cache_creation_input_tokens": 456789,
      "message_count": 34567,
      "workspace_id": "wrkspc_xxx"
    }
  ],
  "has_more": false
}
```

---

**Document Status:** Draft for review
**Next Steps:** Stakeholder approval → Phase 1 kickoff

---

*intent solutions io — confidential*
*Contact: jeremy@intentsolutions.io*
