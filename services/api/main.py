"""
STCI API - Read-only API for serving index data.

This is a minimal stub implementation using Python's built-in http.server.
For production, replace with FastAPI, Flask, or similar.
"""

import json
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs


class STCIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for STCI API."""

    # Data directory (stub - would be database in production)
    DATA_DIR = Path(__file__).parent.parent.parent / "data"

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
        else:
            self._send_error(404, "Not found")

    def _handle_health(self):
        """Health check endpoint."""
        self._send_json({
            "status": "healthy",
            "service": "stci-api",
            "version": "0.1.0",
        })

    def _handle_index_latest(self):
        """Get latest index values."""
        # Stub: return sample data
        # In production, query database for most recent
        self._send_json({
            "date": date.today().isoformat(),
            "indices": {
                "STCI-ALL": {
                    "input_rate": 1.42,
                    "output_rate": 5.67,
                    "blended_rate": 4.61,
                    "model_count": 10,
                },
                "STCI-FRONTIER": {
                    "input_rate": 2.19,
                    "output_rate": 9.00,
                    "blended_rate": 7.30,
                    "model_count": 4,
                },
                "STCI-EFFICIENT": {
                    "input_rate": 0.31,
                    "output_rate": 1.38,
                    "blended_rate": 1.11,
                    "model_count": 4,
                },
            },
            "methodology_version": "1.0.0",
            "note": "Stub data - implement database backend for production",
        })

    def _handle_index_date(self, date_str: str):
        """Get index for specific date."""
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            self._send_error(400, f"Invalid date format: {date_str}")
            return

        # Stub: return sample data with requested date
        self._send_json({
            "date": target_date.isoformat(),
            "indices": {
                "STCI-ALL": {
                    "input_rate": 1.42,
                    "output_rate": 5.67,
                    "blended_rate": 4.61,
                    "model_count": 10,
                },
            },
            "methodology_version": "1.0.0",
            "note": "Stub data - implement database backend for production",
        })

    def _handle_observations_date(self, date_str: str):
        """Get observations for specific date."""
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            self._send_error(400, f"Invalid date format: {date_str}")
            return

        # Try to load from fixtures
        fixture_path = self.DATA_DIR / "fixtures" / "observations.sample.json"
        if fixture_path.exists():
            with open(fixture_path) as f:
                observations = json.load(f)
            self._send_json({
                "date": target_date.isoformat(),
                "observations": observations,
                "count": len(observations),
                "note": "Fixture data - implement database backend for production",
            })
        else:
            self._send_error(404, f"No observations for {date_str}")

    def _handle_methodology(self):
        """Get current methodology."""
        methodology_path = self.DATA_DIR / "fixtures" / "methodology.yaml"
        if methodology_path.exists():
            import yaml
            with open(methodology_path) as f:
                methodology = yaml.safe_load(f)
            self._send_json(methodology)
        else:
            self._send_error(404, "Methodology not found")

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _send_error(self, status: int, message: str):
        """Send error response."""
        self._send_json({"error": message, "status": status}, status)

    def log_message(self, format, *args):
        """Log HTTP requests."""
        print(f"[API] {args[0]}")


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

    server = create_app(args.host, args.port)
    print(f"STCI API running on http://{args.host}:{args.port}")
    print("Endpoints:")
    print("  GET /health")
    print("  GET /v1/index/latest")
    print("  GET /v1/index/{date}")
    print("  GET /v1/observations/{date}")
    print("  GET /v1/methodology")
    print()
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
