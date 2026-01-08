"""
Normalized Usage Schema

Common data structures for usage data across all LLM providers.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ModelUsage:
    """Usage breakdown for a single model."""
    model_id: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: float = 0.0
    request_count: int = 0


@dataclass
class NormalizedUsage:
    """
    Common schema for usage data across providers.

    All provider-specific data is normalized to this format.
    """
    provider: str  # "openai", "anthropic", "google"
    date: str      # YYYY-MM-DD

    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cache_creation_tokens: int = 0

    # Costs
    total_cost_usd: float = 0.0

    # Request counts
    request_count: int = 0

    # Breakdown by model
    by_model: dict[str, ModelUsage] = field(default_factory=dict)

    # Sync metadata
    synced_at: Optional[datetime] = None
    raw_response: Optional[dict] = None  # For debugging

    def to_dict(self) -> dict:
        """Convert to Firestore-compatible dict."""
        return {
            "provider": self.provider,
            "date": self.date,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "total_cost_usd": self.total_cost_usd,
            "request_count": self.request_count,
            "by_model": {
                k: {
                    "model_id": v.model_id,
                    "input_tokens": v.input_tokens,
                    "output_tokens": v.output_tokens,
                    "cached_tokens": v.cached_tokens,
                    "cache_creation_tokens": v.cache_creation_tokens,
                    "cost_usd": v.cost_usd,
                    "request_count": v.request_count,
                }
                for k, v in self.by_model.items()
            },
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }


@dataclass
class UsageSnapshot:
    """
    Daily usage snapshot for an enterprise.

    Stored in: enterprises/{enterprise_id}/usage_snapshots/{date}
    """
    date: str  # YYYY-MM-DD

    # Aggregated totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    total_cost_usd: float = 0.0
    total_request_count: int = 0

    # Computed effective rates ($/1M tokens)
    effective_input_rate: float = 0.0
    effective_output_rate: float = 0.0
    effective_blended_rate: float = 0.0  # 3:1 weighted

    # Benchmark comparison
    stci_frontier_rate: float = 0.0
    discount_vs_market: float = 0.0  # Percentage discount
    percentile_rank: Optional[int] = None  # If opted into benchmarks

    # Optimization metrics
    cache_hit_rate: float = 0.0
    batch_percentage: float = 0.0
    potential_savings_usd: float = 0.0

    # Breakdown by provider
    by_provider: dict[str, NormalizedUsage] = field(default_factory=dict)

    def calculate_rates(self):
        """Calculate effective rates from usage data."""
        if self.total_input_tokens > 0:
            self.effective_input_rate = (
                self.total_cost_usd / self.total_input_tokens * 1_000_000
            )

        if self.total_output_tokens > 0:
            self.effective_output_rate = (
                self.total_cost_usd / self.total_output_tokens * 1_000_000
            )

        # Blended rate: assume 3:1 input:output ratio
        total_blended = self.total_input_tokens + (self.total_output_tokens * 3)
        if total_blended > 0:
            self.effective_blended_rate = (
                self.total_cost_usd / total_blended * 1_000_000
            )

    def calculate_discount(self, stci_frontier_rate: float):
        """Calculate discount vs market rate."""
        self.stci_frontier_rate = stci_frontier_rate
        if stci_frontier_rate > 0 and self.effective_blended_rate > 0:
            self.discount_vs_market = (
                (stci_frontier_rate - self.effective_blended_rate)
                / stci_frontier_rate
            )

    def to_dict(self) -> dict:
        """Convert to Firestore-compatible dict."""
        return {
            "date": self.date,
            "totals": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "cached_tokens": self.total_cached_tokens,
                "cost_usd": self.total_cost_usd,
                "request_count": self.total_request_count,
            },
            "rates": {
                "effective_input_rate": self.effective_input_rate,
                "effective_output_rate": self.effective_output_rate,
                "effective_blended_rate": self.effective_blended_rate,
            },
            "benchmark": {
                "stci_frontier_rate": self.stci_frontier_rate,
                "discount_vs_market": self.discount_vs_market,
                "percentile_rank": self.percentile_rank,
            },
            "optimization": {
                "cache_hit_rate": self.cache_hit_rate,
                "batch_percentage": self.batch_percentage,
                "potential_savings_usd": self.potential_savings_usd,
            },
            "by_provider": {
                k: v.to_dict() for k, v in self.by_provider.items()
            },
        }
