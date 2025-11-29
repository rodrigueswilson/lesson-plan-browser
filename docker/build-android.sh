#!/bin/bash

# Docker Android Build Script
# Bypasses local Tauri caching issues

set -e

echo "🐳 Starting Docker Android build..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker/Dockerfile.android" ]; then
    echo "❌ Please run this script from the LP root directory"
    exit 1
fi

# Build the Docker image first
echo "📦 Building Docker image..."
docker-compose build android-builder

# Run the build
echo "🔨 Building Android APK in Docker..."
docker-compose up --build android-builder

echo "✅ Docker build complete!"
echo ""
echo "📱 APK location: docker-generated APK will be in the container"
echo "🔍 To extract APK: docker cp tauri-android-builder:/app/frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk ./app-arm64-debug.apk"
