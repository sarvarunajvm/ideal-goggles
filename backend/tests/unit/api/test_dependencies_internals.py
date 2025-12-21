"""Unit tests for internal dependencies logic."""

import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.dependencies import (
    _CACHE_TTL,
    _DEPENDENCY_CACHE,
    InstallRequest,
    _to_str_or_none,
    check_python_package,
    check_system_command,
    install_dependencies,
    verify_model_functionality,
)


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

class TestCheckPythonPackage:
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


class TestVerifyModelFunctionality:
    """Test verify_model_functionality."""

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


class TestCheckSystemCommand:
    """Test check_system_command."""

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


class TestInstallDependencies:
    """Test install_dependencies."""

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

