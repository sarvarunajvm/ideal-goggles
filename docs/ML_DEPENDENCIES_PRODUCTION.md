# ML Dependencies in Production Builds

## Issue
ML dependencies (PyTorch, CLIP, InsightFace, etc.) cannot be installed dynamically in the production build of ideal-goggles. This is because the production build uses a frozen executable created by PyInstaller, which bundles Python and all dependencies into a single executable file.

## Why This Happens
1. **Frozen Executables**: The production build (`ideal-goggles.app`) contains a frozen Python executable
2. **Isolated Environment**: The frozen executable runs in its own isolated environment
3. **No pip Access**: Frozen executables cannot use pip to install new packages at runtime
4. **Static Dependencies**: All Python packages must be included at build time

## Solutions

### Option 1: Build with ML Dependencies (Recommended)
Include ML dependencies when building the production app:

1. Install ML dependencies in your development environment:
   ```bash
   cd /Users/sarkalimuthu/WebstormProjects/ideal-goggles/backend
   python3 scripts/install_ml_dependencies.py --all
   ```

2. Rebuild the production app with ML dependencies included:
   ```bash
   # The build script should now include the ML packages
   npm run build:prod
   ```

### Option 2: Use Development Mode for ML Features
Run the app in development mode when ML features are needed:

```bash
# Backend
cd backend
python3 src/main.py

# Frontend
cd ..
npm run dev
```

### Option 3: Create Separate ML Build
Create two versions of the app:
- **Basic Version**: Without ML dependencies (smaller size)
- **ML Version**: With ML dependencies pre-installed (larger size)

## Technical Details

### Detection in Code
The backend now detects if it's running in a frozen environment:

```python
is_frozen = getattr(sys, 'frozen', False)
```

### API Response
The `/dependencies` endpoint now returns:
```json
{
  "is_frozen": true,
  "can_install": false,
  "features": {
    "semantic_search": false,
    "face_detection": false
  }
}
```

### Installation Attempt Response
When trying to install in production, the API returns:
```json
{
  "status": "unavailable",
  "message": "ML dependencies cannot be installed in the packaged application.",
  "output": "ML features must be enabled during the build process..."
}
```

## Build Configuration

To include ML dependencies in the production build, modify the PyInstaller spec file or build script to include:

```python
# In your .spec file or build configuration
hiddenimports = [
    'torch',
    'torchvision',
    'clip',
    'insightface',
    'cv2',
    'PIL',
    'numpy',
    'onnxruntime'
]

# Collect data files for models
datas = [
    ('path/to/clip/models', 'clip'),
    ('path/to/insightface/models', 'insightface'),
]
```

## File Size Considerations

Including ML dependencies will significantly increase the app size:
- **Without ML**: ~150 MB
- **With PyTorch/CLIP**: ~2-3 GB
- **With all ML features**: ~3-4 GB

Consider offering separate downloads for users who need ML features.

## Frontend UI Updates

The frontend should:
1. Check the `can_install` flag from `/dependencies`
2. Hide or disable the "Install" button when `can_install` is false
3. Show an appropriate message explaining that ML features require the development version or a special ML build