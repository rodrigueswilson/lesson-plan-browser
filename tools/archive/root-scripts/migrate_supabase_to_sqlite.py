"""Migrate schedule entries and W47 plans from Supabase to SQLite."""

import os
from datetime import datetime
from backend.config import Settings
from backend.database import SQLiteDatabase
from supabase import create_client
from sqlmodel import Session, select
from backend.schema import ScheduleEntry, WeeklyPlan

settings = Settings()

print("=" * 60)
print("Migrating Schedule Entries and W47 Plans from Supabase to SQLite")
print("=" * 60)

if not settings.USE_SUPABASE:
    print("\nERROR: Supabase is not enabled. Cannot migrate.")
    print("Please enable Supabase temporarily to migrate data.")
    exit(1)

# Connect to Supabase
supabase_url = settings.supabase_url
supabase_key = settings.supabase_key

if not supabase_url or not supabase_key:
    print("\nERROR: Supabase credentials not configured")
    exit(1)

print(f"\nConnecting to Supabase: {supabase_url[:30]}...")
supabase_client = create_client(supabase_url, supabase_key)

# Connect to SQLite
print("Connecting to SQLite...")
sqlite_db = SQLiteDatabase()

target_user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
w47_week = '11-17-11-21'

# 1. Migrate Schedule Entries
print("\n" + "=" * 60)
print("Step 1: Migrating Schedule Entries")
print("=" * 60)

