
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SQLiteDatabase
from backend.schema import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_missing_user():
    logger.info("Fixing missing user...")
    
    db = SQLiteDatabase()
    # We don't need init_db() if it's already initialized, but it's safe to call
    
    user_id = "edcde77c-b14f-4296-9017-b26b0b9a369d"
    
    # Check if user exists first (though we know they likely don't)
    existing_user = db.get_user(user_id)
    if existing_user:
        logger.info(f"User {user_id} already exists.")
        return

    # Create user manually to specify the ID
    try:
        from sqlmodel import Session
        
        user = User(
            id=user_id,
            name="Wilson Rodrigues",
            first_name="Wilson",
            last_name="Rodrigues",
            email="wilson@example.com", # Placeholder
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with Session(db.engine) as session:
            session.add(user)
            session.commit()
            logger.info(f"Successfully created user: {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to create user: {e}")

if __name__ == "__main__":
    fix_missing_user()
