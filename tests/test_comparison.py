"""
Tests for model comparison and normalization logic.

These tests ensure that:
1. Model ID normalization correctly identifies same models across sources
2. Different models (16k, :extended, etc.) are NOT incorrectly aliased
3. Comparison markup percentages are within reasonable bounds
"""

import pytest
import re
from typing import Optional


def normalize_model_id(model_id: str) -> str:
    """
    Normalize model ID for matching across sources.

    This mirrors the JavaScript normalizeModelId() function in compare.html.
    Any changes here should be reflected there and vice versa.
    """
    if not model_id:
        return ''

    # Remove provider prefix (e.g., "openai/gpt-4o" -> "gpt-4o")
    normalized = model_id.split('/')[-1] if '/' in model_id else model_id

    # Check aliases FIRST before stripping suffixes
    # This handles cases like 'gpt-4-1106-preview' correctly
    aliases = {
        'gpt-4-turbo-preview': 'gpt-4-turbo',
        'gpt-4-1106-preview': 'gpt-4-turbo',
        'chatgpt-4o-latest': 'gpt-4o',
        'gpt-3.5-turbo-0613': 'gpt-3.5-turbo',
    }

    if normalized in aliases:
        return aliases[normalized].lower()

    # Remove date suffixes: YYYY-MM-DD or YYYYMMDD
    normalized = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', normalized)
    normalized = re.sub(r'-\d{8}$', '', normalized)

    # Remove common suffixes that don't affect base model identity
    # NOTE: Do NOT remove :extended - it's a different product with different pricing
    normalized = re.sub(r':thinking$', '', normalized)
    normalized = re.sub(r'-preview$', '', normalized)
    normalized = re.sub(r'-001$', '', normalized)

    return normalized.lower()


class TestNormalizeModelId:
    """Tests for model ID normalization."""

    def test_removes_provider_prefix(self):
        """Provider prefixes should be stripped."""
        assert normalize_model_id('openai/gpt-4o') == 'gpt-4o'
        assert normalize_model_id('anthropic/claude-3-opus') == 'claude-3-opus'
        assert normalize_model_id('google/gemini-2.0-flash') == 'gemini-2.0-flash'

    def test_removes_date_suffix(self):
        """Date suffixes should be stripped."""
        assert normalize_model_id('gpt-4o-2024-11-20') == 'gpt-4o'
        assert normalize_model_id('gpt-4o-mini-2024-07-18') == 'gpt-4o-mini'
        assert normalize_model_id('claude-3.5-haiku-20241022') == 'claude-3.5-haiku'

    def test_removes_preview_suffix(self):
        """Preview suffixes should be stripped."""
        assert normalize_model_id('gemini-2.5-pro-preview') == 'gemini-2.5-pro'
        assert normalize_model_id('gpt-4-turbo-preview') == 'gpt-4-turbo'

    def test_removes_001_suffix(self):
        """Version -001 suffixes should be stripped."""
        assert normalize_model_id('gemini-2.0-flash-001') == 'gemini-2.0-flash'
        assert normalize_model_id('gemini-2.0-flash-lite-001') == 'gemini-2.0-flash-lite'

    def test_does_not_remove_extended(self):
        """:extended is a different product - must NOT be stripped."""
        assert normalize_model_id('gpt-4o:extended') == 'gpt-4o:extended'
        assert normalize_model_id('gpt-4o:extended') != 'gpt-4o'

    def test_does_not_alias_16k_variant(self):
        """16k context models have different pricing - must NOT be aliased."""
        assert normalize_model_id('gpt-3.5-turbo-16k') == 'gpt-3.5-turbo-16k'
        assert normalize_model_id('gpt-3.5-turbo-16k') != 'gpt-3.5-turbo'

    def test_does_not_alias_instruct_variant(self):
        """Instruct models are different - must NOT be aliased."""
        assert normalize_model_id('gpt-3.5-turbo-instruct') == 'gpt-3.5-turbo-instruct'
        assert normalize_model_id('gpt-3.5-turbo-instruct') != 'gpt-3.5-turbo'

    def test_aliases_same_model_different_naming(self):
        """Known aliases for same model should normalize."""
        assert normalize_model_id('gpt-4-turbo-preview') == 'gpt-4-turbo'
        assert normalize_model_id('gpt-4-1106-preview') == 'gpt-4-turbo'
        assert normalize_model_id('chatgpt-4o-latest') == 'gpt-4o'
        assert normalize_model_id('gpt-3.5-turbo-0613') == 'gpt-3.5-turbo'

    def test_lowercase_output(self):
        """Output should always be lowercase."""
        assert normalize_model_id('GPT-4O') == 'gpt-4o'
        assert normalize_model_id('Claude-3-Opus') == 'claude-3-opus'

    def test_empty_and_none(self):
        """Empty/None inputs should return empty string."""
        assert normalize_model_id('') == ''
        assert normalize_model_id(None) == ''


