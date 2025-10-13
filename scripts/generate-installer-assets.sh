#!/bin/bash

# Script to generate installer assets from the main icon
# This creates all the required icon formats and installer images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating installer assets...${NC}"

# Check if we're in the project root
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null && ! command -v magick &> /dev/null; then
    echo -e "${YELLOW}Warning: ImageMagick not found. Installing via Homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install imagemagick
    else
        echo -e "${RED}Error: Please install ImageMagick manually:${NC}"
        echo "  brew install imagemagick"
        echo "  OR"
        echo "  https://imagemagick.org/script/download.php"
        exit 1
    fi
fi

# Determine the convert command
if command -v magick &> /dev/null; then
    CONVERT_CMD="magick"
else
    CONVERT_CMD="convert"
fi

# Create build-resources directory if it doesn't exist
mkdir -p build-resources

SOURCE_ICON="build-resources/icon.png"

if [ ! -f "$SOURCE_ICON" ]; then
    echo -e "${RED}Error: Source icon not found at $SOURCE_ICON${NC}"
    exit 1
fi

echo -e "${GREEN}Source icon: $SOURCE_ICON${NC}"

# 1. Generate .icns for macOS (512x512, 256x256, 128x128, 64x64, 32x32, 16x16)
echo -e "${YELLOW}Generating macOS .icns file...${NC}"
if command -v iconutil &> /dev/null; then
    # Create iconset directory
    ICONSET_DIR="build-resources/icon.iconset"
    mkdir -p "$ICONSET_DIR"

    # Generate all required sizes
    $CONVERT_CMD "$SOURCE_ICON" -resize 16x16 "$ICONSET_DIR/icon_16x16.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 32x32 "$ICONSET_DIR/icon_16x16@2x.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 32x32 "$ICONSET_DIR/icon_32x32.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 64x64 "$ICONSET_DIR/icon_32x32@2x.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 128x128 "$ICONSET_DIR/icon_128x128.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 256x256 "$ICONSET_DIR/icon_128x128@2x.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 256x256 "$ICONSET_DIR/icon_256x256.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 512x512 "$ICONSET_DIR/icon_256x256@2x.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 512x512 "$ICONSET_DIR/icon_512x512.png"
    $CONVERT_CMD "$SOURCE_ICON" -resize 1024x1024 "$ICONSET_DIR/icon_512x512@2x.png"

    # Convert to .icns
    iconutil -c icns "$ICONSET_DIR" -o "build-resources/icon.icns"
    rm -rf "$ICONSET_DIR"
    echo -e "${GREEN}✓ Created icon.icns${NC}"
else
    echo -e "${YELLOW}Warning: iconutil not available (macOS only). Skipping .icns generation.${NC}"
fi

# 2. Generate .ico for Windows (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
echo -e "${YELLOW}Generating Windows .ico file...${NC}"
$CONVERT_CMD "$SOURCE_ICON" -define icon:auto-resize=256,128,64,48,32,16 "build-resources/icon.ico"
echo -e "${GREEN}✓ Created icon.ico${NC}"

# 3. Generate NSIS installer sidebar (164x314 pixels)
echo -e "${YELLOW}Generating NSIS installer sidebar...${NC}"
$CONVERT_CMD "$SOURCE_ICON" -resize 164x164 -background "#1a1a1a" -gravity center -extent 164x314 "build-resources/installer-sidebar.bmp"
echo -e "${GREEN}✓ Created installer-sidebar.bmp${NC}"

# 4. Generate DMG background (600x400 pixels with instructions)
echo -e "${YELLOW}Generating DMG background...${NC}"
$CONVERT_CMD -size 600x400 xc:"#1a1a1a" \
  -font "Arial" -pointsize 16 -fill white -gravity north -annotate +0+30 "Ideal Goggles" \
  -pointsize 12 -gravity center -annotate +0+50 "Drag the app to the Applications folder" \
  -draw "stroke white fill none stroke-width 2 stroke-dasharray 5,5 circle 150,200 150,240" \
  -draw "stroke white fill none stroke-width 2 stroke-dasharray 5,5 circle 450,200 450,240" \
  -draw "stroke white fill none stroke-width 2 line 190,200 410,200" \
  -draw "stroke white fill none stroke-width 2 line 400,195 410,200 400,205" \
  "build-resources/dmg-background.png"
echo -e "${GREEN}✓ Created dmg-background.png${NC}"

# 5. Generate README for customization
cat > build-resources/README.md << 'EOF'
# Installer Assets

This directory contains assets used for building installers.

## Files

- **icon.png** - Source icon (512x512 or larger recommended)
- **icon.icns** - macOS icon format (auto-generated)
- **icon.ico** - Windows icon format (auto-generated)
- **installer-sidebar.bmp** - NSIS installer sidebar image (164x314)
- **dmg-background.png** - macOS DMG background (600x400)
- **installer.nsh** - Custom NSIS installer script
- **entitlements.mac.plist** - macOS entitlements

## Customization

### Update Icons
1. Replace `icon.png` with your custom icon (512x512 or larger, PNG format)
2. Run: `bash scripts/generate-installer-assets.sh`

### Customize NSIS Sidebar
1. Create a 164x314 pixel image
2. Save as `installer-sidebar.bmp`

### Customize DMG Background
1. Create a 600x400 pixel image
2. Save as `dmg-background.png`
3. Adjust icon positions in package.json if needed:
   - App icon: x:150, y:200
   - Applications folder: x:450, y:200

### Custom NSIS Script
Edit `installer.nsh` to customize:
- Welcome/finish page text
- Installation steps
- Uninstallation behavior
- Custom registry entries
- File associations

## Regenerate All Assets

Run from project root:
```bash
bash scripts/generate-installer-assets.sh
```

## Requirements

- **ImageMagick**: For image conversion
  ```bash
  brew install imagemagick
  ```

- **iconutil** (macOS only): For .icns generation
  - Pre-installed on macOS
EOF

echo -e "${GREEN}✓ Created README.md${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All installer assets generated!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Generated files:"
echo "  • build-resources/icon.icns (macOS)"
echo "  • build-resources/icon.ico (Windows)"
echo "  • build-resources/installer-sidebar.bmp (NSIS)"
echo "  • build-resources/dmg-background.png (DMG)"
echo "  • build-resources/README.md (documentation)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review generated assets in build-resources/"
echo "  2. Customize images if needed"
echo "  3. Run: pnpm run dist:mac or pnpm run dist:win"
echo ""
