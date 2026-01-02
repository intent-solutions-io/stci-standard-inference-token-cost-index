# STCI Indexer Service
"""
Indexer service for computing STCI daily reference rates.

Usage:
    from services.indexer import Indexer

    indexer = Indexer()
    result = indexer.compute(observations, methodology)
"""

from .indexer import Indexer, compute_index

__all__ = ["Indexer", "compute_index"]
