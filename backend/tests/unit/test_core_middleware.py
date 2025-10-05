"""Unit tests for middleware module."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from src.core.middleware import (
    ErrorLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    RequestLoggingMiddleware,
    get_request_id,
    request_id_var,
)


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware class."""

    @pytest.mark.asyncio
    async def test_request_logging_middleware_success(self):
        """Test middleware logs successful requests."""
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Create mock response
        mock_response = Response(content="OK", status_code=200)

        # Create mock call_next
        async def mock_call_next(request):
            return mock_response

        # Create middleware
        app = Mock()
        middleware = RequestLoggingMiddleware(app)

        # Process request
        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_logging_middleware_slow_request(self):
        """Test middleware logs slow requests."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/slow"
        mock_request.query_params = {"param": "value"}
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        mock_response = Response(content="OK", status_code=200)

        # Simulate slow operation
        async def mock_call_next(request):
            return mock_response

        app = Mock()
        middleware = RequestLoggingMiddleware(app)

        # Mock time to simulate slow request (>1000ms)
        import time

        # Provide enough values for all time.time() calls (start, end, and any intermediates)
        # Use a lambda to always return the right value instead of a list
        time_values = [0.0, 1.5]
        time_index = [0]

        def mock_time():
            idx = time_index[0]
            time_index[0] += 1
            return time_values[min(idx, len(time_values) - 1)]

        with patch.object(time, "time", side_effect=mock_time):
            response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_logging_middleware_exception(self):
        """Test middleware logs exceptions."""
        mock_request = Mock(spec=Request)
        mock_request.method = "DELETE"
        mock_request.url.path = "/api/error"
        mock_request.query_params = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Simulate error
        async def mock_call_next(request):
            msg = "Test error"
            raise ValueError(msg)

        app = Mock()
        middleware = RequestLoggingMiddleware(app)

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_request_logging_middleware_no_client(self):
        """Test middleware handles requests with no client info."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.client = None  # No client info

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        app = Mock()
        middleware = RequestLoggingMiddleware(app)

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200


