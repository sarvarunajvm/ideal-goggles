"""Middleware for request tracking and logging."""

import json
import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

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
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {e.__class__.__name__}",
                exc_info=True,
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
            logger.error(
                f"Unhandled exception in request {request_id}",
                exc_info=True,
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
