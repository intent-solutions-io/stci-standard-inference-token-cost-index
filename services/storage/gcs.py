"""
STCI GCS Storage Backend - Google Cloud Storage implementation.
"""

import logging
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)


class GCSStorage:
    """Google Cloud Storage backend."""

    def __init__(self, bucket_name: str):
        """
        Initialize GCS storage backend.

        Args:
            bucket_name: GCS bucket name (without gs:// prefix)
        """
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name
        logger.info(f"Initialized GCS storage: gs://{bucket_name}")

    def read(self, path: str) -> Optional[str]:
        """
        Read content from GCS.

        Args:
            path: Object path within bucket (e.g., "indices/2026-01-01.json")

        Returns:
            Content as string, or None if not found
        """
        try:
            blob = self.bucket.blob(path)
            content = blob.download_as_text()
            logger.debug(f"Read gs://{self.bucket_name}/{path}")
            return content
        except NotFound:
            logger.debug(f"Not found: gs://{self.bucket_name}/{path}")
            return None

    def write(self, path: str, content: str) -> None:
        """
        Write content to GCS.

        Args:
            path: Object path within bucket
            content: Content to write
        """
        blob = self.bucket.blob(path)
        blob.upload_from_string(content, content_type="application/json")
        logger.info(f"Wrote gs://{self.bucket_name}/{path}")

    def exists(self, path: str) -> bool:
        """
        Check if object exists in GCS.

        Args:
            path: Object path within bucket

        Returns:
            True if exists, False otherwise
        """
        blob = self.bucket.blob(path)
        return blob.exists()

    def list_files(self, prefix: str, suffix: str = "") -> list[str]:
        """
        List files matching prefix and optional suffix.

        Args:
            prefix: Path prefix (e.g., "indices/")
            suffix: Optional suffix filter (e.g., ".json")

        Returns:
            List of matching file paths
        """
        blobs = self.client.list_blobs(self.bucket, prefix=prefix)
        files = []
        for blob in blobs:
            if suffix and not blob.name.endswith(suffix):
                continue
            files.append(blob.name)
        return sorted(files)
