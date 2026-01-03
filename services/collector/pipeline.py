#!/usr/bin/env python3
"""
STCI Collection Pipeline

Orchestrates the full data collection workflow:
1. Fetch raw data from multiple sources
2. Store raw responses (immutable archive)
3. Normalize to observations
4. Validate against schema
5. Detect pricing drift across sources
6. Deduplicate observations
7. Store observations as JSONL

Usage:
    python -m services.collector.pipeline
    python -m services.collector.pipeline --date 2026-01-01
    python -m services.collector.pipeline --fixtures  # Use test data
    python -m services.collector.pipeline --multi     # Use all sources
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
from services.collector.drift import detect_drift, normalize_model_id

# Import direct sources (optional - may not be available yet)
try:
    from services.collector.direct_sources import (
        OpenAIDirectSource,
        AnthropicDirectSource,
        GoogleDirectSource,
    )
    DIRECT_SOURCES_AVAILABLE = True
except ImportError:
    DIRECT_SOURCES_AVAILABLE = False

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

    def run_multi(
        self,
        target_date: Optional[date] = None,
        dry_run: bool = False,
        drift_threshold: float = 0.05,
    ) -> Tuple[int, int, Path]:
        """
        Run collection from multiple sources with drift detection.

        Args:
            target_date: Date to collect for (default: today UTC)
            dry_run: If True, don't write files
            drift_threshold: Maximum allowed price difference (default 5%)

        Returns:
            Tuple of (total_fetched, valid_count, observations_path)
        """
        target_date = target_date or date.today()

        # Build source list
        sources: List[BaseSource] = [OpenRouterSource()]
        if DIRECT_SOURCES_AVAILABLE:
            sources.extend([
                OpenAIDirectSource(),
                AnthropicDirectSource(),
                GoogleDirectSource(),
            ])

        print(f"=== STCI Multi-Source Collection Pipeline ===")
        print(f"Date: {target_date}")
        print(f"Sources: {[s.source_id for s in sources]}")
        print()

        # Step 1: Fetch from all sources
        print("[1/5] Fetching from all sources...")
        all_observations = []
        source_counts = {}

        for source in sources:
            try:
                obs = source.fetch(target_date)
                all_observations.extend(obs)
                source_counts[source.source_id] = len(obs)
                print(f"      {source.source_id}: {len(obs)} observations")
            except Exception as e:
                source_counts[source.source_id] = 0
                print(f"      {source.source_id}: FAILED - {e}")

        print(f"      Total: {len(all_observations)} observations")

        # Step 2: Drift detection
        print("[2/5] Detecting pricing drift...")
        drift_report = detect_drift(all_observations, threshold=drift_threshold)
        if drift_report.has_warnings:
            print(f"      {drift_report.discrepancy_count} discrepancies found:")
            for warning in drift_report.warnings[:5]:  # Show first 5
                print(f"        DRIFT: {warning}")
            if len(drift_report.warnings) > 5:
                print(f"        ... and {len(drift_report.warnings) - 5} more")
        else:
            print("      No significant drift detected")

        # Step 3: Deduplicate (prefer official over aggregator)
        print("[3/5] Deduplicating observations...")
        deduped = self._deduplicate_observations(all_observations)
        print(f"      Deduplicated: {len(all_observations)} -> {len(deduped)}")

        # Step 4: Validate observations
        print("[4/5] Validating observations...")
        valid_observations, invalid_count = self._validate_observations(deduped)
        print(f"      Valid: {len(valid_observations)}, Invalid: {invalid_count}")

        # Step 5: Store observations
        print("[5/5] Storing observations...")
        obs_path = self._store_observations(valid_observations, target_date, dry_run)
        print(f"      Written to: {obs_path}")

        # Summary
        print()
        print("=== Collection Complete ===")
        print(f"Sources queried: {len(sources)}")
        print(f"Total fetched:   {len(all_observations)}")
        print(f"After dedup:     {len(deduped)}")
        print(f"Valid stored:    {len(valid_observations)}")
        print(f"Drift warnings:  {len(drift_report.warnings)}")
        print(f"Observations:    {obs_path}")

        return len(all_observations), len(valid_observations), obs_path

    def _deduplicate_observations(self, observations: List[dict]) -> List[dict]:
        """
        Deduplicate observations, preferring official sources over aggregators.

        Priority:
        1. T1 official (config_file collection_method)
        2. T1 aggregator (aggregator_api collection_method)
        3. T2-T4 sources
        """
        # Group by normalized model ID
        model_groups: dict[str, list[dict]] = {}
        for obs in observations:
            model_id = obs.get("model_id", "")
            normalized = normalize_model_id(model_id)
            if normalized not in model_groups:
                model_groups[normalized] = []
            model_groups[normalized].append(obs)

        # Select best observation for each model
        deduped = []
        for normalized_id, obs_list in model_groups.items():
            # Sort by priority: config_file > aggregator_api > others
            def priority(obs):
                method = obs.get("collection_method", "")
                if method == "config_file":
                    return 0
                elif method == "aggregator_api":
                    return 1
                else:
                    return 2

            obs_list.sort(key=priority)
            deduped.append(obs_list[0])

        return deduped

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

    # Use all sources with drift detection
    python -m services.collector.pipeline --multi

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
        "--multi",
        action="store_true",
        help="Use all available sources with drift detection",
    )
    parser.add_argument(
        "--drift-threshold",
        type=float,
        default=0.05,
        help="Maximum allowed price difference (default: 0.05 = 5%%)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write any files",
    )

    args = parser.parse_args()

    # Parse date
    target_date = date.fromisoformat(args.date) if args.date else date.today()

    # Run pipeline
    pipeline = CollectionPipeline()
    try:
        if args.multi:
            # Multi-source with drift detection
            total, valid, path = pipeline.run_multi(
                target_date=target_date,
                dry_run=args.dry_run,
                drift_threshold=args.drift_threshold,
            )
        else:
            # Single source (legacy behavior)
            source = FixtureSource() if args.fixtures else OpenRouterSource()
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
