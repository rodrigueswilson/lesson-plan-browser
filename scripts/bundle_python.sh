#!/bin/bash
# Python Bundling Script for Android
# Creates standalone executable for Tauri sidecar

set -e

echo "=== Python Sidecar Bundling ==="

# Check if we're in the project root
if [ ! -d "backend" ]; then
    echo "Error: Must run from project root"
    exit 1
fi

# Install bundling tool
echo "Installing PyInstaller..."
pip install pyinstaller

# Create output directory
OUTPUT_DIR="frontend/src-tauri/binaries"
mkdir -p "$OUTPUT_DIR"

# Build for Linux ARM64 (Android)
echo "Building Python executable..."
pyinstaller \
    --onefile \
    --name python-sync-processor \
    --distpath "$OUTPUT_DIR" \
    --workpath /tmp/pyinstaller-work \
    --clean \
    --hidden-import=backend \
    --hidden-import=backend.ipc_database \
    --hidden-import=backend.supabase_database \
    --hidden-import=backend.schema \
    --hidden-import=backend.database \
    --hidden-import=supabase \
    --hidden-import=postgrest \
    --hidden-import=storage \
    --hidden-import=realtime \
    --collect-all supabase \
    --collect-all postgrest \
    backend/sidecar_main.py

# Rename for Android target triple
if [ -f "$OUTPUT_DIR/python-sync-processor" ]; then
    mv "$OUTPUT_DIR/python-sync-processor" \
       "$OUTPUT_DIR/python-sync-processor-aarch64-linux-android"
    echo "✅ Binary created: $OUTPUT_DIR/python-sync-processor-aarch64-linux-android"
else
    echo "❌ Build failed - binary not found"
    exit 1
fi

# Clean up
rm -rf /tmp/pyinstaller-work
rm -f python-sync-processor.spec

echo "✅ Bundling complete!"

