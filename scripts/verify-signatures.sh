#!/bin/bash

# Verify installer signatures for all platforms
# Requirement: Code-signed installers for macOS (notarized), Windows (Authenticode), Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Installer Signature Verification"
echo "======================================"
echo ""

# Track overall status
OVERALL_STATUS=0

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to verify macOS installer
verify_macos() {
    echo "Checking macOS installer..."

    local DMG_FILE="$DIST_DIR/Ideal-Goggles-*.dmg"
    local APP_FILE="$DIST_DIR/mac/Ideal Goggles.app"

    # Check if DMG exists
    if ls $DMG_FILE 1> /dev/null 2>&1; then
        DMG_PATH=$(ls $DMG_FILE | head -n1)
        echo "Found DMG: $(basename "$DMG_PATH")"

        # Verify DMG signature
        if command_exists codesign; then
            echo -n "  Checking DMG signature... "
            if codesign --verify --deep --strict --verbose=2 "$DMG_PATH" 2>&1 | grep -q "valid on disk"; then
                echo -e "${GREEN}✓ Valid${NC}"
            else
                echo -e "${RED}✗ Invalid or unsigned${NC}"
                OVERALL_STATUS=1
            fi
        else
            echo -e "${YELLOW}  ⚠ codesign not available (not on macOS)${NC}"
        fi

        # Check notarization
        if command_exists spctl; then
            echo -n "  Checking notarization... "
            if spctl -a -t open --context context:primary-signature -v "$DMG_PATH" 2>&1 | grep -q "accepted"; then
                echo -e "${GREEN}✓ Notarized${NC}"
            else
                echo -e "${YELLOW}⚠ Not notarized${NC}"
            fi
        fi

        # Mount DMG and check app bundle
        if command_exists hdiutil; then
            echo "  Mounting DMG to verify app bundle..."
            MOUNT_POINT=$(hdiutil attach "$DMG_PATH" -nobrowse -noautoopen | grep Volumes | awk '{print $3}')

            if [ -n "$MOUNT_POINT" ]; then
                APP_IN_DMG="$MOUNT_POINT/Ideal Goggles.app"

                if [ -d "$APP_IN_DMG" ]; then
                    echo -n "  Checking app signature... "
                    if codesign --verify --deep --strict "$APP_IN_DMG" 2>&1 | grep -q "satisfies its Designated Requirement"; then
                        echo -e "${GREEN}✓ Valid${NC}"
                    else
                        echo -e "${RED}✗ Invalid${NC}"
                        OVERALL_STATUS=1
                    fi

                    # Check entitlements
                    echo "  Checking entitlements..."
                    codesign -d --entitlements - "$APP_IN_DMG" 2>/dev/null | head -20
                fi

                # Unmount
                hdiutil detach "$MOUNT_POINT" -quiet
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠ No macOS DMG found${NC}"
    fi

    # Check standalone app if exists
    if [ -d "$APP_FILE" ]; then
        echo "  Checking standalone app bundle..."
        if command_exists codesign; then
            codesign --verify --deep --strict --verbose=2 "$APP_FILE"
        fi
    fi

    echo ""
}

# Function to verify Windows installer
verify_windows() {
    echo "Checking Windows installer..."

    local EXE_FILE="$DIST_DIR/Ideal-Goggles-Setup-*.exe"
    local MSI_FILE="$DIST_DIR/Ideal-Goggles-*.msi"

    # Check for EXE installer
    if ls $EXE_FILE 1> /dev/null 2>&1; then
        EXE_PATH=$(ls $EXE_FILE | head -n1)
        echo "Found EXE: $(basename "$EXE_PATH")"

        # Check with signtool (if available via Wine or on Windows)
        if command_exists signtool; then
            echo -n "  Checking Authenticode signature... "
            if signtool verify /pa "$EXE_PATH" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Valid${NC}"
            else
                echo -e "${RED}✗ Invalid or unsigned${NC}"
                OVERALL_STATUS=1
            fi
        elif command_exists osslsigncode; then
            echo -n "  Checking signature with osslsigncode... "
            if osslsigncode verify "$EXE_PATH" 2>&1 | grep -q "Signature verification: ok"; then
                echo -e "${GREEN}✓ Valid${NC}"
            else
                echo -e "${RED}✗ Invalid or unsigned${NC}"
                OVERALL_STATUS=1
            fi
        else
            # Use basic PE header check
            echo "  Performing basic PE signature check..."
            if command_exists file; then
                FILE_INFO=$(file "$EXE_PATH")
                if echo "$FILE_INFO" | grep -q "PE32"; then
                    echo -e "${GREEN}  ✓ Valid PE executable${NC}"

                    # Check for signature block in PE
                    if command_exists hexdump; then
                        if hexdump -C "$EXE_PATH" | grep -q "Microsoft"; then
                            echo -e "${YELLOW}  ⚠ Contains Microsoft headers (may be signed)${NC}"
                        fi
                    fi
                else
                    echo -e "${RED}  ✗ Invalid PE format${NC}"
                    OVERALL_STATUS=1
                fi
            fi
        fi

        # Check certificate details if possible
        if command_exists openssl; then
            echo "  Extracting certificate info (if signed)..."
            # Try to extract PKCS7 signature
            dd if="$EXE_PATH" bs=1 skip=$(($(stat -f%z "$EXE_PATH" 2>/dev/null || stat -c%s "$EXE_PATH") - 10000)) 2>/dev/null | \
                openssl pkcs7 -inform DER -print_certs -noout 2>/dev/null && \
                echo -e "${GREEN}  ✓ Certificate found${NC}" || \
                echo -e "${YELLOW}  ⚠ No certificate extracted${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ No Windows EXE installer found${NC}"
    fi

    # Check for MSI installer
    if ls $MSI_FILE 1> /dev/null 2>&1; then
        MSI_PATH=$(ls $MSI_FILE | head -n1)
        echo "Found MSI: $(basename "$MSI_PATH")"

        # MSI signature check
        if command_exists msiinfo; then
            echo "  Checking MSI properties..."
            msiinfo suminfo "$MSI_PATH" 2>/dev/null | grep -E "Author|Subject|Comments"
        fi
    fi

    echo ""
}

