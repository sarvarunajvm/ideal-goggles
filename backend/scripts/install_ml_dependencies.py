#!/usr/bin/env python3
"""
ML Dependencies Installer for Ideal Goggles
Installs optional machine learning dependencies for enhanced features.
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional


class DependencyInstaller:
    """Manages installation of ML dependencies."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        self.python_version = sys.version_info

    def log(self, message: str, level: str = "INFO"):
        """Log message with level."""
        if level in {"ERROR", "WARNING"} or level == "SUCCESS":
            pass
        else:
            pass

    def run_command(self, cmd: list[str], check: bool = True) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        if self.verbose:
            self.log(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"

    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        if self.python_version < (3, 8):
            self.log(
                f"Python {self.python_version.major}.{self.python_version.minor} detected. "
                "Python 3.8+ is required.",
                "ERROR",
            )
            return False
        return True

    def check_pip(self) -> bool:
        """Check if pip is available."""
        code, _, _ = self.run_command([sys.executable, "-m", "pip", "--version"])
        if code != 0:
            self.log("pip is not installed", "ERROR")
            return False
        return True

    def install_tesseract(self) -> bool:
        """Install Tesseract OCR based on platform."""
        self.log("Installing Tesseract OCR...")

        if self.platform == "darwin":  # macOS
            # Check if Homebrew is installed
            code, _, _ = self.run_command(["which", "brew"])
            if code != 0:
                self.log(
                    "Homebrew not found. Please install from https://brew.sh", "ERROR"
                )
                return False

            # Install tesseract
            code, _stdout, stderr = self.run_command(["brew", "install", "tesseract"])
            if code != 0:
                self.log(f"Failed to install Tesseract: {stderr}", "ERROR")
                return False

            # Install language packs
            self.log("Installing additional language packs...")
            for lang in ["eng", "fra", "deu", "spa", "chi_sim", "jpn", "kor"]:
                self.run_command(
                    ["brew", "install", f"tesseract-lang-{lang}"], check=False
                )

        elif self.platform == "linux":
            # Check for package manager
            if Path("/etc/debian_version").exists():
                # Debian/Ubuntu
                self.log("Detected Debian/Ubuntu system")
                code, _, _ = self.run_command(["sudo", "apt-get", "update"])
                if code != 0:
                    self.log("Failed to update package list", "ERROR")
                    return False

                code, _, stderr = self.run_command(
                    [
                        "sudo",
                        "apt-get",
                        "install",
                        "-y",
                        "tesseract-ocr",
                        "tesseract-ocr-all",
                    ]
                )
                if code != 0:
                    self.log(f"Failed to install Tesseract: {stderr}", "ERROR")
                    return False

            elif Path("/etc/redhat-release").exists():
                # RHEL/Fedora/CentOS
                self.log("Detected RHEL/Fedora system")
                code, _, stderr = self.run_command(
                    [
                        "sudo",
                        "dnf",
                        "install",
                        "-y",
                        "tesseract",
                        "tesseract-langpack-*",
                    ]
                )
                if code != 0:
                    self.log(f"Failed to install Tesseract: {stderr}", "ERROR")
                    return False
            else:
                self.log(
                    "Unsupported Linux distribution. Please install Tesseract manually:\n"
                    "  https://github.com/tesseract-ocr/tesseract",
                    "WARNING",
                )
                return False

        elif self.platform == "windows":
            self.log(
                "Windows detected. Please install Tesseract manually:\n"
                "  1. Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  2. Run the installer\n"
                "  3. Add Tesseract to your PATH",
                "WARNING",
            )
            return False
        else:
            self.log(f"Unsupported platform: {self.platform}", "ERROR")
            return False

        # Verify installation
        code, _stdout, _ = self.run_command(["tesseract", "--version"])
        if code == 0:
            self.log("Tesseract installed successfully", "SUCCESS")
            if self.verbose:
                pass
            return True

        return False

    def install_python_packages(self, packages: dict[str, str]) -> bool:
        """Install Python packages via pip."""
        failed = []

        for package, version_spec in packages.items():
            package_spec = f"{package}{version_spec}" if version_spec else package
            self.log(f"Installing {package_spec}...")

            code, _, stderr = self.run_command(
                [sys.executable, "-m", "pip", "install", package_spec]
            )

            if code != 0:
                self.log(f"Failed to install {package}: {stderr}", "ERROR")
                failed.append(package)
            else:
                self.log(f"{package} installed successfully", "SUCCESS")

        return len(failed) == 0

    def install_clip(self) -> bool:
        """Install CLIP and dependencies."""
        self.log("Installing CLIP dependencies...")

        # Determine PyTorch version based on platform and CUDA availability
        torch_packages = self.get_torch_packages()

        # Install PyTorch first
        if not self.install_python_packages(torch_packages):
            return False

        # Install CLIP
        clip_packages = {
            "ftfy": "",
            "regex": "",
            "tqdm": "",
            "git+https://github.com/openai/CLIP.git": "",
        }

        return self.install_python_packages(clip_packages)

    def get_torch_packages(self) -> dict[str, str]:
        """Determine appropriate PyTorch packages for the platform."""
        # Check for CUDA
        cuda_available = self.check_cuda()

        if cuda_available:
            self.log("CUDA detected, installing GPU-enabled PyTorch")
            # PyTorch with CUDA 11.8
            return {
                "torch": "",
                "torchvision": "",
                "torchaudio": "",
                "--index-url": "https://download.pytorch.org/whl/cu118",
            }
        self.log("No CUDA detected, installing CPU-only PyTorch")
        if self.platform == "darwin" and "arm" in self.arch:
            # Apple Silicon
            self.log("Apple Silicon detected, installing MPS-enabled PyTorch")
            return {"torch": "", "torchvision": "", "torchaudio": ""}
        # CPU only
        return {
            "torch": "",
            "torchvision": "",
            "torchaudio": "",
            "--index-url": "https://download.pytorch.org/whl/cpu",
        }

    def check_cuda(self) -> bool:
        """Check if CUDA is available."""
        # Check for nvidia-smi
        code, _stdout, _ = self.run_command(["nvidia-smi"], check=False)
        if code == 0:
            if self.verbose:
                self.log("NVIDIA GPU detected")
            return True
        return False

    def install_insightface(self) -> bool:
        """Install InsightFace for face recognition."""
        self.log("Installing InsightFace dependencies...")

        # Core dependencies
        face_packages = {
            "opencv-python": ">=4.5.0",
            "onnxruntime": ">=1.10.0",
            "insightface": ">=0.7.0",
            "numpy": "<2.0.0",  # InsightFace compatibility
        }

        return self.install_python_packages(face_packages)

    def verify_installations(self) -> dict[str, bool]:
        """Verify all installations."""
        results = {}

        # Check Tesseract
        code, _, _ = self.run_command(["tesseract", "--version"], check=False)
        results["tesseract"] = code == 0

        # Check Python packages
        try:
            import torch

            results["pytorch"] = True
        except ImportError:
            results["pytorch"] = False

        try:
            import clip

            results["clip"] = True
        except ImportError:
            results["clip"] = False

        try:
            import insightface

            results["insightface"] = True
        except ImportError:
            results["insightface"] = False

        try:
            import cv2

            results["opencv"] = True
        except ImportError:
            results["opencv"] = False

        return results

    def install_all(
        self,
        skip_tesseract: bool = False,
        skip_clip: bool = False,
        skip_face: bool = False,
    ) -> bool:
        """Install all dependencies."""
        success = True

        if not self.check_python_version():
            return False

        if not self.check_pip():
            return False

        if not skip_tesseract:
            if not self.install_tesseract():
                self.log("Tesseract installation failed", "WARNING")
                success = False

        if not skip_clip:
            if not self.install_clip():
                self.log("CLIP installation failed", "WARNING")
                success = False

        if not skip_face:
            if not self.install_insightface():
                self.log("InsightFace installation failed", "WARNING")
                success = False

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install ML dependencies for Ideal Goggles"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--skip-tesseract", action="store_true", help="Skip Tesseract OCR installation"
    )
    parser.add_argument(
        "--skip-clip", action="store_true", help="Skip CLIP installation"
    )
    parser.add_argument(
        "--skip-face", action="store_true", help="Skip InsightFace installation"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing installations"
    )

    args = parser.parse_args()

    installer = DependencyInstaller(verbose=args.verbose)

    if args.verify_only:
        results = installer.verify_installations()

        for _installed in results.values():
            pass

        all_installed = all(results.values())
        if all_installed:
            pass
        else:
            pass

        return 0 if all_installed else 1

    # Perform installation

    if installer.install_all(
        skip_tesseract=args.skip_tesseract,
        skip_clip=args.skip_clip,
        skip_face=args.skip_face,
    ):
        # Verify
        results = installer.verify_installations()

        for _installed in results.values():
            pass

        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
