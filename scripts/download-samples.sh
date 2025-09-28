#!/usr/bin/env bash
set -euo pipefail

# Download a small, diverse set of public-domain/sample images
# into backend/data/samples to exercise EXIF, OCR, faces, formats.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$ROOT_DIR/backend/data/samples"
mkdir -p "$DEST_DIR"

echo "Downloading sample images to: $DEST_DIR"

download() {
  local url="$1"; shift
  local out="$1"; shift
  echo "- $out"
  curl -k -L --fail --silent --show-error "$url" -o "$DEST_DIR/$out"
}

# EXIF-rich JPEGs (camera make/model, exposure)
download "https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/Canon_40D.jpg" Canon_40D.jpg
download "https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/Nikon_D1X.jpg" Nikon_D1X.jpg

# Landscape/high-res JPEG
download "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg" Fronalpstock_big.jpg

# PNG with transparency
download "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png" transparency_demo.png

# Text image for OCR (English)
download "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Hello_world_%28white_background%29.svg/800px-Hello_world_%28white_background%29.svg.png" hello_world.png

# Public domain portrait photos (faces)
download "https://upload.wikimedia.org/wikipedia/commons/0/0b/Barack_Obama.jpg" obama.jpg
download "https://upload.wikimedia.org/wikipedia/commons/9/9a/George_W_Bush%2C_photographic_portrait.jpg" bush.jpg

# WebP sample
download "https://upload.wikimedia.org/wikipedia/commons/3/3e/Chess_king_2.webp" chess_king.webp

echo "Done. Files in $DEST_DIR:"
ls -la "$DEST_DIR"

cat << 'NOTE'

Next steps:
- Ensure backend is running (port matches frontend proxy):
  cd "$ROOT_DIR/backend" && make dev

- Tell backend where to index (absolute path):
  curl -s -X POST http://127.0.0.1:5555/config/roots \
    -H 'Content-Type: application/json' \
    -d '{"roots": ["'"$DEST_DIR"'"]}' | jq .

- Start indexing:
  curl -s -X POST http://127.0.0.1:5555/index/start | jq .

- Check status:
  curl -s http://127.0.0.1:5555/index/status | jq .

OCR tip:
- If Tesseract is not installed, install on macOS: brew install tesseract

NOTE

