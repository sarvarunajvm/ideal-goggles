#!/usr/bin/env python3
"""
Create elegant installer backgrounds for Ideal Goggles
Generates professional DMG and NSIS installer backgrounds
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import sys

# Color palette
DARK_BG = "#1a1a1a"
GRADIENT_START = "#667eea"
GRADIENT_END = "#764ba2"
ACCENT_COLOR = "#16a085"
TEXT_WHITE = "#ffffff"
TEXT_GRAY = "#cccccc"

def create_gradient(width, height, start_color, end_color):
    """Create a vertical gradient image"""
    base = Image.new('RGB', (width, height), start_color)
    top = Image.new('RGB', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_dmg_background():
    """Create elegant DMG background (600x400)"""
    print("Creating DMG background...")

    # Create base with dark background
    img = Image.new('RGB', (600, 400), hex_to_rgb(DARK_BG))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Add subtle gradient circles for depth
    circle1 = Image.new('RGBA', (600, 400), (0, 0, 0, 0))
    draw1 = ImageDraw.Draw(circle1)
    draw1.ellipse([50, 300, 250, 500], fill=(102, 126, 234, 38))  # 15% opacity

    circle2 = Image.new('RGBA', (600, 400), (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(circle2)
    draw2.ellipse([450, 0, 650, 200], fill=(118, 75, 162, 38))

    circle3 = Image.new('RGBA', (600, 400), (0, 0, 0, 0))
    draw3 = ImageDraw.Draw(circle3)
    draw3.ellipse([200, 150, 400, 350], fill=(22, 160, 133, 25))

    # Blur circles for smooth effect
    circle1 = circle1.filter(ImageFilter.GaussianBlur(40))
    circle2 = circle2.filter(ImageFilter.GaussianBlur(40))
    circle3 = circle3.filter(ImageFilter.GaussianBlur(40))

    # Composite circles
    img = Image.alpha_composite(img.convert('RGBA'), circle1).convert('RGB')
    img = Image.alpha_composite(img.convert('RGBA'), circle2).convert('RGB')
    img = Image.alpha_composite(img.convert('RGBA'), circle3).convert('RGB')

    # Convert back to RGBA for drawing
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Try to use system fonts, fall back to default
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        font_instruction = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_footer = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = font_title
        font_instruction = font_title
        font_footer = font_title

    # Draw title
    draw.text((300, 45), "Ideal Goggles", fill=(255, 255, 255, 255),
              font=font_title, anchor="mt")

    # Draw subtitle
    draw.text((300, 85), "AI-Powered Photo Search & Organization",
              fill=(255, 255, 255, 179), font=font_subtitle, anchor="mt")

    # Draw rounded rectangles for app and Applications
    # App icon area
    draw.rounded_rectangle([105, 160, 195, 250], radius=20,
                          outline=(22, 160, 133, 204), width=3)

    # Applications folder area
    draw.rounded_rectangle([405, 160, 495, 250], radius=20,
                          outline=(22, 160, 133, 204), width=3)

    # Draw arrow
    draw.line([(210, 205), (390, 205)], fill=(22, 160, 133, 230), width=3)
    # Arrow head
    draw.polygon([(375, 195), (390, 205), (375, 215)],
                 fill=(22, 160, 133, 230))

    # Draw instruction text
    draw.text((300, 285), "Drag to Applications",
              fill=(22, 160, 133, 230), font=font_instruction, anchor="mt")

    # Draw outer border
    draw.rounded_rectangle([15, 15, 585, 385], radius=25,
                          outline=(255, 255, 255, 38), width=1)

    # Draw footer text
    draw.text((300, 370), "Privacy-focused • Local-first • AI-enhanced",
              fill=(255, 255, 255, 128), font=font_footer, anchor="mt")

    return img.convert('RGB')

def create_nsis_sidebar():
    """Create elegant NSIS sidebar (164x314)"""
    print("Creating NSIS sidebar...")

    # Create gradient background
    img = create_gradient(164, 314, hex_to_rgb(GRADIENT_START), hex_to_rgb(GRADIENT_END))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Add subtle circles
    circle1 = Image.new('RGBA', (164, 314), (0, 0, 0, 0))
    draw1 = ImageDraw.Draw(circle1)
    draw1.ellipse([10, 10, 70, 70], fill=(255, 255, 255, 25))
    draw1.ellipse([94, 90, 154, 150], fill=(255, 255, 255, 25))
    draw1.ellipse([30, 210, 90, 270], fill=(255, 255, 255, 25))

    img = Image.alpha_composite(img.convert('RGBA'), circle1)
    draw = ImageDraw.Draw(img)

    # Try to use system fonts
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
        font_version = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 8)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = font_title
        font_version = font_title

    # Draw title
    draw.text((82, 100), "Ideal", fill=(255, 255, 255, 255),
              font=font_title, anchor="mt")
    draw.text((82, 125), "Goggles", fill=(255, 255, 255, 255),
              font=font_title, anchor="mt")

    # Draw subtitle
    draw.text((82, 160), "AI-Powered", fill=(255, 255, 255, 204),
              font=font_subtitle, anchor="mt")
    draw.text((82, 175), "Photo Search", fill=(255, 255, 255, 204),
              font=font_subtitle, anchor="mt")

    # Draw version
    draw.text((82, 284), "Version 1.0", fill=(255, 255, 255, 153),
              font=font_version, anchor="mt")

    # Draw border
    draw.rounded_rectangle([15, 15, 149, 299], radius=10,
                          outline=(255, 255, 255, 77), width=2)

    return img.convert('RGB')

def main():
    """Main function to create all backgrounds"""
    print("╔════════════════════════════════════════════╗")
    print("║  Creating Elegant Installer Backgrounds   ║")
    print("╚════════════════════════════════════════════╝")
    print()

    # Ensure build-resources directory exists
    os.makedirs('build-resources', exist_ok=True)

    try:
        # Create DMG background
        dmg_bg = create_dmg_background()
        dmg_bg.save('build-resources/dmg-background.png', 'PNG', quality=95)
        print("✓ Created elegant DMG background (600x400)")

        # Create NSIS sidebar
        nsis_sidebar = create_nsis_sidebar()
        nsis_sidebar.save('build-resources/installer-sidebar.bmp', 'BMP')
        print("✓ Created elegant NSIS sidebar (164x314)")

        print()
        print("╔════════════════════════════════════════════╗")
        print("║     All Backgrounds Created Successfully   ║")
        print("╚════════════════════════════════════════════╝")
        print()
        print("Generated files:")
        print("  • build-resources/dmg-background.png (macOS)")
        print("  • build-resources/installer-sidebar.bmp (Windows)")
        print()
        print("Next steps:")
        print("  1. Review backgrounds in build-resources/")
        print("  2. Run: pnpm run dist:mac")
        print()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
