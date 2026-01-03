#!/usr/bin/env python3
"""
STCI Indexing Pipeline

Computes STCI indices from collected observations:
1. Load observations from JSONL
2. Compute indices per methodology
3. Generate verification hash
4. Store index output

Usage:
    python -m services.indexer.pipeline
    python -m services.indexer.pipeline --date 2026-01-01
    python -m services.indexer.pipeline --dry-run
"""

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.indexer.indexer import Indexer


class IndexingPipeline:
    """
    Full indexing pipeline with storage.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        methodology_path: Optional[Path] = None,
    ):
        self.data_dir = data_dir or PROJECT_ROOT / "data"
        self.methodology_path = methodology_path or (
            self.data_dir / "fixtures" / "methodology.yaml"
        )

        # Ensure output directory exists
        (self.data_dir / "indices").mkdir(parents=True, exist_ok=True)

        # Initialize indexer
        self.indexer = Indexer(self.methodology_path)

    def run(
        self,
        target_date: Optional[date] = None,
        dry_run: bool = False,
    ) -> Tuple[dict, Path]:
        """
        Run the full indexing pipeline.

        Args:
            target_date: Date to compute index for (default: today)
            dry_run: If True, don't write files

        Returns:
            Tuple of (index_result, output_path)
        """
        target_date = target_date or date.today()

        print(f"=== STCI Indexing Pipeline ===")
        print(f"Date: {target_date}")
        print(f"Methodology: v{self.indexer.methodology.get('methodology_version', '?')}")
        print()

        # Step 1: Load observations
        print("[1/3] Loading observations...")
        observations = self._load_observations(target_date)
        print(f"      Loaded {len(observations)} observations")

        if not observations:
            print("ERROR: No observations found for this date")
            sys.exit(1)

        # Step 2: Compute indices
        print("[2/3] Computing indices...")
        result = self.indexer.compute(observations, target_date)

        for idx_name, idx_data in result.get("indices", {}).items():
            model_count = idx_data.get("model_count", 0)
            blended = idx_data.get("blended_rate", 0)
            print(f"      {idx_name}: ${blended:.2f}/1M ({model_count} models)")

        # Step 3: Store index
        print("[3/3] Storing index...")
        output_path = self._store_index(result, target_date, dry_run)
        print(f"      Written to: {output_path}")

        # Summary
        print()
        print("=== Indexing Complete ===")
        print(f"Date:              {result['date']}")
        print(f"Observations:      {result['observation_count']}")
        print(f"Indices computed:  {len(result['indices'])}")
        print(f"Verification hash: {result['verification_hash']}")
        print(f"Output:            {output_path}")

        return result, output_path

    def _load_observations(self, target_date: date) -> List[dict]:
        """Load observations from JSONL file."""
        obs_path = self.data_dir / "observations" / f"{target_date}.jsonl"

        if not obs_path.exists():
            # Try JSON format as fallback
            json_path = self.data_dir / "observations" / f"{target_date}.json"
            if json_path.exists():
                with open(json_path) as f:
                    return json.load(f)
            return []

        observations = []
        with open(obs_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    observations.append(json.loads(line))

        return observations

    def _store_index(
        self,
        result: dict,
        target_date: date,
        dry_run: bool,
    ) -> Path:
        """Store index result as JSON."""
        output_path = self.data_dir / "indices" / f"{target_date}.json"

        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)

        return output_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="STCI Indexing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Compute today's index
    python -m services.indexer.pipeline

    # Compute for specific date
    python -m services.indexer.pipeline --date 2026-01-01

    # Dry run (no files written)
    python -m services.indexer.pipeline --dry-run
        """,
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to compute index for (YYYY-MM-DD, default: today)",
        default=None,
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
    pipeline = IndexingPipeline()
    try:
        result, path = pipeline.run(
            target_date=target_date,
            dry_run=args.dry_run,
        )
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
