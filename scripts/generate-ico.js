// Simple ICO generator that wraps a single 256x256 PNG
// into an .ico container, compatible with modern Windows.
// Reads build-resources/icon.png and writes build-resources/icon.ico

const fs = require('fs');
const path = require('path');

function buildIcoFromPng(pngBuffer) {
  const entries = 1;
  const header = Buffer.alloc(6);
  // ICONDIR
  header.writeUInt16LE(0, 0); // reserved
  header.writeUInt16LE(1, 2); // type: 1 = icon
  header.writeUInt16LE(entries, 4); // count

  const dir = Buffer.alloc(16);
  // ICONDIRENTRY
  // width/height: 0 means 256
  dir.writeUInt8(0, 0); // width
  dir.writeUInt8(0, 1); // height
  dir.writeUInt8(0, 2); // colorCount
  dir.writeUInt8(0, 3); // reserved
  dir.writeUInt16LE(1, 4); // planes
  dir.writeUInt16LE(32, 6); // bitCount
  dir.writeUInt32LE(pngBuffer.length, 8); // bytesInRes
  const imageOffset = header.length + dir.length; // 6 + 16 = 22
  dir.writeUInt32LE(imageOffset, 12); // imageOffset

  return Buffer.concat([header, dir, pngBuffer]);
}

function main() {
  const pngPath = path.resolve(__dirname, '..', 'build-resources', 'icon.png');
  const icoPath = path.resolve(__dirname, '..', 'build-resources', 'icon.ico');

  if (!fs.existsSync(pngPath)) {
    console.error('PNG icon not found at:', pngPath);
    process.exit(1);
  }

  const png = fs.readFileSync(pngPath);
  const ico = buildIcoFromPng(png);
  fs.writeFileSync(icoPath, ico);
  console.log('Wrote ICO:', icoPath, 'size=', ico.length);
}

main();

