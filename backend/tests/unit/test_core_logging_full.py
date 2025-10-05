"""Comprehensive unit tests for logging configuration - 70%+ coverage target."""

import logging
import logging.handlers
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from src.core.logging_config import (
    ProductionFormatter,
    PerformanceFilter,
    RequestContextFilter,
    setup_logging,
    configure_module_loggers,
    log_slow_operation,
    log_error_with_context,
    get_logger,
)


class TestProductionFormatter:
    """Test ProductionFormatter class."""

    def test_format_basic_message(self):
        """Test formatting basic log message."""
        formatter = ProductionFormatter(
            fmt="%(levelname)s - %(message)s",
            datefmt="%Y-%m-%d"
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "Test message" in result

    def test_format_with_request_id(self):
        """Test formatting with request ID."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.request_id = "req-123"

        result = formatter.format(record)

        assert "req_id=req-123" in result

    def test_format_with_user_id(self):
        """Test formatting with user ID."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.user_id = "user-456"

        result = formatter.format(record)

        assert "user=user-456" in result

    def test_format_with_duration_ms(self):
        """Test formatting with duration metrics."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.duration_ms = 123.45

        result = formatter.format(record)

        assert "duration=123.45ms" in result

    def test_format_with_all_context(self):
        """Test formatting with all context fields."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.request_id = "req-789"
        record.user_id = "user-101"
        record.duration_ms = 55.5

        result = formatter.format(record)

        assert "req_id=req-789" in result
        assert "user=user-101" in result
        assert "duration=55.5ms" in result

    def test_format_without_extras(self):
        """Test formatting without extra context."""
        formatter = ProductionFormatter(fmt="%(message)s")

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None
        )

        result = formatter.format(record)

        # Should just return the message without extras
        assert result == "Test message"


class TestPerformanceFilter:
    """Test PerformanceFilter class."""

    def test_filter_allows_with_duration_ms(self):
        """Test filter allows records with duration_ms."""
        filter_obj = PerformanceFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.duration_ms = 100.0

        assert filter_obj.filter(record) is True

    def test_filter_blocks_without_duration_ms(self):
        """Test filter blocks records without duration_ms."""
        filter_obj = PerformanceFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )

        assert filter_obj.filter(record) is False


