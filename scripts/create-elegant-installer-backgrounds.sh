#!/bin/bash

# Script to create elegant installer backgrounds with professional design
# This creates visually appealing backgrounds for both macOS DMG and Windows NSIS installers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Creating Elegant Installer Backgrounds   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v magick &> /dev/null && ! command -v convert &> /dev/null; then
    echo -e "${YELLOW}ImageMagick is required. Installing via Homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install imagemagick
    else
        echo -e "${RED}Error: Please install ImageMagick:${NC}"
        echo "  brew install imagemagick"
        exit 1
    fi
fi

# Determine the convert command
if command -v magick &> /dev/null; then
    CONVERT="magick"
else
    CONVERT="convert"
fi

# Create build-resources directory
mkdir -p build-resources

# === DMG BACKGROUND (600x400) ===
echo -e "${YELLOW}Creating elegant DMG background...${NC}"

$CONVERT -size 600x400 gradient:"#1a1a2e-#0f3460" \
  \( -size 600x400 xc:none -fill "rgba(255,255,255,0.05)" \
     -draw "circle 100,100 100,200" \
     -draw "circle 500,300 500,380" \
     -draw "circle 300,50 300,100" \) -composite \
  -fill white -font "Helvetica-Bold" -pointsize 32 -gravity north \
  -annotate +0+40 "Ideal Goggles" \
  -fill "rgba(255,255,255,0.8)" -font "Helvetica" -pointsize 14 \
  -annotate +0+80 "Privacy-focused Photo Organization" \
  -fill "rgba(22,160,133,1)" -font "Helvetica" -pointsize 16 -gravity center \
  -annotate -120+80 "Drag to install ➜" \
  -strokewidth 3 -stroke "rgba(22,160,133,0.6)" -fill none \
  -draw "roundrectangle 110,170 190,230 15,15" \
  -draw "roundrectangle 410,170 490,230 15,15" \
  -draw "line 200,200 400,200" \
  -draw "path 'M 390,190 L 400,200 L 390,210'" \
  -fill "rgba(255,255,255,0.1)" \
  -draw "roundrectangle 20,20 580,380 20,20" \
  build-resources/dmg-background.png

echo -e "${GREEN}✓ Created elegant DMG background (600x400)${NC}"

# === NSIS INSTALLER SIDEBAR (164x314) ===
echo -e "${YELLOW}Creating elegant NSIS sidebar...${NC}"

$CONVERT -size 164x314 gradient:"#667eea-#764ba2" \
  \( -size 164x314 xc:none -fill "rgba(255,255,255,0.1)" \
     -draw "circle 40,40 40,80" \
     -draw "circle 124,120 124,150" \
     -draw "circle 60,240 60,270" \) -composite \
  -fill white -font "Helvetica-Bold" -pointsize 18 -gravity north \
  -annotate +0+100 "Ideal" \
  -annotate +0+125 "Goggles" \
  -fill "rgba(255,255,255,0.8)" -font "Helvetica" -pointsize 10 \
  -annotate +0+160 "AI-Powered" \
  -annotate +0+175 "Photo Search" \
  -fill "rgba(255,255,255,0.6)" -pointsize 8 -gravity south \
  -annotate +0+30 "Version 1.0" \
  -strokewidth 2 -stroke "rgba(255,255,255,0.3)" -fill none \
  -draw "roundrectangle 15,15 149,299 10,10" \
  build-resources/installer-sidebar.bmp

echo -e "${GREEN}✓ Created elegant NSIS sidebar (164x314)${NC}"

# === ALTERNATIVE MODERN DMG BACKGROUND ===
echo -e "${YELLOW}Creating alternative modern DMG background...${NC}"

$CONVERT -size 600x400 xc:"#0a0e27" \
  \( -size 600x400 plasma:fractal -blur 0x8 -fill "rgba(102,126,234,0.4)" -colorize 100% \) -composite \
  -fill white -font "Helvetica-Bold" -pointsize 36 -gravity north \
  -annotate +0+35 "Ideal Goggles" \
  -fill "rgba(255,255,255,0.7)" -font "Helvetica-Light" -pointsize 15 \
  -annotate +0+78 "Your photos, organized with AI" \
  -strokewidth 0 -fill "rgba(22,160,133,0.9)" -font "Helvetica" -pointsize 14 \
  -gravity center -annotate +0+60 "Drag app to Applications folder" \
  -strokewidth 4 -stroke "rgba(22,160,133,0.5)" -fill none \
  -draw "circle 150,200 150,250" \
  -draw "circle 450,200 450,250" \
  -strokewidth 3 -stroke "rgba(22,160,133,0.7)" \
  -draw "line 200,200 400,200" \
  -draw "path 'M 385,190 L 400,200 L 385,210'" \
  -fill "rgba(255,255,255,0.05)" -strokewidth 2 -stroke "rgba(255,255,255,0.2)" \
  -draw "roundrectangle 10,10 590,390 25,25" \
  build-resources/dmg-background-modern.png

