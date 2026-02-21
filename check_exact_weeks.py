import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlmodel import Session, select, func

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from backend.schema import WeeklyPlan, User
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

def main():
    # We established this is the active DB
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        print(f"DB not found at {db_path}")
        return

    print(f"Checking {db_path}...")
    sqlite_url = f"sqlite:///{db_path.resolve()}"
    engine = create_engine(sqlite_url)

    with Session(engine) as session:
        # Find Wilson
        users = session.exec(select(User).where(User.name.contains("Wilson"))).all()
        if not users:
            print("User Wilson not found.")
            return

        for user in users:
            print(f"\nUser: {user.name} (ID: {user.id})")
            
            # Get ALL plans to list their week_of exactly
            plans = session.exec(
                select(WeeklyPlan)
                .where(WeeklyPlan.user_id == user.id)
                .order_by(WeeklyPlan.week_of)
            ).all()

            if not plans:
                print("  No plans found.")
                continue

            print(f"  Found {len(plans)} plans. Listing distinct weeks:")
            
            # Aggregate in python to see distinct strings
            week_counts = {}
            for p in plans:
                w = p.week_of
                week_counts[w] = week_counts.get(w, 0) + 1

            for w, count in sorted(week_counts.items()):
                print(f"    '{w}': {count} versions")
                
            # Specific check for the user's requested range
            print("\n  Looking for '12-15' or '12-19' or '15-12'...")
            matches = [p for p in plans if "12-15" in p.week_of or "12-19" in p.week_of or "15-12" in p.week_of]
            if matches:
                print(f"  !!! FOUND {len(matches)} MATCHES !!!")
                for m in matches:
                    print(f"    - ID: {m.id} | Week: '{m.week_of}' | Status: {m.status}")
            else:
                print("  No matches found for that specific date pattern.")

if __name__ == "__main__":
    main()
