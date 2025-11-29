"""
Migration: Add structured name fields to users and class_slots tables.

This migration adds first_name/last_name columns for better name management
and consistent formatting in lesson plan outputs.

Run with: python -m backend.migrations.add_structured_names [--dry-run]
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import Database


class StructuredNamesMigration:
    """Migration to add structured name fields."""
    
    def __init__(self, db: Database, dry_run: bool = False):
        self.db = db
        self.dry_run = dry_run
        self.warnings: List[str] = []
    
    def check_columns_exist(self) -> Dict[str, bool]:
        """Check which new columns already exist."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check users table
            cursor.execute("PRAGMA table_info(users)")
            user_columns = {row[1] for row in cursor.fetchall()}
            
            # Check class_slots table
            cursor.execute("PRAGMA table_info(class_slots)")
            slot_columns = {row[1] for row in cursor.fetchall()}
            
            return {
                'users.first_name': 'first_name' in user_columns,
                'users.last_name': 'last_name' in user_columns,
                'class_slots.primary_teacher_first_name': 'primary_teacher_first_name' in slot_columns,
                'class_slots.primary_teacher_last_name': 'primary_teacher_last_name' in slot_columns,
            }
    
    def add_columns(self):
        """Add new columns to tables."""
        print("\n" + "="*80)
        print("STEP 1: Adding new columns")
        print("="*80)
        
        existing = self.check_columns_exist()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Add columns to users table
            if not existing['users.first_name']:
                sql = "ALTER TABLE users ADD COLUMN first_name TEXT"
                print(f"  {'[DRY RUN] ' if self.dry_run else ''}Adding users.first_name")
                if not self.dry_run:
                    cursor.execute(sql)
            else:
                print("  ✓ users.first_name already exists")
            
            if not existing['users.last_name']:
                sql = "ALTER TABLE users ADD COLUMN last_name TEXT"
                print(f"  {'[DRY RUN] ' if self.dry_run else ''}Adding users.last_name")
                if not self.dry_run:
                    cursor.execute(sql)
            else:
                print("  ✓ users.last_name already exists")
            
            # Add columns to class_slots table
            if not existing['class_slots.primary_teacher_first_name']:
                sql = "ALTER TABLE class_slots ADD COLUMN primary_teacher_first_name TEXT"
                print(f"  {'[DRY RUN] ' if self.dry_run else ''}Adding class_slots.primary_teacher_first_name")
                if not self.dry_run:
                    cursor.execute(sql)
            else:
                print("  ✓ class_slots.primary_teacher_first_name already exists")
            
            if not existing['class_slots.primary_teacher_last_name']:
                sql = "ALTER TABLE class_slots ADD COLUMN primary_teacher_last_name TEXT"
                print(f"  {'[DRY RUN] ' if self.dry_run else ''}Adding class_slots.primary_teacher_last_name")
                if not self.dry_run:
                    cursor.execute(sql)
            else:
                print("  ✓ class_slots.primary_teacher_last_name already exists")
        
        print("\n✅ Column addition complete")
    
    def split_name(self, name: str) -> Tuple[str, str, bool]:
        """
        Split a full name into first and last name.
        
        Returns:
            (first_name, last_name, needs_review)
        """
        if not name or not name.strip():
            return ("", "", True)
        
        parts = name.strip().split()
        
        if len(parts) >= 2:
            # Multiple parts - first is first name, rest is last name
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
            needs_review = False
        elif len(parts) == 1:
            # Single part - assume it's first name, flag for review
            first_name = parts[0]
            last_name = ""
            needs_review = True
        else:
            # Empty or whitespace only
            first_name = ""
            last_name = ""
            needs_review = True
        
        return (first_name, last_name, needs_review)
    
    def migrate_user_names(self):
        """Split existing user names into first/last."""
        print("\n" + "="*80)
        print("STEP 2: Migrating user names")
        print("="*80)
        
        users = self.db.list_users()
        print(f"\nFound {len(users)} users to migrate")
        
        migrated = 0
        needs_review = 0
        
        for user in users:
            name = user.get('name', '')
            user_id = user['id']
            
            # Check if already migrated
            if user.get('first_name') and user.get('last_name'):
                print(f"  ✓ User '{name}' already migrated")
                continue
            
            first_name, last_name, review = self.split_name(name)
            
            if review:
                print(f"  ⚠️  User '{name}' → first='{first_name}', last='{last_name}' (NEEDS REVIEW)")
                self.warnings.append(f"User '{name}' (ID: {user_id}) needs manual review")
                needs_review += 1
            else:
                print(f"  ✓ User '{name}' → first='{first_name}', last='{last_name}'")
            
            if not self.dry_run:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
                        (first_name, last_name, user_id)
                    )
            
            migrated += 1
        
        print(f"\n✅ Migrated {migrated} users ({needs_review} need review)")
    
    def migrate_slot_teacher_names(self):
        """Split existing primary teacher names into first/last."""
        print("\n" + "="*80)
        print("STEP 3: Migrating slot teacher names")
        print("="*80)
        
        users = self.db.list_users()
        total_slots = 0
        migrated = 0
        needs_review = 0
        
        for user in users:
            slots = self.db.get_user_slots(user['id'])
            total_slots += len(slots)
            
            for slot in slots:
                teacher_name = slot.get('primary_teacher_name', '').strip()
                slot_id = slot['id']
                
                if not teacher_name:
                    continue
                
                # Check if already migrated
                if slot.get('primary_teacher_first_name') and slot.get('primary_teacher_last_name'):
                    print(f"  ✓ Slot {slot['slot_number']} ('{teacher_name}') already migrated")
                    continue
                
                first_name, last_name, review = self.split_name(teacher_name)
                
                # For single-word teacher names, assume it's the last name
                if review and first_name and not last_name:
                    last_name = first_name
                    first_name = ""
                    review = True
                
                if review:
                    print(f"  ⚠️  Slot {slot['slot_number']}: '{teacher_name}' → first='{first_name}', last='{last_name}' (NEEDS REVIEW)")
                    self.warnings.append(f"Slot {slot['slot_number']} teacher '{teacher_name}' (ID: {slot_id}) needs manual review")
                    needs_review += 1
                else:
                    print(f"  ✓ Slot {slot['slot_number']}: '{teacher_name}' → first='{first_name}', last='{last_name}'")
                
                if not self.dry_run:
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """UPDATE class_slots 
                               SET primary_teacher_first_name = ?, 
                                   primary_teacher_last_name = ? 
                               WHERE id = ?""",
                            (first_name, last_name, slot_id)
                        )
                
                migrated += 1
        
        print(f"\n✅ Migrated {migrated} slots out of {total_slots} total ({needs_review} need review)")
    
    def run(self):
        """Run the complete migration."""
        print("\n" + "="*80)
        print("STRUCTURED NAMES MIGRATION")
        print("="*80)
        
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")
        
        try:
            self.add_columns()
            self.migrate_user_names()
            self.migrate_slot_teacher_names()
            
            print("\n" + "="*80)
            print("MIGRATION SUMMARY")
            print("="*80)
            
            if self.warnings:
                print(f"\n⚠️  {len(self.warnings)} items need manual review:")
                for warning in self.warnings:
                    print(f"  - {warning}")
                print("\nPlease update these records manually through the UI or database.")
            else:
                print("\n✅ All records migrated successfully with no warnings")
            
            if self.dry_run:
                print("\n⚠️  This was a DRY RUN - run without --dry-run to apply changes")
            else:
                print("\n✅ Migration complete!")
            
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Add structured name fields to database")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run migration without making changes (preview mode)'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Path to database file (defaults to settings.DATABASE_URL)'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    if args.db_path:
        db = Database(db_path=args.db_path)
    else:
        db = Database()
    
    print(f"\nDatabase: {db.db_path}")
    
    # Create backup recommendation
    if not args.dry_run:
        print("\n" + "="*80)
        print("⚠️  IMPORTANT: Backup your database before proceeding!")
        print("="*80)
        print(f"\nRecommended command:")
        print(f"  cp {db.db_path} {db.db_path}.backup")
        print()
        response = input("Have you backed up your database? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("\n❌ Migration cancelled. Please backup your database first.")
            return 1
    
    # Run migration
    migration = StructuredNamesMigration(db, dry_run=args.dry_run)
    success = migration.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
