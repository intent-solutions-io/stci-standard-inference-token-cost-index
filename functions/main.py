"""
Inference Price Index - Firebase Functions API

Serves the STCI API from Firestore data.
Includes Enterprise Usage Tracking endpoints.
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
import json
import os
from datetime import datetime

# Defer initialization until runtime (not during function analysis)
_app = None
_db = None
_secret_manager = None


def get_db():
    """Lazy-load Firestore client on first use."""
    global _app, _db
    if _db is None:
        _app = initialize_app()
        _db = firestore.client()
    return _db


def get_secret_manager():
    """Lazy-load Secret Manager client."""
    global _secret_manager
    if _secret_manager is None:
        from enterprise.secrets import SecretManager
        project_id = os.environ.get("GCLOUD_PROJECT", "stci-production")
        _secret_manager = SecretManager(project_id)
    return _secret_manager


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Main API handler - routes to appropriate endpoint."""
    path = req.path
    method = req.method

    # Handle CORS preflight
    if method == "OPTIONS":
        return cors_response()

    # Public STCI API endpoints
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

    # Enterprise API endpoints
    elif path == "/api/v1/enterprise/connect/openai" and method == "POST":
        return handle_connect_openai(req)
    elif path == "/api/v1/enterprise/connect/anthropic" and method == "POST":
        return handle_connect_anthropic(req)
    elif path == "/api/v1/enterprise/providers":
        return handle_list_providers(req)
    elif path == "/api/v1/enterprise/usage":
        return handle_enterprise_usage(req)
    elif path == "/api/v1/enterprise/sync" and method == "POST":
        return handle_trigger_sync(req)
    elif path == "/api/v1/benchmarks/current":
        return handle_benchmarks(req)

    else:
        return https_fn.Response(
            json.dumps({"error": "Not found"}),
            status=404,
            headers={"Content-Type": "application/json"}
        )


def cors_response():
    """Handle CORS preflight requests."""
    return https_fn.Response(
        "",
        status=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
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


def json_response(data: dict, status: int = 200, cache: bool = True):
    """Create a JSON response with standard headers."""
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }
    if cache:
        headers["Cache-Control"] = "public, max-age=60"
    else:
        headers["Cache-Control"] = "no-store"

    return https_fn.Response(
        json.dumps(data, indent=2),
        status=status,
        headers=headers
    )


# ============================================
# Enterprise API Handlers
# ============================================

def get_enterprise_id(req: https_fn.Request) -> str:
    """
    Extract enterprise ID from request.

    For MVP, we use a simple API key in the Authorization header.
    Format: Bearer enterprise_{id}
    """
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer enterprise_"):
        return auth.replace("Bearer enterprise_", "")
    return None


def handle_connect_openai(req: https_fn.Request):
    """
    Connect an OpenAI account.

    POST /api/v1/enterprise/connect/openai
    Body: {"admin_api_key": "sk-admin-..."}
    """
    try:
        data = req.get_json()
        admin_key = data.get("admin_api_key", "")

        if not admin_key.startswith("sk-admin-"):
            return json_response(
                {"error": "Invalid key format. Expected sk-admin-..."},
                status=400,
                cache=False
            )

        # Validate the key
        from enterprise.providers import OpenAIUsageClient
        client = OpenAIUsageClient(admin_key)
        result = client.validate_key()
        client.close()

        if not result.get("valid"):
            return json_response(
                {"error": result.get("error", "Invalid API key")},
                status=401,
                cache=False
            )

        # For MVP, generate a simple enterprise ID
        import hashlib
        enterprise_id = hashlib.sha256(admin_key[:20].encode()).hexdigest()[:16]

        # Store the key in Secret Manager
        secret_mgr = get_secret_manager()
        key_id = secret_mgr.store_api_key(enterprise_id, "openai", admin_key)

        # Store enterprise record in Firestore
        db = get_db()
        db.collection("enterprises").document(enterprise_id).set({
            "created_at": datetime.utcnow(),
            "providers": {
                "openai": {
                    "connected": True,
                    "key_id": key_id,
                    "connected_at": datetime.utcnow(),
                }
            },
            "settings": {
                "sync_frequency": "daily",
                "share_anonymous_benchmarks": False,
            }
        }, merge=True)

        return json_response({
            "success": True,
            "enterprise_id": enterprise_id,
            "provider": "openai",
            "key_id": key_id,
        }, cache=False)

    except Exception as e:
        return json_response(
            {"error": str(e)},
            status=500,
            cache=False
        )


