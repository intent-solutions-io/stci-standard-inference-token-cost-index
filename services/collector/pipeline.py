#!/usr/bin/env python3
"""
STCI Collection Pipeline

Orchestrates the full data collection workflow:
1. Fetch raw data from sources
2. Store raw responses (immutable archive)
3. Normalize to observations
4. Validate against schema
5. Store observations as JSONL

Usage:
    python -m services.collector.pipeline
    python -m services.collector.pipeline --date 2026-01-01
    python -m services.collector.pipeline --fixtures  # Use test data
"""

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.collector.sources import OpenRouterSource, FixtureSource, BaseSource

# Optional: JSON Schema validation
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class CollectionPipeline:
    """
    Full collection pipeline with storage and validation.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        schema_dir: Optional[Path] = None,
    ):
        self.data_dir = data_dir or PROJECT_ROOT / "data"
        self.schema_dir = schema_dir or PROJECT_ROOT / "schemas"

        # Ensure directories exist
        (self.data_dir / "raw" / "openrouter").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "observations").mkdir(parents=True, exist_ok=True)

        # Load schema for validation
        self.observation_schema = self._load_schema("observation.schema.json")

    def _load_schema(self, filename: str) -> Optional[dict]:
        """Load JSON schema if available."""
        schema_path = self.schema_dir / filename
        if schema_path.exists():
            with open(schema_path) as f:
                return json.load(f)
        return None

    def run(
        self,
        target_date: Optional[date] = None,
        source: Optional[BaseSource] = None,
        dry_run: bool = False,
    ) -> Tuple[int, int, Path]:
        """
        Run the full collection pipeline.

        Args:
            target_date: Date to collect for (default: today UTC)
            source: Data source to use (default: OpenRouterSource)
            dry_run: If True, don't write files

        Returns:
            Tuple of (total_fetched, valid_count, observations_path)
        """
        target_date = target_date or date.today()
        source = source or OpenRouterSource()

        print(f"=== STCI Collection Pipeline ===")
        print(f"Date: {target_date}")
        print(f"Source: {source.source_id} (Tier {source.source_tier})")
        print()

        # Step 1: Fetch raw data
        print("[1/4] Fetching raw data...")
        raw_data, raw_path = self._fetch_and_store_raw(source, target_date, dry_run)
        print(f"      Fetched {len(raw_data.get('data', []))} models")

        # Step 2: Normalize to observations
        print("[2/4] Normalizing observations...")
        observations = source.fetch(target_date)
        print(f"      Normalized {len(observations)} observations")

        # Step 3: Validate observations
        print("[3/4] Validating observations...")
        valid_observations, invalid_count = self._validate_observations(observations)
        print(f"      Valid: {len(valid_observations)}, Invalid: {invalid_count}")

        # Step 4: Store observations
        print("[4/4] Storing observations...")
        obs_path = self._store_observations(valid_observations, target_date, dry_run)
        print(f"      Written to: {obs_path}")

        # Summary
        print()
        print("=== Collection Complete ===")
        print(f"Total fetched:  {len(observations)}")
        print(f"Valid stored:   {len(valid_observations)}")
        print(f"Raw archive:    {raw_path}")
        print(f"Observations:   {obs_path}")

        return len(observations), len(valid_observations), obs_path

    def _fetch_and_store_raw(
        self,
        source: BaseSource,
        target_date: date,
        dry_run: bool,
    ) -> Tuple[dict, Path]:
        """Fetch raw API response and store it."""
        import requests

        raw_path = self.data_dir / "raw" / source.source_id / f"{target_date}.json"

        if isinstance(source, OpenRouterSource):
            response = requests.get(source.api_url, timeout=30)
            response.raise_for_status()
            raw_data = response.json()
        elif isinstance(source, FixtureSource):
            # For fixtures, create a synthetic raw response
            with open(source.fixture_path) as f:
                fixture_data = json.load(f)
            raw_data = {"data": fixture_data, "source": "fixture"}
        else:
            raw_data = {"data": [], "source": source.source_id}

        # Add metadata
        raw_data["_meta"] = {
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_id": source.source_id,
            "target_date": target_date.isoformat(),
        }

        if not dry_run:
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "w") as f:
                json.dump(raw_data, f, indent=2)

        return raw_data, raw_path

    def _validate_observations(
        self,
        observations: List[dict],
    ) -> Tuple[List[dict], int]:
        """Validate observations against schema."""
        if not JSONSCHEMA_AVAILABLE or not self.observation_schema:
            # Basic validation without jsonschema
            return self._basic_validate(observations)

        valid = []
        invalid_count = 0

        for obs in observations:
            try:
                jsonschema.validate(obs, self.observation_schema)
                valid.append(obs)
            except jsonschema.ValidationError as e:
                invalid_count += 1
                print(f"      [INVALID] {obs.get('model_id', 'unknown')}: {e.message[:50]}")

        return valid, invalid_count

    def _basic_validate(self, observations: List[dict]) -> Tuple[List[dict], int]:
        """Basic validation without jsonschema library."""
        required_fields = [
            "observation_id",
            "schema_version",
            "provider",
            "model_id",
            "input_rate_usd_per_1m",
            "output_rate_usd_per_1m",
            "effective_date",
            "collected_at",
            "source_url",
            "source_tier",
            "currency",
            "collection_method",
        ]

        valid = []
        invalid_count = 0

        for obs in observations:
            missing = [f for f in required_fields if f not in obs]
            if missing:
                invalid_count += 1
                print(f"      [INVALID] {obs.get('model_id', 'unknown')}: missing {missing}")
            else:
                valid.append(obs)

        return valid, invalid_count

    def _store_observations(
        self,
        observations: List[dict],
        target_date: date,
        dry_run: bool,
    ) -> Path:
        """Store observations as JSONL."""
        obs_path = self.data_dir / "observations" / f"{target_date}.jsonl"

        if not dry_run:
            obs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(obs_path, "w") as f:
                for obs in observations:
                    f.write(json.dumps(obs, separators=(",", ":")) + "\n")

        return obs_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="STCI Collection Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Collect today's data from OpenRouter
    python -m services.collector.pipeline

    # Collect for specific date
    python -m services.collector.pipeline --date 2026-01-01

    # Use fixture data for testing
    python -m services.collector.pipeline --fixtures

    # Dry run (no files written)
    python -m services.collector.pipeline --dry-run
        """,
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to collect (YYYY-MM-DD, default: today)",
        default=None,
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Use fixture data instead of live API",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write any files",
    )

    args = parser.parse_args()

    # Parse date
    target_date = date.fromisoformat(args.date) if args.date else date.today()

    # Select source
    source = FixtureSource() if args.fixtures else OpenRouterSource()

    # Run pipeline
    pipeline = CollectionPipeline()
    try:
        total, valid, path = pipeline.run(
            target_date=target_date,
            source=source,
            dry_run=args.dry_run,
        )
        sys.exit(0 if valid > 0 else 1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
