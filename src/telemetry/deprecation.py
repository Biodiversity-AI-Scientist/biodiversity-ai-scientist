import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import Request

logger = logging.getLogger("bais.telemetry.deprecation")


def log_legacy_api_access(
    request: Request,
    legacy_endpoint: str,
    canonical_endpoint: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Structured telemetry logging whenever a deprecated Analysis API endpoint is accessed.
    Records route, method, timestamp, explicit client identifier (X-Client-Id), user agent,
    and referrer.
    """
    client_id = (
        request.headers.get("X-Client-Id")
        or request.headers.get("X-Application-Id")
        or request.headers.get("X-Client-Name")
        or "unknown_client"
    )
    user_agent = request.headers.get("User-Agent", "unknown_user_agent")
    referer = request.headers.get("Referer", None)
    client_ip = request.client.host if request.client else "unknown_ip"

    record = {
        "event": "legacy_api_deprecation_access",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "legacy_endpoint": legacy_endpoint,
        "canonical_endpoint": canonical_endpoint,
        "http_method": request.method,
        "url_path": request.url.path,
        "client_id": client_id,
        "user_agent": user_agent,
        "referer": referer,
        "client_ip": client_ip,
    }
    if extra:
        record["details"] = extra

    # Emit structured log
    logger.warning("[DEPRECATION_TELEMETRY] %s", json.dumps(record))
    return record
