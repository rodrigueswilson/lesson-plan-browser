import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


def get_db_path() -> Path:
    """
    Resolve the SQLite database path.

    For this offline analysis script we keep it simple and point directly
    to the same location used by the backend: data/lesson_planner.db
    under the project root.
    """
    root = Path(__file__).resolve().parents[1]
    return (root / "data" / "lesson_planner.db").absolute()


def fetch_user_id(conn: sqlite3.Connection, name: str) -> str | None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
    row = cursor.fetchone()
    return str(row[0]) if row else None


def fetch_weekly_plans_for_user(conn: sqlite3.Connection, user_id: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, week_of, lesson_json
        FROM weekly_plans
        WHERE user_id = ?
        ORDER BY generated_at DESC
        LIMIT 50
        """,
        (user_id,),
    )
    plans: List[Dict[str, Any]] = []
    for plan_id, week_of, lesson_json in cursor.fetchall():
        plans.append(
            {
                "id": plan_id,
                "week_of": week_of,
                "lesson_json": lesson_json,
            }
        )
    return plans


def is_week_11(week_of: str) -> bool:
    """Heuristic match for Week 11 based on stored week_of formats."""
    if not week_of:
        return False

    text = week_of.strip().lower()
    candidates = ["w11", "week 11", "03-09", "03/09", "03-09-03-13", "03/09-03/13"]
    return any(token in text for token in candidates)


def collect_vocab_and_frames(lesson: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    vocab_all: List[Dict[str, Any]] = []
    frames_all: List[Dict[str, Any]] = []

    days = lesson.get("days") or {}
    for day_key, day_value in days.items():
        if not isinstance(day_value, dict):
            continue

        slots = day_value.get("slots")
        # Some structures might not have slots; support day-level vocab/frames as well.
        day_containers: List[Dict[str, Any]] = []

        if isinstance(slots, list):
            for slot in slots:
                if isinstance(slot, dict):
                    day_containers.append(slot)
        else:
            day_containers.append(day_value)

        for container in day_containers:
            vocab_list = container.get("vocabulary_cognates") or []
            if isinstance(vocab_list, list):
                for item in vocab_list:
                    if isinstance(item, dict):
                        vocab_all.append(
                            {
                                "english": item.get("english"),
                                "portuguese": item.get("portuguese"),
                                "day": day_key,
                            }
                        )

            frames_list = container.get("sentence_frames") or []
            if isinstance(frames_list, list):
                for frame in frames_list:
                    if isinstance(frame, dict):
                        frames_all.append(
                            {
                                "english": frame.get("english"),
                                "portuguese": frame.get("portuguese"),
                                "proficiency_level": frame.get("proficiency_level"),
                                "day": day_key,
                            }
                        )

    return {
        "vocabulary_cognates": vocab_all,
        "sentence_frames": frames_all,
    }


def extract_for_user(name: str, out_path: Path) -> Dict[str, Any]:
    db_path = get_db_path()
    if not db_path.exists():
        raise SystemExit(f"Database not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        user_id = fetch_user_id(conn, name)
        if user_id is None:
            print(f"No user found with name '{name}'. Skipping.")
            return {"user": name, "plans": []}

        plans = fetch_weekly_plans_for_user(conn, user_id)
        week11_plans: List[Dict[str, Any]] = []

        for plan in plans:
            week_of = plan["week_of"] or ""
            if not is_week_11(str(week_of)):
                continue

            lesson_raw = plan["lesson_json"]
            if isinstance(lesson_raw, str):
                try:
                    lesson = json.loads(lesson_raw)
                except json.JSONDecodeError as exc:
                    print(f"Failed to parse lesson_json for plan {plan['id']}: {exc}")
                    continue
            elif isinstance(lesson_raw, dict):
                lesson = lesson_raw
            else:
                print(f"Unexpected lesson_json type for plan {plan['id']}: {type(lesson_raw)}")
                continue

            collected = collect_vocab_and_frames(lesson)
            week11_plans.append(
                {
                    "plan_id": plan["id"],
                    "week_of": plan["week_of"],
                    "vocabulary_cognates": collected["vocabulary_cognates"],
                    "sentence_frames": collected["sentence_frames"],
                }
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "user": name,
                    "plans": week11_plans,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Wrote {len(week11_plans)} Week 11 plan(s) for {name} "
            f"to {out_path} (total vocab={sum(len(p['vocabulary_cognates']) for p in week11_plans)}, "
            f"frames={sum(len(p['sentence_frames']) for p in week11_plans)})"
        )

        return {"user": name, "plans": week11_plans}
    finally:
        conn.close()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    analysis_dir = root / "scripts" / "analysis"

    # Wilson Rodrigues (primary target)
    wilson_out = analysis_dir / "wilson_w11_vocab_frames.json"
    extract_for_user("Wilson Rodrigues", wilson_out)

    # Optional: Daniela Silva for comparison. This will simply report if user/plans not found.
    daniela_out = analysis_dir / "daniela_w11_vocab_frames.json"
    extract_for_user("Daniela Silva", daniela_out)


if __name__ == "__main__":
    main()

