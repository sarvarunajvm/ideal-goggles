"""Unit tests for logging API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from src.api.logs import ErrorReport, LogEntry, submit_client_logs, submit_error_report


class TestLogEntry:
    """Test LogEntry model."""

    def test_log_entry_creation_debug(self):
        """Test creating LogEntry with DEBUG level."""
        log_entry = LogEntry(
            level="DEBUG",
            message="Debug message",
            context={"key": "value"},
            timestamp="2022-01-01T12:00:00Z",
            userAgent="Mozilla/5.0",
            url="http://example.com",
            error=None,
        )

        assert log_entry.level == "DEBUG"
        assert log_entry.message == "Debug message"
        assert log_entry.context == {"key": "value"}
        assert log_entry.timestamp == "2022-01-01T12:00:00Z"
        assert log_entry.user_agent == "Mozilla/5.0"
        assert log_entry.url == "http://example.com"
        assert log_entry.error is None

    def test_log_entry_creation_info(self):
        """Test creating LogEntry with INFO level."""
        log_entry = LogEntry(
            level="INFO",
            message="Info message",
            timestamp="2022-01-01T12:00:00Z",
        )

        assert log_entry.level == "INFO"
        assert log_entry.message == "Info message"

    def test_log_entry_creation_warn(self):
        """Test creating LogEntry with WARN level."""
        log_entry = LogEntry(
            level="WARN",
            message="Warning message",
            timestamp="2022-01-01T12:00:00Z",
        )

        assert log_entry.level == "WARN"
        assert log_entry.message == "Warning message"

    def test_log_entry_creation_error(self):
        """Test creating LogEntry with ERROR level."""
        log_entry = LogEntry(
            level="ERROR",
            message="Error message",
            timestamp="2022-01-01T12:00:00Z",
            error={"type": "TypeError", "message": "Something went wrong"},
        )

        assert log_entry.level == "ERROR"
        assert log_entry.message == "Error message"
        assert log_entry.error["type"] == "TypeError"

    def test_log_entry_invalid_level(self):
        """Test that invalid level raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            LogEntry(
                level="INVALID",
                message="Test message",
                timestamp="2022-01-01T12:00:00Z",
            )

    def test_log_entry_optional_fields(self):
        """Test LogEntry with only required fields."""
        log_entry = LogEntry(
            level="INFO",
            message="Simple message",
            timestamp="2022-01-01T12:00:00Z",
        )

        assert log_entry.context is None
        assert log_entry.user_agent is None
        assert log_entry.url is None
        assert log_entry.error is None


class TestErrorReport:
    """Test ErrorReport model."""

    def test_error_report_creation_full(self):
        """Test creating ErrorReport with all fields."""
        error_report = ErrorReport(
            message="Component crashed",
            stack="Error: Something went wrong\n  at Component.render",
            componentStack="    at ErrorBoundary\n    at App",
            componentName="PhotoGrid",
            timestamp="2022-01-01T12:00:00Z",
            userAgent="Mozilla/5.0",
            url="http://example.com/photos",
        )

        assert error_report.message == "Component crashed"
        assert "Error: Something went wrong" in error_report.stack
        assert "ErrorBoundary" in error_report.component_stack
        assert error_report.component_name == "PhotoGrid"
        assert error_report.timestamp == "2022-01-01T12:00:00Z"
        assert error_report.user_agent == "Mozilla/5.0"
        assert error_report.url == "http://example.com/photos"

    def test_error_report_optional_fields(self):
        """Test ErrorReport with only required fields."""
        error_report = ErrorReport(
            message="Error occurred",
            timestamp="2022-01-01T12:00:00Z",
        )

        assert error_report.message == "Error occurred"
        assert error_report.stack is None
        assert error_report.component_stack is None
        assert error_report.component_name is None
        assert error_report.user_agent is None
        assert error_report.url is None


