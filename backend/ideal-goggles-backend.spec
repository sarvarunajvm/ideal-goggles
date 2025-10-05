# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # Include CLIP model tokenizer files if they exist
        # Note: You may need to adjust these paths based on your environment
        # ('~/.cache/clip', 'clip'),  # Uncomment if CLIP models are pre-downloaded
    ],
    hiddenimports=[
        # Face detection dependencies
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'cv2',
        'numpy',
        'onnxruntime',
        'sklearn',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._partition_nodes',
        # PyTorch and CLIP for semantic search
        'torch',
        'torch._C',
        'torch._inductor',
        'torch._dynamo',
        'torch.nn',
        'torch.utils',
        'torch.utils.data',
        'torchvision',
        'torchvision.transforms',
        'clip',
        'clip.model',
        'clip.simple_tokenizer',
        'ftfy',
        'regex',
        'tqdm',
        # Additional ML utilities
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
