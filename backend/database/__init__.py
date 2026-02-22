"""
SQLite database package: engine, domain modules, and get_db.

Public API: SQLiteDatabase, Database (alias), get_db.
DatabaseInterface remains in backend.database_interface.
"""

from backend.database.get_db import get_db
from backend.database.sqlite_impl import SQLiteDatabase

Database = SQLiteDatabase

__all__ = ["SQLiteDatabase", "Database", "get_db"]