class TestErrorLoggingMiddleware:
    """Test ErrorLoggingMiddleware class."""

    @pytest.mark.asyncio
    async def test_error_logging_middleware_success(self):
        """Test middleware passes through successful requests."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_logging_middleware_logs_exception(self):
        """Test middleware logs exceptions with context."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/error"
        mock_request.query_params = {"key": "value"}

        # Set request ID in context
        request_id_var.set("test-req-123")

        async def mock_call_next(request):
            msg = "Test runtime error"
            raise RuntimeError(msg)

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        with pytest.raises(RuntimeError):
            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_error_logging_middleware_with_post_body(self):
        """Test middleware logs POST request body on error."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/create"
        mock_request.query_params = {}

        # Mock request body
        request_body = json.dumps({"name": "test", "value": 123}).encode()

        async def mock_body():
            return request_body

        mock_request.body = mock_body

        async def mock_call_next(request):
            msg = "Validation error"
            raise ValueError(msg)

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_error_logging_middleware_with_large_body(self):
        """Test middleware handles large request bodies."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/upload"
        mock_request.query_params = {}

        # Mock large body (>10000 bytes)
        large_body = b"x" * 15000

        async def mock_body():
            return large_body

        mock_request.body = mock_body

        async def mock_call_next(request):
            msg = "Upload error"
            raise ValueError(msg)

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_error_logging_middleware_with_non_json_body(self):
        """Test middleware handles non-JSON request bodies."""
        mock_request = Mock(spec=Request)
        mock_request.method = "PUT"
        mock_request.url.path = "/api/update"
        mock_request.query_params = {}

        # Non-JSON body
        request_body = b"This is plain text, not JSON"

        async def mock_body():
            return request_body

        mock_request.body = mock_body

        async def mock_call_next(request):
            msg = "Missing field"
            raise KeyError(msg)

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        with pytest.raises(KeyError):
            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_error_logging_middleware_body_read_error(self):
        """Test middleware handles errors when reading request body."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}

        # Mock body that raises an error
        async def mock_body():
            msg = "Cannot read body"
            raise OSError(msg)

        mock_request.body = mock_body

        async def mock_call_next(request):
            msg = "Processing error"
            raise ValueError(msg)

        app = Mock()
        middleware = ErrorLoggingMiddleware(app)

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)


class TestPerformanceMonitoringMiddleware:
    """Test PerformanceMonitoringMiddleware class."""

    @pytest.mark.asyncio
    async def test_performance_monitoring_basic(self):
        """Test performance monitoring middleware tracks requests."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/items"

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        app = Mock()
        middleware = PerformanceMonitoringMiddleware(app, threshold_ms=1000)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        # Check that statistics were updated
        endpoint_key = "GET /api/items"
        assert endpoint_key in middleware.request_stats
        assert middleware.request_stats[endpoint_key]["count"] == 1

    @pytest.mark.asyncio
    async def test_performance_monitoring_multiple_requests(self):
        """Test performance monitoring tracks multiple requests to same endpoint."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/create"

        mock_response = Response(content="Created", status_code=201)

        async def mock_call_next(request):
            return mock_response

        app = Mock()
        middleware = PerformanceMonitoringMiddleware(app)

        # Make multiple requests
        for i in range(5):
            await middleware.dispatch(mock_request, mock_call_next)

        endpoint_key = "POST /api/create"
        assert middleware.request_stats[endpoint_key]["count"] == 5
        assert middleware.request_stats[endpoint_key]["total_time"] > 0
        assert middleware.request_stats[endpoint_key]["max_time"] > 0
        assert middleware.request_stats[endpoint_key]["min_time"] < float("inf")

    @pytest.mark.asyncio
    async def test_performance_monitoring_periodic_logging(self):
        """Test performance monitoring logs stats periodically."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/status"

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            await asyncio.sleep(0.001)  # Small delay
            return mock_response

        app = Mock()
        middleware = PerformanceMonitoringMiddleware(app, threshold_ms=500)

        # Make 100 requests to trigger periodic logging
        for i in range(100):
            await middleware.dispatch(mock_request, mock_call_next)

        endpoint_key = "GET /api/status"
        assert middleware.request_stats[endpoint_key]["count"] == 100

    @pytest.mark.asyncio
    async def test_performance_monitoring_different_endpoints(self):
        """Test performance monitoring tracks different endpoints separately."""
        app = Mock()
        middleware = PerformanceMonitoringMiddleware(app)

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        # Request to endpoint 1
        mock_request1 = Mock(spec=Request)
        mock_request1.method = "GET"
        mock_request1.url.path = "/api/users"
        await middleware.dispatch(mock_request1, mock_call_next)

        # Request to endpoint 2
        mock_request2 = Mock(spec=Request)
        mock_request2.method = "POST"
        mock_request2.url.path = "/api/items"
        await middleware.dispatch(mock_request2, mock_call_next)

        assert "GET /api/users" in middleware.request_stats
        assert "POST /api/items" in middleware.request_stats
        assert middleware.request_stats["GET /api/users"]["count"] == 1
        assert middleware.request_stats["POST /api/items"]["count"] == 1

    @pytest.mark.asyncio
    async def test_performance_monitoring_custom_threshold(self):
        """Test performance monitoring with custom threshold."""
        app = Mock()
        middleware = PerformanceMonitoringMiddleware(app, threshold_ms=100)

        assert middleware.threshold_ms == 100

        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/fast"

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200


class TestGetRequestId:
    """Test get_request_id function."""

    def test_get_request_id_default(self):
        """Test getting request ID when not set."""
        # Reset context var
        request_id_var.set("no-request")

        request_id = get_request_id()
        assert request_id == "no-request"

    def test_get_request_id_custom(self):
        """Test getting custom request ID."""
        request_id_var.set("custom-req-123")

        request_id = get_request_id()
        assert request_id == "custom-req-123"

    def test_get_request_id_multiple_contexts(self):
        """Test request ID in different contexts."""
        # Set in main context
        request_id_var.set("main-req")
        assert get_request_id() == "main-req"

        # The context var should maintain its value
        request_id_var.set("other-req")
        assert get_request_id() == "other-req"
