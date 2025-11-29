"""
Migration script to add template_path and signature_image_path columns to users table in Supabase.
This script connects directly to PostgreSQL to execute DDL statements.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 is required for this migration.")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)


def get_postgres_connection_string(supabase_url: str, db_password: str = None):
    """Convert Supabase URL to PostgreSQL connection string.
    
    Args:
        supabase_url: Supabase project URL (e.g., https://xxxxx.supabase.co)
        db_password: Database password (required for direct PostgreSQL connection)
    
    Returns:
        PostgreSQL connection string
    """
    # Extract project reference from Supabase URL
    # Format: https://xxxxx.supabase.co
    parsed = urlparse(supabase_url)
    host = parsed.hostname
    
    if not host:
        raise ValueError(f"Invalid Supabase URL: {supabase_url}")
    
    # Supabase PostgreSQL connection details
    # Port 5432 is the default PostgreSQL port
    # Database name is usually 'postgres'
    # User is usually 'postgres'
    
    if not db_password:
        # Try to get from environment variable
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        if not db_password:
            raise ValueError(
                "Database password is required for direct PostgreSQL connection. "
                "Set SUPABASE_DB_PASSWORD environment variable or pass it as argument."
            )
    
    # Construct connection string
    # Format: postgresql://postgres:[password]@[host]:5432/postgres
    conn_string = f"postgresql://postgres:{db_password}@{host}:5432/postgres"
    return conn_string


def run_migration(project: str = None):
    """Run migration to add template_path and signature_image_path columns.
    
    Args:
        project: Which Supabase project to migrate ('project1' or 'project2'). 
                 If None, uses settings.SUPABASE_PROJECT
    """
    # Determine which project to use
    if project:
        original_project = settings.SUPABASE_PROJECT
        settings.SUPABASE_PROJECT = project
    
    try:
        supabase_url = settings.supabase_url
        if not supabase_url:
            print(f"ERROR: Supabase URL not configured for {settings.SUPABASE_PROJECT}")
            print("Set SUPABASE_URL_PROJECT1/2 or SUPABASE_URL environment variable")
            return False
        
        print(f"Migrating Supabase project: {settings.SUPABASE_PROJECT}")
        print(f"Supabase URL: {supabase_url}")
        
        # Get database password
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        if not db_password:
            print("\nERROR: Database password required for direct PostgreSQL connection.")
            print("Please set SUPABASE_DB_PASSWORD environment variable.")
            print("\nTo get your database password:")
            print("1. Go to your Supabase project dashboard")
            print("2. Go to Settings -> Database")
            print("3. Find the 'Connection string' section")
            print("4. Copy the password from the connection string")
            print("\nThen set it:")
            print("  set SUPABASE_DB_PASSWORD=your_password_here  (Windows)")
            print("  export SUPABASE_DB_PASSWORD=your_password_here  (Linux/Mac)")
            return False
        
        # Get connection string
        conn_string = get_postgres_connection_string(supabase_url, db_password)
        
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read migration SQL
        migration_file = Path(__file__).parent.parent / "sql" / "add_user_template_fields.sql"
        if not migration_file.exists():
            print(f"ERROR: Migration file not found: {migration_file}")
            return False
        
        migration_sql = migration_file.read_text()
        
        # Execute migration
        print("\nExecuting migration...")
        print("-" * 60)
        cursor.execute(migration_sql)
        
        # Check results
        print("\nVerifying columns were added...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('template_path', 'signature_image_path')
            ORDER BY column_name
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "=" * 60)
        if 'template_path' in columns:
            print("✓ template_path column exists")
        else:
            print("✗ template_path column NOT found")
        
        if 'signature_image_path' in columns:
            print("✓ signature_image_path column exists")
        else:
            print("✗ signature_image_path column NOT found")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
        if len(columns) == 2:
            print("\n✓ Migration completed successfully!")
            return True
        else:
            print("\n⚠ Migration completed but some columns may be missing.")
            return False
        
    except psycopg2.OperationalError as e:
        print(f"\nERROR: Could not connect to PostgreSQL database")
        print(f"Details: {e}")
        print("\nPossible issues:")
        print("1. Incorrect database password")
        print("2. Network/firewall blocking connection")
        print("3. Supabase project may not allow direct PostgreSQL connections")
        return False
    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if project:
            settings.SUPABASE_PROJECT = original_project


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate Supabase schema to add template_path and signature_image_path columns"
    )
    parser.add_argument(
        "--project",
        choices=["project1", "project2"],
        default=None,
        help="Which Supabase project to migrate (default: from settings)"
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Run migration for both projects"
    )
    
    args = parser.parse_args()
    
    if args.both:
        print("Running migration for both projects...\n")
        success1 = run_migration("project1")
        print("\n" + "=" * 60 + "\n")
        success2 = run_migration("project2")
        success = success1 and success2
    else:
        success = run_migration(args.project)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

