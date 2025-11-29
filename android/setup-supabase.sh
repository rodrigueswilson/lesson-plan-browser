#!/bin/bash
# Supabase Configuration Setup Script for Linux/Mac
# This script helps you set up your Supabase credentials

echo "=== Supabase Configuration Setup ==="
echo ""

# Check if local.properties already exists
if [ -f "local.properties" ]; then
    echo "⚠️  local.properties already exists!"
    read -p "Do you want to overwrite it? (y/N) " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Copy example file
if [ -f "local.properties.example" ]; then
    cp local.properties.example local.properties
    echo "✅ Created local.properties from example"
else
    echo "❌ local.properties.example not found!"
    exit 1
fi

echo ""
echo "Please enter your Supabase credentials:"
echo ""

# Get Project 1 credentials
echo "--- Project 1 (Wilson Rodrigues) ---"
read -p "Project 1 URL (e.g., https://xxxxx.supabase.co): " url1
read -p "Project 1 anon key: " key1

echo ""
echo "--- Project 2 (Daniela Silva) ---"
read -p "Project 2 URL (e.g., https://xxxxx.supabase.co): " url2
read -p "Project 2 anon key: " key2

# Update local.properties
cat > local.properties << EOF
# Supabase Configuration
# Project 1 (Wilson Rodrigues)
SUPABASE_URL_PROJECT1=$url1
SUPABASE_KEY_PROJECT1=$key1

# Project 2 (Daniela Silva)
SUPABASE_URL_PROJECT2=$url2
SUPABASE_KEY_PROJECT2=$key2
EOF

echo ""
echo "✅ Configuration saved to local.properties"
echo ""
echo "Next steps:"
echo "1. Review local.properties to verify your credentials"
echo "2. Run: ./gradlew clean build"
echo "3. Test the app on a device or emulator"
echo ""