# Function to verify Linux installer
verify_linux() {
    echo "Checking Linux installers..."

    local DEB_FILE="$DIST_DIR/ideal-goggles_*_amd64.deb"
    local RPM_FILE="$DIST_DIR/ideal-goggles-*.x86_64.rpm"
    local APPIMAGE_FILE="$DIST_DIR/Ideal-Goggles-*.AppImage"
    local SNAP_FILE="$DIST_DIR/ideal-goggles_*.snap"

    # Check DEB package
    if ls $DEB_FILE 1> /dev/null 2>&1; then
        DEB_PATH=$(ls $DEB_FILE | head -n1)
        echo "Found DEB: $(basename "$DEB_PATH")"

        if command_exists dpkg-sig; then
            echo -n "  Checking DEB signature... "
            if dpkg-sig --verify "$DEB_PATH" 2>&1 | grep -q "GOODSIG"; then
                echo -e "${GREEN}✓ Valid${NC}"
            else
                echo -e "${YELLOW}⚠ Unsigned${NC}"
            fi
        else
            echo "  Using dpkg to verify package integrity..."
            if command_exists dpkg; then
                dpkg -I "$DEB_PATH" > /dev/null 2>&1 && \
                    echo -e "${GREEN}  ✓ Package structure valid${NC}" || \
                    echo -e "${RED}  ✗ Invalid package${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠ No DEB package found${NC}"
    fi

    # Check RPM package
    if ls $RPM_FILE 1> /dev/null 2>&1; then
        RPM_PATH=$(ls $RPM_FILE | head -n1)
        echo "Found RPM: $(basename "$RPM_PATH")"

        if command_exists rpm; then
            echo -n "  Checking RPM signature... "
            if rpm --checksig "$RPM_PATH" 2>&1 | grep -q "OK"; then
                echo -e "${GREEN}✓ Valid${NC}"
            else
                echo -e "${YELLOW}⚠ Unsigned or invalid${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠ No RPM package found${NC}"
    fi

    # Check AppImage
    if ls $APPIMAGE_FILE 1> /dev/null 2>&1; then
        APPIMAGE_PATH=$(ls $APPIMAGE_FILE | head -n1)
        echo "Found AppImage: $(basename "$APPIMAGE_PATH")"

        # Check if AppImage is signed
        if command_exists appimagetool; then
            echo -n "  Checking AppImage signature... "
            # AppImages can be signed with GPG
            if gpg --verify "$APPIMAGE_PATH.sig" "$APPIMAGE_PATH" 2>/dev/null; then
                echo -e "${GREEN}✓ Valid GPG signature${NC}"
            else
                echo -e "${YELLOW}⚠ No GPG signature${NC}"
            fi
        fi

        # Verify AppImage is executable
        if [ -x "$APPIMAGE_PATH" ]; then
            echo -e "${GREEN}  ✓ Executable flag set${NC}"
        else
            echo -e "${RED}  ✗ Not executable${NC}"
            OVERALL_STATUS=1
        fi
    else
        echo -e "${YELLOW}  ⚠ No AppImage found${NC}"
    fi

    # Check Snap package
    if ls $SNAP_FILE 1> /dev/null 2>&1; then
        SNAP_PATH=$(ls $SNAP_FILE | head -n1)
        echo "Found Snap: $(basename "$SNAP_PATH")"

        if command_exists snap; then
            echo "  Snap packages are automatically signed by Snapcraft"
            # Verify snap structure
            if command_exists unsquashfs; then
                echo -n "  Checking snap integrity... "
                if unsquashfs -l "$SNAP_PATH" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Valid${NC}"
                else
                    echo -e "${RED}✗ Corrupted${NC}"
                    OVERALL_STATUS=1
                fi
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠ No Snap package found${NC}"
    fi

    echo ""
}

