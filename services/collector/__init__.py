# STCI Collector Service
"""
Collector service for fetching pricing data from sources.

Primary source: OpenRouter API
Fallback: Manual fixtures

Usage:
    from services.collector import Collector

    collector = Collector()
    observations = collector.collect(date="2026-01-01")
"""

from .collector import Collector
from .sources import OpenRouterSource, FixtureSource

__all__ = ["Collector", "OpenRouterSource", "FixtureSource"]
