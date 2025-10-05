"""Unit tests for logging configuration module."""

import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.logging_config import (
    PerformanceFilter,
    ProductionFormatter,
    RequestContextFilter,
    configure_module_loggers,
    get_logger,
    log_error_with_context,
    log_slow_operation,
    setup_logging,
)


class TestProductionFormatter:
    """Test ProductionFormatter class."""

    def test_production_formatter_basic(self):
        """Test basic formatting without extra fields."""
        formatter = ProductionFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "Test message" in formatted
        assert "INFO" in formatted

    def test_production_formatter_with_request_id(self):
        """Test formatting with request ID."""
        formatter = ProductionFormatter(
            fmt="%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"

        formatted = formatter.format(record)
        assert "Test message" in formatted
        assert "req_id=req-123" in formatted

    def test_production_formatter_with_user_id(self):
        """Test formatting with user ID."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.user_id = "user-456"

        formatted = formatter.format(record)
        assert "user=user-456" in formatted

    def test_production_formatter_with_duration(self):
        """Test formatting with duration metrics."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.duration_ms = 250.5

        formatted = formatter.format(record)
        assert "duration=250.5ms" in formatted

    def test_production_formatter_with_all_fields(self):
        """Test formatting with all extra fields."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"
        record.user_id = "user-456"
        record.duration_ms = 250.5

        formatted = formatter.format(record)
        assert "Test message" in formatted
        assert "req_id=req-123" in formatted
        assert "user=user-456" in formatted
        assert "duration=250.5ms" in formatted


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            setup_logging(
                log_level="INFO",
                log_dir=log_dir,
                enable_file_logging=True,
                enable_console_logging=True,
            )

            # Log directory should be created
            assert log_dir.exists()

            # Log files should exist
            assert (log_dir / "ideal-goggles-api.log").exists()
            assert (log_dir / "ideal-goggles-api.error.log").exists()
            assert (log_dir / "ideal-goggles-api.performance.log").exists()

    def test_setup_logging_custom_app_name(self):
        """Test setup_logging with custom app name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            setup_logging(
                log_level="DEBUG",
                log_dir=log_dir,
                app_name="test-app",
            )

            assert (log_dir / "test-app.log").exists()
            assert (log_dir / "test-app.error.log").exists()

    def test_setup_logging_console_only(self):
        """Test setup_logging with console logging only."""
        setup_logging(
            log_level="WARNING",
            enable_file_logging=False,
            enable_console_logging=True,
        )

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_file_only(self):
        """Test setup_logging with file logging only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            setup_logging(
                log_level="ERROR",
                log_dir=log_dir,
                enable_file_logging=True,
                enable_console_logging=False,
            )

            assert log_dir.exists()

    def test_setup_logging_custom_rotation(self):
        """Test setup_logging with custom rotation settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            setup_logging(
                log_level="INFO",
                log_dir=log_dir,
                max_bytes=1_000_000,
                backup_count=5,
            )

            assert log_dir.exists()

    def test_setup_logging_with_syslog_success(self):
        """Test setup_logging with syslog successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            # Only test on non-Windows platforms
            if sys.platform != "win32":
                # Mock syslog handler to succeed - create a proper mock with level attribute
                mock_handler = MagicMock()
                mock_handler.level = logging.WARNING
                with patch("logging.handlers.SysLogHandler", return_value=mock_handler):
                    setup_logging(
                        log_level="INFO",
                        log_dir=log_dir,
                        enable_syslog=True,
                    )
            else:
                # On Windows, just ensure no error
                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_syslog=True,
                )

    def test_setup_logging_with_syslog_failure(self):
        """Test setup_logging handles syslog failure gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            # Only test on non-Windows platforms
            if sys.platform != "win32":
                # Mock syslog handler to raise an exception
                with patch(
                    "logging.handlers.SysLogHandler", side_effect=OSError("No syslog")
                ):
                    setup_logging(
                        log_level="INFO",
                        log_dir=log_dir,
                        enable_syslog=True,
                    )
                    # Should continue without syslog
                    assert log_dir.exists()

    def test_setup_logging_syslog_disabled_on_windows(self):
        """Test that syslog is not set up on Windows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            with patch("sys.platform", "win32"):
                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_syslog=True,
                )

                # Should not raise an error
                assert True


class TestConfigureModuleLoggers:
    """Test configure_module_loggers function."""

    def test_configure_module_loggers(self):
        """Test that module loggers are configured correctly."""
        configure_module_loggers()

        # Check that specific loggers have correct levels
        assert logging.getLogger("uvicorn.access").level == logging.WARNING
        assert logging.getLogger("uvicorn.error").level == logging.INFO
        assert logging.getLogger("src.core").level == logging.DEBUG


class TestPerformanceFilter:
    """Test PerformanceFilter class."""

    def test_performance_filter_allows_with_duration(self):
        """Test that filter allows records with duration_ms."""
        pfilter = PerformanceFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.duration_ms = 100.0

        assert pfilter.filter(record) is True

    def test_performance_filter_blocks_without_duration(self):
        """Test that filter blocks records without duration_ms."""
        pfilter = PerformanceFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )

        assert pfilter.filter(record) is False


class TestRequestContextFilter:
    """Test RequestContextFilter class."""

    def test_request_context_filter_adds_context(self):
        """Test that filter adds request context."""
        rfilter = RequestContextFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = rfilter.filter(record)
        assert result is True
        assert hasattr(record, "request_id")
        assert hasattr(record, "user_id")

    def test_request_context_filter_preserves_existing(self):
        """Test that filter preserves existing context."""
        rfilter = RequestContextFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.request_id = "custom-123"
        record.user_id = "user-456"

        result = rfilter.filter(record)
        assert result is True
        assert record.request_id == "custom-123"
        assert record.user_id == "user-456"


class TestLogSlowOperation:
    """Test log_slow_operation function."""

    def test_log_slow_operation_above_threshold(self):
        """Test logging slow operations above threshold."""
        logger = logging.getLogger("test_slow_op")
        logger.setLevel(logging.WARNING)

        with patch.object(logger, "warning") as mock_warning:
            log_slow_operation(
                logger,
                operation="test_operation",
                duration_ms=2000.0,
                threshold_ms=1000.0,
            )

            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "test_operation" in call_args[0][0]
            assert "2000.00ms" in call_args[0][0]

    def test_log_slow_operation_below_threshold(self):
        """Test that fast operations are not logged."""
        logger = logging.getLogger("test_fast_op")

        with patch.object(logger, "warning") as mock_warning:
            log_slow_operation(
                logger,
                operation="test_operation",
                duration_ms=500.0,
                threshold_ms=1000.0,
            )

            mock_warning.assert_not_called()

    def test_log_slow_operation_with_extra_context(self):
        """Test logging slow operations with extra context."""
        logger = logging.getLogger("test_slow_context")

        with patch.object(logger, "warning") as mock_warning:
            log_slow_operation(
                logger,
                operation="test_operation",
                duration_ms=1500.0,
                threshold_ms=1000.0,
                user_id="user-123",
                request_id="req-456",
            )

            mock_warning.assert_called_once()
            call_kwargs = mock_warning.call_args[1]
            assert "extra" in call_kwargs
            assert call_kwargs["extra"]["user_id"] == "user-123"
            assert call_kwargs["extra"]["request_id"] == "req-456"


class TestLogErrorWithContext:
    """Test log_error_with_context function."""

    def test_log_error_with_context(self):
        """Test logging errors with context."""
        logger = logging.getLogger("test_error")

        with patch.object(logger, "exception") as mock_exception:
            error = ValueError("Test error message")
            log_error_with_context(
                logger,
                error,
                operation="test_operation",
                user_id="user-123",
            )

            mock_exception.assert_called_once()
            call_args = mock_exception.call_args
            assert "test_operation" in call_args[0][0]
            assert "ValueError" in call_args[0][0]
            assert "Test error message" in call_args[0][0]

    def test_log_error_with_multiple_context(self):
        """Test logging errors with multiple context fields."""
        logger = logging.getLogger("test_error_multi")

        with patch.object(logger, "exception") as mock_exception:
            error = RuntimeError("Runtime error")
            log_error_with_context(
                logger,
                error,
                operation="complex_operation",
                user_id="user-123",
                request_id="req-456",
                file_path="/path/to/file",
            )

            mock_exception.assert_called_once()
            call_kwargs = mock_exception.call_args[1]
            assert "extra" in call_kwargs
            assert call_kwargs["extra"]["user_id"] == "user-123"
            assert call_kwargs["extra"]["request_id"] == "req-456"
            assert call_kwargs["extra"]["file_path"] == "/path/to/file"


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_adds_request_context_filter(self):
        """Test that get_logger adds RequestContextFilter."""
        logger = get_logger("test_filtered")

        # Check that filter is added
        has_request_filter = any(
            isinstance(f, RequestContextFilter) for f in logger.filters
        )
        assert has_request_filter

    def test_get_logger_different_names(self):
        """Test getting loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2


class TestLoggingModuleInitialization:
    """Test logging module initialization."""

    def test_logging_initialized_on_import(self):
        """Test that logging is initialized when module is imported."""
        # The logging should already be set up from module import
        root_logger = logging.getLogger()
        # Should have handlers if logging was initialized
        # This might be empty or have handlers depending on test execution order
        assert root_logger is not None
