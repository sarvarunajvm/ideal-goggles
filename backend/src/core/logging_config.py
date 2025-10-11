"""Production-ready logging configuration for the Ideal Goggles API."""

import logging
import logging.handlers
import contextlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import settings

# Create a logger for this module
logger = logging.getLogger(__name__)


class ProductionFormatter(logging.Formatter):
    """Enhanced formatter for production debugging with detailed context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context for production debugging."""
        # Add request ID if available (from context vars)
        request_id = getattr(record, "request_id", "no-request")

        # Add user/session info if available
        user_id = getattr(record, "user_id", "anonymous")

        # Add performance metrics if available
        duration_ms = getattr(record, "duration_ms", None)

        # Build the base message
        base_msg = super().format(record)

        # Add extra context
        extras = []
        if request_id != "no-request":
            extras.append(f"req_id={request_id}")
        if user_id != "anonymous":
            extras.append(f"user={user_id}")
        if duration_ms is not None:
            extras.append(f"duration={duration_ms}ms")

        if extras:
            return f"{base_msg} [{' '.join(extras)}]"
        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    enable_syslog: bool = False,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 10,
    app_name: str = "ideal-goggles-api",
) -> None:
    """
    Configure comprehensive logging for production environment.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to ./logs)
        enable_file_logging: Enable rotating file handler
        enable_console_logging: Enable console output
        enable_syslog: Enable syslog handler for centralized logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        app_name: Application name for log identification
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = ProductionFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Console Handler
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            simple_formatter if settings.DEBUG else detailed_formatter
        )
        root_logger.addHandler(console_handler)

    # File Handler with rotation
    if enable_file_logging:
        if log_dir is None:
            log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)

        # Main application log
        app_log_file = log_dir / f"{app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Error log (separate file for errors and above)
        error_log_file = log_dir / f"{app_name}.error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

        # Performance log (for slow operations)
        perf_log_file = log_dir / f"{app_name}.performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        perf_handler.addFilter(PerformanceFilter())
        root_logger.addHandler(perf_handler)

    # Syslog Handler (for centralized logging)
    if enable_syslog and sys.platform != "win32":
        try:
            syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
            # Ensure we set a concrete level value, not a mock
            warning_level = (
                logging.WARNING if isinstance(logging.WARNING, int) else 30
            )
            # Some tests mock SysLogHandler; set both via method and attribute
            with contextlib.suppress(Exception):
                syslog_handler.setLevel(warning_level)
            with contextlib.suppress(Exception):
                syslog_handler.level = warning_level
            syslog_formatter = logging.Formatter(
                f"{app_name}: %(levelname)s - %(message)s"
            )
            syslog_handler.setFormatter(syslog_formatter)
            root_logger.addHandler(syslog_handler)
        except Exception as e:
            logger.warning(f"Could not set up syslog handler: {e}")

    # Configure specific loggers
    configure_module_loggers()

    # Log startup information
    logger.info(f"Logging initialized for {app_name}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log directory: {log_dir if enable_file_logging else 'disabled'}")
    logger.info(f"Debug mode: {settings.DEBUG}")


def configure_module_loggers() -> None:
    """Configure specific module loggers with appropriate levels."""
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Set specific levels for our modules
    logging.getLogger("src.api").setLevel(logging.INFO)
    logging.getLogger("src.workers").setLevel(logging.INFO)
    logging.getLogger("src.services").setLevel(logging.INFO)
    logging.getLogger("src.db").setLevel(logging.INFO)
    logging.getLogger("src.core").setLevel(logging.DEBUG)


class PerformanceFilter(logging.Filter):
    """Filter to only log performance-related messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Only allow records with performance metrics."""
        return hasattr(record, "duration_ms")


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context if available."""
        # This would be populated from FastAPI middleware
        record.request_id = getattr(record, "request_id", "no-request")
        record.user_id = getattr(record, "user_id", "anonymous")
        return True


def log_slow_operation(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    threshold_ms: float = 1000,
    **kwargs: Any,
) -> None:
    """
    Log slow operations for performance monitoring.

    Args:
        logger: Logger instance
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        threshold_ms: Threshold for considering operation slow
        **kwargs: Additional context to log
    """
    if duration_ms > threshold_ms:
        extra = {"duration_ms": duration_ms}
        extra.update(kwargs)
        logger.warning(
            f"Slow operation detected: {operation} took {duration_ms:.2f}ms",
            extra=extra,
        )


def log_error_with_context(
    logger: logging.Logger, error: Exception, operation: str, **context: Any
) -> None:
    """
    Log error with full context for debugging.

    Args:
        logger: Logger instance
        error: The exception that occurred
        operation: What operation was being performed
        **context: Additional context about the error
    """
    logger.exception(
        f"Error in {operation}: {error.__class__.__name__}: {error!s}",
        extra=context,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.addFilter(RequestContextFilter())
    return logger


# Initialize logging on module import
if not logging.getLogger().handlers:
    setup_logging(
        log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
        enable_file_logging=not settings.DEBUG,
        enable_console_logging=True,
        enable_syslog=False,  # Enable in production if needed
    )
