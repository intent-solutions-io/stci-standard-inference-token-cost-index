"""
STCI Local Storage Backend - Filesystem implementation.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalStorage:
    """Local filesystem storage backend."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize local storage backend.

        Args:
            base_path: Base directory for storage. Defaults to project data/ dir.
        """
        if base_path is None:
            # Default to project root data/ directory
            self.base_path = Path(__file__).parent.parent.parent / "data"
        else:
            self.base_path = Path(base_path)
        logger.info(f"Initialized local storage: {self.base_path}")

    def _full_path(self, path: str) -> Path:
        """Get full filesystem path."""
        return self.base_path / path

    def read(self, path: str) -> Optional[str]:
        """
        Read content from local filesystem.

        Args:
            path: Relative path within data directory

        Returns:
            Content as string, or None if not found
        """
        full_path = self._full_path(path)
        if not full_path.exists():
            logger.debug(f"Not found: {full_path}")
            return None
        content = full_path.read_text()
        logger.debug(f"Read {full_path}")
        return content

    def write(self, path: str, content: str) -> None:
        """
        Write content to local filesystem.

        Args:
            path: Relative path within data directory
            content: Content to write
        """
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        logger.info(f"Wrote {full_path}")

    def exists(self, path: str) -> bool:
        """
        Check if file exists.

        Args:
            path: Relative path within data directory

        Returns:
            True if exists, False otherwise
        """
        return self._full_path(path).exists()

    def list_files(self, prefix: str, suffix: str = "") -> list[str]:
        """
        List files matching prefix and optional suffix.

        Args:
            prefix: Path prefix (e.g., "indices/")
            suffix: Optional suffix filter (e.g., ".json")

        Returns:
            List of matching file paths (relative to base)
        """
        prefix_path = self._full_path(prefix)
        if not prefix_path.exists():
            return []

        files = []
        if prefix_path.is_dir():
            for f in prefix_path.iterdir():
                if f.is_file() and (not suffix or f.name.endswith(suffix)):
                    # Return path relative to base
                    files.append(str(f.relative_to(self.base_path)))
        return sorted(files)
