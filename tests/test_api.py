"""
Tests for the STCI API service.
"""

import json
import threading
import time
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

import pytest

from services.api.main import STCIHandler, create_app


class TestSTCIHandler:
    """Tests for API handlers using direct method calls."""

    @pytest.fixture
    def handler_with_data(self, temp_data_dir, sample_observations):
        """Create a handler with data directory set."""
        # Create index file
        index_data = {
            "date": "2026-01-01",
            "indices": {
                "STCI-ALL": {
                    "input_rate": 1.88,
                    "output_rate": 8.53,
                    "blended_rate": 6.87,
                    "model_count": 3,
                    "models_included": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"],
                }
            },
            "methodology_version": "1.0.0",
            "computed_at": "2026-01-01T00:35:00Z",
            "verification_hash": "abc123def456",
            "observation_count": 3,
        }
        with open(temp_data_dir / "indices" / "2026-01-01.json", "w") as f:
            json.dump(index_data, f)

        # Patch DATA_DIR
        original_data_dir = STCIHandler.DATA_DIR
        STCIHandler.DATA_DIR = temp_data_dir
        STCIHandler._index_cache = {}
        STCIHandler._methodology_cache = None

        yield temp_data_dir

        # Restore
        STCIHandler.DATA_DIR = original_data_dir
        STCIHandler._index_cache = {}
        STCIHandler._methodology_cache = None


class TestAPIServer:
    """Integration tests for API server."""

    @pytest.fixture
    def server(self, temp_data_dir, sample_observations):
        """Start a test server."""
        # Create index file
        index_data = {
            "date": "2026-01-01",
            "indices": {
                "STCI-ALL": {
                    "input_rate": 1.88,
                    "output_rate": 8.53,
                    "blended_rate": 6.87,
                    "model_count": 3,
                }
            },
            "methodology_version": "1.0.0",
            "computed_at": "2026-01-01T00:35:00Z",
            "verification_hash": "abc123",
            "observation_count": 3,
        }
        with open(temp_data_dir / "indices" / "2026-01-01.json", "w") as f:
            json.dump(index_data, f)

        # Patch DATA_DIR before creating server
        original_data_dir = STCIHandler.DATA_DIR
        STCIHandler.DATA_DIR = temp_data_dir
        STCIHandler._index_cache = {}
        STCIHandler._methodology_cache = None

        # Create and start server
        server = create_app("127.0.0.1", 0)  # Port 0 = random available port
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)  # Give server time to start

        yield {"host": "127.0.0.1", "port": port, "data_dir": temp_data_dir}

        server.shutdown()
        STCIHandler.DATA_DIR = original_data_dir
        STCIHandler._index_cache = {}

    def _get(self, server, path):
        """Make GET request to test server."""
        conn = HTTPConnection(server["host"], server["port"])
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read().decode()
        conn.close()
        return response.status, json.loads(data) if data else None

    def test_health_endpoint(self, server):
        """Test /health endpoint."""
        status, data = self._get(server, "/health")

        assert status == 200
        assert data["status"] == "healthy"
        assert data["service"] == "stci-api"
        assert data["data_available"] is True

    def test_root_endpoint(self, server):
        """Test / endpoint returns API docs."""
        status, data = self._get(server, "/")

        assert status == 200
        assert data["name"] == "STCI API"
        assert "endpoints" in data

    def test_indices_list(self, server):
        """Test /v1/indices endpoint."""
        status, data = self._get(server, "/v1/indices")

        assert status == 200
        assert "dates" in data
        assert "2026-01-01" in data["dates"]
        assert data["latest"] == "2026-01-01"

    def test_index_latest(self, server):
        """Test /v1/index/latest endpoint."""
        status, data = self._get(server, "/v1/index/latest")

        assert status == 200
        assert data["date"] == "2026-01-01"
        assert "STCI-ALL" in data["indices"]

    def test_index_by_date(self, server):
        """Test /v1/index/{date} endpoint."""
        status, data = self._get(server, "/v1/index/2026-01-01")

        assert status == 200
        assert data["date"] == "2026-01-01"
        assert data["indices"]["STCI-ALL"]["blended_rate"] == 6.87

    def test_index_not_found(self, server):
        """Test 404 for missing date."""
        status, data = self._get(server, "/v1/index/1999-01-01")

        assert status == 404
        assert "error" in data

    def test_index_invalid_date(self, server):
        """Test 400 for invalid date format."""
        status, data = self._get(server, "/v1/index/not-a-date")

        assert status == 400
        assert "error" in data

    def test_observations_endpoint(self, server):
        """Test /v1/observations/{date} endpoint."""
        status, data = self._get(server, "/v1/observations/2026-01-01")

        assert status == 200
        assert data["date"] == "2026-01-01"
        assert data["count"] == 3
        assert len(data["observations"]) == 3

    def test_observations_not_found(self, server):
        """Test 404 for missing observations."""
        status, data = self._get(server, "/v1/observations/1999-01-01")

        assert status == 404

    def test_methodology_endpoint(self, server):
        """Test /v1/methodology endpoint."""
        status, data = self._get(server, "/v1/methodology")

        assert status == 200
        assert data["methodology_version"] == "1.0.0"
        assert "indices" in data

    def test_cors_headers(self, server):
        """Test CORS headers are present."""
        conn = HTTPConnection(server["host"], server["port"])
        conn.request("GET", "/health")
        response = conn.getresponse()

        assert response.getheader("Access-Control-Allow-Origin") == "*"
        conn.close()

    def test_content_type_json(self, server):
        """Test Content-Type is application/json."""
        conn = HTTPConnection(server["host"], server["port"])
        conn.request("GET", "/health")
        response = conn.getresponse()

        assert response.getheader("Content-Type") == "application/json"
        conn.close()

    def test_not_found_endpoint(self, server):
        """Test 404 for unknown endpoints."""
        status, data = self._get(server, "/unknown/endpoint")

        assert status == 404
        assert "error" in data

    def test_caching(self, server):
        """Test that index data is cached."""
        # First request
        status1, data1 = self._get(server, "/v1/index/2026-01-01")
        assert status1 == 200

        # Second request should use cache
        status2, data2 = self._get(server, "/v1/index/2026-01-01")
        assert status2 == 200

        # Data should be identical
        assert data1 == data2


class TestAPIDataFormats:
    """Tests for API data format handling."""

    @pytest.fixture
    def server_with_jsonl(self, temp_data_dir, sample_observations):
        """Server with JSONL observations."""
        # Write as JSONL
        with open(temp_data_dir / "observations" / "2026-01-01.jsonl", "w") as f:
            for obs in sample_observations:
                f.write(json.dumps(obs) + "\n")

        original_data_dir = STCIHandler.DATA_DIR
        STCIHandler.DATA_DIR = temp_data_dir
        STCIHandler._index_cache = {}

        server = create_app("127.0.0.1", 0)
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.1)

        yield {"host": "127.0.0.1", "port": port}

        server.shutdown()
        STCIHandler.DATA_DIR = original_data_dir

    def test_jsonl_observations(self, server_with_jsonl):
        """Test loading observations from JSONL."""
        conn = HTTPConnection(server_with_jsonl["host"], server_with_jsonl["port"])
        conn.request("GET", "/v1/observations/2026-01-01")
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()

        assert response.status == 200
        assert data["count"] == 3
