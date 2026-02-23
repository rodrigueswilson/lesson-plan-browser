"""
Fetch active users from Supabase and/or SQLite fallback.
Used by users router list_users endpoint.
"""

from backend.config import settings
from backend.database import get_db
from backend.telemetry import logger

_supabase_fallback_logged: set = set()


def fetch_active_users():
    """
    Return list of active users from Supabase (if configured) and/or SQLite fallback.
    Deduplicates by user ID and filters to allowed user IDs.
    """
    all_users = []

    if settings.USE_SUPABASE:
        from backend.config import Settings
        from backend.supabase_database import SupabaseDatabase

        _supabase_note = (
            "Supabase will be fully implemented in a later stage. "
            "SQLite fallback in use. This warning is expected."
        )

        if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
            try:
                s1 = Settings()
                s1.SUPABASE_PROJECT = "project1"
                db1 = SupabaseDatabase(custom_settings=s1)
                users1 = db1.list_users()
                all_users.extend(users1)
                logger.info(
                    "users_loaded_from_project",
                    extra={"project": "project1", "count": len(users1)},
                )
            except Exception as e:
                if "project1" not in _supabase_fallback_logged:
                    _supabase_fallback_logged.add("project1")
                    logger.warning(
                        "users_load_project1_failed",
                        extra={"error": str(e), "note": _supabase_note},
                    )
                else:
                    logger.debug(
                        "users_load_project1_failed",
                        extra={"error": str(e), "note": _supabase_note},
                    )

        if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
            try:
                s2 = Settings()
                s2.SUPABASE_PROJECT = "project2"
                db2 = SupabaseDatabase(custom_settings=s2)
                users2 = db2.list_users()
                all_users.extend(users2)
                logger.info(
                    "users_loaded_from_project",
                    extra={"project": "project2", "count": len(users2)},
                )
            except Exception as e:
                if "project2" not in _supabase_fallback_logged:
                    _supabase_fallback_logged.add("project2")
                    logger.warning(
                        "users_load_project2_failed",
                        extra={"error": str(e), "note": _supabase_note},
                    )
                else:
                    logger.debug(
                        "users_load_project2_failed",
                        extra={"error": str(e), "note": _supabase_note},
                    )

        if not all_users:
            try:
                db = get_db()
                fallback_users = db.list_users()
                all_users.extend(fallback_users)
                logger.info(
                    "users_loaded_from_sqlite_fallback",
                    extra={"count": len(fallback_users)},
                )
            except Exception as e:
                logger.warning(
                    "users_load_sqlite_fallback_failed",
                    extra={"error": str(e)},
                )
    else:
        db = get_db()
        all_users = db.list_users()

    seen_ids = set()
    unique_users = []
    for user in all_users:
        if user.id not in seen_ids:
            seen_ids.add(user.id)
            unique_users.append(user)

    ALLOWED_USER_IDS = {
        "04fe8898-cb89-4a73-affb-64a97a98f820",
        "29fa9ed7-3174-4999-86fd-40a542c28cff",
    }
    active_users = [u for u in unique_users if u.id in ALLOWED_USER_IDS]
    active_users.sort(key=lambda u: u.name or "")
    return active_users
