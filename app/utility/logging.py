import logging
import time
import json
from typing import Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Sensitive fields to mask in request body logs
SENSITIVE_FIELDS: Set[str] = {"password", "password_hash", "secret_key", "access_token"}


def setup_logging(debug: bool = False) -> None:
    """Configure application-wide logging."""
    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def _mask_sensitive(data: dict) -> dict:
    """Return a copy of data with sensitive field values replaced by '***'."""
    masked = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive(value)
        else:
            masked[key] = value
    return masked


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request and response."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("medbase.request")

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()

        # --- Log request ---
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        url_display = f"{path}?{query}" if query else path

        self.logger.info("→ %s %s", method, url_display)

        # Log body for mutating methods
        if method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    # Try JSON first
                    try:
                        body_json = json.loads(body_bytes)
                        masked = _mask_sensitive(body_json)
                        self.logger.info("  Body: %s", json.dumps(masked))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Form data — parse it manually
                        body_text = body_bytes.decode("utf-8", errors="replace")
                        # Mask password in form data (key=value&key=value)
                        parts = body_text.split("&")
                        masked_parts = []
                        for part in parts:
                            if "=" in part:
                                k, _v = part.split("=", 1)
                                if k.lower() in SENSITIVE_FIELDS:
                                    masked_parts.append(f"{k}=***")
                                else:
                                    masked_parts.append(part)
                            else:
                                masked_parts.append(part)
                        self.logger.info("  Body: %s", "&".join(masked_parts))
            except Exception:
                self.logger.debug("  Body: <unreadable>")

        # --- Call the actual endpoint ---
        response = await call_next(request)

        # --- Log response ---
        duration_ms = (time.time() - start) * 1000
        self.logger.info(
            "← %s %s %d (%.0fms)",
            method,
            path,
            response.status_code,
            duration_ms,
        )

        return response
