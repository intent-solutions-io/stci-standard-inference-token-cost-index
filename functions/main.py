"""
Inference Price Index - Firebase Functions API

Serves the STCI API from Firestore data.
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
import json

# Defer initialization until runtime (not during function analysis)
_app = None
_db = None


def get_db():
    """Lazy-load Firestore client on first use."""
    global _app, _db
    if _db is None:
        _app = initialize_app()
        _db = firestore.client()
    return _db


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Main API handler - routes to appropriate endpoint."""
    path = req.path

    if path == "/health":
        return handle_health()
    elif path == "/v1/index/latest":
        return handle_index_latest()
    elif path.startswith("/v1/index/"):
        date = path.split("/")[-1]
        return handle_index_date(date)
    elif path == "/v1/indices":
        return handle_indices_list()
    elif path.startswith("/v1/observations/"):
        date = path.split("/")[-1]
        return handle_observations(date)
    elif path == "/v1/methodology":
        return handle_methodology()
    else:
        return https_fn.Response(
            json.dumps({"error": "Not found"}),
            status=404,
            headers={"Content-Type": "application/json"}
        )


def handle_health():
    """Health check endpoint."""
    return json_response({
        "status": "healthy",
        "service": "inference-price-index"
    })


def handle_index_latest():
    """Get the most recent index."""
    db = get_db()
    docs = db.collection("indices").order_by(
        "date", direction=firestore.Query.DESCENDING
    ).limit(1).stream()

    for doc in docs:
        return json_response(doc.to_dict())

    return json_response({"error": "No data"}, 404)


def handle_index_date(date: str):
    """Get index for a specific date."""
    db = get_db()
    doc = db.collection("indices").document(date).get()
    if doc.exists:
        return json_response(doc.to_dict())
    return json_response({"error": f"No data for {date}"}, 404)


def handle_indices_list():
    """List all available index dates."""
    db = get_db()
    docs = db.collection("indices").order_by(
        "date", direction=firestore.Query.DESCENDING
    ).stream()

    dates = [doc.id for doc in docs]
    return json_response({
        "dates": dates,
        "count": len(dates),
        "latest": dates[0] if dates else None
    })


def handle_observations(date: str):
    """Get raw pricing observations for a date."""
    db = get_db()
    doc = db.collection("observations").document(date).get()
    if doc.exists:
        return json_response(doc.to_dict())
    return json_response({"error": f"No observations for {date}"}, 404)


def handle_methodology():
    """Get current index methodology."""
    db = get_db()
    doc = db.collection("methodology").document("current").get()
    if doc.exists:
        return json_response(doc.to_dict())
    return json_response({"error": "Methodology not found"}, 404)


def json_response(data: dict, status: int = 200):
    """Create a JSON response with standard headers."""
    return https_fn.Response(
        json.dumps(data, indent=2),
        status=status,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=60"
        }
    )
