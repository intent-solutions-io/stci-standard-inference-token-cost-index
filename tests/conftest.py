"""
Pytest configuration and shared fixtures for STCI tests.
"""

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def sample_observations():
    """Sample observation data for testing."""
    return [
        {
            "observation_id": "obs-2026-01-01-openai-gpt-4o",
            "schema_version": "1.0.0",
            "provider": "openai",
            "model_id": "openai/gpt-4o",
            "model_display_name": "GPT-4o",
            "input_rate_usd_per_1m": 2.50,
            "output_rate_usd_per_1m": 10.00,
            "effective_date": "2026-01-01",
            "collected_at": "2026-01-01T00:30:00Z",
            "source_url": "https://openrouter.ai/api/v1/models",
            "source_tier": "T1",
            "currency": "USD",
            "collection_method": "aggregator_api",
            "confidence_level": "high",
            "context_window": 128000,
        },
        {
            "observation_id": "obs-2026-01-01-anthropic-claude-3-5-sonnet",
            "schema_version": "1.0.0",
            "provider": "anthropic",
            "model_id": "anthropic/claude-3.5-sonnet",
            "model_display_name": "Claude 3.5 Sonnet",
            "input_rate_usd_per_1m": 3.00,
            "output_rate_usd_per_1m": 15.00,
            "effective_date": "2026-01-01",
            "collected_at": "2026-01-01T00:30:00Z",
            "source_url": "https://openrouter.ai/api/v1/models",
            "source_tier": "T1",
            "currency": "USD",
            "collection_method": "aggregator_api",
            "confidence_level": "high",
            "context_window": 200000,
        },
        {
            "observation_id": "obs-2026-01-01-openai-gpt-4o-mini",
            "schema_version": "1.0.0",
            "provider": "openai",
            "model_id": "openai/gpt-4o-mini",
            "model_display_name": "GPT-4o Mini",
            "input_rate_usd_per_1m": 0.15,
            "output_rate_usd_per_1m": 0.60,
            "effective_date": "2026-01-01",
            "collected_at": "2026-01-01T00:30:00Z",
            "source_url": "https://openrouter.ai/api/v1/models",
            "source_tier": "T1",
            "currency": "USD",
            "collection_method": "aggregator_api",
            "confidence_level": "high",
            "context_window": 128000,
        },
    ]


@pytest.fixture
def sample_openrouter_response():
    """Sample OpenRouter API response."""
    return {
        "data": [
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "pricing": {
                    "prompt": "0.0000025",
                    "completion": "0.00001",
                },
                "context_length": 128000,
            },
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "pricing": {
                    "prompt": "0.000003",
                    "completion": "0.000015",
                },
                "context_length": 200000,
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini",
                "pricing": {
                    "prompt": "0.00000015",
                    "completion": "0.0000006",
                },
                "context_length": 128000,
            },
            # Model without pricing (should be skipped)
            {
                "id": "test/no-pricing",
                "name": "No Pricing Model",
            },
            # Free model (should be skipped)
            {
                "id": "test/free-model",
                "name": "Free Model",
                "pricing": {
                    "prompt": "0",
                    "completion": "0",
                },
            },
        ]
    }


@pytest.fixture
def sample_methodology():
    """Sample methodology configuration."""
    return {
        "methodology_version": "1.0.0",
        "output_ratio": 3.0,
        "carry_forward_max_days": 7,
        "min_basket_coverage": 0.5,
        "decimal_places": {
            "rates": 6,
            "weights": 8,
            "output": 2,
        },
        "indices": {
            "STCI-ALL": {
                "description": "All eligible models",
                "weighting": "equal",
                "filter": None,
            },
            "STCI-TEST": {
                "description": "Test basket",
                "weighting": "equal",
                "models": [
                    "openai/gpt-4o",
                    "anthropic/claude-3.5-sonnet",
                ],
            },
        },
    }


@pytest.fixture
def temp_data_dir(tmp_path, sample_observations, sample_methodology):
    """Create temporary data directory with sample data."""
    # Create directories
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "observations").mkdir()
    (tmp_path / "indices").mkdir()
    (tmp_path / "raw" / "openrouter").mkdir(parents=True)

    # Write methodology
    with open(tmp_path / "fixtures" / "methodology.yaml", "w") as f:
        yaml.dump(sample_methodology, f)

    # Write sample observations as JSONL
    with open(tmp_path / "observations" / "2026-01-01.jsonl", "w") as f:
        for obs in sample_observations:
            f.write(json.dumps(obs) + "\n")

    # Write sample observations as JSON (for fixtures)
    with open(tmp_path / "fixtures" / "observations.sample.json", "w") as f:
        json.dump(sample_observations, f)

    return tmp_path


@pytest.fixture
def target_date():
    """Standard test date."""
    return date(2026, 1, 1)
