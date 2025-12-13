"""Logging endpoints for Ideal Goggles API."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class LogEntry(BaseModel):
    """Log entry model for client-side logging."""

    level: str = Field(description="Log level", pattern="^(DEBUG|INFO|WARN|ERROR)$")
    message: str = Field(description="Log message")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    timestamp: str = Field(description="ISO timestamp")
    user_agent: str | None = Field(
        None, alias="userAgent", description="User agent string"
    )
    url: str | None = Field(None, description="Current URL")
    error: dict[str, Any] | None = Field(None, description="Error details")


class ErrorReport(BaseModel):
    """Error report model for error boundary reporting."""

    message: str = Field(description="Error message")
    stack: str | None = Field(None, description="Error stack trace")
    component_stack: str | None = Field(
        None, alias="componentStack", description="React component stack"
    )
    component_name: str | None = Field(
        None, alias="componentName", description="Component name"
    )
    timestamp: str = Field(description="ISO timestamp")
    user_agent: str | None = Field(
        None, alias="userAgent", description="User agent string"
    )
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
        user_agent_str = (
            f" | UA: {log_entry.user_agent}" if log_entry.user_agent else ""
        )
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
            f" | Component: {error_report.component_name}"
            if error_report.component_name
            else ""
        )
        url_str = f" | URL: {error_report.url}" if error_report.url else ""
        user_agent_str = (
            f" | UA: {error_report.user_agent}" if error_report.user_agent else ""
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

        if error_report.component_stack:
            logger.error(f"[CLIENT-COMPONENT-STACK] {error_report.component_stack}")

    except Exception as e:
        # Don't fail client requests due to logging issues
        logger.exception(f"Failed to process error report: {e}")


class LogLine(BaseModel):
    """Parsed log line."""

    timestamp: str
    level: str
    logger_name: str
    message: str
    source: Literal["backend", "frontend", "electron"]
    function: str | None = None
    line_number: int | None = None
    request_id: str | None = None


class LogsResponse(BaseModel):
    """Response model for logs endpoint."""

    logs: list[LogLine]
    total: int
    has_more: bool
    sources: list[str]


@router.get("/logs/fetch", response_model=LogsResponse)
async def fetch_logs(
    source: str = Query(
        "all", description="Log source: backend, frontend, electron, or all"
    ),
    level: str = Query(
        "all", description="Filter by log level: DEBUG, INFO, WARN, ERROR, or all"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of log lines to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    search: str | None = Query(None, description="Search term to filter logs"),
) -> LogsResponse:
    """
    Fetch logs from backend log files.

    Args:
        source: Filter by log source
        level: Filter by log level
        limit: Number of lines to return
        offset: Pagination offset
        search: Search term

    Returns:
        Log entries with metadata
    """
    try:
        logs_dir = Path.cwd() / "logs"

        # Determine which log files to read based on source
        log_files = []

        if source in ("backend", "all"):
            backend_log = logs_dir / "ideal-goggles-api.log"
            if backend_log.exists():
                log_files.append(("backend", backend_log))

        if not log_files:
            return LogsResponse(logs=[], total=0, has_more=False, sources=[])

        # Parse log files
        all_logs: list[LogLine] = []

        for src, log_file in log_files:
            try:
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()

                for line in lines:
                    parsed = _parse_log_line(line.strip(), src)
                    if parsed:
                        # Apply filters
                        if level not in ("all", parsed.level):
                            continue
                        if search and search.lower() not in parsed.message.lower():
                            continue

                        all_logs.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")

        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total = len(all_logs)
        paginated = all_logs[offset : offset + limit]
        has_more = (offset + limit) < total

        sources = list({log.source for log in all_logs})

        return LogsResponse(
            logs=paginated, total=total, has_more=has_more, sources=sources
        )

    except Exception as e:
        logger.exception(f"Failed to fetch logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {e!s}",
        )


def _parse_log_line(line: str, source: str) -> LogLine | None:
    """
    Parse a log line into structured format.

    Expected format:
    2025-12-13 10:30:45 - src.api.health - INFO - health_check:25 - Health check requested

    Or for client logs:
    2025-12-13 10:30:45 - src.api.logs - INFO - submit_client_logs:78 - [CLIENT-INFO] Message
    """
    try:
        # Pattern for backend logs
        pattern = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^ ]+) - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - ([^:]+):(\d+) - (.+)$"

        match = re.match(pattern, line)
        if match:
            timestamp, logger_name, level, function, line_num, message = match.groups()

            # Normalize level names
            if level == "WARNING":
                level = "WARN"

            # Extract request_id if present
            request_id = None
            req_match = re.search(r"\[req_id=([^\]]+)\]", message)
            if req_match:
                request_id = req_match.group(1)

            # Detect client logs and update source
            detected_source = source
            if "[CLIENT-" in message:
                detected_source = "frontend"

            return LogLine(
                timestamp=timestamp,
                level=level,
                logger_name=logger_name,
                message=message,
                source=detected_source,
                function=function,
                line_number=int(line_num),
                request_id=request_id,
            )

        return None

    except Exception as e:
        logger.debug(f"Failed to parse log line: {e}")
        return None
