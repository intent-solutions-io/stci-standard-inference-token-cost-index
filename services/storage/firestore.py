"""
Firestore Storage Backend - Store indices and observations in Cloud Firestore.
"""

import json
from typing import List, Optional

from google.cloud import firestore


class FirestoreStorage:
    """Firestore implementation for storing STCI data."""

    def __init__(self, project_id: Optional[str] = None):
        self.db = firestore.Client(project=project_id)

    def read_index(self, date: str) -> Optional[dict]:
        """Read index data for a specific date."""
        doc = self.db.collection("indices").document(date).get()
        return doc.to_dict() if doc.exists else None

    def write_index(self, date: str, data: dict) -> None:
        """Write index data for a specific date."""
        self.db.collection("indices").document(date).set(data)

    def list_indices(self) -> List[str]:
        """List all available index dates."""
        docs = self.db.collection("indices").stream()
        return sorted([doc.id for doc in docs], reverse=True)

    def read_observations(self, date: str) -> Optional[List[dict]]:
        """Read observations for a specific date."""
        doc = self.db.collection("observations").document(date).get()
        data = doc.to_dict()
        return data.get("items", []) if data else None

    def write_observations(self, date: str, observations: List[dict]) -> None:
        """Write observations for a specific date."""
        self.db.collection("observations").document(date).set({
            "date": date,
            "count": len(observations),
            "items": observations
        })

    def read_methodology(self) -> Optional[dict]:
        """Read the current methodology document."""
        doc = self.db.collection("methodology").document("current").get()
        return doc.to_dict() if doc.exists else None

    def write_methodology(self, data: dict) -> None:
        """Write the current methodology document."""
        self.db.collection("methodology").document("current").set(data)

    # Compatibility with StorageBackend protocol
    def read(self, path: str) -> Optional[str]:
        """Read content from path (compatibility method)."""
        # Parse path like "indices/2026-01-03" or "observations/2026-01-03"
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            collection, doc_id = parts[0], parts[1]
            doc = self.db.collection(collection).document(doc_id).get()
            if doc.exists:
                return json.dumps(doc.to_dict())
        return None

    def write(self, path: str, content: str) -> None:
        """Write content to path (compatibility method)."""
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            collection, doc_id = parts[0], parts[1]
            data = json.loads(content)
            self.db.collection(collection).document(doc_id).set(data)

    def exists(self, path: str) -> bool:
        """Check if path exists (compatibility method)."""
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            collection, doc_id = parts[0], parts[1]
            doc = self.db.collection(collection).document(doc_id).get()
            return doc.exists
        return False

    def list_files(self, prefix: str, suffix: str = "") -> list[str]:
        """List files matching prefix (compatibility method)."""
        # For Firestore, we interpret prefix as collection name
        collection = prefix.strip("/")
        docs = self.db.collection(collection).stream()
        return [f"{collection}/{doc.id}" for doc in docs]
