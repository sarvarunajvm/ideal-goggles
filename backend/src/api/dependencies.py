"""Dependency status and management endpoints."""

import subprocess
import sys
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class DependencyStatus(BaseModel):
    """Status of a dependency."""

    name: str = Field(description="Dependency name")
    installed: bool = Field(description="Whether the dependency is installed")
    version: str | None = Field(description="Installed version if available")
    required: bool = Field(description="Whether this is a required dependency")
    description: str = Field(description="What this dependency enables")


class DependenciesResponse(BaseModel):
    """Response model for dependencies status."""

    core: list[DependencyStatus] = Field(description="Core dependencies")
    ml: list[DependencyStatus] = Field(description="ML dependencies")
    features: dict[str, bool] = Field(
        description="Feature availability based on dependencies"
    )


def _to_str_or_none(value: Any) -> str | None:
    """Coerce any version-like value to a string or None."""
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


def check_python_package(package_name: str) -> tuple[bool, str | None]:
    """Check if a Python package is installed and get its version.

    Robust to unexpected import errors and non-string version attributes.
    """
    try:
        import importlib

        module = importlib.import_module(package_name)
        # Many packages expose __version__, some use {pkg}.__version__ or version attributes
        version = getattr(module, "__version__", None)
        # Special cases where version may be exposed differently
        if version is None and package_name == "sqlite3":
            version = getattr(module, "version", None)
        return True, _to_str_or_none(version)
    except ImportError:
        return False, None
    except Exception:
        # Catch-all to prevent a single misbehaving import from breaking the endpoint
        logger.exception("Failed to check python package '%s'", package_name)
        return False, None


def check_system_command(command: str) -> tuple[bool, str | None]:
    """Check if a system command is available and get its version.

    Returns (installed, version) and never raises.
    """
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Extract version from output (usually first line)
            version_line = (result.stdout or result.stderr).split("\n")[0]
            # Try to extract version number
            import re

            version_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_line)
            version = (
                version_match.group(1)
                if version_match
                else version_line.strip() or "unknown"
            )
            return True, version
        return False, None
    except (subprocess.SubprocessError, FileNotFoundError):
        return False, None
    except Exception:
        logger.exception("Failed to check system command '%s'", command)
        return False, None


@router.get("/dependencies", response_model=DependenciesResponse)
async def get_dependencies_status() -> DependenciesResponse:
    """
    Get status of all dependencies.

    Returns:
        Status of core and ML dependencies, and feature availability
    """
    # Check core dependencies
    core_deps: list[DependencyStatus] = []

    # Python packages
    for package, description in [
        ("PIL", "Image processing and thumbnail generation"),
        ("sqlite3", "Database operations"),
        ("fastapi", "API framework"),
        ("pydantic", "Data validation"),
    ]:
        installed, version = check_python_package(package)
        core_deps.append(
            DependencyStatus(
                name=package,
                installed=installed,
                version=version,
                required=True,
                description=description,
            )
        )

    # Check ML dependencies
    ml_deps: list[DependencyStatus] = []

    # Tesseract OCR
    tesseract_installed, tesseract_version = check_system_command("tesseract")
    ml_deps.append(
        DependencyStatus(
            name="tesseract",
            installed=tesseract_installed,
            version=tesseract_version,
            required=False,
            description="OCR text extraction from images",
        )
    )

    # CLIP and PyTorch
    torch_installed, torch_version = check_python_package("torch")
    ml_deps.append(
        DependencyStatus(
            name="pytorch",
            installed=torch_installed,
            version=torch_version,
            required=False,
            description="Deep learning framework for ML models",
        )
    )

    clip_installed, clip_version = check_python_package("clip")
    ml_deps.append(
        DependencyStatus(
            name="clip",
            installed=clip_installed,
            version=clip_version,
            required=False,
            description="Semantic search with natural language",
        )
    )

    # InsightFace
    insightface_installed, insightface_version = check_python_package("insightface")
    ml_deps.append(
        DependencyStatus(
            name="insightface",
            installed=insightface_installed,
            version=insightface_version,
            required=False,
            description="Face detection and recognition",
        )
    )

    # OpenCV
    cv2_installed, cv2_version = check_python_package("cv2")
    ml_deps.append(
        DependencyStatus(
            name="opencv",
            installed=cv2_installed,
            version=cv2_version,
            required=False,
            description="Computer vision operations",
        )
    )

    # Determine feature availability
    features = {
        "basic_search": True,  # Always available
        "thumbnail_generation": any(d.name == "PIL" and d.installed for d in core_deps),
        "ocr_text_extraction": tesseract_installed,
        "semantic_search": clip_installed and torch_installed,
        "image_similarity": clip_installed and torch_installed,
        "face_detection": insightface_installed and cv2_installed,
        "face_recognition": insightface_installed and cv2_installed,
    }

    try:
        return DependenciesResponse(core=core_deps, ml=ml_deps, features=features)
    except Exception as e:
        # In case model validation fails unexpectedly, degrade gracefully instead of 500
        logger.exception("Failed to build DependenciesResponse: %s", e)
        # Return a minimal but valid response
        return DependenciesResponse(core=[], ml=[], features={"basic_search": True})