# Function to check installer file sizes
check_sizes() {
    echo "Checking installer sizes..."
    echo ""

    if [ -d "$DIST_DIR" ]; then
        echo "Installer sizes:"

        # Find all installer files
        find "$DIST_DIR" -maxdepth 1 \( \
            -name "*.dmg" -o \
            -name "*.exe" -o \
            -name "*.msi" -o \
            -name "*.deb" -o \
            -name "*.rpm" -o \
            -name "*.AppImage" -o \
            -name "*.snap" \
        \) -exec ls -lh {} \; | awk '{print "  " $9 ": " $5}'

        echo ""

        # Check against size requirement (<150MB compressed)
        for installer in "$DIST_DIR"/*.{dmg,exe,msi,deb,rpm,AppImage,snap} 2>/dev/null; do
            if [ -f "$installer" ]; then
                SIZE=$(du -m "$installer" | cut -f1)
                if [ "$SIZE" -gt 150 ]; then
                    echo -e "${YELLOW}⚠ $(basename "$installer") is ${SIZE}MB (exceeds 150MB limit)${NC}"
                    OVERALL_STATUS=1
                fi
            fi
        done
    else
        echo -e "${RED}✗ Distribution directory not found${NC}"
        OVERALL_STATUS=1
    fi

    echo ""
}

# Function to verify auto-update configuration
check_auto_update() {
    echo "Checking auto-update configuration..."

    # Check package.json for update configuration
    if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
        echo "  Checking package.json configuration..."

        if grep -q '"publish"' "$PROJECT_ROOT/frontend/package.json"; then
            echo -e "${GREEN}  ✓ Publish configuration found${NC}"

            # Extract publish config
            node -e "
                const pkg = require('$PROJECT_ROOT/frontend/package.json');
                if (pkg.build && pkg.build.publish) {
                    console.log('  Provider:', pkg.build.publish.provider || 'Not set');
                    console.log('  URL:', pkg.build.publish.url || pkg.build.publish.repo || 'Not set');
                }
            " 2>/dev/null
        else
            echo -e "${YELLOW}  ⚠ No publish configuration for auto-update${NC}"
        fi
    fi

    # Check for update manifest files
    echo "  Checking for update manifests..."
    for manifest in latest.yml latest-mac.yml latest-linux.yml; do
        if [ -f "$DIST_DIR/$manifest" ]; then
            echo -e "${GREEN}  ✓ Found $manifest${NC}"
        fi
    done

    echo ""
}

# Main execution
main() {
    echo "Project root: $PROJECT_ROOT"
    echo "Distribution directory: $DIST_DIR"
    echo ""

    # Check if dist directory exists
    if [ ! -d "$DIST_DIR" ]; then
        echo -e "${RED}✗ Distribution directory not found!${NC}"
        echo "Please build the installers first with: pnpm run build:installers"
        exit 1
    fi

    # Detect platform and run appropriate checks
    case "$(uname -s)" in
        Darwin)
            echo "Running on macOS"
            echo ""
            verify_macos
            verify_windows  # Can partially check
            verify_linux    # Can partially check
            ;;
        Linux)
            echo "Running on Linux"
            echo ""
            verify_linux
            verify_windows  # Can partially check
            verify_macos    # Can partially check
            ;;
        MINGW*|CYGWIN*|MSYS*)
            echo "Running on Windows"
            echo ""
            verify_windows
            verify_macos    # Can partially check
            verify_linux    # Can partially check
            ;;
        *)
            echo -e "${YELLOW}Unknown platform: $(uname -s)${NC}"
            echo "Running basic checks..."
            echo ""
            ;;
    esac

    # Common checks
    check_sizes
    check_auto_update

    # Summary
    echo "======================================"
    if [ $OVERALL_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ Signature verification completed successfully${NC}"
    else
        echo -e "${RED}✗ Some verification checks failed${NC}"
        echo ""
        echo "To sign installers:"
        echo "  macOS: Configure codesigning in electron-builder with Developer ID"
        echo "  Windows: Use signtool with an Authenticode certificate"
        echo "  Linux: Sign with GPG for DEB/RPM packages"
    fi
    echo "======================================"

    exit $OVERALL_STATUS
}

# Run main function
main "$@"