import sqlite3
import pandas as pd
from datetime import datetime

# Path to the local database synced to tablet
DB_PATH = "data/lesson_planner.db"

def inspect_sorting(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get users if not specified
        if not user_id:
            users = conn.execute("SELECT id, name FROM users").fetchall()
            print(f"Found {len(users)} users.")
            for uid, name in users:
                print(f"--- User: {name} ({uid}) ---")
                inspect_user_plans(conn, uid)
        else:
             inspect_user_plans(conn, user_id)
            
    finally:
        conn.close()

def inspect_user_plans(conn, user_id):
    query = """
    SELECT week_of, generated_at
    FROM weekly_plans
    WHERE user_id = ? AND week_of IS NOT NULL
    ORDER BY generated_at DESC
    LIMIT 20
    """
    rows = conn.execute(query, (user_id,)).fetchall()
    
    print(f"{'Week Of':<20} | {'Generated At':<30}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:<30}")

if __name__ == "__main__":
    # Wilson's ID from previous context
    WILSON_ID = "04fe8898-cb89-4a73-affb-64a97a98f820" 
    inspect_sorting(WILSON_ID)
