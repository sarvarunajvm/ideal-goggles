#!/usr/bin/env node
// Generate icons for all platforms: Windows (.ico), macOS (.icns), Linux (PNG)
// Reads build-resources/icon.png and generates platform-specific formats

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ICON_SIZES = {
  mac: [16, 32, 64, 128, 256, 512, 1024],
  windows: [256], // Single 256x256 for modern Windows
};

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

function generateWindowsIco(pngPath, outputPath) {
  console.log('Generating Windows .ico...');
  const png = fs.readFileSync(pngPath);
  const ico = buildIcoFromPng(png);
  fs.writeFileSync(outputPath, ico);
  console.log('✓ Created:', outputPath, `(${ico.length} bytes)`);
}

function generateMacOsIcns(pngPath, outputPath) {
  console.log('Generating macOS .icns...');
  
  // Create temporary iconset directory
  const iconsetPath = path.join(path.dirname(outputPath), 'icon.iconset');
  
  if (fs.existsSync(iconsetPath)) {
    fs.rmSync(iconsetPath, { recursive: true });
  }
  fs.mkdirSync(iconsetPath);

  try {
    // Check if sips is available (macOS image processing tool)
    try {
      execSync('which sips', { stdio: 'ignore' });
    } catch {
      console.warn('⚠ sips not found - skipping .icns generation (macOS builds may fail)');
      console.warn('  Run this script on macOS to generate .icns, or use electron-builder auto-generation');
      return;
    }

    // Generate all required sizes
    ICON_SIZES.mac.forEach(size => {
      const outputFile = path.join(iconsetPath, `icon_${size}x${size}.png`);
      const output2xFile = path.join(iconsetPath, `icon_${size}x${size}@2x.png`);
      
      // Regular size
      execSync(`sips -z ${size} ${size} "${pngPath}" --out "${outputFile}"`, { stdio: 'ignore' });
      
      // @2x size (if applicable)
      if (size <= 512) {
        const size2x = size * 2;
        execSync(`sips -z ${size2x} ${size2x} "${pngPath}" --out "${output2xFile}"`, { stdio: 'ignore' });
      }
    });

    // Convert iconset to icns using iconutil
    execSync(`iconutil -c icns "${iconsetPath}" -o "${outputPath}"`);
    console.log('✓ Created:', outputPath);
    
    // Clean up iconset directory
    fs.rmSync(iconsetPath, { recursive: true });
  } catch (error) {
    console.error('Error generating .icns:', error.message);
    // Clean up on error
    if (fs.existsSync(iconsetPath)) {
      fs.rmSync(iconsetPath, { recursive: true });
    }
    throw error;
  }
}

function main() {
  const buildResourcesDir = path.resolve(__dirname, '..', 'build-resources');
  const pngPath = path.join(buildResourcesDir, 'icon.png');
  const icoPath = path.join(buildResourcesDir, 'icon.ico');
  const icnsPath = path.join(buildResourcesDir, 'icon.icns');

  console.log('Icon Generation Script');
  console.log('======================\n');

  // Verify source PNG exists
  if (!fs.existsSync(pngPath)) {
    console.error('❌ Source PNG not found:', pngPath);
    process.exit(1);
  }

  console.log('Source:', pngPath);
  console.log('');

  // Generate Windows .ico
  try {
    generateWindowsIco(pngPath, icoPath);
  } catch (error) {
    console.error('❌ Failed to generate Windows .ico:', error.message);
    process.exit(1);
  }

  // Generate macOS .icns (only on macOS or skip with warning)
  try {
    generateMacOsIcns(pngPath, icnsPath);
  } catch (error) {
    console.error('❌ Failed to generate macOS .icns:', error.message);
    console.log('');
    console.log('Note: .icns generation requires macOS with sips and iconutil');
    console.log('      electron-builder can auto-generate from icon.png on macOS builds');
  }

  console.log('');
  console.log('✓ Icon generation complete');
}

main();
