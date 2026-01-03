"""
STCI API - Read-only API for serving index data.

Serves computed indices and observations from the data directory.
"""

import json
import os
from datetime import date, datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

import yaml


class STCIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for STCI API."""

    # Data directory
    DATA_DIR = Path(__file__).parent.parent.parent / "data"

    # Cache for loaded data
    _index_cache = {}
    _methodology_cache = None

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Route to handlers
        if path == "/health":
            self._handle_health()
        elif path == "/v1/index/latest":
            self._handle_index_latest()
        elif path.startswith("/v1/index/"):
            date_str = path.split("/")[-1]
            self._handle_index_date(date_str)
        elif path.startswith("/v1/observations/"):
            date_str = path.split("/")[-1]
            self._handle_observations_date(date_str)
        elif path == "/v1/methodology":
            self._handle_methodology()
        elif path == "/v1/indices":
            self._handle_available_indices()
        elif path == "/":
            self._handle_root()
        else:
            self._send_error(404, "Not found")

    def _handle_root(self):
        """API documentation endpoint."""
        self._send_json({
            "name": "STCI API",
            "version": "0.1.0",
            "description": "Standard Token Cost Index - LLM pricing reference rates",
            "endpoints": {
                "GET /health": "Health check",
                "GET /v1/index/latest": "Latest computed index",
                "GET /v1/index/{date}": "Index for specific date (YYYY-MM-DD)",
                "GET /v1/indices": "List all available index dates",
                "GET /v1/observations/{date}": "Observations for date",
                "GET /v1/methodology": "Current methodology configuration",
            },
            "repository": "https://github.com/intent-solutions-io/stci-standard-llm-token-cost-index",
        })

    def _handle_health(self):
        """Health check endpoint."""
        # Check if we have any data
        indices_dir = self.DATA_DIR / "indices"
        has_data = indices_dir.exists() and any(indices_dir.glob("*.json"))

        self._send_json({
            "status": "healthy",
            "service": "stci-api",
            "version": "0.1.0",
            "data_available": has_data,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })

    def _handle_index_latest(self):
        """Get latest index values."""
        latest_date = self._find_latest_index_date()

        if not latest_date:
            self._send_error(404, "No index data available")
            return

        self._handle_index_date(latest_date)

    def _handle_index_date(self, date_str: str):
        """Get index for specific date."""
        # Validate date format
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            self._send_error(400, f"Invalid date format: {date_str}. Use YYYY-MM-DD")
            return

        # Check cache
        if date_str in self._index_cache:
            self._send_json(self._index_cache[date_str])
            return

        # Load from file
        index_path = self.DATA_DIR / "indices" / f"{date_str}.json"

        if not index_path.exists():
            self._send_error(404, f"No index data for {date_str}")
            return

        try:
            with open(index_path) as f:
                index_data = json.load(f)

            # Cache it
            self._index_cache[date_str] = index_data
            self._send_json(index_data)

        except json.JSONDecodeError as e:
            self._send_error(500, f"Error parsing index data: {e}")

    def _handle_observations_date(self, date_str: str):
        """Get observations for specific date."""
        # Validate date format
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            self._send_error(400, f"Invalid date format: {date_str}. Use YYYY-MM-DD")
            return

        # Try JSONL first
        obs_path = self.DATA_DIR / "observations" / f"{date_str}.jsonl"

        if obs_path.exists():
            observations = self._load_jsonl(obs_path)
            self._send_json({
                "date": date_str,
                "count": len(observations),
                "observations": observations,
            })
            return

        # Try JSON fallback
        json_path = self.DATA_DIR / "observations" / f"{date_str}.json"
        if json_path.exists():
            with open(json_path) as f:
                observations = json.load(f)
            self._send_json({
                "date": date_str,
                "count": len(observations),
                "observations": observations,
            })
            return

        self._send_error(404, f"No observations for {date_str}")

    def _handle_methodology(self):
        """Get current methodology."""
        if self._methodology_cache:
            self._send_json(self._methodology_cache)
            return

        methodology_path = self.DATA_DIR / "fixtures" / "methodology.yaml"

        if not methodology_path.exists():
            self._send_error(404, "Methodology not found")
            return

        try:
            with open(methodology_path) as f:
                methodology = yaml.safe_load(f)
            STCIHandler._methodology_cache = methodology
            self._send_json(methodology)
        except Exception as e:
            self._send_error(500, f"Error loading methodology: {e}")

    def _handle_available_indices(self):
        """List all available index dates."""
        indices_dir = self.DATA_DIR / "indices"

        if not indices_dir.exists():
            self._send_json({"dates": [], "count": 0})
            return

        dates = []
        for f in sorted(indices_dir.glob("*.json"), reverse=True):
            date_str = f.stem
            try:
                date.fromisoformat(date_str)
                dates.append(date_str)
            except ValueError:
                continue

        self._send_json({
            "dates": dates,
            "count": len(dates),
            "latest": dates[0] if dates else None,
        })

    def _find_latest_index_date(self) -> Optional[str]:
        """Find the most recent index date."""
        indices_dir = self.DATA_DIR / "indices"

        if not indices_dir.exists():
            return None

        # Get all JSON files and sort by name (date)
        index_files = sorted(indices_dir.glob("*.json"), reverse=True)

        for f in index_files:
            date_str = f.stem
            try:
                date.fromisoformat(date_str)
                return date_str
            except ValueError:
                continue

        return None

    def _load_jsonl(self, path: Path) -> List[dict]:
        """Load JSONL file."""
        observations = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    observations.append(json.loads(line))
        return observations

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _send_error(self, status: int, message: str):
        """Send error response."""
        self._send_json({"error": message, "status": status}, status)

    def log_message(self, format, *args):
        """Log HTTP requests."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def create_app(host: str = "0.0.0.0", port: int = 8000) -> HTTPServer:
    """Create API server instance."""
    return HTTPServer((host, port), STCIHandler)


def main():
    """Run the API server."""
    import argparse

    parser = argparse.ArgumentParser(description="STCI API Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    args = parser.parse_args()

    # Check for data
    data_dir = Path(__file__).parent.parent.parent / "data"
    indices_dir = data_dir / "indices"
    if indices_dir.exists():
        index_count = len(list(indices_dir.glob("*.json")))
        print(f"Found {index_count} index file(s)")
    else:
        print("Warning: No index data found. Run the collector and indexer first.")

    server = create_app(args.host, args.port)
    print()
    print(f"STCI API running on http://{args.host}:{args.port}")
    print()
    print("Endpoints:")
    print("  GET /                      API documentation")
    print("  GET /health                Health check")
    print("  GET /v1/index/latest       Latest index values")
    print("  GET /v1/index/{date}       Index for specific date")
    print("  GET /v1/indices            List available dates")
    print("  GET /v1/observations/{date} Observations for date")
    print("  GET /v1/methodology        Methodology config")
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
