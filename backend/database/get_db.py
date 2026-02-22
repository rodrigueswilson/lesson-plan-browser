"""Singleton and cache for get_db()."""

import logging
from typing import Dict, Optional

from backend.config import settings

from backend.database.sqlite_impl import SQLiteDatabase
from backend.database_interface import DatabaseInterface

logger = logging.getLogger(__name__)

_db_instance = None
_user_db_cache: Dict[str, DatabaseInterface] = {}


def get_db(user_id: Optional[str] = None, **kwargs) -> DatabaseInterface:
    """Get database instance (Singleton or user-specific for Supabase multi-project)."""
    global _db_instance, _user_db_cache

    from backend.settings_store import get_supabase_sync_enabled

    use_supabase = settings.USE_SUPABASE and get_supabase_sync_enabled()

    if use_supabase and user_id:
        if user_id in _user_db_cache:
            return _user_db_cache[user_id]

        try:
            from backend.config import Settings
            from backend.supabase_database import SupabaseDatabase

            if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
                try:
                    s1 = Settings()
                    s1.SUPABASE_PROJECT = "project1"
                    db1 = SupabaseDatabase(custom_settings=s1)
                    user1 = db1.get_user(user_id)
                    if user1:
                        logger.info(f"User {user_id} found in project1")
                        _user_db_cache[user_id] = db1
                        return db1
                except Exception as e:
                    logger.debug(f"User {user_id} not found in project1: {e}")

            if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
                try:
                    s2 = Settings()
                    s2.SUPABASE_PROJECT = "project2"
                    db2 = SupabaseDatabase(custom_settings=s2)
                    user2 = db2.get_user(user_id)
                    if user2:
                        logger.info(f"User {user_id} found in project2")
                        _user_db_cache[user_id] = db2
                        return db2
                except Exception as e:
                    logger.debug(f"User {user_id} not found in project2: {e}")

            logger.warning(
                f"User {user_id} not found in any Supabase project, using default database"
            )
        except ImportError:
            logger.debug("SupabaseDatabase not available, using default database")
        except Exception as e:
            logger.warning(
                f"Error determining user database project: {e}, using default database"
            )

    if _db_instance is None:
        from backend.settings_store import get_supabase_sync_enabled

        use_supabase = settings.USE_SUPABASE and get_supabase_sync_enabled()
        if use_supabase:
            logger.info(
                "Using SQLite Database (Supabase flag set but not implemented in this factory)"
            )
            _db_instance = SQLiteDatabase()
        else:
            logger.info("Using SQLite Database")
            _db_instance = SQLiteDatabase()

        _db_instance.init_db()

    return _db_instance
