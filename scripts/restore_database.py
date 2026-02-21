#!/usr/bin/env python3
"""
Restore database from a backup file.
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def list_backups(backup_dir: Path) -> list[Path]:
    """List all backup files, sorted by creation time (newest first)."""
    if not backup_dir.exists():
        return []
    
    backups = sorted(
        backup_dir.glob("lesson_planner_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return backups


def restore_database(db_path: Path, backup_path: Path, dry_run: bool = False) -> None:
    """Restore database from backup."""
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_path}")
        return
    
    if not dry_run:
        # Create a backup of current database before restoring
        if db_path.exists():
            backup_dir = db_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = backup_dir / f"{db_path.stem}_before_restore_{timestamp}.db"
            shutil.copy2(db_path, current_backup)
            print(f"✓ Current database backed up to: {current_backup.name}")
        
        # Restore from backup
        shutil.copy2(backup_path, db_path)
        print(f"✓ Database restored from: {backup_path.name}")
    else:
        print(f"[DRY RUN] Would restore {db_path} from {backup_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Restore database from a backup file"
    )
    parser.add_argument(
        "--db-path",
        default="data/lesson_planner.db",
        help="Path to the SQLite database to restore",
    )
    parser.add_argument(
        "--backup-path",
        help="Path to the backup file to restore from",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore from the most recent backup",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be restored without actually restoring",
    )
    args = parser.parse_args()
    
    db_path = Path(args.db_path)
    backup_dir = db_path.parent / "backups"
    
    if args.list:
        backups = list_backups(backup_dir)
        if not backups:
            print("No backups found.")
            return
        print("Available backups (newest first):")
        for i, backup in enumerate(backups, 1):
            size = backup.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {i}. {backup.name} ({size:.1f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        return
    
    if args.latest:
        backups = list_backups(backup_dir)
        if not backups:
            print("No backups found.")
            return
        backup_path = backups[0]
    elif args.backup_path:
        backup_path = Path(args.backup_path)
    else:
        print("Error: Must specify --backup-path, --latest, or --list")
        return
    
    restore_database(db_path, backup_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

