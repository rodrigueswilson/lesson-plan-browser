#!/bin/bash
# Docker-based Python Bundling for Android
# Cross-compiles Python executable for Linux ARM64

set -e

echo "=== Python Sidecar Bundling (Docker) ==="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required for cross-compilation"
    exit 1
fi

# Create Dockerfile for bundling
cat > Dockerfile.bundle << 'EOF'
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install PyInstaller
RUN pip install pyinstaller

WORKDIR /app

# Copy project files
COPY backend/ /app/backend/
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Build executable
RUN pyinstaller \
    --onefile \
    --name python-sync-processor \
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

# Output will be in /app/dist/python-sync-processor
EOF

# Build Docker image
echo "Building Docker image..."
docker build -f Dockerfile.bundle -t python-bundler .

# Create output directory
OUTPUT_DIR="frontend/src-tauri/binaries"
mkdir -p "$OUTPUT_DIR"

# Extract binary from container
echo "Extracting binary..."
docker create --name temp-container python-bundler
docker cp temp-container:/app/dist/python-sync-processor "$OUTPUT_DIR/python-sync-processor-aarch64-linux-android"
docker rm temp-container

# Clean up
rm -f Dockerfile.bundle

echo "✅ Binary created: $OUTPUT_DIR/python-sync-processor-aarch64-linux-android"

