"""Logging endpoints for Ideal Goggles API."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class LogEntry(BaseModel):
    """Log entry model for client-side logging."""

    level: str = Field(description="Log level", pattern="^(DEBUG|INFO|WARN|ERROR)$")
    message: str = Field(description="Log message")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    timestamp: str = Field(description="ISO timestamp")
    userAgent: str | None = Field(None, description="User agent string")
    url: str | None = Field(None, description="Current URL")
    error: dict[str, Any] | None = Field(None, description="Error details")


class ErrorReport(BaseModel):
    """Error report model for error boundary reporting."""

    message: str = Field(description="Error message")
    stack: str | None = Field(None, description="Error stack trace")
    componentStack: str | None = Field(None, description="React component stack")
    componentName: str | None = Field(None, description="Component name")
    timestamp: str = Field(description="ISO timestamp")
    userAgent: str | None = Field(None, description="User agent string")
    url: str | None = Field(None, description="Current URL")


@router.post("/logs", status_code=status.HTTP_204_NO_CONTENT)
async def submit_client_logs(log_entry: LogEntry) -> None:
    """
    Submit client-side logs.

    Args:
        log_entry: Log entry from frontend

    Returns:
        204 No Content on success
    """
    try:
        # Parse timestamp
        datetime.fromisoformat(log_entry.timestamp)

        # Format log message for backend logger
        context_str = f" | Context: {log_entry.context}" if log_entry.context else ""
        url_str = f" | URL: {log_entry.url}" if log_entry.url else ""
        user_agent_str = f" | UA: {log_entry.userAgent}" if log_entry.userAgent else ""
        error_str = f" | Error: {log_entry.error}" if log_entry.error else ""

        formatted_message = (
            f"[CLIENT-{log_entry.level}] {log_entry.message}"
            f"{context_str}{url_str}{user_agent_str}{error_str}"
        )

        # Log with appropriate level
        if log_entry.level == "DEBUG":
            logger.debug(formatted_message)
        elif log_entry.level == "INFO":
            logger.info(formatted_message)
        elif log_entry.level == "WARN":
            logger.warning(formatted_message)
        elif log_entry.level == "ERROR":
            logger.error(formatted_message)
        else:
            logger.info(formatted_message)  # Fallback

    except Exception as e:
        # Don't fail client requests due to logging issues
        logger.exception(f"Failed to process client log: {e}")


@router.post("/logs/errors", status_code=status.HTTP_204_NO_CONTENT)
async def submit_error_report(error_report: ErrorReport) -> None:
    """
    Submit error reports from error boundaries.

    Args:
        error_report: Error report from frontend error boundary

    Returns:
        204 No Content on success
    """
    try:
        # Parse timestamp
        datetime.fromisoformat(error_report.timestamp)

        # Format error report for backend logger
        component_str = (
            f" | Component: {error_report.componentName}"
            if error_report.componentName
            else ""
        )
        url_str = f" | URL: {error_report.url}" if error_report.url else ""
        user_agent_str = (
            f" | UA: {error_report.userAgent}" if error_report.userAgent else ""
        )

        formatted_message = (
            f"[CLIENT-ERROR] {error_report.message}"
            f"{component_str}{url_str}{user_agent_str}"
        )

        # Log the error
        logger.error(formatted_message)

        # Also log stack traces if available
        if error_report.stack:
            logger.error(f"[CLIENT-ERROR-STACK] {error_report.stack}")

        if error_report.componentStack:
            logger.error(f"[CLIENT-COMPONENT-STACK] {error_report.componentStack}")

    except Exception as e:
        # Don't fail client requests due to logging issues
        logger.exception(f"Failed to process error report: {e}")
