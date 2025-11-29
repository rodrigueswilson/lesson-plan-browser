#!/bin/bash
# Script to bundle Python sidecar for Android
# Usage: ./bundle_sidecar.sh [pyinstaller|nuitka|docker]

set -e

BUNDLER=${1:-pyinstaller}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
OUTPUT_DIR="$SCRIPT_DIR/frontend/src-tauri/binaries"

echo "=== Python Sidecar Bundling ==="
echo "Bundler: $BUNDLER"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

case "$BUNDLER" in
    pyinstaller)
        echo "Using PyInstaller..."
        cd "$BACKEND_DIR"
        
        pyinstaller --onefile \
            --name python-sync-processor \
            --hidden-import=backend.ipc_database \
            --hidden-import=backend.supabase_database \
            --hidden-import=backend.schema \
            --hidden-import=backend.config \
            --hidden-import=backend.database_interface \
            --hidden-import=supabase \
            --hidden-import=postgrest \
            --hidden-import=pydantic \
            --collect-all=supabase \
            --collect-all=postgrest \
            sidecar_main.py
        
        # Move to binaries directory
        if [ -f "dist/python-sync-processor" ]; then
            mv dist/python-sync-processor "$OUTPUT_DIR/python-sync-processor-$(uname -m)-linux"
            echo "✓ Binary created: $OUTPUT_DIR/python-sync-processor-$(uname -m)-linux"
        else
            echo "✗ Build failed - binary not found"
            exit 1
        fi
        ;;
    
    nuitka)
        echo "Using Nuitka..."
        cd "$BACKEND_DIR"
        
        python -m nuitka \
            --standalone \
            --onefile \
            --include-module=backend \
            --include-module=backend.sidecar_main \
            --include-module=backend.ipc_database \
            --include-module=backend.supabase_database \
            --include-module=backend.schema \
            --include-module=backend.config \
            --include-module=backend.database_interface \
            --output-filename=python-sync-processor \
            --assume-yes-for-downloads \
            sidecar_main.py
        
        # Move to binaries directory
        if [ -f "python-sync-processor" ]; then
            mv python-sync-processor "$OUTPUT_DIR/python-sync-processor-$(uname -m)-linux"
            echo "✓ Binary created: $OUTPUT_DIR/python-sync-processor-$(uname -m)-linux"
        else
            echo "✗ Build failed - binary not found"
            exit 1
        fi
        ;;
    
    docker)
        echo "Using Docker for cross-compilation..."
        
        # Build Docker image
        docker build -f Dockerfile.android-python -t python-android-build .
        
        # Extract binary from container
        CONTAINER_ID=$(docker create python-android-build)
        docker cp "$CONTAINER_ID:/app/python-sync-processor" "$OUTPUT_DIR/python-sync-processor-aarch64-linux-android"
        docker rm "$CONTAINER_ID"
        
        echo "✓ Binary created: $OUTPUT_DIR/python-sync-processor-aarch64-linux-android"
        ;;
    
    *)
        echo "Unknown bundler: $BUNDLER"
        echo "Usage: $0 [pyinstaller|nuitka|docker]"
        exit 1
        ;;
esac

echo ""
echo "=== Bundle Complete ==="
echo "Binary location: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/python-sync-processor* 2>/dev/null || echo "No binaries found"