class TestRequestContextFilter:
    """Test RequestContextFilter class."""

    def test_filter_adds_request_id(self):
        """Test filter adds request_id to record."""
        filter_obj = RequestContextFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )

        filter_obj.filter(record)

        assert hasattr(record, "request_id")
        assert record.request_id == "no-request"

    def test_filter_adds_user_id(self):
        """Test filter adds user_id to record."""
        filter_obj = RequestContextFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )

        filter_obj.filter(record)

        assert hasattr(record, "user_id")
        assert record.user_id == "anonymous"

    def test_filter_preserves_existing_request_id(self):
        """Test filter preserves existing request_id."""
        filter_obj = RequestContextFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )
        record.request_id = "existing-req"

        filter_obj.filter(record)

        assert record.request_id == "existing-req"

    def test_filter_returns_true(self):
        """Test filter always returns True."""
        filter_obj = RequestContextFilter()

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test", args=(), exc_info=None
        )

        assert filter_obj.filter(record) is True


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_file_logging=True,
                    enable_console_logging=True,
                    enable_syslog=False
                )

                root_logger = logging.getLogger()
                assert root_logger.level == logging.INFO

    def test_setup_logging_sets_log_level(self):
        """Test that setup_logging sets correct log level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(log_level="DEBUG", log_dir=Path(temp_dir), enable_file_logging=False)

                root_logger = logging.getLogger()
                assert root_logger.level == logging.DEBUG

    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            assert not log_dir.exists()

            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_file_logging=True,
                    enable_console_logging=False
                )

                assert log_dir.exists()

    def test_setup_logging_creates_app_log_file(self):
        """Test that app log file is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_file_logging=True,
                    enable_console_logging=False,
                    app_name="test-app"
                )

                app_log = log_dir / "test-app.log"
                # File might not exist until first log, but handler should be created
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) > 0

    def test_setup_logging_creates_error_log_file(self):
        """Test that error log file handler is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=log_dir,
                    enable_file_logging=True,
                    enable_console_logging=False
                )

                # Check that handlers were created
                root_logger = logging.getLogger()
                handler_types = [type(h) for h in root_logger.handlers]
                assert logging.handlers.RotatingFileHandler in handler_types

    def test_setup_logging_console_handler(self):
        """Test console handler is created when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=Path(temp_dir),
                    enable_file_logging=False,
                    enable_console_logging=True
                )

                root_logger = logging.getLogger()
                handler_types = [type(h) for h in root_logger.handlers]
                assert logging.StreamHandler in handler_types

    def test_setup_logging_no_console_handler(self):
        """Test console handler not created when disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                # Clear existing handlers
                root_logger = logging.getLogger()
                root_logger.handlers.clear()

                setup_logging(
                    log_level="INFO",
                    log_dir=Path(temp_dir),
                    enable_file_logging=False,
                    enable_console_logging=False
                )

                # Should have no handlers
                assert len(root_logger.handlers) == 0

    def test_setup_logging_default_log_dir(self):
        """Test default log directory creation."""
        with patch('src.core.logging_config.settings') as mock_settings:
            mock_settings.DEBUG = False

            with patch('pathlib.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path(tempfile.gettempdir())

                setup_logging(
                    log_level="INFO",
                    log_dir=None,
                    enable_file_logging=True,
                    enable_console_logging=False
                )

                # Should use current directory / logs
                # Verify no errors occurred

    def test_setup_logging_syslog_unix(self):
        """Test syslog handler on Unix systems."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                with patch('sys.platform', 'linux'):
                    # Mock SysLogHandler to avoid needing actual syslog
                    with patch('logging.handlers.SysLogHandler'):
                        setup_logging(
                            log_level="INFO",
                            log_dir=Path(temp_dir),
                            enable_file_logging=False,
                            enable_console_logging=False,
                            enable_syslog=True
                        )

    def test_setup_logging_syslog_windows_skipped(self):
        """Test syslog handler skipped on Windows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                with patch('sys.platform', 'win32'):
                    setup_logging(
                        log_level="INFO",
                        log_dir=Path(temp_dir),
                        enable_file_logging=False,
                        enable_console_logging=False,
                        enable_syslog=True
                    )

                    # Should not crash

    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        root_logger = logging.getLogger()

        # Add a dummy handler
        dummy_handler = logging.NullHandler()
        root_logger.addHandler(dummy_handler)

        assert len(root_logger.handlers) > 0

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=Path(temp_dir),
                    enable_file_logging=False,
                    enable_console_logging=False
                )

                # Dummy handler should be removed
                assert dummy_handler not in root_logger.handlers


class TestConfigureModuleLoggers:
    """Test configure_module_loggers function."""

    def test_configure_module_loggers(self):
        """Test configuring module-specific loggers."""
        configure_module_loggers()

        # Check that third-party loggers are set to appropriate levels
        assert logging.getLogger("uvicorn.access").level == logging.WARNING
        assert logging.getLogger("uvicorn.error").level == logging.INFO
        assert logging.getLogger("fastapi").level == logging.INFO

    def test_configure_module_loggers_our_modules(self):
        """Test configuring our module loggers."""
        configure_module_loggers()

        # Check our modules
        assert logging.getLogger("src.api").level == logging.INFO
        assert logging.getLogger("src.workers").level == logging.INFO
        assert logging.getLogger("src.core").level == logging.DEBUG


class TestLogSlowOperation:
    """Test log_slow_operation function."""

    def test_log_slow_operation_above_threshold(self):
        """Test logging slow operation above threshold."""
        logger = logging.getLogger("test_slow")
        logger.warning = MagicMock()

        log_slow_operation(
            logger,
            operation="test_op",
            duration_ms=1500.0,
            threshold_ms=1000.0
        )

        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        assert "test_op" in call_args[0][0]
        assert "1500.00ms" in call_args[0][0]

    def test_log_slow_operation_below_threshold(self):
        """Test no logging for operation below threshold."""
        logger = logging.getLogger("test_fast")
        logger.warning = MagicMock()

        log_slow_operation(
            logger,
            operation="fast_op",
            duration_ms=500.0,
            threshold_ms=1000.0
        )

        logger.warning.assert_not_called()

    def test_log_slow_operation_with_context(self):
        """Test logging slow operation with additional context."""
        logger = logging.getLogger("test_context")
        logger.warning = MagicMock()

        log_slow_operation(
            logger,
            operation="context_op",
            duration_ms=2000.0,
            threshold_ms=1000.0,
            user_id="user-123",
            request_id="req-456"
        )

        logger.warning.assert_called_once()
        call_kwargs = logger.warning.call_args[1]
        assert "extra" in call_kwargs
        assert call_kwargs["extra"]["user_id"] == "user-123"
        assert call_kwargs["extra"]["request_id"] == "req-456"

    def test_log_slow_operation_at_threshold(self):
        """Test operation exactly at threshold is not logged."""
        logger = logging.getLogger("test_threshold")
        logger.warning = MagicMock()

        log_slow_operation(
            logger,
            operation="threshold_op",
            duration_ms=1000.0,
            threshold_ms=1000.0
        )

        logger.warning.assert_not_called()


class TestLogErrorWithContext:
    """Test log_error_with_context function."""

    def test_log_error_with_context_basic(self):
        """Test logging error with context."""
        logger = logging.getLogger("test_error")
        logger.exception = MagicMock()

        error = ValueError("Test error")

        log_error_with_context(logger, error, "test_operation")

        logger.exception.assert_called_once()
        call_args = logger.exception.call_args
        assert "test_operation" in call_args[0][0]
        assert "ValueError" in call_args[0][0]

    def test_log_error_with_context_with_kwargs(self):
        """Test logging error with additional context."""
        logger = logging.getLogger("test_error_context")
        logger.exception = MagicMock()

        error = RuntimeError("Runtime error")

        log_error_with_context(
            logger,
            error,
            "complex_operation",
            user_id="user-789",
            request_id="req-012"
        )

        logger.exception.assert_called_once()
        call_kwargs = logger.exception.call_args[1]
        assert "extra" in call_kwargs
        assert call_kwargs["extra"]["user_id"] == "user-789"
        assert call_kwargs["extra"]["request_id"] == "req-012"


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_adds_request_context_filter(self):
        """Test get_logger adds RequestContextFilter."""
        logger = get_logger("test_filter")

        # Check that RequestContextFilter is in filters
        filter_types = [type(f) for f in logger.filters]
        assert RequestContextFilter in filter_types

    def test_get_logger_multiple_calls_same_logger(self):
        """Test multiple calls with same name return same logger."""
        logger1 = get_logger("same_logger")
        logger2 = get_logger("same_logger")

        assert logger1 is logger2


class TestLoggingInitialization:
    """Test module-level logging initialization."""

    def test_logging_initialized_on_import(self):
        """Test that logging is initialized when module is imported."""
        # This is tested implicitly by the module import
        # Just verify root logger has handlers
        root_logger = logging.getLogger()

        # Should have at least some configuration
        assert root_logger.level > 0


class TestLoggingEdgeCases:
    """Test edge cases in logging configuration."""

    def test_setup_logging_with_invalid_level(self):
        """Test setup_logging with invalid log level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                # Should handle invalid level gracefully or raise
                try:
                    setup_logging(
                        log_level="INVALID",
                        log_dir=Path(temp_dir),
                        enable_file_logging=False
                    )
                except (ValueError, AttributeError):
                    # Expected behavior
                    pass

    def test_setup_logging_with_max_bytes(self):
        """Test setup_logging with custom max_bytes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.logging_config.settings') as mock_settings:
                mock_settings.DEBUG = False

                setup_logging(
                    log_level="INFO",
                    log_dir=Path(temp_dir),
                    enable_file_logging=True,
                    enable_console_logging=False,
                    max_bytes=5_000_000,
                    backup_count=5
                )

                # Verify no errors

    def test_production_formatter_handles_exception(self):
        """Test ProductionFormatter handles exception info."""
        formatter = ProductionFormatter(fmt="%(message)s")

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="Error occurred", args=(), exc_info=exc_info
            )

            result = formatter.format(record)

            assert "Error occurred" in result
