"""Unit tests for health API endpoints."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.health import (
    _check_database_health,
    _check_dependencies,
    _get_environment_info,
    _get_performance_metrics,
    _get_system_info,
    _get_uptime,
    detailed_health_check,
    health_check,
    liveness_check,
    readiness_check,
)
from src.db.connection import DatabaseManager


@pytest.fixture
def db_manager():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        manager = DatabaseManager(str(db_path))
        yield manager


@pytest.fixture
def mock_db_manager(db_manager):
    """Mock the get_database_manager function."""
    with patch("src.api.health.get_database_manager") as mock:
        mock.return_value = db_manager
        yield mock


class TestSystemInfo:
    """Test _get_system_info function."""

    @patch("src.api.health.psutil")
    def test_get_system_info_success(self, mock_psutil):
        """Test successful system info retrieval."""
        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.total = 16 * (1024**3)  # 16 GB
        mock_memory.available = 8 * (1024**3)  # 8 GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock disk info
        mock_disk = MagicMock()
        mock_disk.total = 500 * (1024**3)  # 500 GB
        mock_disk.free = 250 * (1024**3)  # 250 GB
        mock_disk.used = 250 * (1024**3)  # 250 GB
        mock_psutil.disk_usage.return_value = mock_disk

        # Mock CPU info
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.cpu_count.return_value = 8

        result = _get_system_info()

        assert "memory" in result
        assert result["memory"]["total_gb"] == 16.0
        assert result["memory"]["available_gb"] == 8.0
        assert result["memory"]["used_percent"] == 50.0

        assert "disk" in result
        assert result["disk"]["total_gb"] == 500.0
        assert result["disk"]["free_gb"] == 250.0

        assert "cpu" in result
        assert result["cpu"]["usage_percent"] == 25.5
        assert result["cpu"]["cores"] == 8

        assert "platform" in result

    @patch("src.api.health.psutil")
    def test_get_system_info_error(self, mock_psutil):
        """Test system info retrieval with error."""
        mock_psutil.virtual_memory.side_effect = Exception("Memory error")

        result = _get_system_info()

        assert "error" in result
        assert "Memory error" in result["error"]


class TestDatabaseHealth:
    """Test _check_database_health function."""

    @pytest.mark.asyncio
    async def test_check_database_health_success(self, mock_db_manager, db_manager):
        """Test successful database health check."""
        # Mock database query
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={
                "database_size_mb": 10.5,
                "settings": {"schema_version": "1.0"},
                "table_counts": {"photos": 100, "exif": 50},
            }
        )

        result = await _check_database_health()

        assert result["healthy"] is True
        assert result["database_size_mb"] == 10.5
        assert result["schema_version"] == "1.0"
        assert "photos" in result["tables"]
        assert result["tables"]["photos"] == 100

    @pytest.mark.asyncio
    async def test_check_database_health_query_failed(
        self, mock_db_manager, db_manager
    ):
        """Test database health check when query fails."""
        db_manager.execute_query = MagicMock(return_value=[])

        result = await _check_database_health()

        assert result["healthy"] is False
        assert "error" in result
        assert "query test failed" in result["error"]

    @pytest.mark.asyncio
    async def test_check_database_health_exception(self, mock_db_manager, db_manager):
        """Test database health check with exception."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        result = await _check_database_health()

        assert result["healthy"] is False
        assert "error" in result
        assert "DB error" in result["error"]


