import sqlite3

conn = sqlite3.connect('data/lesson_planner.db')
cursor = conn.cursor()

# Check all plans for Wilson
cursor.execute("""
    SELECT id, week_of, status, created_at, updated_at 
    FROM weekly_plans 
    WHERE user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
    ORDER BY created_at DESC
""")
plans = cursor.fetchall()
print(f'All plans for Wilson Rodrigues ({len(plans)} total):')
for plan in plans:
    print(f'  ID: {plan[0][:8]}..., Week: {plan[1]}, Status: {plan[2]}, Created: {plan[3][:19]}')

# Check for the specific plan ID mentioned in logs
cursor.execute("""
    SELECT id, week_of, status, created_at, updated_at, lesson_json 
    FROM weekly_plans 
    WHERE id = '6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0'
""")
specific_plans = cursor.fetchall()
print(f'\nSpecific plan ID 6dc1bd72 entries ({len(specific_plans)} total):')
for plan in specific_plans:
    print(f'  ID: {plan[0][:8]}..., Week: {plan[1]}, Status: {plan[2]}, Created: {plan[3][:19]}')
    if plan[5]:
        print(f'    Has lesson_json: {len(str(plan[5]))} chars')

# Check for duplicates by week
cursor.execute("""
    SELECT week_of, COUNT(*) as count 
    FROM weekly_plans 
    WHERE user_id = '04fe8898-cb89-4a73-affb-64a97a98f820'
    GROUP BY week_of
    HAVING COUNT(*) > 1
""")
week_duplicates = cursor.fetchall()
print(f'\nWeeks with multiple entries:')
for dup in week_duplicates:
    print(f'  Week: {dup[0]}, Count: {dup[1]}')

conn.close()
