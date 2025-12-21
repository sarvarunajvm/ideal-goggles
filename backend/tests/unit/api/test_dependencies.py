"""Unit tests for API dependencies module."""

import subprocess
import sys
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    _CACHE_TTL,
    _DEPENDENCY_CACHE,
    DependencyStatus,
    InstallRequest,
    _to_str_or_none,
    check_python_package,
    check_system_command,
    install_dependencies,
    router,
    verify_model_functionality,
)
from src.main import app

client = TestClient(app)


class TestCheckPythonPackage:
    """Test check_python_package function."""

    def setup_method(self):
        """Clear dependency cache before each test."""
        _DEPENDENCY_CACHE.clear()

    def test_check_installed_package_with_version(self):
        """Test checking an installed package with __version__."""
        import importlib

        mock_module = Mock()
        mock_module.__version__ = "1.2.3"

        with patch.object(importlib, "import_module", return_value=mock_module):
            installed, version = check_python_package("test_package")
            assert installed is True
            assert version == "1.2.3"

    def test_check_installed_package_no_version(self):
        """Test checking an installed package without version info."""
        import importlib

        mock_module = Mock(spec=[])  # No __version__ attribute

        with patch.object(importlib, "import_module", return_value=mock_module):
            installed, version = check_python_package("test_package")
            assert installed is True
            assert version is None

    def test_check_sqlite3_special_case(self):
        """Test special case for sqlite3 version attribute."""
        import importlib

        mock_module = Mock(spec=["version"])
        mock_module.version = "2.6.0"

        with patch.object(importlib, "import_module", return_value=mock_module):
            installed, version = check_python_package("sqlite3")
            assert installed is True
            assert version == "2.6.0"

    def test_check_package_not_installed(self):
        """Test checking a package that is not installed."""
        import importlib

        with patch.object(
            importlib,
            "import_module",
            side_effect=ImportError("No module named 'test_package'"),
        ):
            installed, version = check_python_package("test_package")
            assert installed is False
            assert version is None

    def test_check_package_import_error(self):
        """Test handling of unexpected import errors."""
        import importlib

        with patch.object(
            importlib, "import_module", side_effect=Exception("Unexpected error")
        ):
            installed, version = check_python_package("test_package")
            assert installed is False
            assert version is None

    def test_check_package_non_string_version(self):
        """Test handling of non-string version attributes."""
        import importlib

        mock_module = Mock()
        mock_module.__version__ = 123  # Non-string version

        with patch.object(importlib, "import_module", return_value=mock_module):
            installed, version = check_python_package("test_package")
            assert installed is True
            assert version == "123"


