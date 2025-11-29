
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_path = "data/lesson_planner.db"

def migrate_db():
    if not os.path.exists(db_path):
        logger.info("Database not found, skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Users table
    logger.info("Checking users table...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "template_path" not in columns:
        logger.info("Adding template_path to users...")
        cursor.execute("ALTER TABLE users ADD COLUMN template_path TEXT")
    
    if "signature_image_path" not in columns:
        logger.info("Adding signature_image_path to users...")
        cursor.execute("ALTER TABLE users ADD COLUMN signature_image_path TEXT")

    # 2. Class Slots table
    logger.info("Checking class_slots table...")
    cursor.execute("PRAGMA table_info(class_slots)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "primary_teacher_file_pattern" not in columns:
        logger.info("Adding primary_teacher_file_pattern to class_slots...")
        cursor.execute("ALTER TABLE class_slots ADD COLUMN primary_teacher_file_pattern TEXT")
    
    if "plan_group_label" not in columns:
        logger.info("Adding plan_group_label to class_slots...")
        cursor.execute("ALTER TABLE class_slots ADD COLUMN plan_group_label TEXT")
        
    # 3. Weekly Plans table
    logger.info("Checking weekly_plans table...")
    cursor.execute("PRAGMA table_info(weekly_plans)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "lesson_json" not in columns:
        logger.info("Adding lesson_json to weekly_plans...")
        cursor.execute("ALTER TABLE weekly_plans ADD COLUMN lesson_json JSON")

    conn.commit()
    conn.close()
    logger.info("Migration completed.")

if __name__ == "__main__":
    migrate_db()
