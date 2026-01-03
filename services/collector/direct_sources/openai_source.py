"""
OpenAI Direct Source - Official pricing from config file.
"""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml

from services.collector.sources import BaseSource


class OpenAIDirectSource(BaseSource):
    """
    Load OpenAI pricing from local config file.

    Since OpenAI doesn't provide a public pricing API, we maintain
    a YAML config with manually verified pricing from openai.com/api/pricing/
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            self.config_path = (
                Path(__file__).parent.parent.parent.parent
                / "data"
                / "fixtures"
                / "openai_pricing.yaml"
            )
        else:
            self.config_path = Path(config_path)

        self._config = None

    @property
    def source_id(self) -> str:
        return "openai_direct"

    @property
    def source_tier(self) -> str:
        return "T1"

    def _load_config(self) -> dict:
        """Load and cache the config file."""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f)
        return self._config

    def fetch(self, target_date: date) -> List[dict]:
        """
        Load pricing observations from config file.

        Args:
            target_date: Date for the observations

        Returns:
            List of observation dictionaries
        """
        config = self._load_config()
        collected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        observations = []
        models = config.get("models", {})
        source_url = config.get("source_url", "https://openai.com/api/pricing/")

        for model_id, model_data in models.items():
            input_rate = model_data.get("input_rate", 0)
            output_rate = model_data.get("output_rate", 0)

            # Skip if no pricing
            if input_rate == 0 and output_rate == 0:
                continue

            obs = {
                "observation_id": f"obs-{target_date.isoformat()}-openai-{model_id}",
                "schema_version": "1.0.0",
                "provider": "openai",
                "model_id": f"openai/{model_id}",
                "model_display_name": model_id,
                "input_rate_usd_per_1m": round(float(input_rate), 6),
                "output_rate_usd_per_1m": round(float(output_rate), 6),
                "effective_date": target_date.isoformat(),
                "collected_at": collected_at,
                "source_url": source_url,
                "source_tier": self.source_tier,
                "currency": "USD",
                "collection_method": "config_file",
                "confidence_level": "high",
            }

            # Add optional fields if available
            if context_window := model_data.get("context_window"):
                obs["context_window"] = context_window

            if tier := model_data.get("tier"):
                obs["model_tier"] = tier

            observations.append(obs)

        return observations
