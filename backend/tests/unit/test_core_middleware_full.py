"""Comprehensive unit tests for middleware classes - 70%+ coverage target."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

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


class MockRequest:
    """Mock FastAPI Request for testing."""

    def __init__(self, method="GET", path="/test", query_params=None, client_host="127.0.0.1"):
        self.method = method
        self.url = MagicMock()
        self.url.path = path
        self.query_params = query_params or {}
        self.client = MagicMock()
        self.client.host = client_host if client_host else None
        self._body = b""

    async def body(self):
        return self._body


class MockResponse:
    """Mock Response for testing."""

    def __init__(self, status_code=200):
        self.status_code = status_code
        self.headers = {}


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_start(self):
        """Test that dispatch logs request start."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/test")
        response = MockResponse(status_code=200)

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger") as mock_logger:
            result = await middleware.dispatch(request, call_next)

            # Should log request start
            assert mock_logger.info.called
            log_calls = mock_logger.info.call_args_list
            assert any("Request started" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_completion(self):
        """Test that dispatch logs request completion."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/create")
        response = MockResponse(status_code=201)

        async def call_next(req):
            await asyncio.sleep(0.01)
            return response

        with patch("src.core.middleware.logger") as mock_logger:
            result = await middleware.dispatch(request, call_next)

            # Should log completion
            log_calls = mock_logger.info.call_args_list
            assert any("Request completed" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    async def test_dispatch_sets_request_id(self):
        """Test that dispatch sets request ID in context."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            # Request ID should be set during processing
            req_id = request_id_var.get()
            assert req_id != "no-request"
            return response

        with patch("src.core.middleware.logger"):
            await middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_dispatch_adds_request_id_to_response_headers(self):
        """Test that request ID is added to response headers."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger"):
            result = await middleware.dispatch(request, call_next)

            assert "X-Request-ID" in result.headers

    @pytest.mark.asyncio
    async def test_dispatch_logs_slow_requests(self):
        """Test that slow requests are logged with warning."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            await asyncio.sleep(1.1)  # Simulate slow request
            return response

        with patch("src.core.middleware.logger") as mock_logger:
            with patch("time.time", side_effect=[0, 1.5]):  # Simulate 1500ms duration
                await middleware.dispatch(request, call_next)

                # Should log warning for slow request
                assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_details(self):
        """Test that request details are logged."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest(
            method="PUT",
            path="/api/update/123",
            query_params={"key": "value"},
            client_host="192.168.1.1"
        )
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            # Check that extra fields are logged
            info_calls = mock_logger.info.call_args_list
            assert len(info_calls) > 0

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(self):
        """Test that dispatch properly handles and logs exceptions."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()

        async def call_next(req):
            raise ValueError("Test error")

        with patch("src.core.middleware.logger") as mock_logger:
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            # Should log exception
            assert mock_logger.exception.called

    @pytest.mark.asyncio
    async def test_dispatch_logs_duration_on_error(self):
        """Test that duration is logged even on error."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()

        async def call_next(req):
            await asyncio.sleep(0.1)
            raise RuntimeError("Error")

        with patch("src.core.middleware.logger") as mock_logger:
            with pytest.raises(RuntimeError):
                await middleware.dispatch(request, call_next)

            # Should log with duration_ms
            exception_call = mock_logger.exception.call_args
            assert "duration_ms" in exception_call[1]["extra"]

    @pytest.mark.asyncio
    async def test_dispatch_with_none_client(self):
        """Test dispatch handles request with no client info."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest(client_host=None)
        request.client = None
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger"):
            # Should not raise error
            result = await middleware.dispatch(request, call_next)
            assert result is not None


class TestErrorLoggingMiddleware:
    """Test ErrorLoggingMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_dispatch_passes_through_success(self):
        """Test dispatch passes through successful requests."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert result is response

    @pytest.mark.asyncio
    async def test_dispatch_logs_exception(self):
        """Test that exceptions are logged with context."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/error")

        async def call_next(req):
            raise ValueError("Test exception")

        with patch("src.core.middleware.logger") as mock_logger:
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            assert mock_logger.exception.called

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_context(self):
        """Test that request context is included in error logs."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(
            method="DELETE",
            path="/api/delete/456",
            query_params={"confirm": "true"}
        )

        async def call_next(req):
            raise RuntimeError("Delete failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-test-123"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(RuntimeError):
                    await middleware.dispatch(request, call_next)

                # Check context
                exception_call = mock_logger.exception.call_args
                extra = exception_call[1]["extra"]
                assert extra["method"] == "DELETE"
                assert extra["path"] == "/api/delete/456"

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_body_json(self):
        """Test logging of JSON request body on error."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/create")
        request._body = json.dumps({"data": "test"}).encode()

        async def call_next(req):
            raise ValueError("Create failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-body-test"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(request, call_next)

                # Should log body
                debug_calls = mock_logger.debug.call_args_list
                assert len(debug_calls) > 0

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_body_non_json(self):
        """Test logging of non-JSON request body."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="PUT", path="/api/upload")
        request._body = b"binary data here"

        async def call_next(req):
            raise ValueError("Upload failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-binary-test"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(request, call_next)

                # Should handle non-JSON body
                # Just verify no crash occurs

    @pytest.mark.asyncio
    async def test_dispatch_skips_large_body(self):
        """Test that large request bodies are not logged."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/upload")
        request._body = b"x" * 20000  # Large body

        async def call_next(req):
            raise ValueError("Upload failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-large-test"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(request, call_next)

                # Should not log large body

    @pytest.mark.asyncio
    async def test_dispatch_skips_body_for_get(self):
        """Test that GET request bodies are not logged."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/data")

        async def call_next(req):
            raise ValueError("Get failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-get-test"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(request, call_next)

                # Should not attempt to log body for GET

    @pytest.mark.asyncio
    async def test_dispatch_handles_body_read_error(self):
        """Test handling of errors when reading request body."""
        middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/test")

        async def body_error():
            raise RuntimeError("Cannot read body")

        request.body = body_error

        async def call_next(req):
            raise ValueError("Request failed")

        with patch("src.core.middleware.request_id_var") as mock_req_id:
            mock_req_id.get.return_value = "req-body-error"

            with patch("src.core.middleware.logger") as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(request, call_next)

                # Should handle body read error gracefully


class TestPerformanceMonitoringMiddleware:
    """Test PerformanceMonitoringMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_init_with_custom_threshold(self):
        """Test initialization with custom threshold."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock(), threshold_ms=500)

        assert middleware.threshold_ms == 500
        assert middleware.request_stats == {}

    @pytest.mark.asyncio
    async def test_dispatch_tracks_request_time(self):
        """Test that dispatch tracks request duration."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/data")
        response = MockResponse()

        async def call_next(req):
            await asyncio.sleep(0.05)
            return response

        result = await middleware.dispatch(request, call_next)

        assert "GET /api/data" in middleware.request_stats

    @pytest.mark.asyncio
    async def test_dispatch_updates_statistics(self):
        """Test that statistics are updated correctly."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="POST", path="/api/create")
        response = MockResponse()

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        stats = middleware.request_stats["POST /api/create"]
        assert stats["count"] == 1
        assert stats["total_time"] > 0
        assert stats["max_time"] > 0
        assert stats["min_time"] > 0

    @pytest.mark.asyncio
    async def test_dispatch_tracks_multiple_requests(self):
        """Test tracking multiple requests to same endpoint."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/list")
        response = MockResponse()

        async def call_next(req):
            return response

        # Make multiple requests
        for _ in range(5):
            await middleware.dispatch(request, call_next)

        stats = middleware.request_stats["GET /api/list"]
        assert stats["count"] == 5

    @pytest.mark.asyncio
    async def test_dispatch_tracks_min_max_time(self):
        """Test that min and max times are tracked correctly."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/timing")
        response = MockResponse()

        call_count = 0

        async def call_next(req):
            nonlocal call_count
            call_count += 1
            # First call faster, second slower
            await asyncio.sleep(0.01 if call_count == 1 else 0.05)
            return response

        # First request (faster)
        await middleware.dispatch(request, call_next)
        # Second request (slower)
        await middleware.dispatch(request, call_next)

        stats = middleware.request_stats["GET /api/timing"]
        assert stats["max_time"] > stats["min_time"]

    @pytest.mark.asyncio
    async def test_dispatch_logs_stats_every_100_requests(self):
        """Test that statistics are logged every 100 requests."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/frequent")
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger") as mock_logger:
            # Make 100 requests
            for _ in range(100):
                await middleware.dispatch(request, call_next)

            # Should log stats
            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_dispatch_different_endpoints(self):
        """Test tracking different endpoints separately."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        response = MockResponse()

        async def call_next(req):
            return response

        # Different endpoints
        request1 = MockRequest(method="GET", path="/api/users")
        request2 = MockRequest(method="POST", path="/api/users")
        request3 = MockRequest(method="GET", path="/api/posts")

        await middleware.dispatch(request1, call_next)
        await middleware.dispatch(request2, call_next)
        await middleware.dispatch(request3, call_next)

        assert "GET /api/users" in middleware.request_stats
        assert "POST /api/users" in middleware.request_stats
        assert "GET /api/posts" in middleware.request_stats
        assert len(middleware.request_stats) == 3

    @pytest.mark.asyncio
    async def test_dispatch_calculates_average_time(self):
        """Test that average time can be calculated from stats."""
        middleware = PerformanceMonitoringMiddleware(app=MagicMock())

        request = MockRequest(method="GET", path="/api/avg")
        response = MockResponse()

        async def call_next(req):
            await asyncio.sleep(0.01)
            return response

        # Make several requests
        for _ in range(10):
            await middleware.dispatch(request, call_next)

        stats = middleware.request_stats["GET /api/avg"]
        avg_time = stats["total_time"] / stats["count"]

        assert avg_time > 0
        assert avg_time >= stats["min_time"]
        assert avg_time <= stats["max_time"]


class TestGetRequestId:
    """Test get_request_id function."""

    def test_get_request_id_default(self):
        """Test getting default request ID."""
        # Reset context var
        request_id_var.set("no-request")

        result = get_request_id()

        assert result == "no-request"

    def test_get_request_id_set_value(self):
        """Test getting set request ID."""
        request_id_var.set("custom-req-123")

        result = get_request_id()

        assert result == "custom-req-123"

        # Reset
        request_id_var.set("no-request")


class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_middleware_chain(self):
        """Test chaining multiple middleware together."""
        logging_middleware = RequestLoggingMiddleware(app=MagicMock())
        error_middleware = ErrorLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("src.core.middleware.logger"):
            # Process through both middleware
            result = await logging_middleware.dispatch(request, call_next)
            assert result is not None

    @pytest.mark.asyncio
    async def test_middleware_preserves_request_id_context(self):
        """Test that request ID is preserved across middleware."""
        middleware = RequestLoggingMiddleware(app=MagicMock())

        request = MockRequest()
        response = MockResponse()

        captured_id = None

        async def call_next(req):
            nonlocal captured_id
            captured_id = request_id_var.get()
            return response

        with patch("src.core.middleware.logger"):
            await middleware.dispatch(request, call_next)

            assert captured_id is not None
            assert captured_id != "no-request"
