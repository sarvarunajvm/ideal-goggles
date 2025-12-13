"""Health check endpoint for Ideal Goggles API."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException

from ..db.connection import get_database_manager

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Lightweight health check endpoint for quick availability checks.
    For detailed health information, use /health/detailed

    Returns:
        Dict containing basic health status
    """
    try:
        # Quick database connectivity check
        db_manager = get_database_manager()
        test_query = "SELECT 1 as test"
        result = db_manager.execute_query(test_query)
        db_healthy = result and len(result) > 0 and result[0][0] == 1

    except Exception as e:
        # Do not fail the health endpoint; return degraded status and error info
        db_healthy = False
        db_error = f"Database check failed: {e!s}"
    else:
        db_error = None

    # Basic health response augmented with system and dependency information
    try:
        system_info = _get_system_info()
        deps_health = _check_dependencies()

        status = (
            "healthy"
            if (db_healthy and deps_health.get("critical_available", True))
            else "degraded"
        )

        response = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.8",
            "service": "ideal-goggles-api",
            "system": system_info,
            "database": {"healthy": db_healthy},
            "dependencies": deps_health,
        }

        if db_error:
            response["database"]["error"] = db_error

        return response
    except Exception as e:
        # If system info or dependency checks fail, report service unavailable
        raise HTTPException(status_code=503, detail=f"Health check failed: {e!s}")


def _get_system_info() -> dict[str, Any]:
    """Get system resource information."""
    try:
        # Memory information
        memory = psutil.virtual_memory()

        # Disk information
        disk = psutil.disk_usage("/")

        # CPU information (non-blocking)
        cpu_percent = psutil.cpu_percent(interval=None)

        return {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 1),
            },
            "cpu": {"usage_percent": cpu_percent, "cores": psutil.cpu_count()},
            "platform": os.name,
        }
    except Exception as e:
        return {"error": f"Could not retrieve system info: {e!s}"}


async def _check_database_health() -> dict[str, Any]:
    """Check database connectivity and basic operations."""
    try:
        db_manager = get_database_manager()

        # Test basic database operation
        test_query = "SELECT 1 as test"
        result = db_manager.execute_query(test_query)

        if result and len(result) > 0 and result[0][0] == 1:
            # Get database info
            db_info = db_manager.get_database_info()

            return {
                "healthy": True,
                "database_size_mb": db_info.get("database_size_mb", 0),
                "schema_version": db_info.get("settings", {}).get(
                    "schema_version", "unknown"
                ),
                "tables": db_info.get("table_counts", {}),
            }
        return {"healthy": False, "error": "Database query test failed"}

    except Exception as e:
        return {"healthy": False, "error": f"Database connection failed: {e!s}"}