class TestSubmitClientLogs:
    """Test submit_client_logs endpoint."""

    @pytest.mark.asyncio
    async def test_submit_client_logs_debug(self):
        """Test submitting DEBUG level log."""
        log_entry = LogEntry(
            level="DEBUG",
            message="Debug message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_client_logs(log_entry)

            # Should return None (204 No Content)
            assert result is None
            mock_logger.debug.assert_called_once()
            assert "[CLIENT-DEBUG]" in mock_logger.debug.call_args[0][0]
            assert "Debug message" in mock_logger.debug.call_args[0][0]

    @pytest.mark.asyncio
    async def test_submit_client_logs_info(self):
        """Test submitting INFO level log."""
        log_entry = LogEntry(
            level="INFO",
            message="Info message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_client_logs(log_entry)

            assert result is None
            mock_logger.info.assert_called_once()
            assert "[CLIENT-INFO]" in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_submit_client_logs_warn(self):
        """Test submitting WARN level log."""
        log_entry = LogEntry(
            level="WARN",
            message="Warning message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_client_logs(log_entry)

            assert result is None
            mock_logger.warning.assert_called_once()
            assert "[CLIENT-WARN]" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_submit_client_logs_error(self):
        """Test submitting ERROR level log."""
        log_entry = LogEntry(
            level="ERROR",
            message="Error message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_client_logs(log_entry)

            assert result is None
            mock_logger.error.assert_called_once()
            assert "[CLIENT-ERROR]" in mock_logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_submit_client_logs_with_context(self):
        """Test submitting log with context."""
        log_entry = LogEntry(
            level="INFO",
            message="User action",
            context={"action": "click", "element": "button"},
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            call_args = mock_logger.info.call_args[0][0]
            assert "Context:" in call_args
            assert "action" in call_args
            assert "click" in call_args

    @pytest.mark.asyncio
    async def test_submit_client_logs_with_url(self):
        """Test submitting log with URL."""
        log_entry = LogEntry(
            level="INFO",
            message="Page view",
            url="http://example.com/photos",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            call_args = mock_logger.info.call_args[0][0]
            assert "URL:" in call_args
            assert "http://example.com/photos" in call_args

    @pytest.mark.asyncio
    async def test_submit_client_logs_with_user_agent(self):
        """Test submitting log with user agent."""
        log_entry = LogEntry(
            level="INFO",
            message="Browser info",
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            call_args = mock_logger.info.call_args[0][0]
            assert "UA:" in call_args
            assert "Mozilla/5.0" in call_args

    @pytest.mark.asyncio
    async def test_submit_client_logs_with_error(self):
        """Test submitting log with error details."""
        log_entry = LogEntry(
            level="ERROR",
            message="Request failed",
            error={"type": "NetworkError", "code": 500},
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            call_args = mock_logger.error.call_args[0][0]
            assert "Error:" in call_args
            assert "NetworkError" in call_args

    @pytest.mark.asyncio
    async def test_submit_client_logs_with_all_fields(self):
        """Test submitting log with all fields."""
        log_entry = LogEntry(
            level="ERROR",
            message="Complete log entry",
            context={"user_id": "123"},
            url="http://example.com",
            userAgent="Mozilla/5.0",
            error={"type": "Error"},
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            call_args = mock_logger.error.call_args[0][0]
            assert "[CLIENT-ERROR]" in call_args
            assert "Complete log entry" in call_args
            assert "Context:" in call_args
            assert "URL:" in call_args
            assert "UA:" in call_args
            assert "Error:" in call_args

    @pytest.mark.asyncio
    async def test_submit_client_logs_invalid_timestamp(self):
        """Test submitting log with invalid timestamp doesn't fail."""
        log_entry = LogEntry(
            level="INFO",
            message="Test message",
            timestamp="invalid-timestamp",
        )

        with patch("src.api.logs.logger") as mock_logger:
            # Should not raise exception, but log the error
            result = await submit_client_logs(log_entry)

            # Should still return None (doesn't fail client request)
            assert result is None
            # Exception should be logged
            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_client_logs_logging_exception(self):
        """Test that logging exceptions don't fail the request."""
        log_entry = LogEntry(
            level="INFO",
            message="Test message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            # Make logger.info raise an exception
            mock_logger.info.side_effect = Exception("Logging failed")

            # Should not raise exception
            result = await submit_client_logs(log_entry)

            assert result is None
            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_client_logs_unknown_level_fallback(self):
        """Test that unknown log level falls back to info."""
        # This is a bit tricky since pydantic validates the level
        # We'll patch after validation
        log_entry = LogEntry(
            level="INFO",
            message="Test message",
            timestamp=datetime.now().isoformat(),
        )
        # Manually set an invalid level after creation
        log_entry.level = "UNKNOWN"

        with patch("src.api.logs.logger") as mock_logger:
            await submit_client_logs(log_entry)

            # Should fallback to info
            mock_logger.info.assert_called_once()


class TestSubmitErrorReport:
    """Test submit_error_report endpoint."""

    @pytest.mark.asyncio
    async def test_submit_error_report_basic(self):
        """Test submitting basic error report."""
        error_report = ErrorReport(
            message="Component error",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_error_report(error_report)

            assert result is None
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "[CLIENT-ERROR]" in call_args
            assert "Component error" in call_args

    @pytest.mark.asyncio
    async def test_submit_error_report_with_stack(self):
        """Test submitting error report with stack trace."""
        error_report = ErrorReport(
            message="Component crashed",
            stack="Error: Something went wrong\n  at Component.render\n  at App",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            # Should be called 2 times: once for message, once for stack
            assert mock_logger.error.call_count == 2
            # First call is the error message
            assert "[CLIENT-ERROR]" in mock_logger.error.call_args_list[0][0][0]
            # Second call is the stack trace
            assert "[CLIENT-ERROR-STACK]" in mock_logger.error.call_args_list[1][0][0]
            assert "Something went wrong" in mock_logger.error.call_args_list[1][0][0]

    @pytest.mark.asyncio
    async def test_submit_error_report_with_component_stack(self):
        """Test submitting error report with component stack."""
        error_report = ErrorReport(
            message="Component crashed",
            componentStack="    at ErrorBoundary\n    at App",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            # Should be called 2 times: once for message, once for component stack
            assert mock_logger.error.call_count == 2
            assert (
                "[CLIENT-COMPONENT-STACK]" in mock_logger.error.call_args_list[1][0][0]
            )
            assert "ErrorBoundary" in mock_logger.error.call_args_list[1][0][0]

    @pytest.mark.asyncio
    async def test_submit_error_report_with_both_stacks(self):
        """Test submitting error report with both stacks."""
        error_report = ErrorReport(
            message="Component crashed",
            stack="Error: Something went wrong\n  at Component.render",
            componentStack="    at ErrorBoundary\n    at App",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            # Should be called 3 times: message, stack, component stack
            assert mock_logger.error.call_count == 3
            assert "[CLIENT-ERROR]" in mock_logger.error.call_args_list[0][0][0]
            assert "[CLIENT-ERROR-STACK]" in mock_logger.error.call_args_list[1][0][0]
            assert (
                "[CLIENT-COMPONENT-STACK]" in mock_logger.error.call_args_list[2][0][0]
            )

    @pytest.mark.asyncio
    async def test_submit_error_report_with_component_name(self):
        """Test submitting error report with component name."""
        error_report = ErrorReport(
            message="Component error",
            componentName="PhotoGrid",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            call_args = mock_logger.error.call_args_list[0][0][0]
            assert "Component:" in call_args
            assert "PhotoGrid" in call_args

    @pytest.mark.asyncio
    async def test_submit_error_report_with_url(self):
        """Test submitting error report with URL."""
        error_report = ErrorReport(
            message="Page error",
            url="http://example.com/photos",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            call_args = mock_logger.error.call_args_list[0][0][0]
            assert "URL:" in call_args
            assert "http://example.com/photos" in call_args

    @pytest.mark.asyncio
    async def test_submit_error_report_with_user_agent(self):
        """Test submitting error report with user agent."""
        error_report = ErrorReport(
            message="Browser error",
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            call_args = mock_logger.error.call_args_list[0][0][0]
            assert "UA:" in call_args
            assert "Mozilla/5.0" in call_args

    @pytest.mark.asyncio
    async def test_submit_error_report_with_all_fields(self):
        """Test submitting complete error report."""
        error_report = ErrorReport(
            message="Complete error",
            stack="Error: test\n  at function",
            componentStack="    at Component",
            componentName="TestComponent",
            url="http://example.com",
            userAgent="Mozilla/5.0",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            await submit_error_report(error_report)

            # Should be called 3 times
            assert mock_logger.error.call_count == 3

            # Check main error message
            main_call = mock_logger.error.call_args_list[0][0][0]
            assert "[CLIENT-ERROR]" in main_call
            assert "Complete error" in main_call
            assert "Component: TestComponent" in main_call
            assert "URL: http://example.com" in main_call
            assert "UA: Mozilla/5.0" in main_call

            # Check stack trace
            stack_call = mock_logger.error.call_args_list[1][0][0]
            assert "[CLIENT-ERROR-STACK]" in stack_call

            # Check component stack
            comp_stack_call = mock_logger.error.call_args_list[2][0][0]
            assert "[CLIENT-COMPONENT-STACK]" in comp_stack_call

    @pytest.mark.asyncio
    async def test_submit_error_report_invalid_timestamp(self):
        """Test submitting error report with invalid timestamp doesn't fail."""
        error_report = ErrorReport(
            message="Error message",
            timestamp="invalid-timestamp",
        )

        with patch("src.api.logs.logger") as mock_logger:
            result = await submit_error_report(error_report)

            # Should not raise exception
            assert result is None
            # Exception should be logged
            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_error_report_logging_exception(self):
        """Test that logging exceptions don't fail the request."""
        error_report = ErrorReport(
            message="Error message",
            timestamp=datetime.now().isoformat(),
        )

        with patch("src.api.logs.logger") as mock_logger:
            # Make logger.error raise an exception
            mock_logger.error.side_effect = Exception("Logging failed")

            # Should not raise exception
            result = await submit_error_report(error_report)

            assert result is None
            mock_logger.exception.assert_called_once()
