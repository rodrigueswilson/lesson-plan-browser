#!/usr/bin/env python3
"""
Force sync script - Always re-syncs plans even if they exist locally.
This is a wrapper around sync_browser_plans_to_tablet_db.py with --include-existing.
"""

import subprocess
import sys
from pathlib import Path

# Get the original script path
script_dir = Path(__file__).parent
original_script = script_dir / "sync_browser_plans_to_tablet_db.py"

# Build command with --include-existing flag
cmd = [sys.executable, str(original_script), "--include-existing"] + sys.argv[1:]

print("Running sync with --include-existing flag to force re-sync...")
print(f"Command: {' '.join(cmd)}")
print()

# Run the original script
result = subprocess.run(cmd)
sys.exit(result.returncode)