def handle_connect_anthropic(req: https_fn.Request):
    """
    Connect an Anthropic account.

    POST /api/v1/enterprise/connect/anthropic
    Body: {"admin_api_key": "sk-ant-admin-..."}
    """
    try:
        data = req.get_json()
        admin_key = data.get("admin_api_key", "")

        if not admin_key.startswith("sk-ant-admin-"):
            return json_response(
                {"error": "Invalid key format. Expected sk-ant-admin-..."},
                status=400,
                cache=False
            )

        # Validate the key
        from enterprise.providers import AnthropicUsageClient
        client = AnthropicUsageClient(admin_key)
        result = client.validate_key()
        client.close()

        if not result.get("valid"):
            return json_response(
                {"error": result.get("error", "Invalid API key")},
                status=401,
                cache=False
            )

        # For MVP, generate a simple enterprise ID
        import hashlib
        enterprise_id = hashlib.sha256(admin_key[:20].encode()).hexdigest()[:16]

        # Store the key in Secret Manager
        secret_mgr = get_secret_manager()
        key_id = secret_mgr.store_api_key(enterprise_id, "anthropic", admin_key)

        # Store enterprise record in Firestore
        db = get_db()
        db.collection("enterprises").document(enterprise_id).set({
            "created_at": datetime.utcnow(),
            "providers": {
                "anthropic": {
                    "connected": True,
                    "key_id": key_id,
                    "connected_at": datetime.utcnow(),
                }
            },
            "settings": {
                "sync_frequency": "daily",
                "share_anonymous_benchmarks": False,
            }
        }, merge=True)

        return json_response({
            "success": True,
            "enterprise_id": enterprise_id,
            "provider": "anthropic",
            "key_id": key_id,
        }, cache=False)

    except Exception as e:
        return json_response(
            {"error": str(e)},
            status=500,
            cache=False
        )


def handle_list_providers(req: https_fn.Request):
    """
    List connected providers for an enterprise.

    GET /api/v1/enterprise/providers
    """
    enterprise_id = get_enterprise_id(req)
    if not enterprise_id:
        return json_response(
            {"error": "Missing or invalid Authorization header"},
            status=401,
            cache=False
        )

    db = get_db()
    doc = db.collection("enterprises").document(enterprise_id).get()

    if not doc.exists:
        return json_response(
            {"error": "Enterprise not found"},
            status=404,
            cache=False
        )

    data = doc.to_dict()
    providers = []

    for provider, info in data.get("providers", {}).items():
        if info.get("connected"):
            providers.append({
                "provider": provider,
                "connected": True,
                "connected_at": info.get("connected_at"),
                "last_sync": info.get("last_sync"),
            })

    return json_response({
        "enterprise_id": enterprise_id,
        "providers": providers,
    }, cache=False)


