"""Unit tests for API dependencies module."""

import subprocess
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    DependencyStatus,
    check_python_package,
    check_system_command,
    router,
)
from src.main import app

client = TestClient(app)


class TestCheckPythonPackage:
    """Test check_python_package function."""

    @patch("importlib.import_module")
    def test_check_installed_package_with_version(self, mock_import):
        """Test checking an installed package with __version__."""
        mock_module = Mock()
        mock_module.__version__ = "1.2.3"
        mock_import.return_value = mock_module

        installed, version = check_python_package("test_package")
        assert installed is True
        assert version == "1.2.3"

    @patch("importlib.import_module")
    def test_check_installed_package_no_version(self, mock_import):
        """Test checking an installed package without version info."""
        mock_module = Mock(spec=[])  # No __version__ attribute
        mock_import.return_value = mock_module

        installed, version = check_python_package("test_package")
        assert installed is True
        assert version is None

    @patch("importlib.import_module")
    def test_check_sqlite3_special_case(self, mock_import):
        """Test special case for sqlite3 version attribute."""
        mock_module = Mock(spec=["version"])
        mock_module.version = "2.6.0"
        mock_import.return_value = mock_module

        installed, version = check_python_package("sqlite3")
        assert installed is True
        assert version == "2.6.0"

    @patch("importlib.import_module")
    def test_check_package_not_installed(self, mock_import):
        """Test checking a package that is not installed."""
        mock_import.side_effect = ImportError("No module named 'test_package'")

        installed, version = check_python_package("test_package")
        assert installed is False
        assert version is None

    @patch("importlib.import_module")
    def test_check_package_import_error(self, mock_import):
        """Test handling of unexpected import errors."""
        mock_import.side_effect = Exception("Unexpected error")

        installed, version = check_python_package("test_package")
        assert installed is False
        assert version is None

    @patch("importlib.import_module")
    def test_check_package_non_string_version(self, mock_import):
        """Test handling of non-string version attributes."""
        mock_module = Mock()
        mock_module.__version__ = 123  # Non-string version

        mock_import.return_value = mock_module

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
        # OCR text extraction should be disabled if tesseract is missing
        assert data["features"]["ocr_text_extraction"] is False

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
