"""
STCI Data Sources - Implementations for fetching pricing data.
"""

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

# Requests import is optional - graceful fallback if not installed
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class BaseSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def fetch(self, target_date: date) -> List[dict]:
        """
        Fetch observations for a given date.

        Args:
            target_date: Date to fetch data for

        Returns:
            List of observation dictionaries
        """
        pass

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Return source identifier."""
        pass

    @property
    @abstractmethod
    def source_tier(self) -> str:
        """Return source tier (T1-T4)."""
        pass


class OpenRouterSource(BaseSource):
    """
    OpenRouter API source.

    Fetches model pricing from OpenRouter's public models endpoint.
    See: https://openrouter.ai/docs/api/api-reference/models/get-models
    """

    API_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or self.API_URL

    @property
    def source_id(self) -> str:
        return "openrouter"

    @property
    def source_tier(self) -> str:
        return "T1"

    def fetch(self, target_date: date) -> List[dict]:
        """
        Fetch pricing data from OpenRouter API.

        Args:
            target_date: Date for the observation

        Returns:
            List of normalized observation dictionaries
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for OpenRouter source")

        response = requests.get(self.api_url, timeout=30)
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        observations = []
        collected_at = datetime.utcnow().isoformat() + "Z"

        for model in models:
            pricing = model.get("pricing", {})

            # Skip models without pricing
            prompt_rate = pricing.get("prompt")
            completion_rate = pricing.get("completion")

            if prompt_rate is None or completion_rate is None:
                continue

            # Convert from $/token to $/1M tokens
            try:
                input_rate = float(prompt_rate) * 1_000_000
                output_rate = float(completion_rate) * 1_000_000
            except (ValueError, TypeError):
                continue

            # Skip free models (rate = 0)
            if input_rate == 0 and output_rate == 0:
                continue

            model_id = model.get("id", "")
            provider = model_id.split("/")[0] if "/" in model_id else "unknown"

            obs = {
                "observation_id": f"obs-{target_date.isoformat()}-{model_id.replace('/', '-')}",
                "schema_version": "1.0.0",
                "provider": provider,
                "model_id": model_id,
                "model_display_name": model.get("name", model_id),
                "input_rate_usd_per_1m": round(input_rate, 6),
                "output_rate_usd_per_1m": round(output_rate, 6),
                "effective_date": target_date.isoformat(),
                "collected_at": collected_at,
                "source_url": self.api_url,
                "source_tier": self.source_tier,
                "currency": "USD",
                "collection_method": "aggregator_api",
                "confidence_level": "high",
            }

            # Add optional fields if available
            if context_length := model.get("context_length"):
                obs["context_window"] = context_length

            observations.append(obs)

        return observations


class FixtureSource(BaseSource):
    """
    Fixture data source for testing and fallback.

    Loads observations from local JSON fixtures.
    """

    def __init__(self, fixture_path: Optional[Path] = None):
        if fixture_path is None:
            # Default to project fixtures directory
            self.fixture_path = (
                Path(__file__).parent.parent.parent
                / "data"
                / "fixtures"
                / "observations.sample.json"
            )
        else:
            self.fixture_path = Path(fixture_path)

    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def source_tier(self) -> str:
        return "T4"  # Lowest tier - fixture data

    def fetch(self, target_date: date) -> List[dict]:
        """
        Load observations from fixture file.

        Args:
            target_date: Date for the observations (updates effective_date)

        Returns:
            List of observation dictionaries with updated dates
        """
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.fixture_path}")

        with open(self.fixture_path) as f:
            observations = json.load(f)

        # Update dates in fixtures
        collected_at = datetime.utcnow().isoformat() + "Z"
        for obs in observations:
            obs["effective_date"] = target_date.isoformat()
            obs["collected_at"] = collected_at
            # Update observation_id to reflect date
            model_id = obs.get("model_id", "unknown").replace("/", "-")
            obs["observation_id"] = f"obs-{target_date.isoformat()}-{obs['provider']}-{model_id}"

        return observations
