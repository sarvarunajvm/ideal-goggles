# ML Setup & Packaging Guide

Complete guide for ML dependencies setup, packaging, and platform compatibility.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Builds](#production-builds)
- [Platform Compatibility](#platform-compatibility)
- [Packaging Strategy](#packaging-strategy)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Developers

```bash
# Install all ML dependencies and verify they work
pnpm run backend:install-ml

# Or manually
cd backend
python3 scripts/setup_ml_models.py --all

# Verify models work correctly
pnpm run backend:verify-models
```

### For Production Builds

```bash
# Full build with ML dependencies (~3-4 GB)
pnpm run dist:mac          # macOS
pnpm run dist:win          # Windows
pnpm run dist:linux        # Linux

# Lite build without ML (~150 MB)
pnpm run backend:package-lite
pnpm run dist:mac
```

---

## Development Setup

### Installation

ML dependencies are **automatically included** in production builds. For development:

```bash
# Install + download + verify (recommended)
python scripts/setup_ml_models.py --all

# Or separate steps
python scripts/setup_ml_models.py --install-only    # Just install
python scripts/setup_ml_models.py --verify-only     # Just verify
```

### What Gets Installed

**Core ML Libraries:**
- PyTorch (CPU/MPS/CUDA optimized)
- CLIP (semantic search)
- InsightFace (face recognition)
- OpenCV (computer vision)
- ONNX Runtime (model inference)
- FAISS (vector search)

**Models Downloaded:**
- CLIP ViT-B/32 (~350 MB) - For semantic search
- InsightFace buffalo_l (~500 MB) - For face detection

### Verification

The setup script **verifies models actually work** (not just installed):

```python
✓ Downloads CLIP ViT-B/32 model
✓ Tests image embedding (512 dims, normalized)
✓ Tests text embedding (512 dims, normalized)
✓ Downloads InsightFace buffalo_l model
✓ Tests face detection on synthetic images
✓ Verifies embedding dimensions and normalization
```

**Build fails if models don't work** - preventing broken releases!

---

## Production Builds

### Automated ML Inclusion

Production builds **automatically include all ML dependencies**. Users install nothing manually.

### Build Process

```bash
# Full build (recommended)
pnpm run dist:mac

# This automatically:
# 1. Installs ML dependencies
# 2. Downloads and verifies models
# 3. Bundles everything with PyInstaller
# 4. Creates platform-specific installer
```

### Build Targets

| Command | Platform | Size | ML Features |
|---------|----------|------|-------------|
| `pnpm run dist:mac` | macOS (arm64/x64) | ~3-4 GB | ✅ All |
| `pnpm run dist:win` | Windows (x64) | ~3.5-4.5 GB | ✅ All |
| `pnpm run dist:linux` | Linux (x64) | ~3-4 GB | ✅ All |
| `pnpm run backend:package-lite` | Any | ~150 MB | ❌ None |

### What's Bundled

✅ **Face Recognition** - InsightFace models pre-installed
✅ **Semantic Search** - PyTorch + CLIP models included
✅ **Vector Search** - FAISS for fast similarity search
✅ **All dependencies bundled** - End users install nothing

---

## Platform Compatibility

### Supported Platforms

| Platform | ML Support | Models | Device | Status |
|----------|-----------|--------|--------|---------|
| **macOS (Apple Silicon)** | ✅ Full | ✅ MPS Optimized | GPU (Metal) | ✅ Tested |
| **macOS (Intel)** | ✅ Full | ✅ CPU | CPU | ✅ Tested |
| **Linux (Ubuntu/Debian)** | ✅ Full | ✅ CPU/CUDA | CPU/GPU | ✅ Compatible |
| **Linux (RHEL/Fedora)** | ✅ Full | ✅ CPU/CUDA | CPU/GPU | ✅ Compatible |
| **Windows 10/11** | ✅ Full | ✅ CPU/CUDA | CPU/GPU | ✅ Compatible |

### Platform-Specific Details

#### macOS

**Apple Silicon (M1/M2/M3):**
```bash
# Automatically uses MPS (Metal Performance Shaders) for GPU acceleration
✓ CLIP ViT-B/32 (MPS-accelerated)
✓ InsightFace buffalo_l (CPU via ONNX Runtime)
⚡ Performance: ~5-10 images/sec (GPU accelerated)
```

**Intel Macs:**
```bash
# Uses CPU-only PyTorch
✓ CLIP ViT-B/32 (CPU)
✓ InsightFace buffalo_l (CPU via ONNX Runtime)
⚡ Performance: ~2-3 images/sec
```

**Installation:**
```bash
pip install torch torchvision  # Auto-detects Apple Silicon and uses MPS
python scripts/setup_ml_models.py --all
```

#### Linux

**With NVIDIA GPU:**
```bash
# Automatically detects CUDA and installs GPU-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
⚡ Performance: ~15-30 images/sec (CUDA accelerated)
```

**Without GPU:**
```bash
# Uses CPU-only PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
⚡ Performance: ~2-3 images/sec
```

**System Dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-dev build-essential

# RHEL/Fedora
sudo dnf install -y python3-devel gcc gcc-c++
```

#### Windows

**With NVIDIA GPU:**
```powershell
# Uses CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
⚡ Performance: ~15-30 images/sec
```

**Without GPU:**
```powershell
# Uses CPU-only PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
⚡ Performance: ~1-2 images/sec
```

### Performance Comparison

| Platform | Device | CLIP Embedding | Face Detection | Build Time |
|----------|--------|----------------|----------------|------------|
| **macOS M2** | MPS | ~100ms | ~200ms | ~8 min |
| **macOS Intel i7** | CPU | ~300ms | ~400ms | ~10 min |
| **Linux (RTX 3080)** | CUDA | ~50ms | ~150ms | ~8 min |
| **Linux (CPU only)** | CPU | ~400ms | ~500ms | ~12 min |
| **Windows (RTX 3070)** | CUDA | ~60ms | ~180ms | ~10 min |
| **Windows (CPU only)** | CPU | ~500ms | ~600ms | ~15 min |

---

## Packaging Strategy

### Why PyInstaller?

We use **PyInstaller** for desktop app packaging because:

1. **Single file distribution** - Users download one .dmg/.exe/.AppImage
2. **No runtime dependencies** - Works without Python installed
3. **Electron compatibility** - Easy to bundle with Electron
4. **Offline support** - All ML models included locally
5. **Cross-platform** - Works on macOS, Windows, Linux

### Build Pipeline

```bash
# 1. Clean environment
make clean

# 2. Install base dependencies
pip install -e ".[dev]"

# 3. Install ML dependencies AND verify models (unified!)
python scripts/setup_ml_models.py --all

# 4. Build with PyInstaller
pyinstaller --clean ideal-goggles-backend.spec

# 5. Package with Electron
pnpm run dist:mac

# Or use Makefile (does all steps):
make package  # Runs setup_ml_models.py --all automatically
```

### File Size Optimization

**Current sizes:**
- Base Python + FastAPI: ~50 MB
- + NumPy + OpenCV: ~100 MB
- + FAISS + ONNX: ~150 MB
- + PyTorch: ~2.5 GB
- + CLIP + InsightFace models: ~3.5 GB

**Optimizations applied:**
1. ✅ CPU-only PyTorch (saves ~500 MB vs CUDA)
2. ✅ CLIP ViT-B/32 (saves ~500 MB vs ViT-L/14)
3. ✅ Exclude dev dependencies (pytest, mypy, black, ruff)
4. ✅ Platform-specific builds (no cross-compilation bloat)

### PyInstaller Configuration

```python
# From ideal-goggles-backend.spec
def collect_ml_data_files():
    """Collect ML model files for packaging."""
    datas = []

    # InsightFace models
    import insightface
    models_path = Path(insightface.__file__).parent / 'models'
    datas.append((str(models_path), 'insightface/models'))

    # CLIP models
    clip_cache = Path.home() / '.cache' / 'clip'
    datas.append((str(clip_cache), 'clip_models'))

    return datas

# Hidden imports (critical!)
hiddenimports = [
    'numpy.core._dtype_ctypes',
    'numpy.core._multiarray_umath',
    'torch', 'torch._C', 'clip',
    'insightface', 'cv2',
    'onnxruntime.capi.onnxruntime_pybind11_state',
]
```

---

## Troubleshooting

### Common Issues

**1. "Module not found" at runtime:**
```python
# Add to hiddenimports in .spec file
hiddenimports.append('missing_module')
```

**2. Models not loading:**
```python
# Check if running from frozen exe
import sys
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

model_path = os.path.join(base_path, 'models', 'model.onnx')
```

**3. Installation fails:**
```bash
# Check Python version (needs 3.12+)
python3 --version

# Reinstall dependencies
cd backend
pip3 install -e ".[dev]"
python3 scripts/setup_ml_models.py --all -v  # Verbose mode
```

**4. Build too large:**
```bash
# Use lite build without ML
pnpm run backend:package-lite

# Or analyze what's taking space
pyinstaller --clean --log-level=DEBUG ideal-goggles-backend.spec 2>&1 | grep "WARNING"
```

### Platform-Specific Issues

**macOS:**
```bash
# "Cannot verify developer" warning
xattr -d com.apple.quarantine /Applications/ideal-goggles.app

# Permission denied on first run
# Right-click app → Open
# Or: System Preferences → Security & Privacy → Allow
```

**Linux:**
```bash
# AppImage won't execute
chmod +x ideal-goggles-1.0.24-x64.AppImage

# Missing libraries (Ubuntu/Debian)
sudo apt-get install -y libglib2.0-0 libnss3 libatk-bridge2.0-0
```

**Windows:**
```powershell
# "Windows protected your PC" warning
# Click "More info" → "Run anyway"

# Missing Visual C++ Redistributable
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Verification Failures

If model verification fails:

```bash
# Run with verbose mode to see detailed errors
python scripts/setup_ml_models.py --all -v

# Check available memory (needs 2+ GB)
# Check disk space (needs 5+ GB for models)

# Try installing individual components
python scripts/setup_ml_models.py --install-only
# Check what failed, then manually install
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

## Model Details

### CLIP ViT-B/32

- **Source:** OpenAI CLIP
- **Size:** ~350 MB
- **Purpose:** Semantic image search with natural language
- **Embedding:** 512 dimensions, L2 normalized
- **Location:** `~/.cache/clip/ViT-B-32.pt`

### InsightFace buffalo_l

- **Source:** InsightFace
- **Size:** ~500 MB
- **Purpose:** Face detection and recognition
- **Embedding:** 512 dimensions, L2 normalized
- **Location:** `~/.insightface/models/buffalo_l/`

---

## Best Practices

1. ✅ Use **PyInstaller** for desktop apps
2. ✅ **Verify models** before packaging (build fails if broken)
3. ✅ Use **CPU-only PyTorch** to save space
4. ✅ **Exclude dev dependencies** from production
5. ✅ Test the **frozen executable** before release
6. ✅ Provide **clear file size expectations** to users
7. ✅ Use **lazy imports** for faster startup
8. ✅ **Platform-specific optimization** (MPS/CUDA/CPU)

---

## Further Reading

- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [ONNX Runtime](https://onnxruntime.ai/)
- [PyTorch Mobile](https://pytorch.org/mobile/home/)
- [CLIP Model Card](https://github.com/openai/CLIP)
- [InsightFace Documentation](https://github.com/deepinsight/insightface)
