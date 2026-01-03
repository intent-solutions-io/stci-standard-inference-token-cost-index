"""
Tests for the STCI collector service.
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import responses

from services.collector.sources import OpenRouterSource, FixtureSource, BaseSource
from services.collector.collector import Collector, CollectionError


class TestOpenRouterSource:
    """Tests for OpenRouterSource."""

    def test_source_properties(self):
        """Test source ID and tier."""
        source = OpenRouterSource()
        assert source.source_id == "openrouter"
        assert source.source_tier == "T1"

    @responses.activate
    def test_fetch_success(self, sample_openrouter_response, target_date):
        """Test successful fetch from OpenRouter API."""
        responses.add(
            responses.GET,
            "https://openrouter.ai/api/v1/models",
            json=sample_openrouter_response,
            status=200,
        )

        source = OpenRouterSource()
        observations = source.fetch(target_date)

        # Should have 3 observations (skipped no-pricing and free models)
        assert len(observations) == 3

        # Check first observation structure
        obs = observations[0]
        assert obs["provider"] == "openai"
        assert obs["model_id"] == "openai/gpt-4o"
        assert obs["input_rate_usd_per_1m"] == 2.5
        assert obs["output_rate_usd_per_1m"] == 10.0
        assert obs["source_tier"] == "T1"
        assert obs["currency"] == "USD"
        assert obs["collection_method"] == "aggregator_api"
        assert obs["effective_date"] == target_date.isoformat()

    @responses.activate
    def test_fetch_skips_models_without_pricing(self, target_date):
        """Test that models without pricing are skipped."""
        responses.add(
            responses.GET,
            "https://openrouter.ai/api/v1/models",
            json={
                "data": [
                    {"id": "test/no-pricing", "name": "No Pricing"},
                    {"id": "test/null-pricing", "name": "Null", "pricing": None},
                    {"id": "test/partial", "name": "Partial", "pricing": {"prompt": "0.001"}},
                ]
            },
            status=200,
        )

        source = OpenRouterSource()
        observations = source.fetch(target_date)

        assert len(observations) == 0

    @responses.activate
    def test_fetch_skips_free_models(self, target_date):
        """Test that free models (rate=0) are skipped."""
        responses.add(
            responses.GET,
            "https://openrouter.ai/api/v1/models",
            json={
                "data": [
                    {
                        "id": "test/free",
                        "name": "Free Model",
                        "pricing": {"prompt": "0", "completion": "0"},
                    }
                ]
            },
            status=200,
        )

        source = OpenRouterSource()
        observations = source.fetch(target_date)

        assert len(observations) == 0

    @responses.activate
    def test_fetch_rate_conversion(self, target_date):
        """Test rate conversion from per-token to per-1M."""
        responses.add(
            responses.GET,
            "https://openrouter.ai/api/v1/models",
            json={
                "data": [
                    {
                        "id": "test/model",
                        "name": "Test",
                        "pricing": {
                            "prompt": "0.000001",  # $1 per 1M
                            "completion": "0.000002",  # $2 per 1M
                        },
                    }
                ]
            },
            status=200,
        )

        source = OpenRouterSource()
        observations = source.fetch(target_date)

        assert len(observations) == 1
        assert observations[0]["input_rate_usd_per_1m"] == 1.0
        assert observations[0]["output_rate_usd_per_1m"] == 2.0

    @responses.activate
    def test_fetch_api_error(self, target_date):
        """Test handling of API errors."""
        responses.add(
            responses.GET,
            "https://openrouter.ai/api/v1/models",
            json={"error": "Internal error"},
            status=500,
        )

        source = OpenRouterSource()

        with pytest.raises(Exception):
            source.fetch(target_date)

    def test_custom_api_url(self):
        """Test custom API URL."""
        source = OpenRouterSource(api_url="https://custom.api/models")
        assert source.api_url == "https://custom.api/models"


class TestFixtureSource:
    """Tests for FixtureSource."""

    def test_source_properties(self):
        """Test source ID and tier."""
        source = FixtureSource()
        assert source.source_id == "fixture"
        assert source.source_tier == "T4"

    def test_fetch_from_fixtures(self, temp_data_dir, target_date):
        """Test loading from fixture file."""
        fixture_path = temp_data_dir / "fixtures" / "observations.sample.json"
        source = FixtureSource(fixture_path=fixture_path)

        observations = source.fetch(target_date)

        assert len(observations) == 3
        # Check dates are updated
        for obs in observations:
            assert obs["effective_date"] == target_date.isoformat()

    def test_fetch_missing_file(self, tmp_path, target_date):
        """Test error when fixture file is missing."""
        source = FixtureSource(fixture_path=tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError):
            source.fetch(target_date)


class TestCollector:
    """Tests for the Collector class."""

    def test_default_sources(self):
        """Test default source initialization."""
        collector = Collector()
        assert isinstance(collector.primary_source, OpenRouterSource)
        assert isinstance(collector.fallback_source, FixtureSource)

    def test_custom_sources(self):
        """Test custom source injection."""
        primary = FixtureSource()
        fallback = FixtureSource()
        collector = Collector(primary_source=primary, fallback_source=fallback)

        assert collector.primary_source is primary
        assert collector.fallback_source is fallback

    def test_collect_uses_primary(self, temp_data_dir, target_date):
        """Test that collect uses primary source first."""
        fixture_path = temp_data_dir / "fixtures" / "observations.sample.json"
        primary = FixtureSource(fixture_path=fixture_path)
        collector = Collector(primary_source=primary)

        observations = collector.collect(target_date)

        assert len(observations) == 3

    def test_collect_fallback_on_failure(self, temp_data_dir, target_date):
        """Test fallback when primary fails."""
        # Primary that always fails
        failing_source = MagicMock(spec=BaseSource)
        failing_source.fetch.side_effect = Exception("API Error")

        # Working fallback
        fixture_path = temp_data_dir / "fixtures" / "observations.sample.json"
        fallback = FixtureSource(fixture_path=fixture_path)

        collector = Collector(primary_source=failing_source, fallback_source=fallback)
        observations = collector.collect(target_date)

        assert len(observations) == 3

    def test_collect_no_fallback_raises(self, target_date):
        """Test that collection raises when fallback disabled."""
        failing_source = MagicMock(spec=BaseSource)
        failing_source.fetch.side_effect = Exception("API Error")

        collector = Collector(primary_source=failing_source)

        with pytest.raises(CollectionError):
            collector.collect(target_date, use_fallback=False)

    def test_validate_observations(self, sample_observations):
        """Test observation validation."""
        collector = Collector()

        valid = collector.validate_observations(sample_observations)
        assert len(valid) == 3

    def test_validate_rejects_incomplete(self):
        """Test that incomplete observations are rejected."""
        collector = Collector()

        incomplete = [
            {"observation_id": "test", "provider": "test"},  # Missing required fields
            {"model_id": "test"},  # Missing most fields
        ]

        valid = collector.validate_observations(incomplete)
        assert len(valid) == 0

    def test_default_date_is_today(self):
        """Test that default date is today."""
        fixture_path = Path(__file__).parent.parent / "data" / "fixtures" / "observations.sample.json"
        if fixture_path.exists():
            source = FixtureSource(fixture_path=fixture_path)
            collector = Collector(primary_source=source)
            observations = collector.collect()

            today = date.today().isoformat()
            assert all(obs["effective_date"] == today for obs in observations)
