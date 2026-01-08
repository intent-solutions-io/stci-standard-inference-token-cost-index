"""
Anthropic Usage API Client

Fetches usage and cost data from Anthropic's Admin API.
Requires an Admin API key (starts with sk-ant-admin-...).

API Docs: https://docs.anthropic.com/en/api/admin-api
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..schema import NormalizedUsage, ModelUsage

logger = logging.getLogger(__name__)


class AnthropicUsageClient:
    """
    Client for Anthropic's Admin API.

    Uses the organization-level endpoints:
    - /v1/organizations/usage_report/messages
    - /v1/organizations/cost_report
    """

    BASE_URL = "https://api.anthropic.com/v1/organizations"

    def __init__(self, admin_key: str):
        """
        Initialize with an Anthropic Admin API key.

        Args:
            admin_key: Anthropic admin key (starts with sk-ant-admin-...)
        """
        self.admin_key = admin_key
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-load the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers={
                    "x-api-key": self.admin_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def get_usage_report(
        self,
        starting_at: datetime,
        ending_at: datetime,
        bucket_width: str = "1d",
        group_by: Optional[list[str]] = None,
    ) -> dict:
        """
        Fetch usage report for messages.

        Args:
            starting_at: Start of the time range (ISO 8601)
            ending_at: End of the time range (ISO 8601)
            bucket_width: Aggregation bucket (1m, 1h, 1d)
            group_by: Fields to group by (model, workspace_id, api_key_id)

        Returns:
            Raw API response dict
        """
        params = {
            "starting_at": starting_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ending_at": ending_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bucket_width": bucket_width,
        }
        if group_by:
            # Anthropic uses array syntax for group_by
            for field in group_by:
                params[f"group_by[]"] = field

        response = self.client.get(
            f"{self.BASE_URL}/usage_report/messages",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_cost_report(
        self,
        starting_at: datetime,
        ending_at: datetime,
    ) -> dict:
        """
        Fetch cost report.

        Returns costs organized by workspace.
        """
        params = {
            "starting_at": starting_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ending_at": ending_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        response = self.client.get(
            f"{self.BASE_URL}/cost_report",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def validate_key(self) -> dict:
        """
        Validate the API key by fetching minimal data.

        Returns organization info if valid, raises on failure.
        """
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            self.get_usage_report(start, now, bucket_width="1d")
            return {"valid": True, "provider": "anthropic"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"valid": False, "error": "Invalid API key"}
            elif e.response.status_code == 403:
                return {"valid": False, "error": "Insufficient permissions"}
            raise

    def fetch_daily_usage(self, date: str) -> NormalizedUsage:
        """
        Fetch and normalize all usage for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            NormalizedUsage with aggregated data
        """
        start = datetime.fromisoformat(f"{date}T00:00:00")
        end = start + timedelta(days=1)

        # Fetch usage with model grouping
        usage_report = self.get_usage_report(
            start, end,
            bucket_width="1d",
            group_by=["model"]
        )

        # Fetch costs
        cost_report = self.get_cost_report(start, end)

        return self._normalize(date, usage_report, cost_report)

    def _normalize(
        self,
        date: str,
        usage_report: dict,
        cost_report: dict,
    ) -> NormalizedUsage:
        """Normalize Anthropic response to common schema."""
        usage = NormalizedUsage(
            provider="anthropic",
            date=date,
            synced_at=datetime.utcnow(),
        )

        # Process usage data
        for bucket in usage_report.get("data", []):
            model = bucket.get("model", "unknown")
            input_tokens = bucket.get("input_tokens", 0)
            output_tokens = bucket.get("output_tokens", 0)
            cached_input = bucket.get("cached_input_tokens", 0)
            cache_creation = bucket.get("cache_creation_input_tokens", 0)
            requests = bucket.get("message_count", 0)

            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.cached_tokens += cached_input
            usage.cache_creation_tokens += cache_creation
            usage.request_count += requests

            # Add to model breakdown
            if model not in usage.by_model:
                usage.by_model[model] = ModelUsage(model_id=model)

            usage.by_model[model].input_tokens += input_tokens
            usage.by_model[model].output_tokens += output_tokens
            usage.by_model[model].cached_tokens += cached_input
            usage.by_model[model].cache_creation_tokens += cache_creation
            usage.by_model[model].request_count += requests

        # Process cost data
        # Anthropic returns costs as a total
        total_cost = 0.0
        for item in cost_report.get("data", []):
            total_cost += item.get("cost_usd", 0.0)

        usage.total_cost_usd = total_cost

        # Store raw response for debugging
        usage.raw_response = {
            "usage_report": usage_report,
            "cost_report": cost_report,
        }

        return usage
