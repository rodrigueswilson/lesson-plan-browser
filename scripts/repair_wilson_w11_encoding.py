"""
One-time repair of Wilson Rodrigues Week 11 lesson_json encoding corruption.

- All strings: NULL/control chars removed (sanitize_xml_text).
- Portuguese-only fields: known bad->correct fixes and hex mojibake (e7->c, e3->a,
  etc.) applied. Portuguese fields are those with keys: "portuguese" (vocabulary
  and sentence_frames), "bilingual_bridge", "family_connection". English and
  other fields are left unchanged to avoid corrupting e.g. "reading", "speaking".
Use --dry-run to preview without writing.
"""

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from copy import deepcopy
from pathlib import Path

# Ensure project root is on path for backend/tools imports
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.docx_renderer.style import sanitize_xml_text

# Known bad -> correct (Portuguese/vocab and sentence frame strings).
# Includes Portuguese words corrupted by ê/ea: rêge->reage, vea->vê (sees).
# mío->medo is done by regex in _apply_known_fixes; rêção->reação first in list.
_KNOWN_FIXES = [
    ("r\u00ea\u00e7\u00e3o", "reação"),  # rêção -> reação (reaction)
    ("evideancia", "evidência"),
    ("evideAncia", "evidência"),
    ("histf3ria", "história"),
    ("ninada", "ninhada"),
    ("care1ter", "carácter"),
    ("car\u0000e1ter", "carácter"),
    ("trae7o", "traço"),
    ("conspirae7e3o", "conspiração"),
    ("rêge", "reage"),
    ("vea", "vê"),
]
# Word-boundary style: " e9 " -> " é ", "Isto e9 " -> "Isto é "
_E9_FIX = (" e9 ", " é ")
_E9_FIX_START = ("Isto e9 ", "Isto é ")

# Portuguese mojibake: hex-digit pairs (Latin-1/CP1252) when inside a word.
# Only replace when surrounded by letters (ASCII or Latin-1) to avoid breaking "grade 7", etc.
_WORD_CHAR = r"[a-zA-Z\u00c0-\u00ff]"
# Revert accidental "ea"->ê in English words (from a previous run that had ea in _HEX_MOJIBAKE).
# Applied to ALL string fields so sentence_frames[].english and objectives are fixed too.
_ENGLISH_EA_REVERT = [
    ("rêading", "reading"),
    ("Rêading", "Reading"),
    ("Rêding", "reading"),
    ("spêaking", "speaking"),
    ("Spêaking", "Speaking"),
    ("rêason", "reason"),
    ("rehêarsal", "rehearsal"),
    ("grêater", "greater"),
    ("neêds", "needs"),
    ("hêr", "hear"),
    ("lêrns", "learns"),
    ("Lêrns", "Learns"),
    ("fêr", "fear"),
    ("Fêr", "Fear"),
    ("hêrs", "hears"),
    ("rêcts", "reacts"),
    ("Rêcts", "Reacts"),
]
# Do not include "ea"->ê or "e2"->â: they would corrupt English (e.g. "reading"->"rêading").
_HEX_MOJIBAKE = [
    ("e7", "\u00e7"),   # c-cedilla
    ("e3", "\u00e3"),   # a-tilde
    ("e9", "\u00e9"),   # e-acute
    ("f3", "\u00f3"),   # o-acute
    ("e1", "\u00e1"),   # a-acute
    ("ed", "\u00ed"),   # i-acute
    ("fa", "\u00fa"),   # u-acute
    ("f5", "\u00f5"),   # o-tilde
    ("f4", "\u00f4"),   # o-circumflex
    ("e0", "\u00e0"),   # a-grave
]

# Lesson JSON keys whose string values are Portuguese (or Portuguese-including).
# Only these fields get known fixes and hex mojibake; all other strings get only sanitize.
_PORTUGUESE_FIELD_NAMES = frozenset({"portuguese", "bilingual_bridge", "family_connection"})


def get_db_path() -> Path:
    """SQLite DB path under project root (same as extract script)."""
    return (_ROOT / "data" / "lesson_planner.db").absolute()


def fetch_user_id(conn: sqlite3.Connection, name: str) -> str | None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
    row = cursor.fetchone()
    return str(row[0]) if row else None


def fetch_weekly_plans_for_user(conn: sqlite3.Connection, user_id: str, limit: int = 50):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, week_of, lesson_json
        FROM weekly_plans
        WHERE user_id = ?
        ORDER BY generated_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    return [
        {"id": plan_id, "week_of": week_of, "lesson_json": raw}
        for plan_id, week_of, raw in cursor.fetchall()
    ]


def is_week_11(week_of: str) -> bool:
    if not week_of:
        return False
    text = week_of.strip().lower()
    candidates = ["w11", "week 11", "03-09", "03/09", "03-09-03-13", "03/09-03/13"]
    return any(t in text for t in candidates)


