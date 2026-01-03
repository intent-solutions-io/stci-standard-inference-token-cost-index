"""
Tests for the STCI indexer service.
"""

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from services.indexer.indexer import Indexer, compute_index


class TestIndexer:
    """Tests for the Indexer class."""

    def test_load_methodology(self, temp_data_dir):
        """Test methodology loading from YAML."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        assert indexer.methodology["methodology_version"] == "1.0.0"
        assert indexer.methodology["output_ratio"] == 3.0
        assert "STCI-ALL" in indexer.methodology["indices"]

    def test_compute_all_index(self, temp_data_dir, sample_observations, target_date):
        """Test computing STCI-ALL index."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result = indexer.compute(sample_observations, target_date)

        assert result["date"] == target_date.isoformat()
        assert "STCI-ALL" in result["indices"]
        assert result["observation_count"] == 3

        stci_all = result["indices"]["STCI-ALL"]
        assert stci_all["model_count"] == 3
        assert "input_rate" in stci_all
        assert "output_rate" in stci_all
        assert "blended_rate" in stci_all

    def test_compute_basket_index(self, temp_data_dir, sample_observations, target_date):
        """Test computing index with specific basket."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result = indexer.compute(sample_observations, target_date)

        # STCI-TEST basket has 2 models: gpt-4o and claude-3.5-sonnet
        assert "STCI-TEST" in result["indices"]
        stci_test = result["indices"]["STCI-TEST"]
        assert stci_test["model_count"] == 2

    def test_blended_rate_calculation(self, temp_data_dir, target_date):
        """Test blended rate calculation with output_ratio."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        # Create observations with known rates
        observations = [
            {
                "observation_id": "test-1",
                "provider": "test",
                "model_id": "test/model",
                "input_rate_usd_per_1m": 1.0,
                "output_rate_usd_per_1m": 4.0,
                "effective_date": target_date.isoformat(),
            }
        ]

        result = indexer.compute(observations, target_date)

        # With output_ratio=3.0: blended = (1.0 + 3.0*4.0) / (1 + 3.0) = 13/4 = 3.25
        stci_all = result["indices"]["STCI-ALL"]
        assert stci_all["blended_rate"] == 3.25

    def test_average_rates(self, temp_data_dir, target_date):
        """Test average rate calculation."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        observations = [
            {
                "observation_id": "test-1",
                "provider": "test",
                "model_id": "test/model1",
                "input_rate_usd_per_1m": 2.0,
                "output_rate_usd_per_1m": 8.0,
                "effective_date": target_date.isoformat(),
            },
            {
                "observation_id": "test-2",
                "provider": "test",
                "model_id": "test/model2",
                "input_rate_usd_per_1m": 4.0,
                "output_rate_usd_per_1m": 12.0,
                "effective_date": target_date.isoformat(),
            },
        ]

        result = indexer.compute(observations, target_date)
        stci_all = result["indices"]["STCI-ALL"]

        # Average input: (2 + 4) / 2 = 3
        assert stci_all["input_rate"] == 3.0
        # Average output: (8 + 12) / 2 = 10
        assert stci_all["output_rate"] == 10.0

    def test_verification_hash(self, temp_data_dir, sample_observations, target_date):
        """Test verification hash is generated."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result = indexer.compute(sample_observations, target_date)

        assert "verification_hash" in result
        assert len(result["verification_hash"]) == 16  # First 16 chars of SHA256

    def test_verification_hash_deterministic(self, temp_data_dir, sample_observations, target_date):
        """Test that same inputs produce same hash."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result1 = indexer.compute(sample_observations, target_date)
        result2 = indexer.compute(sample_observations, target_date)

        assert result1["verification_hash"] == result2["verification_hash"]

    def test_verification_hash_changes_with_data(self, temp_data_dir, sample_observations, target_date):
        """Test that different data produces different hash."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result1 = indexer.compute(sample_observations, target_date)

        # Modify observations
        modified = sample_observations.copy()
        modified[0] = modified[0].copy()
        modified[0]["input_rate_usd_per_1m"] = 999.0

        result2 = indexer.compute(modified, target_date)

        assert result1["verification_hash"] != result2["verification_hash"]

    def test_dispersion_calculation(self, temp_data_dir, target_date):
        """Test standard deviation (dispersion) calculation."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        observations = [
            {"observation_id": "1", "provider": "a", "model_id": "a/1",
             "input_rate_usd_per_1m": 1.0, "output_rate_usd_per_1m": 1.0,
             "effective_date": target_date.isoformat()},
            {"observation_id": "2", "provider": "b", "model_id": "b/2",
             "input_rate_usd_per_1m": 3.0, "output_rate_usd_per_1m": 3.0,
             "effective_date": target_date.isoformat()},
        ]

        result = indexer.compute(observations, target_date)
        stci_all = result["indices"]["STCI-ALL"]

        # With 2 observations, dispersion should be calculated
        assert "dispersion" in stci_all
        assert stci_all["dispersion"] > 0

    def test_single_observation_no_dispersion(self, temp_data_dir, target_date):
        """Test that single observation has no dispersion."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        observations = [
            {"observation_id": "1", "provider": "a", "model_id": "a/1",
             "input_rate_usd_per_1m": 1.0, "output_rate_usd_per_1m": 1.0,
             "effective_date": target_date.isoformat()},
        ]

        result = indexer.compute(observations, target_date)
        stci_all = result["indices"]["STCI-ALL"]

        # Single observation can't have dispersion
        assert stci_all.get("dispersion") is None

    def test_empty_basket_returns_none(self, temp_data_dir, target_date):
        """Test that empty basket doesn't create index."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        # Observations that don't match STCI-TEST basket
        observations = [
            {"observation_id": "1", "provider": "other", "model_id": "other/model",
             "input_rate_usd_per_1m": 1.0, "output_rate_usd_per_1m": 1.0,
             "effective_date": target_date.isoformat()},
        ]

        result = indexer.compute(observations, target_date)

        # STCI-ALL should exist (all models)
        assert "STCI-ALL" in result["indices"]
        # STCI-TEST should not exist (no matching models)
        assert "STCI-TEST" not in result["indices"]

    def test_infer_date_from_observations(self, temp_data_dir, sample_observations):
        """Test date inference from observations."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result = indexer.compute(sample_observations)  # No explicit date

        assert result["date"] == "2026-01-01"  # From sample data

    def test_models_included_list(self, temp_data_dir, sample_observations, target_date):
        """Test that models_included list is populated."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"
        indexer = Indexer(methodology_path)

        result = indexer.compute(sample_observations, target_date)
        stci_all = result["indices"]["STCI-ALL"]

        assert "models_included" in stci_all
        assert len(stci_all["models_included"]) == 3
        assert "openai/gpt-4o" in stci_all["models_included"]


class TestComputeIndexFunction:
    """Tests for the compute_index convenience function."""

    def test_compute_index(self, temp_data_dir, sample_observations, target_date):
        """Test the convenience function."""
        methodology_path = temp_data_dir / "fixtures" / "methodology.yaml"

        result = compute_index(
            sample_observations,
            methodology_path=methodology_path,
            target_date=target_date,
        )

        assert result["date"] == target_date.isoformat()
        assert "STCI-ALL" in result["indices"]

    def test_compute_index_default_methodology(self, sample_observations, target_date):
        """Test with default methodology path."""
        # This will use the project's methodology.yaml
        result = compute_index(sample_observations, target_date=target_date)

        assert result["date"] == target_date.isoformat()
        # Should have indices from default methodology
        assert len(result["indices"]) > 0
