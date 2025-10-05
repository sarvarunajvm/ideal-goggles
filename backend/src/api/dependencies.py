"""Dependency status and management endpoints."""

import platform
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
    is_frozen: bool = Field(
        default=False,
        description="Whether running in production build (frozen executable)",
    )
    can_install: bool = Field(
        default=True,
        description="Whether dependencies can be installed in current environment",
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
    Works for both normal and frozen (PyInstaller) environments.
    """
    # In frozen executables, we need to check if the package was bundled
    if getattr(sys, "frozen", False):
        # For frozen executables, check if package can be imported
        # If it's not bundled, it won't be available even if installed in system
        try:
            import importlib

            module = importlib.import_module(package_name)
            version = getattr(module, "__version__", None)
            if version is None and package_name == "sqlite3":
                version = getattr(module, "version", None)
            return True, _to_str_or_none(version)
        except ImportError:
            # In production build, package is not bundled
            return False, None
        except Exception:
            logger.exception(
                "Failed to check python package '%s' in frozen env", package_name
            )
            return False, None
    else:
        # Development environment - normal import check
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


def verify_model_functionality(model_type: str) -> dict[str, Any]:
    """Verify that a model can actually be loaded and used.

    Returns dict with:
    - functional: bool - whether the model works
    - error: str | None - error message if not functional
    - details: dict - additional details (memory usage, model path, etc.)
    """
    import psutil

    result = {"functional": False, "error": None, "details": {}}

    # Check available memory first
    memory = psutil.virtual_memory()
    result["details"]["available_memory_gb"] = round(memory.available / (1024**3), 2)
    result["details"]["total_memory_gb"] = round(memory.total / (1024**3), 2)

    if model_type == "clip":
        try:
            import clip
            import torch

            # Check if CUDA is available
            result["details"]["cuda_available"] = torch.cuda.is_available()
            result["details"]["device"] = "cuda" if torch.cuda.is_available() else "cpu"

            # Try to load the model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-B/32", device=device, jit=False)

            # Test with a dummy tensor
            dummy_image = torch.randn(1, 3, 224, 224).to(device)
            with torch.no_grad():
                _ = model.encode_image(dummy_image)

            result["functional"] = True
            result["details"]["model_name"] = "ViT-B/32"
            result["details"]["model_loaded"] = True

            # Clean up
            del model, preprocess, dummy_image
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            result["error"] = str(e)
            result["details"]["error_type"] = type(e).__name__

    elif model_type == "face":
        try:
            from ..workers.face_worker import FaceDetectionWorker

            # Try to initialize the worker
            worker = FaceDetectionWorker()
            result["functional"] = worker.is_available()
            result["details"]["model_loaded"] = worker.is_available()

            if not result["functional"]:
                result["error"] = "Face detection model not available"

        except Exception as e:
            result["error"] = str(e)
            result["details"]["error_type"] = type(e).__name__

    return result


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
        "semantic_search": clip_installed and torch_installed,
        "image_similarity": clip_installed and torch_installed,
        "face_detection": insightface_installed and cv2_installed,
        "face_recognition": insightface_installed and cv2_installed,
        "text_recognition": False,  # OCR/Tesseract was removed from the system
    }

    # Check if running in frozen environment
    is_frozen = getattr(sys, "frozen", False)
    can_install = not is_frozen  # Can only install in development environment

    try:
        return DependenciesResponse(
            core=core_deps,
            ml=ml_deps,
            features=features,
            is_frozen=is_frozen,
            can_install=can_install,
        )
    except Exception as e:
        # In case model validation fails unexpectedly, degrade gracefully instead of 500
        logger.exception("Failed to build DependenciesResponse: %s", e)
        # Return a minimal but valid response
        return DependenciesResponse(
            core=[],
            ml=[],
            features={"basic_search": True},
            is_frozen=is_frozen,
            can_install=can_install,
        )


@router.get("/dependencies/verify")
async def verify_dependencies() -> dict[str, Any]:
    """
    Verify that dependencies are not just installed but actually functional.

    Returns detailed information about each model's status including:
    - Whether it can be loaded
    - Memory requirements
    - Actual errors if any
    """
    verification_results = {
        "summary": {"all_functional": True, "issues_found": []},
        "models": {},
        "system": {},
    }

    # Get system information
    import psutil

    memory = psutil.virtual_memory()
    verification_results["system"] = {
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent,
        },
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system(),
        "architecture": platform.machine(),
    }

    # Verify each model
    for model_type in ["clip", "face"]:
        result = verify_model_functionality(model_type)
        verification_results["models"][model_type] = result

        if not result["functional"]:
            verification_results["summary"]["all_functional"] = False
            verification_results["summary"]["issues_found"].append(
                {"model": model_type, "error": result["error"]}
            )

    # Add recommendations based on issues
    recommendations = []
    if verification_results["system"]["memory"]["available_gb"] < 2:
        recommendations.append(
            "Low memory available. Close other applications to free up memory."
        )

    for issue in verification_results["summary"]["issues_found"]:
        error_str = str(issue.get("error", "")).lower()
        model = issue["model"]

        if "cuda" in error_str:
            recommendations.append(
                f"{model}: CUDA error detected. Model will use CPU instead."
            )
        elif "import" in error_str or "module" in error_str or "not found" in error_str:
            if model == "clip":
                recommendations.append(
                    f"{model}: CLIP model not installed. Run: pip install torch torchvision ftfy regex git+https://github.com/openai/CLIP.git"
                )
            elif model == "face":
                recommendations.append(
                    f"{model}: Face detection not installed. Run: pip install insightface opencv-python onnxruntime"
                )
            else:
                recommendations.append(
                    f"{model}: Model not installed. Run dependency installation."
                )
        elif "memory" in error_str:
            recommendations.append(
                f"{model}: Insufficient memory. Consider using a smaller model or closing other applications."
            )
        else:
            recommendations.append(
                f"{model}: Check error details and ensure all dependencies are properly installed."
            )

    verification_results["recommendations"] = recommendations

    return verification_results


class InstallRequest(BaseModel):
    """Request model for dependency installation."""

    components: list[str] = Field(
        default=["all"], description="Components to install (clip, face, all)"
    )


@router.post("/dependencies/install")
async def install_dependencies(request: InstallRequest) -> dict[str, Any]:
    """
    Install ML dependencies.

    Args:
        components: List of components to install (clip, face, all)

    Returns:
        Installation status
    """
    try:
        import platform
        from pathlib import Path

        # Check if running in frozen executable (production build)
        is_frozen = getattr(sys, "frozen", False)

        if is_frozen:
            # In production builds, ML dependencies cannot be installed dynamically
            # They must be bundled at build time
            logger.warning("Attempted to install dependencies in frozen executable")
            return {
                "status": "unavailable",
                "message": "ML dependencies cannot be installed in the packaged application.",
                "output": "ML features must be enabled during the build process. "
                "Please use the development version to install ML dependencies, "
                "or rebuild the application with ML dependencies included.",
                "errors": "Dynamic dependency installation is not supported in production builds.",
            }

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
                # Always skip tesseract since we're removing OCR
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
        # Fallback to direct pip installation (development mode without script)
        logger.info("Installer script not found, using direct pip installation")

        outputs = []
        errors = []
        components_to_install = (
            request.components if "all" not in request.components else ["clip", "face"]
        )

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
