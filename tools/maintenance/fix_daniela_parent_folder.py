from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
print(f"User: {user['name']} (ID: {user['id']})")

# Update the weekly plan with the PARENT folder
with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Get latest plan
    cursor.execute("""
        SELECT id, week_of, week_folder_path
        FROM weekly_plans 
        WHERE user_id = ? AND week_of = '10-27-10-31'
        ORDER BY generated_at DESC
        LIMIT 1
    """, (user['id'],))
    
    plan = cursor.fetchone()
    if plan:
        plan_id = plan[0]
        print(f"\nLatest Plan: {plan_id}")
        print(f"Week: {plan[1]}")
        print(f"Current folder path: '{plan[2]}'")
        
        # Update with PARENT folder path (not the W44 subfolder)
        parent_path = r"F:\rodri\Documents\OneDrive\AS\Daniela LP"
        cursor.execute("""
            UPDATE weekly_plans
            SET week_folder_path = ?
            WHERE id = ?
        """, (parent_path, plan_id))
        
        conn.commit()
        print(f"\n✅ Updated folder path to: {parent_path}")
        print(f"   System will automatically find most recent subfolder (e.g., '25 W44')")
    else:
        print("\n❌ No plan found for week 10-27-10-31")
