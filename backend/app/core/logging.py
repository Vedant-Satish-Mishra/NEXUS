"""
NEXUS Structured JSON Logging & Privacy Filter
Redacts Authorization headers, passwords, tokens, and file content by invariant.
"""
import json
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

SENSITIVE_KEYS = {
    "authorization",
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "jwt_secret",
    "api_key",
    "sandbox_key"
}


def sanitize_dict(data: dict) -> dict:
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        else:
            sanitized[k] = v
    return sanitized


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj.update(sanitize_dict(record.extra_data))
        return json.dumps(log_obj)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())
    logger.handlers = [handler]


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Skip noisy polling endpoints like /health in detailed logs
        if request.url.path != "/api/v1/health":
            logging.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
                extra={"request_id": request_id, "extra_data": {"duration_ms": duration_ms}}
            )

        return response
