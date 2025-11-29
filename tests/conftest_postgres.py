"""
Postgres test fixtures for CI integration tests.

This module provides Postgres-based test fixtures that can be used
instead of SQLite for more production-like testing.
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
import os

from backend.api import app
from backend.config import Settings
from backend.database_interface import DatabaseInterface


class PostgresTestDatabase(DatabaseInterface):
    """Postgres database adapter for testing."""
    
    def __init__(self, connection_string: str):
        """Initialize Postgres test database.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(self.connection_string)
        conn.set_session(autocommit=False)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """Create database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    base_path_override TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Class slots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS class_slots (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    slot_number INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    grade TEXT NOT NULL,
                    homeroom TEXT,
                    plan_group_label TEXT,
                    proficiency_levels TEXT,
                    primary_teacher_file TEXT,
                    primary_teacher_name TEXT,
                    primary_teacher_first_name TEXT,
                    primary_teacher_last_name TEXT,
                    primary_teacher_file_pattern TEXT,
                    display_order INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, slot_number)
                )
            """)
            
            # Weekly plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_plans (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    week_of TEXT NOT NULL,
                    week_folder_path TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_unit TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE
                )
            """)
            
            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_class_slots_user_id ON class_slots(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON weekly_plans(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_plan_id ON performance_metrics(plan_id)
            """)
            
            conn.commit()
    
    def get_user(self, user_id: str):
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_user(self, user_id: str, name: str, **kwargs):
        """Create a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, name, first_name, last_name, email)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                user_id,
                name,
                kwargs.get('first_name'),
                kwargs.get('last_name'),
                kwargs.get('email')
            ))
            conn.commit()
    
    def get_slot(self, slot_id: str):
        """Get slot by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM class_slots WHERE id = %s", (slot_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_class_slot(self, user_id: str, slot_number: int, subject: str, grade: str, **kwargs):
        """Create a class slot."""
        import uuid
        slot_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO class_slots (
                    id, user_id, slot_number, subject, grade, homeroom,
                    proficiency_levels, primary_teacher_file, primary_teacher_name,
                    primary_teacher_first_name, primary_teacher_last_name,
                    primary_teacher_file_pattern, display_order
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                slot_id,
                user_id,
                slot_number,
                subject,
                grade,
                kwargs.get('homeroom'),
                kwargs.get('proficiency_levels'),
                kwargs.get('primary_teacher_file'),
                kwargs.get('primary_teacher_name'),
                kwargs.get('primary_teacher_first_name'),
                kwargs.get('primary_teacher_last_name'),
                kwargs.get('primary_teacher_file_pattern'),
                kwargs.get('display_order')
            ))
            conn.commit()
        return slot_id
    
    def get_user_slots(self, user_id: str):
        """Get all slots for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM class_slots WHERE user_id = %s ORDER BY slot_number", (user_id,))
            return [dict(row) for row in cursor.fetchall()]


@pytest.fixture(scope="function")
def postgres_test_db():
    """Create Postgres test database connection."""
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        pytest.skip("DATABASE_URL not set - skipping Postgres tests")
    
    db = PostgresTestDatabase(connection_string)
    
    # Clean up after test
    yield db
    
    # Cleanup: Drop all test data
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE performance_metrics CASCADE")
        cursor.execute("TRUNCATE TABLE weekly_plans CASCADE")
        cursor.execute("TRUNCATE TABLE class_slots CASCADE")
        cursor.execute("TRUNCATE TABLE users CASCADE")
        conn.commit()


@pytest.fixture(scope="function")
def postgres_test_client(postgres_test_db, monkeypatch):
    """Create FastAPI test client with Postgres test database."""
    # Override get_db to return Postgres test database
    def get_test_db(user_id=None):
        return postgres_test_db
    
    monkeypatch.setattr("backend.api.get_db", get_test_db)
    
    # Set test settings
    test_settings = Settings(
        DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://test:test@localhost/test"),
        USE_SUPABASE=False,
    )
    monkeypatch.setattr("backend.config.settings", test_settings)
    
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture(scope="function")
def postgres_user_a(postgres_test_db):
    """Create test user A in Postgres."""
    user_id = "test-user-a-123"
    postgres_test_db.create_user(
        user_id=user_id,
        name="Alice Test",
        first_name="Alice",
        last_name="Test",
        email="alice@test.com"
    )
    return user_id


@pytest.fixture(scope="function")
def postgres_user_b(postgres_test_db):
    """Create test user B in Postgres."""
    user_id = "test-user-b-456"
    postgres_test_db.create_user(
        user_id=user_id,
        name="Bob Test",
        first_name="Bob",
        last_name="Test",
        email="bob@test.com"
    )
    return user_id


@pytest.fixture(scope="function")
def postgres_slot_a(postgres_test_db, postgres_user_a):
    """Create a test slot owned by user A in Postgres."""
    slot_id = postgres_test_db.create_class_slot(
        user_id=postgres_user_a,
        slot_number=1,
        subject="Math",
        grade="5",
        homeroom="Room 101"
    )
    return slot_id

