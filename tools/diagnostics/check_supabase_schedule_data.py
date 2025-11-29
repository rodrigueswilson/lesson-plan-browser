"""Check Supabase for schedule entries and W47 plan data."""

import os
from backend.config import Settings
from supabase import create_client

settings = Settings()

print("=" * 60)
print("Checking Supabase for Schedule and Plan Data")
print("=" * 60)

print(f"\nUSE_SUPABASE: {settings.USE_SUPABASE}")
print(f"SUPABASE_PROJECT: {settings.SUPABASE_PROJECT}")

if not settings.USE_SUPABASE:
    print("\nSupabase is not enabled. Checking if credentials are available...")
    
    if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
        print("\nProject 1 credentials found. Checking Project 1...")
        try:
            client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
            
            # Check schedule entries
            schedules_response = client1.table("schedules").select("*").execute()
            print(f"\nProject 1 - Schedule entries: {len(schedules_response.data)}")
            if schedules_response.data:
                wilson_schedules = [s for s in schedules_response.data if '04fe8898' in s.get('user_id', '')]
                print(f"  Wilson schedules: {len(wilson_schedules)}")
                if wilson_schedules:
                    for s in wilson_schedules[:5]:
                        print(f"    {s.get('day_of_week')} {s.get('start_time')}-{s.get('end_time')}: {s.get('subject')} {s.get('grade')} {s.get('homeroom')}")
            
            # Check W47 plans
            plans_response = client1.table("weekly_plans").select("*").eq("week_of", "11-17-11-21").execute()
            print(f"\nProject 1 - W47 plans: {len(plans_response.data)}")
            if plans_response.data:
                for p in plans_response.data:
                    print(f"  ID: {p.get('id')}")
                    print(f"  User: {p.get('user_id')}")
                    print(f"  Status: {p.get('status')}")
                    print(f"  Has lesson_json: {p.get('lesson_json') is not None}")
        except Exception as e:
            print(f"Error checking Project 1: {e}")
    
    if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
        print("\nProject 2 credentials found. Checking Project 2...")
        try:
            client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
            
            # Check schedule entries
            schedules_response = client2.table("schedules").select("*").execute()
            print(f"\nProject 2 - Schedule entries: {len(schedules_response.data)}")
            if schedules_response.data:
                wilson_schedules = [s for s in schedules_response.data if '04fe8898' in s.get('user_id', '')]
                print(f"  Wilson schedules: {len(wilson_schedules)}")
                if wilson_schedules:
                    for s in wilson_schedules[:5]:
                        print(f"    {s.get('day_of_week')} {s.get('start_time')}-{s.get('end_time')}: {s.get('subject')} {s.get('grade')} {s.get('homeroom')}")
            
            # Check W47 plans
            plans_response = client2.table("weekly_plans").select("*").eq("week_of", "11-17-11-21").execute()
            print(f"\nProject 2 - W47 plans: {len(plans_response.data)}")
            if plans_response.data:
                for p in plans_response.data:
                    print(f"  ID: {p.get('id')}")
                    print(f"  User: {p.get('user_id')}")
                    print(f"  Status: {p.get('status')}")
                    print(f"  Has lesson_json: {p.get('lesson_json') is not None}")
        except Exception as e:
            print(f"Error checking Project 2: {e}")
else:
    print("\nSupabase is enabled. Checking active project...")
    try:
        supabase_url = settings.supabase_url
        supabase_key = settings.supabase_key
        
        if not supabase_url or not supabase_key:
            print("ERROR: Supabase credentials not configured for active project")
        else:
            client = create_client(supabase_url, supabase_key)
            
            # Check schedule entries
            schedules_response = client.table("schedules").select("*").execute()
            print(f"\nSchedule entries: {len(schedules_response.data)}")
            if schedules_response.data:
                wilson_schedules = [s for s in schedules_response.data if '04fe8898' in s.get('user_id', '')]
                print(f"  Wilson schedules: {len(wilson_schedules)}")
                if wilson_schedules:
                    for s in wilson_schedules[:5]:
                        print(f"    {s.get('day_of_week')} {s.get('start_time')}-{s.get('end_time')}: {s.get('subject')} {s.get('grade')} {s.get('homeroom')}")
            
            # Check W47 plans
            plans_response = client.table("weekly_plans").select("*").eq("week_of", "11-17-11-21").execute()
            print(f"\nW47 plans: {len(plans_response.data)}")
            if plans_response.data:
                for p in plans_response.data:
                    print(f"  ID: {p.get('id')}")
                    print(f"  User: {p.get('user_id')}")
                    print(f"  Status: {p.get('status')}")
                    print(f"  Has lesson_json: {p.get('lesson_json') is not None}")
    except Exception as e:
        print(f"Error checking Supabase: {e}")

print("\n" + "=" * 60)