class TestCheckSystemCommand:
    """Test check_system_command function."""

    @patch("subprocess.run")
    def test_check_command_available_with_version(self, mock_run):
        """Test checking an available system command with version."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_run.return_value = mock_result

        installed, version = check_system_command("git")
        assert installed is True
        assert "2.34.1" in version

    @patch("subprocess.run")
    def test_check_command_not_available(self, mock_run):
        """Test checking a command that is not available."""
        mock_run.side_effect = FileNotFoundError()

        installed, version = check_system_command("nonexistent")
        assert installed is False
        assert version is None

    @patch("subprocess.run")
    def test_check_command_fails(self, mock_run):
        """Test handling command that returns non-zero exit code."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        installed, version = check_system_command("failing_command")
        assert installed is False
        assert version is None

    @patch("subprocess.run")
    def test_check_command_timeout(self, mock_run):
        """Test handling command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("command", 5)

        installed, version = check_system_command("slow_command")
        assert installed is False
        assert version is None

    @patch("subprocess.run")
    def test_check_command_unexpected_error(self, mock_run):
        """Test handling unexpected errors."""
        mock_run.side_effect = Exception("Unexpected error")

        installed, version = check_system_command("error_command")
        assert installed is False
        assert version is None


class TestDependenciesAPI:
    """Test dependencies API endpoints."""

    @patch("src.api.dependencies.check_python_package")
    @patch("src.api.dependencies.check_system_command")
    def test_get_dependencies_all_installed(self, mock_system, mock_python):
        """Test getting dependencies when all are installed."""
        # Mock all checks to return installed
        mock_python.return_value = (True, "1.0.0")
        mock_system.return_value = (True, "2.0.0")

        response = client.get("/dependencies")
        assert response.status_code == 200

        data = response.json()
        assert "core" in data
        assert "ml" in data
        assert "features" in data

        # Check that some core dependencies are listed
        core_names = [dep["name"] for dep in data["core"]]
        assert any("PIL" in name or "pillow" in name for name in core_names)

    @patch("src.api.dependencies.check_python_package")
    @patch("src.api.dependencies.check_system_command")
    def test_get_dependencies_some_missing(self, mock_system, mock_python):
        """Test getting dependencies when some are missing."""

        def python_side_effect(package):
            if package in ["torch", "transformers"]:
                return (False, None)
            return (True, "1.0.0")

        mock_python.side_effect = python_side_effect
        mock_system.return_value = (True, "2.0.0")

        response = client.get("/dependencies")
        assert response.status_code == 200

        data = response.json()
        # Semantic search and image similarity should be disabled if torch is missing
        assert data["features"]["semantic_search"] is False
        assert data["features"]["image_similarity"] is False

    @patch("src.api.dependencies.check_python_package")
    @patch("src.api.dependencies.check_system_command")
    def test_get_dependencies_tesseract_missing(self, mock_system, mock_python):
        """Test dependencies when tesseract is missing."""
        mock_python.return_value = (True, "1.0.0")

        def system_side_effect(command):
            if command == "tesseract":
                return (False, None)
            return (True, "2.0.0")

        mock_system.side_effect = system_side_effect

        response = client.get("/dependencies")
        assert response.status_code == 200

        data = response.json()
        # Text recognition should be disabled (OCR/Tesseract was removed from the system)
        assert data["features"]["text_recognition"] is False

    def test_dependency_status_model(self):
        """Test DependencyStatus model."""
        dep = DependencyStatus(
            name="test",
            installed=True,
            version="1.0.0",
            required=True,
            description="Test dependency",
        )
        assert dep.name == "test"
        assert dep.installed is True
        assert dep.version == "1.0.0"
        assert dep.required is True
        assert dep.description == "Test dependency"

    def test_dependency_status_optional(self):
        """Test DependencyStatus with optional fields."""
        dep = DependencyStatus(
            name="optional",
            installed=False,
            version=None,
            required=False,
            description="Optional dependency",
        )
        assert dep.name == "optional"
        assert dep.installed is False
        assert dep.version is None
        assert dep.required is False


class TestInstallDependencies:
    """Test install dependencies endpoint."""

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_install_dependency_success(self, mock_exists, mock_run):
        """Test successful dependency installation."""
        # Mock the script path to not exist, forcing fallback to pip
        mock_exists.return_value = False
        mock_run.return_value = Mock(
            returncode=0, stdout="Successfully installed package"
        )

        response = client.post(
            "/dependencies/install", json={"components": ["tesseract"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "partial"]

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_install_dependency_failure(self, mock_exists, mock_run):
        """Test failed dependency installation."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(
            returncode=1, stderr="Error installing package", stdout=""
        )

        response = client.post("/dependencies/install", json={"components": ["clip"]})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial"
        assert "errors" in data or "output" in data

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_install_dependency_timeout(self, mock_exists, mock_run):
        """Test installation timeout."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("pip", 300)

        response = client.post("/dependencies/install", json={"components": ["clip"]})
        assert response.status_code == 504
        detail_lower = response.json()["detail"].lower()
        assert "timed out" in detail_lower or "timeout" in detail_lower

    def test_install_dependency_invalid_package_name(self):
        """Test installation with valid components (no longer validates individual package names)."""
        # The new API accepts components, not individual package names
        # So this test now checks that valid components work
        response = client.post("/dependencies/install", json={"components": ["all"]})
        # Should succeed or fail based on actual installation, not reject the request
        assert response.status_code in [200, 504]

    def test_install_dependency_empty_package_name(self):
        """Test installation with empty components defaults to 'all'."""
        # Empty components should default to ["all"]
        response = client.post("/dependencies/install", json={})
        # Should process with default components
        assert response.status_code in [200, 504]


class TestVerifyDependencies:
    """Test dependency verification."""

    @patch("src.api.dependencies.verify_model_functionality")
    def test_verify_dependencies_success(self, mock_verify):
        """Test verifying dependencies when everything is functional."""
        mock_verify.return_value = {
            "functional": True,
            "error": None,
            "details": {"model_loaded": True},
        }

        with patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value = Mock(
                total=16 * 1024**3, available=8 * 1024**3, percent=50.0
            )

            response = client.get("/dependencies/verify")
            assert response.status_code == 200
            data = response.json()

            assert data["summary"]["all_functional"] is True
            assert len(data["summary"]["issues_found"]) == 0
            assert "clip" in data["models"]
            assert "face" in data["models"]
            assert data["system"]["memory"]["total_gb"] == 16.0

    @patch("src.api.dependencies.verify_model_functionality")
    def test_verify_dependencies_failure(self, mock_verify):
        """Test verifying dependencies when some models fail."""
        # CLIP works, Face fails
        def side_effect(model_type):
            if model_type == "clip":
                return {"functional": True, "error": None, "details": {}}
            return {"functional": False, "error": "Model not found", "details": {}}

        mock_verify.side_effect = side_effect

        with patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value = Mock(
                total=16 * 1024**3, available=8 * 1024**3, percent=50.0
            )

            response = client.get("/dependencies/verify")
            assert response.status_code == 200
            data = response.json()

            assert data["summary"]["all_functional"] is False
            assert len(data["summary"]["issues_found"]) > 0
            assert data["summary"]["issues_found"][0]["model"] == "face"

    @patch("src.api.dependencies.verify_model_functionality")
    def test_verify_dependencies_low_memory(self, mock_verify):
        """Test verifying dependencies with low memory."""
        mock_verify.return_value = {"functional": True, "error": None, "details": {}}

        with patch("psutil.virtual_memory") as mock_memory:
            # Low available memory (1GB)
            mock_memory.return_value = Mock(
                total=8 * 1024**3, available=1 * 1024**3, percent=90.0
            )

            response = client.get("/dependencies/verify")
            assert response.status_code == 200
            data = response.json()

            # Should include recommendations
            recommendations = data["recommendations"]
            assert any("Low memory" in r for r in recommendations)


class TestVerifyModelFunctionality:
    """Test verify_model_functionality function."""

    def test_verify_clip_model_success(self):
        """Test verifying CLIP model successfully."""
        from src.api.dependencies import verify_model_functionality

        mock_clip = Mock()
        mock_clip.load.return_value = (Mock(), Mock())

        # Use MagicMock to handle context managers (__enter__/__exit__)
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        # Ensure chain calls return MagicMocks too
        mock_torch.randn.return_value.to.return_value = MagicMock()

        with patch.dict("sys.modules", {"clip": mock_clip, "torch": mock_torch}):
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value = Mock(total=100, available=50)

                result = verify_model_functionality("clip")

                assert result["functional"] is True
                assert result["details"]["model_name"] == "ViT-B/32"

    def test_verify_clip_model_failure(self):
        """Test verifying CLIP model failure."""
        from src.api.dependencies import verify_model_functionality

        # Mock clip module raising exception
        mock_clip = Mock()
        mock_clip.load.side_effect = Exception("Model load failed")

        with patch.dict("sys.modules", {"clip": mock_clip, "torch": Mock()}):
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value = Mock(total=100, available=50)

                result = verify_model_functionality("clip")
                assert result["functional"] is False
                assert "Model load failed" in result["error"]

    def test_verify_face_model_success(self):
        """Test verifying Face model successfully."""
        from src.api.dependencies import verify_model_functionality

        with patch("src.workers.face_worker.FaceDetectionWorker") as mock_worker:
            mock_worker.return_value.is_available.return_value = True

            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value = Mock(total=100, available=50)

                result = verify_model_functionality("face")
                assert result["functional"] is True

    def test_verify_face_model_failure(self):
        """Test verifying Face model failure."""
        from src.api.dependencies import verify_model_functionality

        with patch("src.workers.face_worker.FaceDetectionWorker") as mock_worker:
            mock_worker.return_value.is_available.return_value = False

            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value = Mock(total=100, available=50)

                result = verify_model_functionality("face")
                assert result["functional"] is False
                assert "not available" in result["error"]



# === Merged from test_dependencies_internals.py ===


class TestDependencyHelpers:
    """Test helper functions."""

    def test_to_str_or_none(self):
        assert _to_str_or_none("1.0.0") == "1.0.0"
        assert _to_str_or_none(None) is None
        assert _to_str_or_none(123) == "123"

        # Test exception
        mock_obj = MagicMock()
        mock_obj.__str__.side_effect = Exception("error")
        assert _to_str_or_none(mock_obj) is None


class TestCheckPythonPackageCaching:
    """Test check_python_package function."""

    def setup_method(self):
        _DEPENDENCY_CACHE.clear()

    @patch("importlib.import_module")
    def test_check_package_installed(self, mock_import):
        """Test checking installed package."""
        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_import.return_value = mock_module

        installed, version = check_python_package("testpkg")
        assert installed is True
        assert version == "1.0.0"
        assert "testpkg" in _DEPENDENCY_CACHE

    @patch("importlib.import_module")
    def test_check_package_cached(self, mock_import):
        """Test cache usage."""
        _DEPENDENCY_CACHE["testpkg"] = (True, "1.0.0", time.time())

        installed, version = check_python_package("testpkg")
        assert installed is True
        assert version == "1.0.0"
        mock_import.assert_not_called()

    @patch("importlib.import_module")
    def test_check_package_expired_cache(self, mock_import):
        """Test expired cache."""
        _DEPENDENCY_CACHE["testpkg"] = (True, "0.9.0", time.time() - _CACHE_TTL - 1)

        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_import.return_value = mock_module

        installed, version = check_python_package("testpkg")
        assert installed is True
        assert version == "1.0.0"
        mock_import.assert_called_once()

    @patch("importlib.import_module")
    def test_check_package_import_error(self, mock_import):
        """Test import error."""
        mock_import.side_effect = ImportError("Not found")

        installed, version = check_python_package("testpkg")
        assert installed is False
        assert version is None

    @patch("importlib.import_module")
    def test_check_package_timeout(self, mock_import):
        """Test timeout."""
        mock_import.side_effect = TimeoutError("Timed out")

        installed, version = check_python_package("testpkg")
        assert installed is False
        assert version is None

    @patch("importlib.import_module")
    def test_check_package_exception(self, mock_import):
        """Test generic exception."""
        mock_import.side_effect = Exception("Boom")

        installed, version = check_python_package("testpkg")
        assert installed is False
        assert version is None

    @patch("src.api.dependencies.sys")
    @patch("importlib.import_module")
    def test_check_package_frozen(self, mock_import, mock_sys):
        """Test checking in frozen environment."""
        mock_sys.frozen = True

        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_import.return_value = mock_module

        installed, version = check_python_package("testpkg")
        assert installed is True
        assert version == "1.0.0"

    @patch("src.api.dependencies.sys")
    @patch("importlib.import_module")
    def test_check_package_frozen_import_error(self, mock_import, mock_sys):
        """Test frozen environment import error."""
        mock_sys.frozen = True
        mock_import.side_effect = ImportError("Not bundled")

        installed, version = check_python_package("testpkg")
        assert installed is False
        assert version is None


class TestVerifyModelFunctionalityInternal:
    """Test verify_model_functionality internal logic."""

    def test_verify_clip_success(self):
        """Test successful CLIP verification."""
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.available = 4 * 1024**3
        mock_psutil.virtual_memory.return_value.total = 8 * 1024**3

        mock_clip = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_model = MagicMock()
        mock_clip.load.return_value = (mock_model, MagicMock())

        with patch.dict(sys.modules, {"psutil": mock_psutil, "clip": mock_clip, "torch": mock_torch}):
            result = verify_model_functionality("clip")
            assert result["functional"] is True
            assert result["details"]["model_loaded"] is True

    def test_verify_clip_failure(self):
        """Test CLIP failure."""
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.available = 4 * 1024**3

        mock_clip = MagicMock()
        mock_clip.load.side_effect = Exception("Load failed")

        with patch.dict(sys.modules, {"psutil": mock_psutil, "clip": mock_clip, "torch": MagicMock()}):
            result = verify_model_functionality("clip")
            assert result["functional"] is False
            assert "Load failed" in result["error"]

    def test_verify_face_success(self):
        """Test successful face verification."""
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.available = 4 * 1024**3

        with patch.dict(sys.modules, {"psutil": mock_psutil}):
            with patch("src.workers.face_worker.FaceDetectionWorker") as mock_worker:
                mock_worker.return_value.is_available.return_value = True

                result = verify_model_functionality("face")
                assert result["functional"] is True

    def test_verify_face_failure(self):
        """Test face verification failure."""
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.available = 4 * 1024**3

        with patch.dict(sys.modules, {"psutil": mock_psutil}):
            with patch("src.workers.face_worker.FaceDetectionWorker") as mock_worker:
                mock_worker.return_value.is_available.return_value = False

                result = verify_model_functionality("face")
                assert result["functional"] is False
                assert "not available" in result["error"]


class TestCheckSystemCommandInternal:
    """Test check_system_command internal logic."""

    @patch("subprocess.run")
    def test_check_command_success(self, mock_run):
        """Test successful command check."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "tool version 1.2.3"

        installed, version = check_system_command("tool")
        assert installed is True
        assert version == "1.2.3"

    @patch("subprocess.run")
    def test_check_command_failure(self, mock_run):
        """Test command failure."""
        mock_run.side_effect = FileNotFoundError()

        installed, version = check_system_command("tool")
        assert installed is False
        assert version is None


