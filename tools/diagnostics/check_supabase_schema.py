"""
Check the actual schema of weekly_plans table in Supabase.
"""

from backend.config import Settings
from supabase import create_client

settings = Settings()

print("=" * 60)
print("Checking Supabase Schema for weekly_plans table")
print("=" * 60)

# Check Project 2 (where Wilson is)
print("\n[Project 2 - Checking weekly_plans schema]")
try:
    client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
    
    # Try to get column info by querying information_schema
    # Note: This might require service role key, so we'll try a different approach
    
    # Try to insert a test value to see what happens
    print("Attempting to check column type by examining existing data...")
    
    # Get a sample plan if it exists
    response = client2.table("weekly_plans").select("id, consolidated, total_slots").limit(1).execute()
    
    if response.data:
        plan = response.data[0]
        print(f"\nSample plan found:")
        print(f"  ID: {plan['id']}")
        print(f"  consolidated value: {plan.get('consolidated')} (type: {type(plan.get('consolidated')).__name__})")
        print(f"  total_slots value: {plan.get('total_slots')} (type: {type(plan.get('total_slots')).__name__})")
    else:
        print("No plans found to examine")
    
    # Try to get table structure via SQL (if we have service role)
    if settings.SUPABASE_SERVICE_ROLE_KEY_PROJECT2:
        print("\nChecking table structure via SQL...")
        try:
            # Use service role client for admin queries
            admin_client = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_SERVICE_ROLE_KEY_PROJECT2)
            # Note: Supabase Python client doesn't directly support raw SQL
            # We'd need to use the REST API or check via dashboard
            print("(SQL queries require REST API calls)")
        except Exception as e:
            print(f"Could not check via SQL: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Recommendation:")
print("=" * 60)
print("Check the Supabase dashboard:")
print("1. Go to Table Editor > weekly_plans")
print("2. Check the 'consolidated' column type")
print("3. It should be INTEGER, not BOOLEAN or TEXT")
print("4. If it's wrong, run: ALTER TABLE weekly_plans ALTER COLUMN consolidated TYPE INTEGER")