class TestDependencies:
    """Test _check_dependencies function."""

    @patch("src.api.health.subprocess.run")
    def test_check_dependencies_all_available(self, mock_run):
        """Test when all dependencies are available."""
        # Mock Tesseract check
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "tesseract 5.0.0\n"
        mock_run.return_value = mock_result

        result = _check_dependencies()

        assert "dependencies" in result
        assert "all_available" in result
        assert "critical_available" in result

        # Check PIL and numpy (should be available in test environment)
        assert result["dependencies"]["PIL"]["available"] is True
        assert result["dependencies"]["numpy"]["available"] is True

    @patch("src.api.health.subprocess.run")
    def test_check_dependencies_tesseract_not_available(self, mock_run):
        """Test when Tesseract is not available."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = _check_dependencies()

        assert result["dependencies"]["tesseract"]["available"] is False

    @patch("src.api.health.subprocess.run")
    def test_check_dependencies_tesseract_timeout(self, mock_run):
        """Test when Tesseract check times out."""
        mock_run.side_effect = Exception("Timeout")

        result = _check_dependencies()

        assert result["dependencies"]["tesseract"]["available"] is False


class TestHealthCheck:
    """Test health_check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_db_manager, db_manager):
        """Test successful health check."""
        # Mock database operations
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={
                "database_size_mb": 10.5,
                "settings": {"schema_version": "1.0"},
                "table_counts": {"photos": 100},
            }
        )

        with (
            patch("src.api.health._get_system_info") as mock_system,
            patch("src.api.health._check_dependencies") as mock_deps,
        ):
            mock_system.return_value = {"cpu": {"cores": 8}}
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": True,
                "critical_available": True,
            }

            result = await health_check()

            assert result["status"] == "healthy"
            assert "timestamp" in result
            assert result["version"] == "1.0.8"
            assert result["service"] == "ideal-goggles-api"
            assert "system" in result
            assert "database" in result
            assert "dependencies" in result

    @pytest.mark.asyncio
    async def test_health_check_degraded_database(self, mock_db_manager, db_manager):
        """Test health check with unhealthy database."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        with (
            patch("src.api.health._get_system_info") as mock_system,
            patch("src.api.health._check_dependencies") as mock_deps,
        ):
            mock_system.return_value = {"cpu": {"cores": 8}}
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": True,
                "critical_available": True,
            }

            result = await health_check()

            assert result["status"] == "degraded"
            assert result["database"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_health_check_degraded_dependencies(
        self, mock_db_manager, db_manager
    ):
        """Test health check with missing critical dependencies."""
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={"database_size_mb": 10.5, "settings": {}, "table_counts": {}}
        )

        with (
            patch("src.api.health._get_system_info") as mock_system,
            patch("src.api.health._check_dependencies") as mock_deps,
        ):
            mock_system.return_value = {"cpu": {"cores": 8}}
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": False,
                "critical_available": False,
            }

            result = await health_check()

            assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_db_manager, db_manager):
        """Test health check with exception."""
        db_manager.execute_query = MagicMock(side_effect=Exception("Fatal error"))

        with patch("src.api.health._get_system_info") as mock_system:
            mock_system.side_effect = Exception("System error")

            with pytest.raises(HTTPException) as exc_info:
                await health_check()

            assert exc_info.value.status_code == 503


class TestDetailedHealthCheck:
    """Test detailed_health_check endpoint."""

    @pytest.mark.asyncio
    async def test_detailed_health_check_success(self, mock_db_manager, db_manager):
        """Test successful detailed health check."""
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={
                "database_size_mb": 10.5,
                "settings": {"schema_version": "1.0"},
                "table_counts": {"photos": 100},
            }
        )

        with (
            patch("src.api.health._get_system_info") as mock_system,
            patch("src.api.health._check_dependencies") as mock_deps,
            patch("src.api.health._get_uptime") as mock_uptime,
            patch("src.api.health._get_environment_info") as mock_env,
            patch("src.api.health._get_performance_metrics") as mock_perf,
        ):
            mock_system.return_value = {"cpu": {"cores": 8}}
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": True,
                "critical_available": True,
            }
            mock_uptime.return_value = {"system_uptime_hours": 24.0}
            mock_env.return_value = {"python_version": "3.12.0"}
            mock_perf.return_value = {"database_query_time_ms": 5.0}

            result = await detailed_health_check()

            assert result["status"] == "healthy"
            assert "diagnostics" in result
            assert "uptime" in result["diagnostics"]
            assert "environment" in result["diagnostics"]
            assert "performance" in result["diagnostics"]

    @pytest.mark.asyncio
    async def test_detailed_health_check_exception(self, mock_db_manager, db_manager):
        """Test detailed health check with exception."""
        db_manager.execute_query = MagicMock(side_effect=Exception("Fatal error"))

        with patch("src.api.health._get_system_info") as mock_system:
            mock_system.side_effect = Exception("System error")

            with pytest.raises(HTTPException) as exc_info:
                await detailed_health_check()

            assert exc_info.value.status_code == 503


class TestReadinessCheck:
    """Test readiness_check endpoint."""

    @pytest.mark.asyncio
    async def test_readiness_check_ready(self, mock_db_manager, db_manager):
        """Test readiness check when service is ready."""
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={"database_size_mb": 10.5, "settings": {}, "table_counts": {}}
        )

        with patch("src.api.health._check_dependencies") as mock_deps:
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": True,
                "critical_available": True,
            }

            result = await readiness_check()

            assert result["ready"] is True
            assert "timestamp" in result
            assert result["checks"]["database"] is True
            assert result["checks"]["critical_dependencies"] is True

    @pytest.mark.asyncio
    async def test_readiness_check_not_ready_database(
        self, mock_db_manager, db_manager
    ):
        """Test readiness check when database is not ready."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        with patch("src.api.health._check_dependencies") as mock_deps:
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": True,
                "critical_available": True,
            }

            result = await readiness_check()

            assert result["ready"] is False
            assert result["checks"]["database"] is False

    @pytest.mark.asyncio
    async def test_readiness_check_not_ready_dependencies(
        self, mock_db_manager, db_manager
    ):
        """Test readiness check when dependencies are not ready."""
        db_manager.execute_query = MagicMock(return_value=[[1]])
        db_manager.get_database_info = MagicMock(
            return_value={"database_size_mb": 10.5, "settings": {}, "table_counts": {}}
        )

        with patch("src.api.health._check_dependencies") as mock_deps:
            mock_deps.return_value = {
                "dependencies": {},
                "all_available": False,
                "critical_available": False,
            }

            result = await readiness_check()

            assert result["ready"] is False
            assert result["checks"]["critical_dependencies"] is False

    @pytest.mark.asyncio
    async def test_readiness_check_exception(self, mock_db_manager, db_manager):
        """Test readiness check with exception."""
        db_manager.execute_query = MagicMock(side_effect=Exception("Fatal error"))

        with patch("src.api.health._check_dependencies") as mock_deps:
            mock_deps.side_effect = Exception("Deps error")

            result = await readiness_check()

            assert result["ready"] is False
            assert "error" in result