def handle_enterprise_usage(req: https_fn.Request):
    """
    Get usage data for an enterprise.

    GET /api/v1/enterprise/usage?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    enterprise_id = get_enterprise_id(req)
    if not enterprise_id:
        return json_response(
            {"error": "Missing or invalid Authorization header"},
            status=401,
            cache=False
        )

    start_date = req.args.get("start")
    end_date = req.args.get("end")

    if not start_date or not end_date:
        return json_response(
            {"error": "Missing start or end parameter"},
            status=400,
            cache=False
        )

    db = get_db()

    # Get usage snapshots for the date range
    snapshots = (
        db.collection("enterprises")
        .document(enterprise_id)
        .collection("usage_snapshots")
        .where("date", ">=", start_date)
        .where("date", "<=", end_date)
        .order_by("date")
        .stream()
    )

    # Aggregate data
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "total_cost_usd": 0,
        "request_count": 0,
    }
    by_day = []
    by_provider = {}
    by_model = {}

    for snapshot in snapshots:
        data = snapshot.to_dict()
        day_totals = data.get("totals", {})

        totals["input_tokens"] += day_totals.get("input_tokens", 0)
        totals["output_tokens"] += day_totals.get("output_tokens", 0)
        totals["cached_tokens"] += day_totals.get("cached_tokens", 0)
        totals["total_cost_usd"] += day_totals.get("cost_usd", 0)
        totals["request_count"] += day_totals.get("request_count", 0)

        by_day.append({
            "date": data.get("date"),
            "input_tokens": day_totals.get("input_tokens", 0),
            "output_tokens": day_totals.get("output_tokens", 0),
            "cost_usd": day_totals.get("cost_usd", 0),
        })

    # Calculate effective rates
    effective_rates = {}
    if totals["input_tokens"] > 0:
        effective_rates["input"] = round(
            totals["total_cost_usd"] / totals["input_tokens"] * 1_000_000, 2
        )
    if totals["output_tokens"] > 0:
        effective_rates["output"] = round(
            totals["total_cost_usd"] / totals["output_tokens"] * 1_000_000, 2
        )

    # Blended rate (3:1 weighted)
    total_blended = totals["input_tokens"] + (totals["output_tokens"] * 3)
    if total_blended > 0:
        effective_rates["blended"] = round(
            totals["total_cost_usd"] / total_blended * 1_000_000, 2
        )

    # Get current STCI-FRONTIER rate for comparison
    frontier_rate = None
    try:
        index_doc = (
            db.collection("indices")
            .order_by("date", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        for doc in index_doc:
            index_data = doc.to_dict()
            frontier = index_data.get("indices", {}).get("STCI-FRONTIER", {})
            frontier_rate = frontier.get("blended_rate") or frontier.get("blended")
    except Exception:
        pass

    benchmark = {}
    if frontier_rate and effective_rates.get("blended"):
        benchmark["stci_frontier_blended"] = frontier_rate
        benchmark["your_discount"] = round(
            (frontier_rate - effective_rates["blended"]) / frontier_rate, 3
        )

    return json_response({
        "period": {
            "start": start_date,
            "end": end_date,
        },
        "totals": totals,
        "effective_rates": effective_rates,
        "benchmark": benchmark,
        "by_day": by_day,
    }, cache=False)


def handle_trigger_sync(req: https_fn.Request):
    """
    Manually trigger a usage sync.

    POST /api/v1/enterprise/sync
    Body: {"date": "YYYY-MM-DD"} (optional, defaults to yesterday)
    """
    enterprise_id = get_enterprise_id(req)
    if not enterprise_id:
        return json_response(
            {"error": "Missing or invalid Authorization header"},
            status=401,
            cache=False
        )

    try:
        data = req.get_json() or {}
        sync_date = data.get("date")

        if not sync_date:
            from datetime import timedelta
            sync_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        db = get_db()
        secret_mgr = get_secret_manager()

        # Get enterprise data
        enterprise_doc = db.collection("enterprises").document(enterprise_id).get()
        if not enterprise_doc.exists:
            return json_response(
                {"error": "Enterprise not found"},
                status=404,
                cache=False
            )

        enterprise = enterprise_doc.to_dict()
        providers = enterprise.get("providers", {})

        from enterprise.schema import UsageSnapshot
        snapshot = UsageSnapshot(date=sync_date)

        # Sync from each connected provider
        for provider, info in providers.items():
            if not info.get("connected"):
                continue

            api_key = secret_mgr.get_api_key(enterprise_id, provider)
            if not api_key:
                continue

            if provider == "openai":
                from enterprise.providers import OpenAIUsageClient
                client = OpenAIUsageClient(api_key)
                usage = client.fetch_daily_usage(sync_date)
                client.close()
            elif provider == "anthropic":
                from enterprise.providers import AnthropicUsageClient
                client = AnthropicUsageClient(api_key)
                usage = client.fetch_daily_usage(sync_date)
                client.close()
            else:
                continue

            # Aggregate into snapshot
            snapshot.total_input_tokens += usage.input_tokens
            snapshot.total_output_tokens += usage.output_tokens
            snapshot.total_cached_tokens += usage.cached_tokens
            snapshot.total_cost_usd += usage.total_cost_usd
            snapshot.total_request_count += usage.request_count
            snapshot.by_provider[provider] = usage

            # Update last_sync timestamp
            db.collection("enterprises").document(enterprise_id).update({
                f"providers.{provider}.last_sync": datetime.utcnow()
            })

        # Calculate rates
        snapshot.calculate_rates()

        # Get STCI-FRONTIER rate for comparison
        try:
            index_doc = (
                db.collection("indices")
                .order_by("date", direction=firestore.Query.DESCENDING)
                .limit(1)
                .stream()
            )
            for doc in index_doc:
                index_data = doc.to_dict()
                frontier = index_data.get("indices", {}).get("STCI-FRONTIER", {})
                rate = frontier.get("blended_rate") or frontier.get("blended")
                if rate:
                    snapshot.calculate_discount(rate)
        except Exception:
            pass

        # Store snapshot
        db.collection("enterprises").document(enterprise_id).collection(
            "usage_snapshots"
        ).document(sync_date).set(snapshot.to_dict())

        return json_response({
            "success": True,
            "date": sync_date,
            "totals": {
                "input_tokens": snapshot.total_input_tokens,
                "output_tokens": snapshot.total_output_tokens,
                "cost_usd": snapshot.total_cost_usd,
            },
            "effective_rate": snapshot.effective_blended_rate,
        }, cache=False)

    except Exception as e:
        return json_response(
            {"error": str(e)},
            status=500,
            cache=False
        )


def handle_benchmarks(req: https_fn.Request):
    """
    Get current benchmark data.

    GET /api/v1/benchmarks/current
    """
    enterprise_id = get_enterprise_id(req)

    db = get_db()

    # Get current month's benchmark
    current_month = datetime.utcnow().strftime("%Y-%m")
    benchmark_doc = db.collection("benchmarks").document(current_month).get()

    if not benchmark_doc.exists:
        # Return placeholder data if no benchmark exists yet
        return json_response({
            "month": current_month,
            "enterprise_count": 0,
            "percentiles": {
                "p10": None,
                "p25": None,
                "p50": None,
                "p75": None,
                "p90": None,
            },
            "your_position": None,
            "message": "Not enough data for benchmarks yet"
        }, cache=False)

    benchmark = benchmark_doc.to_dict()

    # If enterprise is authenticated, show their position
    your_position = None
    if enterprise_id:
        # Get their latest effective rate
        snapshots = (
            db.collection("enterprises")
            .document(enterprise_id)
            .collection("usage_snapshots")
            .order_by("date", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )

        for snapshot in snapshots:
            data = snapshot.to_dict()
            rate = data.get("rates", {}).get("effective_blended_rate")
            if rate:
                # Calculate percentile position
                percentiles = benchmark.get("percentiles", {})
                if rate <= percentiles.get("p10", float("inf")):
                    percentile = 90
                elif rate <= percentiles.get("p25", float("inf")):
                    percentile = 75
                elif rate <= percentiles.get("p50", float("inf")):
                    percentile = 50
                elif rate <= percentiles.get("p75", float("inf")):
                    percentile = 25
                else:
                    percentile = 10

                your_position = {
                    "rate": rate,
                    "percentile": percentile,
                    "better_than": f"{percentile}% of enterprises",
                }

    return json_response({
        "month": current_month,
        "enterprise_count": benchmark.get("stats", {}).get("enterprise_count", 0),
        "percentiles": benchmark.get("percentiles", {}),
        "your_position": your_position,
    }, cache=False)
