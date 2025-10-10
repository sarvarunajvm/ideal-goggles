# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Collect ML model data files
def collect_ml_data_files():
    """Collect ML model files for inclusion in the build."""
    datas = []

    # Try to find InsightFace models
    try:
        import insightface
        insightface_path = Path(insightface.__file__).parent
        models_path = insightface_path / 'models'
        if models_path.exists():
            datas.append((str(models_path), 'insightface/models'))
    except (ImportError, AttributeError):
        print("⚠️  InsightFace not installed - face detection will not be available")

    # Try to find CLIP models (if pre-downloaded)
    clip_cache = Path.home() / '.cache' / 'clip'
    if clip_cache.exists():
        datas.append((str(clip_cache), 'clip_models'))

    # Try to find PyTorch models cache
    torch_cache = Path.home() / '.cache' / 'torch'
    if torch_cache.exists() and os.path.getsize(torch_cache) < 100 * 1024 * 1024:  # Only if < 100MB
        datas.append((str(torch_cache), 'torch_models'))

    return datas

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=collect_ml_data_files(),
    hiddenimports=[
        # Core dependencies
        'multiprocessing',
        'concurrent.futures',
        # Face detection dependencies
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'insightface.utils',
        'cv2',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'onnxruntime',
        'onnxruntime.capi._pybind_state',
        'sklearn',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._partition_nodes',
        # PyTorch and CLIP for semantic search
        'torch',
        'torch._C',
        'torch._inductor',
        'torch._dynamo',
        'torch.nn',
        'torch.nn.functional',
        'torch.utils',
        'torch.utils.data',
        'torchvision',
        'torchvision.transforms',
        'torchvision.transforms.functional',
        'clip',
        'clip.model',
        'clip.simple_tokenizer',
        'ftfy',
        'ftfy.bad_codecs',
        'regex',
        'tqdm',
        # Additional ML utilities
        'PIL',
        'PIL.Image',
        'PIL._imaging',
        # FAISS dependencies
        'faiss',
        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'aiosqlite',
        # FastAPI
        'fastapi',
        'uvicorn',
        'pydantic',
        'pydantic_settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'pandas',
        'scipy',
        'jupyter',
        'notebook',
        'IPython',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ideal-goggles-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