class TestLivenessCheck:
    """Test liveness_check endpoint."""

    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """Test liveness check."""
        result = await liveness_check()

        assert result["alive"] is True
        assert "timestamp" in result
        assert result["service"] == "ideal-goggles-api"


class TestGetUptime:
    """Test _get_uptime function."""

    @patch("src.api.health.psutil")
    @patch("src.api.health.time")
    def test_get_uptime_success(self, mock_time, mock_psutil):
        """Test successful uptime retrieval."""
        mock_psutil.boot_time.return_value = 1000000.0
        mock_time.time.return_value = 1086400.0  # 24 hours later

        result = _get_uptime()

        assert "system_uptime_seconds" in result
        assert result["system_uptime_seconds"] == 86400
        assert "system_uptime_hours" in result
        assert result["system_uptime_hours"] == 24.0
        assert "boot_time" in result

    @patch("src.api.health.psutil")
    def test_get_uptime_error(self, mock_psutil):
        """Test uptime retrieval with error."""
        mock_psutil.boot_time.side_effect = Exception("Uptime error")

        result = _get_uptime()

        assert "error" in result


class TestGetEnvironmentInfo:
    """Test _get_environment_info function."""

    def test_get_environment_info(self):
        """Test environment info retrieval."""
        result = _get_environment_info()

        assert "python_version" in result
        assert "working_directory" in result
        assert "environment_variables" in result
        assert "PATH" in result["environment_variables"]


class TestGetPerformanceMetrics:
    """Test _get_performance_metrics function."""

    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, mock_db_manager, db_manager):
        """Test successful performance metrics retrieval."""
        db_manager.execute_query = MagicMock(return_value=[[100]])

        with patch("src.api.health.psutil") as mock_psutil:
            mock_memory = MagicMock()
            mock_memory.available = 8 * (1024**2)  # 8 MB
            mock_psutil.virtual_memory.return_value = mock_memory

            mock_disk_io = MagicMock()
            mock_disk_io.read_bytes = 1000000
            mock_disk_io.write_bytes = 500000
            mock_psutil.disk_io_counters.return_value = mock_disk_io

            result = await _get_performance_metrics()

            assert "database_query_time_ms" in result
            assert "memory_available_mb" in result
            assert "disk_io" in result

    @pytest.mark.asyncio
    async def test_get_performance_metrics_no_disk_io(
        self, mock_db_manager, db_manager
    ):
        """Test performance metrics when disk IO is not available."""
        db_manager.execute_query = MagicMock(return_value=[[100]])

        with patch("src.api.health.psutil") as mock_psutil:
            mock_memory = MagicMock()
            mock_memory.available = 8 * (1024**2)
            mock_psutil.virtual_memory.return_value = mock_memory
            mock_psutil.disk_io_counters.return_value = None

            result = await _get_performance_metrics()

            assert result["disk_io"]["read_bytes"] == 0
            assert result["disk_io"]["write_bytes"] == 0

    @pytest.mark.asyncio
    async def test_get_performance_metrics_error(self, mock_db_manager, db_manager):
        """Test performance metrics with error."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        result = await _get_performance_metrics()

        assert "error" in result