echo -e "${GREEN}✓ Created modern alternative DMG background${NC}"

# === MINIMALIST DMG BACKGROUND ===
echo -e "${YELLOW}Creating minimalist DMG background...${NC}"

$CONVERT -size 600x400 xc:"#f5f5f7" \
  -fill "#1d1d1f" -font "Helvetica-Bold" -pointsize 28 -gravity north \
  -annotate +0+50 "Ideal Goggles" \
  -fill "#86868b" -font "Helvetica" -pointsize 13 \
  -annotate +0+85 "Privacy-focused photo organization" \
  -strokewidth 2 -stroke "#0071e3" -fill none \
  -draw "roundrectangle 115,160 185,230 12,12" \
  -draw "roundrectangle 415,160 485,230 12,12" \
  -fill "#0071e3" -font "Helvetica" -pointsize 14 -gravity center \
  -annotate +0+85 "→" \
  -strokewidth 1 -stroke "#d2d2d7" -fill none \
  -draw "line 0,120 600,120" \
  build-resources/dmg-background-minimal.png

echo -e "${GREEN}✓ Created minimalist DMG background${NC}"

# === DARK MODERN DMG BACKGROUND (RECOMMENDED) ===
echo -e "${YELLOW}Creating dark modern DMG background (recommended)...${NC}"

$CONVERT -size 600x400 xc:"#1a1a1a" \
  \( -size 600x400 xc:none \
     -fill "rgba(102,126,234,0.15)" -draw "circle 100,350 100,450" \
     -fill "rgba(118,75,162,0.15)" -draw "circle 500,50 500,150" \
     -fill "rgba(22,160,133,0.1)" -draw "circle 300,200 300,300" \
  \) -composite \
  -blur 0x40 \
  -fill white -font "Helvetica-Bold" -pointsize 34 -gravity north \
  -annotate +0+45 "Ideal Goggles" \
  -fill "rgba(255,255,255,0.7)" -font "Helvetica-Light" -pointsize 14 \
  -annotate +0+85 "AI-Powered Photo Search & Organization" \
  -strokewidth 3 -stroke "rgba(22,160,133,0.8)" -fill none \
  -draw "roundrectangle 105,160 195,250 20,20" \
  -draw "roundrectangle 405,160 495,250 20,20" \
  -strokewidth 2.5 -stroke "rgba(22,160,133,0.9)" \
  -draw "line 210,205 390,205" \
  -draw "path 'M 375,195 L 390,205 L 375,215'" \
  -fill "rgba(22,160,133,0.9)" -font "Helvetica" -pointsize 13 -gravity center \
  -annotate +0+90 "Drag to Applications" \
  -fill "rgba(255,255,255,0.05)" -strokewidth 1 -stroke "rgba(255,255,255,0.15)" \
  -draw "roundrectangle 15,15 585,385 25,25" \
  -fill "rgba(255,255,255,0.5)" -pointsize 10 -gravity south \
  -annotate +0+20 "Privacy-focused • Local-first • AI-enhanced" \
  build-resources/dmg-background-dark-modern.png

echo -e "${GREEN}✓ Created dark modern DMG background (RECOMMENDED)${NC}"

# Copy the recommended one as the main background
cp build-resources/dmg-background-dark-modern.png build-resources/dmg-background.png
echo -e "${BLUE}→ Set dark-modern as default background${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     All Backgrounds Created Successfully   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Generated backgrounds:${NC}"
echo "  1. ${GREEN}dmg-background.png${NC} - Dark modern (default, recommended)"
echo "  2. ${YELLOW}dmg-background-dark-modern.png${NC} - Same as above"
echo "  3. ${YELLOW}dmg-background-modern.png${NC} - Plasma gradient variant"
echo "  4. ${YELLOW}dmg-background-minimal.png${NC} - Light minimalist (Apple-style)"
echo "  5. ${YELLOW}installer-sidebar.bmp${NC} - NSIS Windows installer sidebar"
echo ""
echo -e "${BLUE}To use a different background:${NC}"
echo "  cp build-resources/dmg-background-minimal.png build-resources/dmg-background.png"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review backgrounds in build-resources/"
echo "  2. Choose your favorite (or keep the default)"
echo "  3. Run: ${GREEN}pnpm run dist:mac${NC}"
echo ""
