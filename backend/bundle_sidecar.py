#!/usr/bin/env python3
"""
Helper script to bundle Python sidecar for Android.
This script analyzes dependencies and creates the bundle configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def get_sidecar_dependencies():
    """Extract dependencies needed by sidecar_main.py"""
    # Core dependencies for sidecar
    core_deps = [
        'supabase>=2.0.0',
        'postgrest>=0.13.0',
        'pydantic>=2.9.0',
        'python-dotenv==1.0.0',
    ]
    
    # Modules to include
    modules = [
        'backend',
        'backend.sidecar_main',
        'backend.ipc_database',
        'backend.supabase_database',
        'backend.schema',
        'backend.config',
        'backend.database_interface',
    ]
    
    return core_deps, modules

def check_bundler_installed(bundler='pyinstaller'):
    """Check if bundler is installed"""
    try:
        if bundler == 'pyinstaller':
            subprocess.run(['pyinstaller', '--version'], 
                         capture_output=True, check=True)
            return True
        elif bundler == 'nuitka':
            subprocess.run(['python', '-m', 'nuitka', '--version'],
                         capture_output=True, check=True)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return False

def main():
    print("=== Python Sidecar Bundling Setup ===\n")
    
    # Check current platform
    print(f"Platform: {sys.platform}")
    print(f"Architecture: {os.uname().machine if hasattr(os, 'uname') else 'unknown'}\n")
    
    # Get dependencies
    deps, modules = get_sidecar_dependencies()
    print("Required dependencies:")
    for dep in deps:
        print(f"  - {dep}")
    print("\nModules to include:")
    for mod in modules:
        print(f"  - {mod}")
    
    # Check bundlers
    print("\n=== Bundler Availability ===")
    pyinstaller_available = check_bundler_installed('pyinstaller')
    nuitka_available = check_bundler_installed('nuitka')
    
    print(f"PyInstaller: {'[OK] Installed' if pyinstaller_available else '[X] Not installed'}")
    print(f"Nuitka: {'[OK] Installed' if nuitka_available else '[X] Not installed'}")
    
    if not pyinstaller_available and not nuitka_available:
        print("\n⚠️  No bundler found. Install one:")
        print("  pip install pyinstaller  # Easier, larger binaries")
        print("  pip install nuitka      # Smaller, faster, more complex")
        return 1
    
    print("\n=== Recommendations ===")
    if sys.platform == 'win32':
        print("Windows detected. For Android, use:")
        print("  1. Docker (recommended) - See Dockerfile.android-python")
        print("  2. WSL2 with Linux toolchain")
        print("  3. Linux VM")
    else:
        print("For Android (aarch64-linux-android):")
        if nuitka_available:
            print("  ✓ Use Nuitka for smaller binaries")
        else:
            print("  Use PyInstaller (will work but larger)")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