try:
    # Get all schedule entries for Wilson from Supabase
    schedules_response = supabase_client.table("schedules").select("*").eq("user_id", target_user_id).execute()
    supabase_schedules = schedules_response.data
    
    print(f"\nFound {len(supabase_schedules)} schedule entries in Supabase")
    
    if supabase_schedules:
        # Check existing entries in SQLite
        with Session(sqlite_db.engine) as session:
            existing_entries = list(session.exec(
                select(ScheduleEntry).where(ScheduleEntry.user_id == target_user_id)
            ))
            existing_ids = {e.id for e in existing_entries}
            print(f"Found {len(existing_entries)} existing entries in SQLite")
            
            # Migrate entries
            migrated_count = 0
            skipped_count = 0
            
            for sched_data in supabase_schedules:
                if sched_data['id'] in existing_ids:
                    skipped_count += 1
                    continue
                
                try:
                    # Parse datetime strings to datetime objects
                    created_at = sched_data.get('created_at')
                    if created_at and isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    
                    updated_at = sched_data.get('updated_at')
                    if updated_at and isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    
                    entry = ScheduleEntry(
                        id=sched_data['id'],
                        user_id=sched_data['user_id'],
                        day_of_week=sched_data['day_of_week'],
                        slot_number=sched_data['slot_number'],
                        start_time=sched_data['start_time'],
                        end_time=sched_data['end_time'],
                        subject=sched_data.get('subject'),
                        grade=sched_data.get('grade'),
                        homeroom=sched_data.get('homeroom'),
                        is_active=sched_data.get('is_active', True),
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                    session.add(entry)
                    migrated_count += 1
                except Exception as e:
                    print(f"  ERROR migrating schedule {sched_data.get('id', 'unknown')}: {e}")
            
            session.commit()
            print(f"\nMigrated {migrated_count} schedule entries")
            print(f"Skipped {skipped_count} existing entries")
    else:
        print("No schedule entries found in Supabase")
        
except Exception as e:
    print(f"ERROR migrating schedule entries: {e}")
    import traceback
    traceback.print_exc()

# 2. Migrate W47 Plans
print("\n" + "=" * 60)
print("Step 2: Migrating W47 Plans")
print("=" * 60)

try:
    # Get W47 plans from Supabase
    plans_response = supabase_client.table("weekly_plans").select("*").eq("week_of", w47_week).execute()
    supabase_plans = plans_response.data
    
    print(f"\nFound {len(supabase_plans)} W47 plans in Supabase")
    
    if supabase_plans:
        # Filter to Wilson's plans
        wilson_plans = [p for p in supabase_plans if p['user_id'] == target_user_id]
        print(f"Found {len(wilson_plans)} W47 plans for Wilson")
        
        # Check existing plans in SQLite
        with Session(sqlite_db.engine) as session:
            existing_plans = list(session.exec(
                select(WeeklyPlan).where(
                    WeeklyPlan.user_id == target_user_id,
                    WeeklyPlan.week_of == w47_week
                )
            ))
            existing_plan_ids = {p.id for p in existing_plans}
            print(f"Found {len(existing_plans)} existing W47 plans in SQLite")
            
            # Migrate plans
            migrated_count = 0
            skipped_count = 0
            updated_count = 0
            
            for plan_data in wilson_plans:
                plan_id = plan_data['id']
                
                if plan_id in existing_plan_ids:
                    # Update existing plan if it has better data (lesson_json)
                    existing_plan = next(p for p in existing_plans if p.id == plan_id)
                    if plan_data.get('lesson_json') and not existing_plan.lesson_json:
                        existing_plan.lesson_json = plan_data.get('lesson_json')
                        existing_plan.status = plan_data.get('status', existing_plan.status)
                        existing_plan.output_file = plan_data.get('output_file') or existing_plan.output_file
                        updated_count += 1
                        print(f"  Updated plan {plan_id[:8]}... (added lesson_json)")
                    else:
                        skipped_count += 1
                    continue
                
                try:
                    # Parse datetime strings to datetime objects
                    generated_at = plan_data.get('generated_at')
                    if generated_at and isinstance(generated_at, str):
                        generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                    
                    plan = WeeklyPlan(
                        id=plan_data['id'],
                        user_id=plan_data['user_id'],
                        week_of=plan_data['week_of'],
                        status=plan_data.get('status', 'pending'),
                        output_file=plan_data.get('output_file'),
                        week_folder_path=plan_data.get('week_folder_path'),
                        consolidated=plan_data.get('consolidated', 0),
                        total_slots=plan_data.get('total_slots', 1),
                        generated_at=generated_at,
                        processing_time_ms=plan_data.get('processing_time_ms'),
                        total_tokens=plan_data.get('total_tokens'),
                        total_cost_usd=plan_data.get('total_cost_usd'),
                        llm_model=plan_data.get('llm_model'),
                        error_message=plan_data.get('error_message'),
                        lesson_json=plan_data.get('lesson_json'),
                    )
                    session.add(plan)
                    migrated_count += 1
                    print(f"  Migrated plan {plan_id[:8]}... (status: {plan.status}, has lesson_json: {plan.lesson_json is not None})")
                except Exception as e:
                    print(f"  ERROR migrating plan {plan_id[:8]}...: {e}")
            
            session.commit()
            print(f"\nMigrated {migrated_count} W47 plans")
            print(f"Updated {updated_count} existing plans")
            print(f"Skipped {skipped_count} existing plans")
    else:
        print("No W47 plans found in Supabase")
        
except Exception as e:
    print(f"ERROR migrating W47 plans: {e}")
    import traceback
    traceback.print_exc()

# Verify migration
print("\n" + "=" * 60)
print("Step 3: Verifying Migration")
print("=" * 60)

with Session(sqlite_db.engine) as session:
    # Check schedule entries
    final_schedules = list(session.exec(
        select(ScheduleEntry).where(ScheduleEntry.user_id == target_user_id)
    ))
    print(f"\nSchedule entries in SQLite: {len(final_schedules)}")
    if final_schedules:
        print("Sample entries:")
        for s in final_schedules[:5]:
            print(f"  {s.day_of_week} {s.start_time}-{s.end_time}: {s.subject} {s.grade} {s.homeroom}")
    
    # Check W47 plans
    final_plans = list(session.exec(
        select(WeeklyPlan).where(
            WeeklyPlan.user_id == target_user_id,
            WeeklyPlan.week_of == w47_week
        )
    ))
    print(f"\nW47 plans in SQLite: {len(final_plans)}")
    if final_plans:
        for p in final_plans:
            print(f"  Plan {p.id[:8]}...: status={p.status}, has lesson_json={p.lesson_json is not None}")

print("\n" + "=" * 60)
print("Migration Complete!")
print("=" * 60)

