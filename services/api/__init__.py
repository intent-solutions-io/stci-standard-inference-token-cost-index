# STCI API Service
"""
Read-only API for serving STCI index values and observations.

Usage:
    python -m services.api.main

Endpoints:
    GET /health - Health check
    GET /v1/index/latest - Latest index values
    GET /v1/index/{date} - Index for specific date
    GET /v1/observations/{date} - Observations for date
    GET /v1/methodology - Current methodology
"""

__all__ = ["create_app"]