class TestInstallDependenciesInternal:
    """Test install_dependencies internal logic."""

    @patch("src.api.dependencies.sys")
    async def test_install_frozen(self, mock_sys):
        """Test install in frozen environment."""
        mock_sys.frozen = True
        request = InstallRequest(components=["all"])

        result = await install_dependencies(request)
        assert result["status"] == "unavailable"

    @patch("src.api.dependencies.sys")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    async def test_install_script_success(self, mock_exists, mock_run, mock_sys):
        """Test install via script."""
        mock_sys.frozen = False
        mock_sys.executable = "/usr/bin/python" # Must be a string
        mock_exists.return_value = True # Script exists

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"

        request = InstallRequest(components=["all"])
        result = await install_dependencies(request)
        assert result["status"] == "success"

    @patch("src.api.dependencies.sys")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    async def test_install_fallback_success(self, mock_exists, mock_run, mock_sys):
        """Test install fallback to pip."""
        mock_sys.frozen = False
        mock_sys.executable = "/usr/bin/python"
        mock_exists.return_value = False # Script does not exist

        mock_run.return_value.returncode = 0

        request = InstallRequest(components=["all"])
        result = await install_dependencies(request)
        assert result["status"] == "success"

    @patch("src.api.dependencies.sys")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    async def test_install_fallback_failure(self, mock_exists, mock_run, mock_sys):
        """Test install fallback failure."""
        mock_sys.frozen = False
        mock_sys.executable = "/usr/bin/python"
        mock_exists.return_value = False

        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error"

        request = InstallRequest(components=["clip"])
        result = await install_dependencies(request)
        assert result["status"] == "partial"