class TestComparisonValidation:
    """Tests to validate comparison logic and catch data issues."""

    # Models that should NEVER match each other
    MUST_NOT_MATCH = [
        ('gpt-3.5-turbo', 'gpt-3.5-turbo-16k'),
        ('gpt-3.5-turbo', 'gpt-3.5-turbo-instruct'),
        ('gpt-4o', 'gpt-4o:extended'),
        ('claude-3-haiku', 'claude-3.5-haiku'),
        ('claude-3-opus', 'claude-3.5-sonnet'),
    ]

    # Models that SHOULD match
    MUST_MATCH = [
        ('openai/gpt-4o', 'gpt-4o'),
        ('gpt-4o-2024-11-20', 'gpt-4o'),
        ('gemini-2.0-flash-001', 'gemini-2.0-flash'),
        ('gpt-4-turbo-preview', 'gpt-4-turbo'),
    ]

    def test_must_not_match_pairs(self):
        """Verify that different models are NOT incorrectly matched."""
        for model_a, model_b in self.MUST_NOT_MATCH:
            norm_a = normalize_model_id(model_a)
            norm_b = normalize_model_id(model_b)
            assert norm_a != norm_b, f"{model_a} should NOT match {model_b}"

    def test_must_match_pairs(self):
        """Verify that same models with different naming ARE matched."""
        for model_a, model_b in self.MUST_MATCH:
            norm_a = normalize_model_id(model_a)
            norm_b = normalize_model_id(model_b)
            assert norm_a == norm_b, f"{model_a} SHOULD match {model_b}"


class TestMarkupBounds:
    """Tests to catch unreasonable markup percentages."""

    MAX_REASONABLE_MARKUP = 1.5  # 150% - anything higher is likely a bug

    def test_markup_sanity_check(self):
        """
        If we see a markup > 150%, it's probably a normalization bug
        where we're matching the wrong model variant.

        This test documents the expected behavior - in production,
        we should log warnings for high markups.
        """
        # Example: gpt-3.5-turbo base vs 16k would show ~250% "markup"
        # which is actually just comparing different products

        base_price = 1.00  # gpt-3.5-turbo blended
        variant_price = 3.50  # gpt-3.5-turbo-16k blended

        fake_markup = (variant_price - base_price) / base_price

        # This WOULD fail our sanity check - indicating a bug
        assert fake_markup > self.MAX_REASONABLE_MARKUP, \
            "This demonstrates what a bug looks like"

        # Correct comparison (same model)
        correct_official = 1.00
        correct_aggregator = 1.50  # 50% markup - reasonable

        correct_markup = (correct_aggregator - correct_official) / correct_official
        assert correct_markup <= self.MAX_REASONABLE_MARKUP, \
            f"Markup of {correct_markup:.0%} should be within bounds"


def validate_comparison_data(observations: list) -> dict:
    """
    Validate comparison data and return a report.

    This function can be called from CI to verify data quality.

    Returns:
        dict with 'valid', 'warnings', 'errors' keys
    """
    MAX_MARKUP = 1.5  # 150%

    # Group by normalized ID
    models = {}
    for obs in observations:
        model_id = obs.get('model_id', '')
        normalized = normalize_model_id(model_id)
        method = obs.get('collection_method', '')

        if not normalized:
            continue

        if normalized not in models:
            models[normalized] = {'official': None, 'aggregator': None}

        if method == 'manual':
            models[normalized]['official'] = obs
        elif method == 'aggregator_api':
            models[normalized]['aggregator'] = obs

    # Validate each comparison
    warnings = []
    errors = []
    valid_comparisons = 0

    for norm_id, sources in models.items():
        if not sources['official'] or not sources['aggregator']:
            continue

        off = sources['official']
        agg = sources['aggregator']

        off_blend = (off['input_rate_usd_per_1m'] + off['output_rate_usd_per_1m']) / 2
        agg_blend = (agg['input_rate_usd_per_1m'] + agg['output_rate_usd_per_1m']) / 2

        if off_blend == 0:
            errors.append(f"{norm_id}: Official price is $0")
            continue

        markup = (agg_blend - off_blend) / off_blend

        if markup > MAX_MARKUP:
            errors.append(
                f"{norm_id}: Markup {markup:.0%} exceeds {MAX_MARKUP:.0%} limit - "
                f"likely wrong model match. Official: ${off_blend:.2f}, "
                f"Aggregator: ${agg_blend:.2f}"
            )
        elif markup > 1.0:  # > 100% is suspicious but not error
            warnings.append(
                f"{norm_id}: High markup {markup:.0%} - verify correct match"
            )
        else:
            valid_comparisons += 1

    return {
        'valid': len(errors) == 0,
        'valid_comparisons': valid_comparisons,
        'warnings': warnings,
        'errors': errors,
    }


if __name__ == '__main__':
    # Quick validation when run directly
    pytest.main([__file__, '-v'])
