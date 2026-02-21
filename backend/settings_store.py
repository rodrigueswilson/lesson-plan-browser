"""
Simple settings store for application preferences.
Stores settings in a JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "app_settings.json"


def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}")
    # Default settings
    return {
        "enable_supabase_sync": True  # Default to enabled
    }


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to JSON file."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise


def get_supabase_sync_enabled() -> bool:
    """Get whether Supabase sync is enabled."""
    settings = load_settings()
    return settings.get("enable_supabase_sync", True)


def set_supabase_sync_enabled(enabled: bool) -> None:
    """Set whether Supabase sync is enabled."""
    settings = load_settings()
    settings["enable_supabase_sync"] = enabled
    save_settings(settings)

