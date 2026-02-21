
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from backend.maintenance import DatabaseMaintenance, run_maintenance

def main():
    parser = argparse.ArgumentParser(description="Database Maintenance Utility")
    parser.add_argument("--backup", action="store_true", help="Create a backup only")
    parser.add_argument("--cleanup", action="store_true", help="Run full cleanup (backup + user cleanup + plan pruning)")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned up without doing it (not fully implemented in core yet)")

    args = parser.parse_args()

    m = DatabaseMaintenance()

    if args.stats:
        stats = m.get_stats()
        print("\n=== Database Statistics ===")
        print(f"File: {m.db_path}")
        print(f"Size: {stats['db_size_kb']} KB")
        print(f"Users: {stats['total_users']}")
        print(f"Total Plans: {stats['total_plans']}")
        print(f"Completed Plans: {stats['completed_plans']}")
        print(f"Last Backup: {stats['last_backup']}")
        print("==========================\n")

    if args.backup:
        path = m.create_backup()
        print(f"✓ Backup created at: {path}")

    if args.cleanup:
        print("Starting maintenance...")
        results = run_maintenance()
        print("✓ Maintenance complete!")
        print(f"  - Backup: {results['backup_file']}")
        print(f"  - Users deleted: {results['users_deleted']}")
        print(f"  - Redundant plans deleted: {results['redundant_plans_deleted']}")
        print(f"  - Failed plans deleted: {results['failed_plans_deleted']}")
        
    if not (args.stats or args.backup or args.cleanup):
        parser.print_help()

if __name__ == "__main__":
    main()
