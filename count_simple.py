import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlmodel import Session, select, func

sys.path.append(os.getcwd())

try:
    from backend.schema import WeeklyPlan, User
except ImportError:
    sys.exit(1)

def main():
    db_path = Path("data/lesson_planner.db")
    engine = create_engine(f"sqlite:///{db_path.resolve()}")

    with Session(engine) as session:
        # Find Wilson
        user = session.exec(select(User).where(User.name.contains("Wilson"))).first()
        if not user:
            print("User Wilson not found.")
            return

        # Count specific weeks
        plans = session.exec(
            select(WeeklyPlan)
            .where(WeeklyPlan.user_id == user.id)
        ).all()
        
        # Look for the specific date format we saw in the glimse
        # "12-15-12-19"
        
        count = 0
        matches = []
        for p in plans:
            if "12-15" in p.week_of and "12-19" in p.week_of:
                count += 1
                matches.append(p.status)
        
        print(f"FINAL_COUNT: {count}")
        print(f"STATUSES: {', '.join(matches)}")

if __name__ == "__main__":
    main()