def _check_dependencies() -> dict[str, Any]:
    """Check availability of required dependencies."""
    dependencies = {}

    # Check PIL/Pillow
    try:
        import PIL

        dependencies["PIL"] = {"available": True, "version": PIL.__version__}
    except ImportError:
        dependencies["PIL"] = {"available": False, "error": "PIL/Pillow not available"}

    # Check numpy
    try:
        import numpy as np

        dependencies["numpy"] = {"available": True, "version": np.__version__}
    except ImportError:
        dependencies["numpy"] = {"available": False, "error": "NumPy not available"}

    # Check CLIP (optional)
    try:
        import clip

        dependencies["clip"] = {"available": True, "version": "available"}
    except ImportError:
        dependencies["clip"] = {"available": False, "error": "CLIP not available"}

    # Check Tesseract (optional)
    try:
        import subprocess

        from ..core.config import settings

        result = subprocess.run(
            ["tesseract", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=settings.HTTP_REQUEST_TIMEOUT,
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            dependencies["tesseract"] = {"available": True, "version": version}
        else:
            dependencies["tesseract"] = {
                "available": False,
                "error": "Tesseract command failed",
            }
    except Exception:
        dependencies["tesseract"] = {
            "available": False,
            "error": "Tesseract not available",
        }

    # Check InsightFace (optional)
    try:
        import insightface

        dependencies["insightface"] = {"available": True, "version": "available"}
    except ImportError:
        dependencies["insightface"] = {
            "available": False,
            "error": "InsightFace not available",
        }

    # Check watchdog
    try:
        import watchdog

        try:
            version = watchdog.__version__
        except AttributeError:
            version = "available"
        dependencies["watchdog"] = {"available": True, "version": version}
    except ImportError:
        dependencies["watchdog"] = {
            "available": False,
            "error": "Watchdog not available",
        }

    # Determine if all critical dependencies are available
    critical_deps = ["PIL", "numpy"]
    all_critical_available = all(
        dependencies.get(dep, {}).get("available", False) for dep in critical_deps
    )

    all_available = all(
        dep_info.get("available", False) for dep_info in dependencies.values()
    )

    return {
        "dependencies": dependencies,
        "all_available": all_available,
        "critical_available": all_critical_available,
    }


@router.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """
    Detailed health check with comprehensive system information.

    Returns:
        Dict containing detailed health status and diagnostics
    """
    try:
        # Build detailed health response
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.8",
            "service": "ideal-goggles-api",
        }

        # Add system information
        system_info = _get_system_info()
        health_data["system"] = system_info

        # Check database connectivity
        db_health = await _check_database_health()
        health_data["database"] = db_health

        # Check dependencies
        deps_health = _check_dependencies()
        health_data["dependencies"] = deps_health

        # Determine overall health status
        if not db_health["healthy"] or not deps_health["critical_available"]:
            health_data["status"] = "degraded"

        # Add diagnostics
        health_data["diagnostics"] = {
            "uptime": _get_uptime(),
            "environment": _get_environment_info(),
            "performance": await _get_performance_metrics(),
        }

        return health_data

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Detailed health check failed: {e!s}"
        )


def _get_uptime() -> dict[str, Any]:
    """Get system uptime information."""
    try:
        import time

        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = current_time - boot_time

        return {
            "system_uptime_seconds": int(uptime_seconds),
            "system_uptime_hours": round(uptime_seconds / 3600, 1),
            "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
        }
    except Exception as e:
        return {"error": f"Could not get uptime: {e!s}"}


def _get_environment_info() -> dict[str, Any]:
    """Get environment information."""
    return {
        "python_version": os.sys.version,
        "working_directory": str(Path.cwd()),
        "environment_variables": {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "HOME": os.environ.get("HOME", ""),
        },
    }


async def _get_performance_metrics() -> dict[str, Any]:
    """Get performance metrics."""
    try:
        # Database performance test
        db_manager = get_database_manager()
        start_time = datetime.now()

        # Simple query performance test
        db_manager.execute_query("SELECT COUNT(*) FROM photos")

        db_query_time = (datetime.now() - start_time).total_seconds()

        return {
            "database_query_time_ms": round(db_query_time * 1000, 2),
            "memory_available_mb": round(
                psutil.virtual_memory().available / (1024**2), 2
            ),
            "disk_io": {
                "read_bytes": (
                    psutil.disk_io_counters().read_bytes
                    if psutil.disk_io_counters()
                    else 0
                ),
                "write_bytes": (
                    psutil.disk_io_counters().write_bytes
                    if psutil.disk_io_counters()
                    else 0
                ),
            },
        }
    except Exception as e:
        return {"error": f"Could not get performance metrics: {e!s}"}


@router.get("/health/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check to determine if service is ready to handle requests.

    Returns:
        Dict indicating if service is ready
    """
    try:
        # Check critical components
        db_health = await _check_database_health()
        deps_health = _check_dependencies()

        is_ready = db_health["healthy"] and deps_health["critical_available"]

        return {
            "ready": is_ready,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": db_health["healthy"],
                "critical_dependencies": deps_health["critical_available"],
            },
        }

    except Exception as e:
        return {
            "ready": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.get("/health/live")
async def liveness_check() -> dict[str, Any]:
    """
    Liveness check to determine if service is alive.

    Returns:
        Dict indicating if service is alive
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat(),
        "service": "ideal-goggles-api",
    }
