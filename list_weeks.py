import sqlite3

conn = sqlite3.connect('data/lesson_planner.db')
cur = conn.cursor()
cur.execute("SELECT week_of, id, status, generated_at FROM weekly_plans ORDER BY generated_at DESC")
rows = cur.fetchall()
for row in rows:
    print(row)
