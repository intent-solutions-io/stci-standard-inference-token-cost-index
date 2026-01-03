"""
STCI Storage Abstraction - Unified interface for local and cloud storage.
"""

import os
from typing import Protocol, Optional


class StorageBackend(Protocol):
    """Protocol defining storage backend interface."""

    def read(self, path: str) -> Optional[str]:
        """Read content from path. Returns None if not found."""
        ...

    def write(self, path: str, content: str) -> None:
        """Write content to path."""
        ...

    def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...

    def list_files(self, prefix: str, suffix: str = "") -> list[str]:
        """List files matching prefix and optional suffix."""
        ...


def get_storage_backend() -> StorageBackend:
    """
    Factory function to get appropriate storage backend.

    Priority:
    1. Firestore if USE_FIRESTORE is set
    2. GCS if GCS_BUCKET is set
    3. Local filesystem (default)
    """
    if os.environ.get("USE_FIRESTORE"):
        from .firestore import FirestoreStorage
        return FirestoreStorage()
    elif os.environ.get("GCS_BUCKET"):
        from .gcs import GCSStorage
        return GCSStorage(os.environ["GCS_BUCKET"])
    else:
        from .local import LocalStorage
        return LocalStorage()
