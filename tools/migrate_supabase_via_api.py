"""
Migration script to add template_path and signature_image_path columns using Supabase REST API.
This approach uses HTTP requests to execute SQL through Supabase's Management API.
"""

import os
import sys
import requests
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings


def execute_sql_via_api(supabase_url: str, service_role_key: str, sql: str):
    """Execute SQL via Supabase Management API.
    
    Args:
        supabase_url: Supabase project URL
        service_role_key: Supabase service role key (has admin privileges)
        sql: SQL statement to execute
    
    Returns:
        Response from API
    """
    # Supabase Management API endpoint for executing SQL
    # Note: This might not work if Supabase doesn't expose this endpoint publicly
    # Alternative: Use Supabase Dashboard SQL Editor or direct PostgreSQL connection
    
    # Try the SQL execution endpoint (if available)
    api_url = f"{supabase_url}/rest/v1/rpc/exec_sql"
    
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {"query": sql}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        # If RPC endpoint doesn't exist, try alternative approach
        print(f"RPC endpoint not available: {e}")
        return None


def run_migration_via_alter_table(project: str = None):
    """Run migration by attempting to alter table through Supabase client.
    
    This is a workaround that tries to update the schema by checking if columns exist
    and providing instructions if direct execution isn't possible.
    """
    # Determine which project to use
    if project:
        original_project = settings.SUPABASE_PROJECT
        settings.SUPABASE_PROJECT = project
    
    try:
        from backend.supabase_database import SupabaseDatabase
        
        supabase_url = settings.supabase_url
        service_role_key = settings.supabase_service_role_key
        
        if not supabase_url:
            print(f"ERROR: Supabase URL not configured for {settings.SUPABASE_PROJECT}")
            return False
        
        print(f"Checking Supabase project: {settings.SUPABASE_PROJECT}")
        print(f"Supabase URL: {supabase_url}")
        
        # Try to check if columns exist by querying the users table
        db = SupabaseDatabase()
        
        # Try to get a user to test connection
        try:
            users = db.list_users()
            if users:
                # Try to access template_path or signature_image_path
                test_user = users[0]
                has_template = hasattr(test_user, 'template_path') or 'template_path' in test_user
                has_signature = hasattr(test_user, 'signature_image_path') or 'signature_image_path' in test_user
                
                print(f"\nCurrent schema status:")
                print(f"  template_path column: {'EXISTS' if has_template else 'MISSING'}")
                print(f"  signature_image_path column: {'EXISTS' if has_signature else 'MISSING'}")
                
                if has_template and has_signature:
                    print("\n✓ Both columns already exist! Migration not needed.")
                    return True
        except Exception as e:
            print(f"Could not check schema via query: {e}")
        
        # If we have service role key, try to execute SQL via API
        if service_role_key:
            print("\nAttempting to execute migration via Supabase API...")
            
            migration_file = Path(__file__).parent.parent / "sql" / "add_user_template_fields.sql"
            if migration_file.exists():
                migration_sql = migration_file.read_text()
                
                # Try executing via API
                response = execute_sql_via_api(supabase_url, service_role_key, migration_sql)
                
                if response and response.status_code == 200:
                    print("✓ Migration executed successfully via API!")
                    return True
                else:
                    print("API execution not available or failed.")
        
        # If API execution doesn't work, provide manual instructions
        print("\n" + "=" * 60)
        print("MANUAL MIGRATION REQUIRED")
        print("=" * 60)
        print("\nThe migration needs to be run manually in the Supabase Dashboard.")
        print("\nSteps:")
        print("1. Go to your Supabase project dashboard:")
        print(f"   {supabase_url.replace('/rest/v1', '')}")
        print("2. Click on 'SQL Editor' in the left sidebar")
        print("3. Click 'New query'")
        print("4. Copy and paste the following SQL:")
        print("\n" + "-" * 60)
        
        migration_file = Path(__file__).parent.parent / "sql" / "add_user_template_fields.sql"
        if migration_file.exists():
            print(migration_file.read_text())
        else:
            print("-- Migration SQL file not found")
        
        print("-" * 60)
        print("\n5. Click 'Run' to execute the migration")
        print("6. Verify the columns were added by checking the 'Table Editor'")
        print("\n" + "=" * 60)
        
        return False
        
    except Exception as e:
        print(f"\nERROR: Migration check failed: {e}")
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
        description="Check and migrate Supabase schema (adds template_path and signature_image_path columns)"
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
        help="Check migration status for both projects"
    )
    
    args = parser.parse_args()
    
    if args.both:
        print("Checking migration status for both projects...\n")
        success1 = run_migration_via_alter_table("project1")
        print("\n" + "=" * 60 + "\n")
        success2 = run_migration_via_alter_table("project2")
        success = success1 and success2
    else:
        success = run_migration_via_alter_table(args.project)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

