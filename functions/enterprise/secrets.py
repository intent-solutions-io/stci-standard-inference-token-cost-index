"""
Secret Manager Integration

Secure storage for enterprise API keys using Google Secret Manager.
"""

from google.cloud import secretmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Interface to Google Secret Manager for storing enterprise API keys.

    Keys are stored as:
    - projects/{project}/secrets/enterprise-{enterprise_id}-{provider}/versions/latest
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._client: Optional[secretmanager.SecretManagerServiceClient] = None

    @property
    def client(self) -> secretmanager.SecretManagerServiceClient:
        """Lazy-load the Secret Manager client."""
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client

    def _secret_id(self, enterprise_id: str, provider: str) -> str:
        """Generate a consistent secret ID."""
        return f"enterprise-{enterprise_id}-{provider}"

    def _secret_name(self, enterprise_id: str, provider: str) -> str:
        """Full secret resource name."""
        secret_id = self._secret_id(enterprise_id, provider)
        return f"projects/{self.project_id}/secrets/{secret_id}"

    def _version_name(self, enterprise_id: str, provider: str) -> str:
        """Full version resource name (latest)."""
        return f"{self._secret_name(enterprise_id, provider)}/versions/latest"

    def store_api_key(
        self,
        enterprise_id: str,
        provider: str,
        api_key: str
    ) -> str:
        """
        Store an API key in Secret Manager.

        Creates a new secret if it doesn't exist, or adds a new version
        if it does (for key rotation).

        Returns the secret version name.
        """
        secret_id = self._secret_id(enterprise_id, provider)
        secret_name = self._secret_name(enterprise_id, provider)
        parent = f"projects/{self.project_id}"

        # Try to create the secret first
        try:
            self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                        "labels": {
                            "enterprise_id": enterprise_id,
                            "provider": provider,
                            "type": "api-key",
                        },
                    },
                }
            )
            logger.info(f"Created secret {secret_id}")
        except Exception as e:
            # Secret already exists, which is fine
            if "ALREADY_EXISTS" not in str(e):
                raise

        # Add the secret version
        response = self.client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": api_key.encode("UTF-8")},
            }
        )

        logger.info(f"Stored API key version: {response.name}")
        return response.name

    def get_api_key(self, enterprise_id: str, provider: str) -> Optional[str]:
        """
        Retrieve an API key from Secret Manager.

        Returns None if the secret doesn't exist or has been deleted.
        """
        try:
            version_name = self._version_name(enterprise_id, provider)
            response = self.client.access_secret_version(
                request={"name": version_name}
            )
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to access secret for {enterprise_id}/{provider}: {e}")
            return None

    def delete_api_key(self, enterprise_id: str, provider: str) -> bool:
        """
        Delete an API key from Secret Manager.

        This deletes the entire secret, not just a version.
        """
        try:
            secret_name = self._secret_name(enterprise_id, provider)
            self.client.delete_secret(request={"name": secret_name})
            logger.info(f"Deleted secret for {enterprise_id}/{provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret for {enterprise_id}/{provider}: {e}")
            return False

    def key_exists(self, enterprise_id: str, provider: str) -> bool:
        """Check if an API key exists for an enterprise/provider."""
        try:
            version_name = self._version_name(enterprise_id, provider)
            self.client.access_secret_version(request={"name": version_name})
            return True
        except Exception:
            return False