def _walk_strings_by_key(obj, sanitize_fn, english_revert_fn, portuguese_fix_fn):
    """
    Walk lesson_json; apply sanitize_fn and english_revert_fn to every string;
    apply portuguese_fix_fn only to strings under keys in _PORTUGUESE_FIELD_NAMES.
    Mutates obj in place.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                s = sanitize_fn(v)
                s = english_revert_fn(s)
                if k in _PORTUGUESE_FIELD_NAMES:
                    s = portuguese_fix_fn(s)
                obj[k] = s
            else:
                _walk_strings_by_key(v, sanitize_fn, english_revert_fn, portuguese_fix_fn)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                s = sanitize_fn(item)
                obj[i] = english_revert_fn(s)
            else:
                _walk_strings_by_key(item, sanitize_fn, english_revert_fn, portuguese_fix_fn)


def _apply_hex_mojibake(s: str) -> str:
    """Replace hex-digit mojibake (e7, e3, e9, f3, ...) with Portuguese letters when inside a word."""
    out = s
    for hex_pair, char in _HEX_MOJIBAKE:
        # Only when between letters (word-internal) so "trae7o" -> "traço", "conspiraçe3o" -> "conspiração"
        pattern = "(?<=" + _WORD_CHAR + ")" + re.escape(hex_pair) + "(?=" + _WORD_CHAR + ")"
        out = re.sub(pattern, char, out)
    return out


def _revert_english_ea(s: str) -> str:
    """Revert accidental ê in English words (applied to all string fields)."""
    out = s
    for bad, good in _ENGLISH_EA_REVERT:
        out = out.replace(bad, good)
    return out


def _apply_known_fixes(s: str) -> str:
    """Portuguese-only: known bad->correct and hex mojibake. English revert already applied to all."""
    # mío -> medo first (runtime chr so it matches in any encoding)
    _mio = "m" + chr(0xED) + "o"
    if _mio in s:
        s = s.replace(_mio, "medo")
    out = unicodedata.normalize("NFC", s)
    for bad, good in _KNOWN_FIXES:
        out = out.replace(bad, good)
    out = out.replace(_E9_FIX_START[0], _E9_FIX_START[1])
    out = out.replace(_E9_FIX[0], _E9_FIX[1])
    out = _apply_hex_mojibake(out)
    return out


def repair_lesson_json_encoding(lesson: dict) -> dict:
    """
    Sanitize all strings (NULL/control chars). Apply Portuguese known fixes and
    hex mojibake only to fields with keys in _PORTUGUESE_FIELD_NAMES so English
    text (e.g. objectives, vocabulary_cognates[].english) is unchanged.
    Returns a new dict (does not mutate input).
    """
    repaired = deepcopy(lesson)
    _walk_strings_by_key(repaired, sanitize_xml_text, _revert_english_ea, _apply_known_fixes)
    return repaired


def main():
    parser = argparse.ArgumentParser(description="Repair Wilson W11 lesson_json encoding.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write; print what would be updated.")
    args = parser.parse_args()

    db_path = get_db_path()
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        user_id = fetch_user_id(conn, "Wilson Rodrigues")
        if not user_id:
            print("User 'Wilson Rodrigues' not found.")
            return 1

        plans = fetch_weekly_plans_for_user(conn, user_id)
        w11_plans = [p for p in plans if is_week_11(str(p.get("week_of") or ""))]
        if not w11_plans:
            print("No Week 11 plans found for Wilson Rodrigues.")
            return 0

        updates = []
        for p in w11_plans:
            plan_id = p["id"]
            raw = p["lesson_json"]
            if isinstance(raw, str):
                try:
                    lesson = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(f"Skip plan {plan_id}: invalid JSON ({e})")
                    continue
            elif isinstance(raw, dict):
                lesson = raw
            else:
                continue

            repaired = repair_lesson_json_encoding(lesson)
            if repaired != lesson:
                updates.append((plan_id, p.get("week_of"), repaired))

        if not updates:
            print("No plans needed repair.")
            return 0

        print(f"Plans that would be updated: {len(updates)}")
        for plan_id, week_of, repaired in updates:
            print(f"  {plan_id} (week_of={week_of})")

        if args.dry_run:
            print("\n[DRY RUN] No changes written. Run without --dry-run to update the database.")
            return 0

        try:
            from backend.services.objectives_utils import normalize_objectives_in_lesson
        except ImportError:
            normalize_objectives_in_lesson = None

        cursor = conn.cursor()
        for plan_id, _week_of, repaired in updates:
            if normalize_objectives_in_lesson:
                normalize_objectives_in_lesson(repaired)
            cursor.execute(
                "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?",
                (json.dumps(repaired, ensure_ascii=False), plan_id),
            )
        conn.commit()
        print(f"\nUpdated {len(updates)} plan(s).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
