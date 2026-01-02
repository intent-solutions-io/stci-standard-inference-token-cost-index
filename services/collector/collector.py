"""
STCI Collector - Fetches pricing observations from sources.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from .sources import BaseSource, OpenRouterSource, FixtureSource


class Collector:
    """
    Main collector class that orchestrates data collection from sources.

    Uses a waterfall approach:
    1. Try primary source (OpenRouter API)
    2. Fall back to fixture data if primary fails
    """

    def __init__(
        self,
        primary_source: Optional[BaseSource] = None,
        fallback_source: Optional[BaseSource] = None,
    ):
        """
        Initialize collector with sources.

        Args:
            primary_source: Primary data source (default: OpenRouterSource)
            fallback_source: Fallback source (default: FixtureSource)
        """
        self.primary_source = primary_source or OpenRouterSource()
        self.fallback_source = fallback_source or FixtureSource()

    def collect(
        self,
        target_date: Optional[date] = None,
        use_fallback: bool = True,
    ) -> List[dict]:
        """
        Collect observations for a given date.

        Args:
            target_date: Date to collect for (default: today)
            use_fallback: Whether to use fallback on primary failure

        Returns:
            List of observation dictionaries

        Raises:
            CollectionError: If collection fails and no fallback
        """
        target_date = target_date or date.today()

        try:
            observations = self.primary_source.fetch(target_date)
            if observations:
                return observations
        except Exception as e:
            print(f"Primary source failed: {e}")

        if use_fallback:
            print("Using fallback source...")
            return self.fallback_source.fetch(target_date)

        raise CollectionError(f"Failed to collect data for {target_date}")

    def validate_observations(self, observations: List[dict]) -> List[dict]:
        """
        Validate observations against schema.

        Args:
            observations: List of observation dictionaries

        Returns:
            List of valid observations (invalid ones logged and skipped)
        """
        valid = []
        for obs in observations:
            # Basic validation - full schema validation TODO
            required = [
                "observation_id",
                "provider",
                "model_id",
                "input_rate_usd_per_1m",
                "output_rate_usd_per_1m",
            ]
            if all(k in obs for k in required):
                valid.append(obs)
            else:
                print(f"Invalid observation skipped: {obs.get('observation_id', 'unknown')}")

        return valid


class CollectionError(Exception):
    """Raised when data collection fails."""

    pass


def main():
    """CLI entry point for collector."""
    import argparse

    parser = argparse.ArgumentParser(description="STCI Collector")
    parser.add_argument(
        "--date",
        type=str,
        help="Date to collect (YYYY-MM-DD)",
        default=None,
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path",
        default=None,
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Use fixture data only",
    )

    args = parser.parse_args()

    collector = Collector()

    if args.fixtures:
        collector.primary_source = FixtureSource()

    target_date = date.fromisoformat(args.date) if args.date else date.today()

    observations = collector.collect(target_date)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(observations, f, indent=2, default=str)
        print(f"Wrote {len(observations)} observations to {args.output}")
    else:
        print(json.dumps(observations, indent=2, default=str))


if __name__ == "__main__":
    main()
