from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
print(f"User: {user['name']} (ID: {user['id']})")

# Get weekly plans for this user
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, week_of, week_folder_path, status, generated_at
        FROM weekly_plans 
        WHERE user_id = ?
        ORDER BY generated_at DESC
        LIMIT 5
    """, (user['id'],))
    
    plans = cursor.fetchall()
    print(f"\nWeekly Plans for {user['name']}:")
    for plan in plans:
        print(f"  Plan ID: {plan[0]}")
        print(f"  Week: {plan[1]}")
        print(f"  Input Dir: {plan[2]}")
        print(f"  Status: {plan[3]}")
        print(f"  Created: {plan[4]}")
        print()
