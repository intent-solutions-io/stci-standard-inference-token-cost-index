"""
STCI Drift Detection - Compare prices across multiple sources.

Detects discrepancies when the same model has different pricing
from different sources (e.g., OpenRouter vs official API).
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class DriftReport:
    """Results from drift detection analysis."""

    discrepancies: List[Tuple[str, str, str, float, float]] = field(default_factory=list)
    """List of (model_id, source1, source2, input_diff_pct, output_diff_pct)"""

    warnings: List[str] = field(default_factory=list)
    """Human-readable warning messages"""

    @property
    def has_warnings(self) -> bool:
        """Check if any drift warnings were generated."""
        return len(self.warnings) > 0

    @property
    def discrepancy_count(self) -> int:
        """Number of model/source pairs with price drift."""
        return len(self.discrepancies)


def normalize_model_id(model_id: str) -> str:
    """
    Normalize model ID for comparison across sources.

    Different sources may use different naming conventions:
    - OpenRouter: "openai/gpt-4o"
    - Direct: "gpt-4o"

    This normalizes to the base model name.
    """
    # Remove provider prefix if present
    if "/" in model_id:
        parts = model_id.split("/")
        # Handle cases like "openai/gpt-4o" -> "gpt-4o"
        # But keep "meta-llama/llama-3" as "llama-3"
        if len(parts) == 2:
            return parts[1]
    return model_id


def detect_drift(
    observations: List[dict],
    threshold: float = 0.05,
) -> DriftReport:
    """
    Compare prices across sources for the same model.

    Args:
        observations: List of observation dictionaries from multiple sources
        threshold: Maximum allowed price difference as a fraction (default 5%)

    Returns:
        DriftReport with discrepancies and warnings
    """
    report = DriftReport()

    # Group observations by normalized model ID
    model_prices: dict[str, list[dict]] = {}
    for obs in observations:
        model_id = obs.get("model_id", "")
        normalized = normalize_model_id(model_id)

        if normalized not in model_prices:
            model_prices[normalized] = []
        model_prices[normalized].append(obs)

    # Compare prices within each model group
    for normalized_id, obs_list in model_prices.items():
        if len(obs_list) < 2:
            # Need at least 2 sources to compare
            continue

        # Compare all pairs
        for i in range(len(obs_list)):
            for j in range(i + 1, len(obs_list)):
                obs1 = obs_list[i]
                obs2 = obs_list[j]

                source1 = obs1.get("source_url", obs1.get("collection_method", "source1"))
                source2 = obs2.get("source_url", obs2.get("collection_method", "source2"))

                input1 = obs1.get("input_rate_usd_per_1m", 0)
                input2 = obs2.get("input_rate_usd_per_1m", 0)
                output1 = obs1.get("output_rate_usd_per_1m", 0)
                output2 = obs2.get("output_rate_usd_per_1m", 0)

                # Calculate percentage differences
                input_diff = _calc_diff_pct(input1, input2)
                output_diff = _calc_diff_pct(output1, output2)

                # Check if drift exceeds threshold
                if input_diff > threshold or output_diff > threshold:
                    # Extract source names for readable warnings
                    src1_name = _extract_source_name(source1)
                    src2_name = _extract_source_name(source2)

                    report.discrepancies.append(
                        (normalized_id, src1_name, src2_name, input_diff, output_diff)
                    )

                    # Generate warning message
                    if input_diff > threshold and output_diff > threshold:
                        report.warnings.append(
                            f"{normalized_id}: {src1_name} vs {src2_name} - "
                            f"input differs by {input_diff:.1%}, output differs by {output_diff:.1%}"
                        )
                    elif input_diff > threshold:
                        report.warnings.append(
                            f"{normalized_id}: {src1_name} vs {src2_name} - "
                            f"input differs by {input_diff:.1%}"
                        )
                    else:
                        report.warnings.append(
                            f"{normalized_id}: {src1_name} vs {src2_name} - "
                            f"output differs by {output_diff:.1%}"
                        )

    return report


def _calc_diff_pct(val1: float, val2: float) -> float:
    """Calculate percentage difference between two values."""
    if val1 == 0 and val2 == 0:
        return 0.0
    if val1 == 0 or val2 == 0:
        return 1.0  # 100% difference if one is zero
    avg = (val1 + val2) / 2
    return abs(val1 - val2) / avg


def _extract_source_name(source: str) -> str:
    """Extract readable source name from URL or method."""
    if "openrouter" in source.lower():
        return "openrouter"
    if "openai" in source.lower():
        return "openai"
    if "anthropic" in source.lower():
        return "anthropic"
    if "google" in source.lower() or "cloud.google" in source.lower():
        return "google"
    if source == "config_file":
        return "config"
    return source[:20]  # Truncate long strings
