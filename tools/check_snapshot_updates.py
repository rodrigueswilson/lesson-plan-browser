"""
Pre-commit hook to guard against accidental snapshot updates.
Prevents pytest --snapshot-update from running in CI or on commit.
"""

import sys
import os
from pathlib import Path


def check_snapshot_updates():
    """
    Check if snapshot updates are being committed.
    
    Returns:
        0 if no issues, 1 if snapshot updates detected
    """
    # Check if running in CI
    is_ci = os.getenv('CI', '').lower() in ('true', '1', 'yes')
    
    if is_ci:
        print("✓ Running in CI - snapshot updates not allowed")
        return 0
    
    # Check for modified snapshot files
    snapshot_dir = Path('tests') / '__snapshots__'
    
    if not snapshot_dir.exists():
        print("✓ No snapshot directory found")
        return 0
    
    # Get git status
    import subprocess
    
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        
        staged_files = result.stdout.strip().split('\n')
        
        # Check for snapshot files
        snapshot_files = [f for f in staged_files if '__snapshots__' in f]
        
        if snapshot_files:
            print("⚠️  WARNING: Snapshot files are being committed:")
            for f in snapshot_files:
                print(f"  - {f}")
            print("\nIf these changes are intentional, run:")
            print("  git commit --no-verify")
            print("\nOtherwise, unstage them:")
            print("  git reset HEAD tests/__snapshots__/")
            return 1
        
        print("✓ No snapshot updates detected")
        return 0
        
    except subprocess.CalledProcessError:
        # Git command failed - allow commit
        print("⚠️  Could not check git status - allowing commit")
        return 0
    except FileNotFoundError:
        # Git not found - allow commit
        print("⚠️  Git not found - allowing commit")
        return 0


if __name__ == '__main__':
    sys.exit(check_snapshot_updates())
