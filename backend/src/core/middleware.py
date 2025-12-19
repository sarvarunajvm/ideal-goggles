"""Middleware for request tracking and logging."""

import json
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .logging_config import get_logger

logger = get_logger(__name__)

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with detailed information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request_id_var.set(request_id)

        # Add request ID to logger context
        logger_extra = {"request_id": request_id}

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                **logger_extra,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    **logger_extra,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            # Log slow requests
            if duration_ms > 1000:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                    extra={
                        **logger_extra,
                        "duration_ms": duration_ms,
                        "method": request.method,
                        "path": request.url.path,
                    },
                )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - {e.__class__.__name__}",
                extra={
                    **logger_extra,
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
            )
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log errors with full context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch and log errors with context."""
        try:
            return await call_next(request)
        except Exception as e:
            request_id = request_id_var.get()

            # Log error with full context
            logger.exception(
                f"Unhandled exception in request {request_id}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
            )

            # Try to extract request body for debugging (be careful with large bodies)
            try:
                if request.method in ["POST", "PUT", "PATCH"]:
                    body = await request.body()
                    if body and len(body) < 10000:  # Only log small bodies
                        try:
                            body_json = json.loads(body)
                            logger.debug(
                                f"Request body for failed request {request_id}",
                                extra={"request_id": request_id, "body": body_json},
                            )
                        except json.JSONDecodeError:
                            logger.debug(
                                f"Request body (non-JSON) for failed request {request_id}",
                                extra={
                                    "request_id": request_id,
                                    "body_preview": body[:500].decode(
                                        "utf-8", errors="ignore"
                                    ),
                                },
                            )
            except Exception as body_error:
                logger.debug(f"Could not log request body: {body_error}")

            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor performance metrics."""

    def __init__(self, app, threshold_ms: float = 1000):
        super().__init__(app)
        self.threshold_ms = threshold_ms
        self.request_stats = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        path = request.url.path
        method = request.method
        endpoint_key = f"{method} {path}"

        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Update statistics
        if endpoint_key not in self.request_stats:
            self.request_stats[endpoint_key] = {
                "count": 0,
                "total_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
            }

        stats = self.request_stats[endpoint_key]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["max_time"] = max(stats["max_time"], duration_ms)
        stats["min_time"] = min(stats["min_time"], duration_ms)

        # Log performance summary periodically
        if stats["count"] % 100 == 0:
            avg_time = stats["total_time"] / stats["count"]
            logger.info(
                f"Performance stats for {endpoint_key}",
                extra={
                    "endpoint": endpoint_key,
                    "request_count": stats["count"],
                    "avg_time_ms": avg_time,
                    "max_time_ms": stats["max_time"],
                    "min_time_ms": stats["min_time"],
                },
            )

        return response


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware.

    Limits requests per IP address to prevent abuse.
    Uses a sliding window approach.
    """

    # Endpoint-specific rate limits (requests per minute)
    RATE_LIMITS: dict[str, int] = {
        "/search/semantic": 30,  # CPU-intensive CLIP inference
        "/search/image": 20,  # CPU-intensive image processing
        "/index/start": 5,  # Resource-intensive operation
        "/batch/": 10,  # Batch operations
        "default": 120,  # Default limit for other endpoints
    }

    def __init__(self, app, window_seconds: int = 60):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.request_history: dict[str, dict[str, list[tuple[float, int]]]] = (
            defaultdict(lambda: defaultdict(list))
        )

    def _get_rate_limit(self, path: str) -> int:
        """Get the rate limit for a specific path."""
        for pattern, limit in self.RATE_LIMITS.items():
            if pattern != "default" and path.startswith(pattern):
                return limit
        return self.RATE_LIMITS["default"]

    def _get_endpoint_key(self, path: str) -> str:
        """Get a normalized endpoint key for rate limiting."""
        for pattern in self.RATE_LIMITS:
            if pattern != "default" and path.startswith(pattern):
                return pattern
        return "default"

    def _is_rate_limited(self, client_ip: str, path: str) -> tuple[bool, int]:
        """Check if the client is rate limited.

        Returns:
            Tuple of (is_limited, requests_remaining)
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        endpoint_key = self._get_endpoint_key(path)
        rate_limit = self._get_rate_limit(path)

        # Get request history for this client and endpoint
        history = self.request_history[client_ip][endpoint_key]

        # Remove old entries
        history[:] = [(ts, count) for ts, count in history if ts > cutoff_time]

        # Count requests in window
        request_count = sum(count for _, count in history)

        if request_count >= rate_limit:
            return True, 0

        return False, rate_limit - request_count

    def _record_request(self, client_ip: str, path: str) -> None:
        """Record a request for rate limiting."""
        current_time = time.time()
        endpoint_key = self._get_endpoint_key(path)

        # Add current request
        self.request_history[client_ip][endpoint_key].append((current_time, 1))

        # Cleanup old entries periodically (every 100th request)
        total_entries = sum(
            len(hist)
            for ep_hist in self.request_history.values()
            for hist in ep_hist.values()
        )
        if total_entries > 10000:
            self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        """Clean up old entries from request history."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds * 2  # Keep some buffer

        empty_ips = []
        for client_ip, endpoints in self.request_history.items():
            empty_endpoints = []
            for endpoint, history in endpoints.items():
                history[:] = [(ts, count) for ts, count in history if ts > cutoff_time]
                if not history:
                    empty_endpoints.append(endpoint)
            for ep in empty_endpoints:
                del endpoints[ep]
            if not endpoints:
                empty_ips.append(client_ip)

        for ip in empty_ips:
            del self.request_history[ip]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        # Get client IP (handle proxies)
        client_ip = request.client.host if request.client else "unknown"

        # Check X-Forwarded-For header for proxied requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            client_ip = forwarded_for.split(",")[0].strip()

        path = request.url.path

        # Skip rate limiting for health checks and test clients
        if path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Skip rate limiting for test clients (TestClient uses "testclient" as host)
        if client_ip in ("testclient", "localhost", "127.0.0.1"):
            return await call_next(request)

        # Check rate limit
        is_limited, remaining = self._is_rate_limited(client_ip, path)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path}",
                extra={
                    "client_ip": client_ip,
                    "path": path,
                    "request_id": request_id_var.get(),
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self.window_seconds,
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record this request
        self._record_request(client_ip, path)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + self.window_seconds)
        )

        return response


def sanitize_error_message(error: Exception) -> str:
    """Sanitize error message to avoid leaking sensitive information.

    Args:
        error: The exception to sanitize

    Returns:
        A user-friendly error message
    """
    error_str = str(error)

    # List of sensitive patterns to redact
    sensitive_patterns = [
        # File paths
        (r"/Users/[^/\s]+", "/Users/***"),
        (r"/home/[^/\s]+", "/home/***"),
        (r"C:\\Users\\[^\\]+", "C:\\Users\\***"),
        # Database paths
        (r"sqlite:///[^\s]+", "sqlite:///***"),
        # API keys and tokens (generic patterns)
        (r"[a-zA-Z0-9]{32,}", "***REDACTED***"),
        # Email addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***"),
        # IP addresses
        (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "***.***.***.***"),
    ]

    import re

    sanitized = error_str
    for pattern, replacement in sensitive_patterns:
        sanitized = re.sub(pattern, replacement, sanitized)

    # Truncate very long messages
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... (truncated)"

    return sanitized