class InstallRequest(BaseModel):
    """Request model for dependency installation."""

    components: list[str] = Field(default=["all"], description="Components to install")


@router.post("/dependencies/install")
async def install_dependencies(request: InstallRequest) -> dict[str, Any]:
    """
    Install ML dependencies.

    Args:
        components: List of components to install (tesseract, clip, face, all)

    Returns:
        Installation status
    """
    try:
        import platform
        from pathlib import Path

        # First try to find the installer script (for development)
        script_path = (
            Path(__file__).parent.parent.parent
            / "scripts"
            / "install_ml_dependencies.py"
        )

        if script_path.exists():
            # Use the script if available (development mode)
            cmd = [sys.executable, str(script_path)]

            if "all" not in request.components:
                if "tesseract" not in request.components:
                    cmd.append("--skip-tesseract")
                if "clip" not in request.components:
                    cmd.append("--skip-clip")
                if "face" not in request.components:
                    cmd.append("--skip-face")

            logger.info(f"Running ML dependency installer script: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "Dependencies installed successfully",
                    "output": result.stdout,
                }
            return {
                "status": "partial",
                "message": "Some dependencies may have failed to install",
                "output": result.stdout,
                "errors": result.stderr,
            }
        # Fallback to direct pip installation (production mode)
        logger.info("Installer script not found, using direct pip installation")

        outputs = []
        errors = []
        components_to_install = (
            request.components
            if "all" not in request.components
            else ["tesseract", "clip", "face"]
        )

        # Install Tesseract (system package)
        if "tesseract" in components_to_install:
            if platform.system() == "Darwin":  # macOS
                # Check if brew is available
                brew_check = subprocess.run(
                    ["which", "brew"], check=False, capture_output=True
                )
                if brew_check.returncode == 0:
                    logger.info("Installing Tesseract via Homebrew")
                    result = subprocess.run(
                        ["brew", "install", "tesseract"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if result.returncode == 0:
                        outputs.append("Tesseract installed successfully")
                    else:
                        errors.append(f"Tesseract installation failed: {result.stderr}")
                else:
                    errors.append(
                        "Homebrew not found. Please install from https://brew.sh"
                    )
            elif platform.system() == "Linux":
                outputs.append(
                    "Please install Tesseract using: sudo apt-get install tesseract-ocr"
                )
            else:
                outputs.append("Please install Tesseract manually for your system")

        # Install Python packages
        packages = []

        if "clip" in components_to_install:
            # PyTorch and CLIP
            packages.extend(
                [
                    "torch",
                    "torchvision",
                    "torchaudio",
                    "ftfy",
                    "regex",
                    "tqdm",
                    "git+https://github.com/openai/CLIP.git",
                ]
            )

        if "face" in components_to_install:
            # InsightFace and OpenCV
            packages.extend(
                [
                    "opencv-python>=4.5.0",
                    "onnxruntime>=1.10.0",
                    "insightface>=0.7.0",
                    "numpy<2.0.0",  # InsightFace compatibility
                ]
            )

        if packages:
            logger.info(f"Installing Python packages: {packages}")
            # Use system Python3 instead of frozen executable
            python_cmd = "python3" if platform.system() != "Windows" else "python"
            for package in packages:
                result = subprocess.run(
                    [python_cmd, "-m", "pip", "install", "--user", package],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    outputs.append(f"Installed {package}")
                else:
                    errors.append(f"Failed to install {package}: {result.stderr}")

        # Determine overall status
        if errors:
            return {
                "status": "partial",
                "message": "Some dependencies failed to install",
                "output": "\n".join(outputs),
                "errors": "\n".join(errors),
            }
        return {
            "status": "success",
            "message": "Dependencies installed successfully",
            "output": "\n".join(outputs),
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Installation timed out. Please try again or install manually.",
        )
    except Exception as e:
        logger.exception(f"Failed to install dependencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Installation failed: {e!s}",
        )
