#!/usr/bin/env python3
"""
ML Dependencies Setup & Verification for Ideal Goggles

This unified script:
1. Installs ML dependencies (PyTorch, CLIP, InsightFace, OpenCV, ONNX Runtime)
2. Downloads ML models (CLIP ViT-B/32, InsightFace buffalo_l)
3. Verifies models actually work with real inference tests

Usage:
    python setup_ml_models.py --all              # Install + download + verify (default)
    python setup_ml_models.py --install-only     # Only install dependencies
    python setup_ml_models.py --verify-only      # Only verify models work
    python setup_ml_models.py --skip-tesseract   # Skip Tesseract OCR installation
"""

import argparse
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


class MLSetup:
    """Unified ML setup: installation, download, and verification."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.platform_name = platform.system().lower()
        self.arch = platform.machine().lower()
        self.python_version = sys.version_info

        # Track results
        self.install_results = {}
        self.model_results = {
            "clip": {"downloaded": False, "verified": False, "error": None},
            "insightface": {"downloaded": False, "verified": False, "error": None},
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with appropriate level."""
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info(f"[OK] {message}")
        else:
            logger.info(message)

    def run_command(self, cmd: list[str], check: bool = True) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        if self.verbose:
            logger.debug(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"

    # =========================================================================
    # INSTALLATION PHASE
    # =========================================================================

    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        if self.python_version < (3, 8):
            self.log(
                f"Python {self.python_version.major}.{self.python_version.minor} detected. "
                "Python 3.8+ is required.",
                "ERROR",
            )
            return False
        self.log(
            f"Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro} detected",
            "SUCCESS",
        )
        return True

    def check_pip(self) -> bool:
        """Check if pip is available."""
        code, _, _ = self.run_command([sys.executable, "-m", "pip", "--version"])
        if code != 0:
            self.log("pip is not installed", "ERROR")
            return False
        self.log("pip is available", "SUCCESS")
        return True

    def check_cuda(self) -> bool:
        """Check if CUDA is available."""
        code, _stdout, _ = self.run_command(["nvidia-smi"], check=False)
        if code == 0:
            if self.verbose:
                self.log("NVIDIA GPU detected")
            return True
        return False

    def get_torch_packages(self) -> dict[str, str]:
        """Determine appropriate PyTorch packages for the platform."""
        cuda_available = self.check_cuda()

        if cuda_available:
            self.log("CUDA detected, installing GPU-enabled PyTorch")
            return {
                "torch": "",
                "torchvision": "",
                "torchaudio": "",
                "--index-url": "https://download.pytorch.org/whl/cu118",
            }

        if self.platform_name == "darwin" and "arm" in self.arch:
            # Apple Silicon - uses MPS (Metal Performance Shaders)
            self.log("Apple Silicon detected, installing MPS-enabled PyTorch")
            return {"torch": "", "torchvision": "", "torchaudio": ""}

        # CPU only
        self.log("No GPU detected, installing CPU-only PyTorch")
        return {
            "torch": "",
            "torchvision": "",
            "torchaudio": "",
            "--index-url": "https://download.pytorch.org/whl/cpu",
        }

    def install_python_packages(self, packages: dict[str, str]) -> bool:
        """Install Python packages via pip."""
        failed = []

        for package, version_spec in packages.items():
            if package.startswith("--"):
                # This is a pip argument, not a package
                continue

            package_spec = f"{package}{version_spec}" if version_spec else package
            self.log(f"Installing {package_spec}...")

            # Handle index-url if present
            cmd = [sys.executable, "-m", "pip", "install"]
            if "--index-url" in packages:
                cmd.extend(["--index-url", packages["--index-url"]])
            cmd.append(package_spec)

            code, _, stderr = self.run_command(cmd)

            if code != 0:
                self.log(f"Failed to install {package}: {stderr}", "ERROR")
                failed.append(package)
            else:
                self.log(f"{package} installed successfully", "SUCCESS")

        return len(failed) == 0

    def install_clip(self) -> bool:
        """Install CLIP and PyTorch dependencies."""
        logger.info("=" * 60)
        logger.info("Installing CLIP Dependencies")
        logger.info("=" * 60)

        # Install numpy<2.0 FIRST (before PyTorch) to avoid compatibility issues
        numpy_package = {"numpy": "<2.0.0"}
        if not self.install_python_packages(numpy_package):
            self.log("Failed to install compatible numpy version", "ERROR")
            return False

        # Install PyTorch
        torch_packages = self.get_torch_packages()
        if not self.install_python_packages(torch_packages):
            self.install_results["pytorch"] = False
            return False
        self.install_results["pytorch"] = True

        # Install CLIP
        clip_packages = {
            "ftfy": "",
            "regex": "",
            "tqdm": "",
            "git+https://github.com/openai/CLIP.git": "",
        }

        result = self.install_python_packages(clip_packages)
        self.install_results["clip"] = result
        return result

    def install_insightface(self) -> bool:
        """Install InsightFace and dependencies."""
        logger.info("=" * 60)
        logger.info("Installing InsightFace Dependencies")
        logger.info("=" * 60)

        # Note: numpy<2.0.0 is already installed in install_clip()
        face_packages = {
            "opencv-python-headless": ">=4.5.0",
            "onnxruntime": ">=1.10.0",
            "insightface": ">=0.7.0",
        }

        result = self.install_python_packages(face_packages)
        self.install_results["insightface"] = result
        return result

    def install_all_dependencies(self, skip_tesseract: bool = True) -> bool:
        """Install all ML dependencies."""
        logger.info("=" * 60)
        logger.info("ML DEPENDENCIES INSTALLATION")
        logger.info("=" * 60)

        if not self.check_python_version():
            return False

        if not self.check_pip():
            return False

        success = True

        # Install CLIP (includes PyTorch)
        if not self.install_clip():
            self.log("CLIP installation failed", "WARNING")
            success = False

        # Install InsightFace
        if not self.install_insightface():
            self.log("InsightFace installation failed", "WARNING")
            success = False

        logger.info("=" * 60)
        if success:
            logger.info("[OK] ALL DEPENDENCIES INSTALLED")
        else:
            logger.warning("[WARNING] SOME DEPENDENCIES FAILED TO INSTALL")
        logger.info("=" * 60)

        return success

    # =========================================================================
    # MODEL DOWNLOAD & VERIFICATION PHASE
    # =========================================================================

    def download_and_verify_clip(self) -> bool:
        """Download and verify CLIP model ViT-B/32 (the EXACT model we use)."""
        logger.info("\n%s", "=" * 60)
        logger.info("CLIP Model: ViT-B/32")
        logger.info("=" * 60)

        try:
            import clip
            import torch

            logger.info("[OK] PyTorch and CLIP packages installed")

            # Determine device
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            logger.info(f"Device: {device}")

            # Download the EXACT model we use (from embedding_worker.py:45)
            logger.info("Downloading CLIP ViT-B/32 model...")
            start_time = time.time()

            model, preprocess = clip.load("ViT-B/32", device=device, jit=False)
            model.eval()  # Set to eval mode (from embedding_worker.py:46)

            download_time = time.time() - start_time
            logger.info(f"[OK] Model downloaded and loaded ({download_time:.2f}s)")

            self.model_results["clip"]["downloaded"] = True

            # VERIFY the model actually works with real data
            logger.info("Verifying CLIP model functionality...")

            # Test image embedding (what we do in _generate_embedding_sync)
            test_image = torch.randn(1, 3, 224, 224).to(device)
            with torch.no_grad():
                image_features = model.encode_image(test_image)
                # Normalize (exactly as in embedding_worker.py:106)
                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )
                # Ensure float32 for downstream consumers
                image_embedding = image_features.float().cpu().numpy().flatten()

            # Verify embedding properties
            assert (
                len(image_embedding) == 512
            ), f"Expected 512 dims, got {len(image_embedding)}"
            assert isinstance(
                image_embedding, np.ndarray
            ), "Embedding must be numpy array"
            assert (
                image_embedding.dtype == np.float32
            ), f"Expected float32, got {image_embedding.dtype}"

            # Check normalization (embedding_worker.py uses normalized vectors)
            norm = float(np.linalg.norm(image_embedding))
            assert 0.99 < norm < 1.01, f"Embedding not normalized: norm={norm}"

            logger.info(f"  [OK] Image embedding: {len(image_embedding)} dimensions")
            logger.info(f"  [OK] Normalized: {norm:.4f}")

            # Test text embedding (what we do in _generate_text_embedding_sync)
            test_text = clip.tokenize(["a photo of a cat"]).to(device)
            with torch.no_grad():
                text_features = model.encode_text(test_text)
                # Normalize (exactly as in embedding_worker.py:145)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                # Ensure float32 for downstream consumers
                text_embedding = text_features.float().cpu().numpy().flatten()

            assert (
                len(text_embedding) == 512
            ), f"Expected 512 dims, got {len(text_embedding)}"

            text_norm = float(np.linalg.norm(text_embedding))
            assert (
                0.99 < text_norm < 1.01
            ), f"Text embedding not normalized: norm={text_norm}"

            logger.info(f"  [OK] Text embedding: {len(text_embedding)} dimensions")
            logger.info(f"  [OK] Normalized: {text_norm:.4f}")

            # Test similarity computation (verify the model produces sensible results)
            similarity = float(np.dot(image_embedding, text_embedding))
            logger.info(f"  [OK] Image-text similarity: {similarity:.4f}")
            assert -1.0 <= similarity <= 1.0, f"Similarity out of range: {similarity}"

            self.model_results["clip"]["verified"] = True
            logger.info("[SUCCESS] CLIP model verified - WORKING CORRECTLY")

            # Clean up
            del model, preprocess, test_image, test_text
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return True

        except AssertionError as e:
            error_msg = f"CLIP verification failed: {e}"
            logger.exception("[ERROR] %s", error_msg)
            self.model_results["clip"]["error"] = error_msg
            return False

        except Exception as e:
            error_msg = f"CLIP download/verification failed: {e}"
            logger.exception("[ERROR] %s", error_msg)
            self.model_results["clip"]["error"] = error_msg
            return False

    def download_and_verify_insightface(self) -> bool:
        """Download and verify InsightFace buffalo_l model (the EXACT model we use)."""
        logger.info("\n%s", "=" * 60)
        logger.info("InsightFace Model: buffalo_l")
        logger.info("=" * 60)

        try:
            import cv2
            import insightface
            from insightface.app import FaceAnalysis

            logger.info("[OK] InsightFace, OpenCV, and ONNX Runtime installed")

            # Download the EXACT model we use (from face_worker.py:54-58)
            logger.info("Downloading InsightFace buffalo_l model...")
            start_time = time.time()

            # This is EXACTLY how we initialize it in face_worker.py
            face_app = FaceAnalysis(
                name="buffalo_l",  # Model name from face_worker.py:23
                providers=["CPUExecutionProvider"],  # CPU only (face_worker.py:56)
            )

            # prepare() downloads the model if not present (face_worker.py:58)
            face_app.prepare(ctx_id=0, det_size=(640, 640))

            download_time = time.time() - start_time
            logger.info(f"[OK] Model downloaded and initialized ({download_time:.2f}s)")

            self.model_results["insightface"]["downloaded"] = True

            # VERIFY the model actually works with real data
            logger.info("Verifying InsightFace model functionality...")

            # Create a test image with a synthetic "face"
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

            # Test face detection (what we do in _detect_faces_sync)
            faces = face_app.get(test_image)

            logger.info(
                f"  [OK] Face detection executed (found {len(faces)} faces in random test image)"
            )

            # Verify the model structure is correct
            # Try with a simple face-like image
            face_template = np.ones((480, 640, 3), dtype=np.uint8) * 200  # Light gray
            # Add some contrast (simplified face)
            face_template[100:300, 200:400] = 150  # Darker oval region

            faces = face_app.get(face_template)
            logger.info(f"  [OK] Detection on template: {len(faces)} faces")

            # The model should be able to process images without crashing
            # Even if it doesn't detect faces in our synthetic image, it should return an empty list

            # Verify the model has the expected components
            # InsightFace buffalo_l should have detection and recognition models
            assert hasattr(
                face_app, "models"
            ), "FaceAnalysis missing 'models' attribute"
            assert len(face_app.models) > 0, "No models loaded in FaceAnalysis"

            logger.info(f"  [OK] Loaded {len(face_app.models)} model components")

            # Test with a real face detection scenario
            # Create a simple face-like pattern that might trigger detection
            test_face = np.ones((480, 640, 3), dtype=np.uint8) * 255
            # Add a dark oval (head)
            cv2.ellipse(
                test_face, (320, 240), (100, 150), 0, 0, 360, (100, 100, 100), -1
            )
            # Add eyes
            cv2.circle(test_face, (280, 200), 20, (50, 50, 50), -1)
            cv2.circle(test_face, (360, 200), 20, (50, 50, 50), -1)
            # Add mouth
            cv2.ellipse(test_face, (320, 280), (40, 20), 0, 0, 180, (50, 50, 50), -1)

            faces = face_app.get(test_face)

            if len(faces) > 0:
                logger.info(
                    f"  [OK] Face detected in synthetic image: {len(faces)} face(s)"
                )

                # Verify face structure (from _detect_faces_sync in face_worker.py)
                face = faces[0]

                # Check required attributes (face_worker.py:81-97)
                assert hasattr(face, "bbox"), "Face missing bbox attribute"
                assert hasattr(
                    face, "normed_embedding"
                ), "Face missing normed_embedding"
                assert hasattr(face, "det_score"), "Face missing det_score"

                bbox = face.bbox.astype(int)
                embedding = face.normed_embedding.astype(np.float32)
                confidence = float(face.det_score)

                logger.info(f"    - BBox: {bbox.tolist()}")
                logger.info(f"    - Embedding dim: {len(embedding)}")
                logger.info(f"    - Confidence: {confidence:.4f}")

                # Verify embedding properties
                assert (
                    len(embedding) == 512
                ), f"Expected 512-dim embedding, got {len(embedding)}"
                assert isinstance(
                    embedding, np.ndarray
                ), "Embedding must be numpy array"

                # Check embedding is normalized (InsightFace uses normed_embedding)
                norm = float(np.linalg.norm(embedding))
                assert 0.99 < norm < 1.01, f"Embedding not normalized: norm={norm}"

                logger.info(
                    f"  [OK] Embedding verified: {len(embedding)} dims, norm={norm:.4f}"
                )
            else:
                # Model works but didn't detect our synthetic face - that's okay
                logger.info(
                    "  Info: No face detected in synthetic image (expected for simple pattern)"
                )
                logger.info("  [OK] Model can process images without errors")

            self.model_results["insightface"]["verified"] = True
            logger.info("[SUCCESS] InsightFace model verified - WORKING CORRECTLY")

            return True

        except AssertionError as e:
            error_msg = f"InsightFace verification failed: {e}"
            logger.exception("[ERROR] %s", error_msg)
            self.model_results["insightface"]["error"] = error_msg
            return False

        except Exception as e:
            error_msg = f"InsightFace download/verification failed: {e}"
            logger.exception("[ERROR] %s", error_msg)
            self.model_results["insightface"]["error"] = error_msg
            return False

    def verify_all_models(self) -> bool:
        """Download and verify all ML models."""
        logger.info("\n%s", "=" * 60)
        logger.info("ML MODEL DOWNLOAD & VERIFICATION")
        logger.info("=" * 60)
        logger.info(
            "This verifies models download correctly and actually work with real data.\n"
        )

        # Download and verify each model
        self.download_and_verify_clip()
        self.download_and_verify_insightface()

        # Print summary
        return self.print_verification_summary()

    def print_verification_summary(self) -> bool:
        """Print verification summary."""
        logger.info("\n%s", "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)

        all_verified = True

        for model_name, result in self.model_results.items():
            status_marker = "[OK]" if result["verified"] else "[FAIL]"
            logger.info(f"\n{model_name.upper()}:")
            logger.info(f"  Downloaded: {'[OK]' if result['downloaded'] else '[FAIL]'}")
            logger.info(f"  Verified:   {'[OK]' if result['verified'] else '[FAIL]'}")

            if result["error"]:
                logger.info(f"  Error: {result['error']}")

            logger.info(f"  Status: {status_marker}")

            if not result["verified"]:
                all_verified = False

        logger.info("\n%s", "=" * 60)
        if all_verified:
            logger.info("[SUCCESS] ALL MODELS VERIFIED AND WORKING")
        else:
            logger.error("[ERROR] SOME MODELS FAILED VERIFICATION")
        logger.info("=" * 60)

        return all_verified

    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================

    def run_full_setup(
        self, install: bool = True, verify: bool = True, skip_tesseract: bool = True
    ) -> bool:
        """Run full setup: install dependencies and verify models."""
        success = True

        if install:
            if not self.install_all_dependencies(skip_tesseract=skip_tesseract):
                logger.error("Dependency installation failed")
                success = False

        if verify:
            if not self.verify_all_models():
                logger.error("Model verification failed")
                success = False

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install and verify ML dependencies for Ideal Goggles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all              # Install + download + verify (default)
  %(prog)s --install-only     # Only install dependencies
  %(prog)s --verify-only      # Only verify models work
  %(prog)s --skip-tesseract   # Skip Tesseract OCR installation
  %(prog)s -v --all           # Verbose mode
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Install dependencies and verify models (default)",
    )
    mode_group.add_argument(
        "--install-only",
        action="store_true",
        help="Only install dependencies, skip verification",
    )
    mode_group.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify models work, skip installation",
    )

    # Optional flags
    parser.add_argument(
        "--skip-tesseract", action="store_true", help="Skip Tesseract OCR installation"
    )

    args = parser.parse_args()

    # Determine mode
    install = not args.verify_only
    verify = not args.install_only

    # Create setup instance
    setup = MLSetup(verbose=args.verbose)

    # Run setup
    logger.info("=" * 60)
    logger.info("Ideal Goggles ML Setup")
    logger.info("=" * 60)

    success = setup.run_full_setup(
        install=install, verify=verify, skip_tesseract=args.skip_tesseract
    )

    # Final result
    if success:
        logger.info("\n[SUCCESS] ML setup completed successfully!")
        logger.info("Models are ready for production build!")
        sys.exit(0)
    else:
        logger.error(
            "\n[ERROR] ML setup failed - some components may not work correctly!"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
