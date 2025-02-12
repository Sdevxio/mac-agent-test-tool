#!/bin/bash

# Exit on any error
set -e

echo "Building FileService.app..."

# Clean previous builds
rm -rf build dist

# Install required packages
pip install -r requirements.txt

# Debug dependencies
echo "Checking installed packages..."
pip list

echo "Verifying google.protobuf module path..."
python -c "import google.protobuf; print('Protobuf path:', google.protobuf.__path__)" || echo "google.protobuf not found"

# Add verbosity for py2app build
export PY2APP_VERBOSE=3  # Verbosity level for py2app (higher values give more detail)

# Build the .app bundle
python setup.py py2app

# Copy launchd plist to Resources
cp com.macos.fileservice.plist "dist/FileService.app/Contents/Resources/"

# Ensure scripts are executable
chmod +x scripts/postinstall

# Create temporary directory for package
PKG_ROOT=$(mktemp -d)
mkdir -p "${PKG_ROOT}/Applications"
cp -R "dist/FileService.app" "${PKG_ROOT}/Applications/"

# Build the package
pkgbuild \
    --root "${PKG_ROOT}" \
    --scripts scripts \
    --identifier com.macos.fileservice \
    --version 1.0.0 \
    --install-location "/" \
    FileService.pkg

# Clean up
rm -rf "${PKG_ROOT}"

echo "Build complete! FileService.pkg has been created."
