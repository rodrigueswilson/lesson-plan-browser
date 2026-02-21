import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import Session, select
from rich.console import Console
from rich.table import Table

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Load env vars
load_dotenv(project_root / ".env")

from backend.config import settings
# Force DB path
settings.SQLITE_DB_PATH = project_root / "data" / "lesson_planner.db"
settings.DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"

from backend.database import get_db
from backend.schema import WeeklyPlan
from sqlmodel import create_engine

def inspect_db():
    console = Console()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Check counts
        total_plans = session.exec(select(WeeklyPlan)).all()
        populated = [p for p in total_plans if p.processing_time_ms is not None]
        zeros = [p for p in total_plans if p.processing_time_ms == 0]
        
        print(f"Total Plans: {len(total_plans)}")
        print(f"Plans with Processing Time: {len(populated)}")
        print(f"Plans with 0 Processing Time: {len(zeros)}")
        
        if populated:
            avg = sum(p.processing_time_ms for p in populated) / len(populated)
            print(f"Average calc from populated: {avg}")
            
        # Top 5
        print("\nTop 5 Plans by Duration:")
        top5 = sorted(populated, key=lambda p: p.processing_time_ms or 0, reverse=True)[:5]
        for p in top5:
            print(f"  {p.id}: {p.processing_time_ms} ms")

if __name__ == "__main__":
    inspect_db()
