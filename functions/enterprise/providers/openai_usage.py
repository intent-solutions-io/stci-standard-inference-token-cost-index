"""
OpenAI Usage API Client

Fetches usage and cost data from OpenAI's organization API.
Requires an Admin API key with usage:read permissions.

API Docs: https://platform.openai.com/docs/api-reference/usage
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..schema import NormalizedUsage, ModelUsage

logger = logging.getLogger(__name__)


class OpenAIUsageClient:
    """
    Client for OpenAI's Usage API.

    Uses the organization-level endpoints:
    - /v1/organization/usage/completions
    - /v1/organization/usage/embeddings
    - /v1/organization/costs
    """

    BASE_URL = "https://api.openai.com/v1/organization"

    def __init__(self, admin_key: str):
        """
        Initialize with an OpenAI Admin API key.

        Args:
            admin_key: OpenAI admin key (starts with sk-admin-...)
        """
        self.admin_key = admin_key
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-load the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers={
                    "Authorization": f"Bearer {self.admin_key}",
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

    def get_completions_usage(
        self,
        start_time: datetime,
        end_time: datetime,
        bucket_width: str = "1d",
        group_by: Optional[list[str]] = None,
    ) -> dict:
        """
        Fetch completions usage data.

        Args:
            start_time: Start of the time range
            end_time: End of the time range
            bucket_width: Aggregation bucket (1m, 1h, 1d)
            group_by: Fields to group by (model, project_id, user_id, api_key_id)

        Returns:
            Raw API response dict
        """
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "bucket_width": bucket_width,
        }
        if group_by:
            params["group_by"] = group_by

        response = self.client.get(
            f"{self.BASE_URL}/usage/completions",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_embeddings_usage(
        self,
        start_time: datetime,
        end_time: datetime,
        bucket_width: str = "1d",
    ) -> dict:
        """Fetch embeddings usage data."""
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "bucket_width": bucket_width,
        }

        response = self.client.get(
            f"{self.BASE_URL}/usage/embeddings",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_costs(
        self,
        start_time: datetime,
        end_time: datetime,
        bucket_width: str = "1d",
    ) -> dict:
        """
        Fetch cost breakdown.

        Returns costs in cents, organized by line item.
        """
        params = {
            "start_time": int(start_time.timestamp()),
            "end_time": int(end_time.timestamp()),
            "bucket_width": bucket_width,
        }

        response = self.client.get(
            f"{self.BASE_URL}/costs",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def validate_key(self) -> dict:
        """
        Validate the API key by fetching minimal data.

        Returns organization info if valid, raises on failure.
        """
        # Try to fetch today's usage - minimal request
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            self.get_completions_usage(start, now, bucket_width="1d")
            return {"valid": True, "provider": "openai"}
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

        # Fetch completions with model grouping
        completions = self.get_completions_usage(
            start, end,
            bucket_width="1d",
            group_by=["model"]
        )

        # Fetch costs
        costs = self.get_costs(start, end, bucket_width="1d")

        return self._normalize(date, completions, costs)

    def _normalize(
        self,
        date: str,
        completions: dict,
        costs: dict,
    ) -> NormalizedUsage:
        """Normalize OpenAI response to common schema."""
        usage = NormalizedUsage(
            provider="openai",
            date=date,
            synced_at=datetime.utcnow(),
        )

        # Process completions data
        for bucket in completions.get("data", []):
            for result in bucket.get("results", []):
                model = result.get("model", "unknown")
                input_tokens = result.get("input_tokens", 0)
                output_tokens = result.get("output_tokens", 0)
                cached = result.get("input_cached_tokens", 0)
                requests = result.get("num_model_requests", 0)

                usage.input_tokens += input_tokens
                usage.output_tokens += output_tokens
                usage.cached_tokens += cached
                usage.request_count += requests

                # Add to model breakdown
                if model not in usage.by_model:
                    usage.by_model[model] = ModelUsage(model_id=model)

                usage.by_model[model].input_tokens += input_tokens
                usage.by_model[model].output_tokens += output_tokens
                usage.by_model[model].cached_tokens += cached
                usage.by_model[model].request_count += requests

        # Process costs data
        total_cost_cents = 0
        for bucket in costs.get("data", []):
            for result in bucket.get("results", []):
                amount = result.get("amount", {})
                cost_cents = amount.get("value", 0)
                total_cost_cents += cost_cents

        usage.total_cost_usd = total_cost_cents / 100.0

        # Store raw response for debugging
        usage.raw_response = {
            "completions": completions,
            "costs": costs,
        }

        return usage
