#!/usr/bin/env python3
"""
Sync weekly plans that exist in the running backend (PC browser) into the
local SQLite database that we bundle inside the tablet APK.

The script pulls plan summaries + lesson JSON (and optionally lesson steps)
from the HTTP API (default http://localhost:8000/api) and upserts them into
`data/lesson_planner.db`. Once the data is in that file, you can rebuild the
APK or push the DB to the tablet using the usual adb commands.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

DEFAULT_API_BASE = "http://localhost:8000/api"
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy weekly plans from the running backend into data/lesson_planner.db",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE,
        help="Backend API base URL (where the desktop browser gets its data).",
    )
    parser.add_argument(
        "--db-path",
        default="data/lesson_planner.db",
        help="Path to the SQLite database that will later be bundled into the tablet APK.",
    )
    parser.add_argument(
        "--plan-limit",
        type=int,
        default=20,
        help="Number of plans to fetch per user from the API before filtering.",
    )
    parser.add_argument(
        "--user",
        dest="users",
        action="append",
        help="Restrict syncing to specific user IDs or names (repeatable). "
        "Defaults to all users in the local DB.",
    )
    parser.add_argument(
        "--week",
        dest="weeks",
        action="append",
        help="Only sync plans whose week_of string matches one of these tokens "
        "(e.g., 12-01-12-05). When omitted, all remote weeks that are missing locally "
        "will be imported.",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Re-sync plans even if they already exist locally (overwrites lesson_json).",
    )
    parser.add_argument(
        "--skip-steps",
        action="store_true",
        help="Skip copying lesson_steps (only weekly_plans will be updated).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout (seconds) for API requests.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying the SQLite database.",
    )
    return parser.parse_args()


def load_local_users(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()
    return {row[0]: row[1] for row in rows}


def resolve_users(
    all_users: Dict[str, str], requested: Optional[Sequence[str]]
) -> Dict[str, str]:
    if not requested:
        return all_users

    resolved: Dict[str, str] = {}
    lowered = {uid: name.lower() for uid, name in all_users.items()}
    for token in requested:
        token_lower = token.lower()
        if token in all_users:
            resolved[token] = all_users[token]
            continue
        # Try to match on name substring
        matches = [uid for uid, name in lowered.items() if token_lower in name]
        if not matches:
            raise ValueError(f"User '{token}' not found in local database.")
        for uid in matches:
            resolved[uid] = all_users[uid]
    return resolved


def backup_database(db_path: Path, backup_dir: Path = None) -> Path:
    """Create a timestamped backup of the database."""
    if backup_dir is None:
        backup_dir = db_path.parent / "backups"

    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_path.stem}_backup_{timestamp}.db"
    backup_path = backup_dir / backup_name

    shutil.copy2(db_path, backup_path)
    print(f"[OK] Database backed up to: {backup_path}")
    return backup_path


def request_json(
    method: str,
    url: str,
    *,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    response = requests.request(method, url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response.json()


def load_remote_plans(
    api_base: str,
    user_id: str,
    plan_limit: int,
    timeout: float,
) -> List[Dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/users/{user_id}/plans"
    params = {"limit": plan_limit}
    response = requests.get(
        url,
        params=params,
        timeout=timeout,
        headers={"X-Current-User-Id": user_id},
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response at {url}: {data!r}")
    return data


def fetch_plan_detail(
    api_base: str,
    plan_id: str,
    user_id: str,
    timeout: float,
) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/plans/{plan_id}"
    return request_json(
        "GET",
        url,
        timeout=timeout,
        headers={"X-Current-User-Id": user_id},
    )


def fetch_lesson_steps(
    api_base: str,
    plan_id: str,
    day: str,
    slot: int,
    user_id: str,
    timeout: float,
) -> List[Dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/lesson-steps/{plan_id}/{day}/{slot}"
    try:
        data = request_json(
            "GET",
            url,
            timeout=timeout,
            headers={"X-Current-User-Id": user_id},
        )
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected lesson steps response: {data}")
        return data
    except requests.HTTPError as exc:
        print(
            f"[WARN] Failed to fetch lesson steps ({day} slot {slot}) "
            f"for plan {plan_id}: {exc}"
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"[WARN] Unexpected error fetching lesson steps "
            f"({day} slot {slot}) for plan {plan_id}: {exc}"
        )
    return []


def list_local_plan_ids(conn: sqlite3.Connection, user_id: str) -> Dict[str, str]:
    rows = conn.execute(
        "SELECT id, week_of FROM weekly_plans WHERE user_id = ?", (user_id,)
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def select_target_plans(
    remote_plans: Iterable[Dict[str, Any]],
    desired_weeks: Optional[Sequence[str]],
    existing_plan_ids: Dict[str, str],
    include_existing: bool,
) -> List[Dict[str, Any]]:
    desired_set = {w.strip() for w in desired_weeks} if desired_weeks else None
    selected: List[Dict[str, Any]] = []
    for plan in remote_plans:
        week_of = plan.get("week_of") or ""
        if desired_set and week_of not in desired_set:
            continue
        plan_id = plan.get("id")
        if not plan_id:
            continue
        if plan_id in existing_plan_ids and not include_existing:
            continue
        selected.append(plan)
    return selected


def compute_total_slots(lesson_json: Dict[str, Any]) -> int:
    metadata = lesson_json.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("total_slots"):
        try:
            return int(metadata["total_slots"])
        except (TypeError, ValueError):
            pass
    days = lesson_json.get("days") or {}
    if isinstance(days, dict):
        for day_data in days.values():
            slots = day_data.get("slots")
            if isinstance(slots, list):
                return max(len(slots), 1)
    return 1


def day_slot_pairs(lesson_json: Dict[str, Any]) -> List[Tuple[str, int]]:
    pairs: List[Tuple[str, int]] = []
    days = lesson_json.get("days")
    if not isinstance(days, dict):
        return pairs
    for day_name, day_data in days.items():
        if not isinstance(day_name, str):
            continue
        slots = None
        if isinstance(day_data, dict):
            slots = day_data.get("slots")
        if not isinstance(slots, list):
            continue
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            slot_number = slot.get("slot_number")
            try:
                slot_number_int = int(slot_number)
            except (TypeError, ValueError):
                continue
            pairs.append((day_name.lower(), slot_number_int))
    # Deduplicate while preserving order
    seen = set()
    unique_pairs: List[Tuple[str, int]] = []
    for pair in pairs:
        if pair not in seen:
            seen.add(pair)
            unique_pairs.append(pair)
    return unique_pairs


def upsert_weekly_plan(
    conn: sqlite3.Connection,
    *,
    plan_detail: Dict[str, Any],
) -> None:
    columns = [
        "id",
        "user_id",
        "week_of",
        "generated_at",
        "output_file",
        "status",
        "error_message",
        "week_folder_path",
        "consolidated",
        "total_slots",
        "processing_time_ms",
        "total_tokens",
        "total_cost_usd",
        "llm_model",
        "lesson_json",
    ]
    placeholders = ",".join("?" for _ in columns)
    update_clause = ", ".join(
        f"{col} = excluded.{col}" for col in columns if col != "id"
    )
    sql = (
        f"INSERT INTO weekly_plans ({','.join(columns)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {update_clause}"
    )
    conn.execute(
        sql,
        [
            plan_detail["id"],
            plan_detail["user_id"],
            plan_detail["week_of"],
            plan_detail["generated_at"],
            plan_detail.get("output_file"),
            plan_detail.get("status", "completed"),
            plan_detail.get("error_message"),
            plan_detail.get("week_folder_path"),
            plan_detail.get("consolidated", 0),
            plan_detail.get("total_slots", 1),
            plan_detail.get("processing_time_ms"),
            plan_detail.get("total_tokens"),
            plan_detail.get("total_cost_usd"),
            plan_detail.get("llm_model"),
            plan_detail.get("lesson_json_str"),
        ],
    )


def replace_lesson_steps(
    conn: sqlite3.Connection,
    plan_id: str,
    steps: List[Dict[str, Any]],
) -> None:
    if not steps:
        return
    # Remove any existing steps for the same plan/day/slot_number where incoming data exists
    day_slot_map = {
        (step.get("day_of_week", "").lower(), int(step.get("slot_number", 0)))
        for step in steps
        if step.get("day_of_week") and step.get("slot_number") is not None
    }
    for day, slot in day_slot_map:
        conn.execute(
            "DELETE FROM lesson_steps WHERE lesson_plan_id = ? AND lower(day_of_week) = ? AND slot_number = ?",
            (plan_id, day, slot),
        )

    insert_sql = """
        INSERT OR REPLACE INTO lesson_steps
        (id, lesson_plan_id, day_of_week, slot_number, step_number, step_name,
         duration_minutes, start_time_offset, content_type, display_content,
         hidden_content, sentence_frames, materials_needed, created_at, updated_at, vocabulary_cognates)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for step in steps:
        step_id = (
            step.get("id")
            or f"step_{plan_id}_{step.get('day_of_week')}_{step.get('slot_number')}_{step.get('step_number')}"
        )
        created_at = step.get("created_at") or datetime.utcnow().isoformat()
        updated_at = step.get("updated_at") or created_at
        conn.execute(
            insert_sql,
            [
                step_id,
                plan_id,
                step.get("day_of_week"),
                step.get("slot_number"),
                step.get("step_number"),
                step.get("step_name"),
                step.get("duration_minutes"),
                step.get("start_time_offset"),
                step.get("content_type"),
                step.get("display_content"),
                json.dumps(step.get("hidden_content"))
                if step.get("hidden_content") is not None
                else None,
                json.dumps(step.get("sentence_frames"))
                if step.get("sentence_frames") is not None
                else None,
                json.dumps(step.get("materials_needed"))
                if step.get("materials_needed") is not None
                else None,
                created_at,
                updated_at,
                json.dumps(step.get("vocabulary_cognates"))
                if step.get("vocabulary_cognates") is not None
                else None,
            ],
        )


def sync_plan(
    conn: sqlite3.Connection,
    *,
    api_base: str,
    plan_summary: Dict[str, Any],
    user_id: str,
    timeout: float,
    skip_steps: bool,
) -> Tuple[str, int]:
    plan_id = plan_summary["id"]
    detail = fetch_plan_detail(api_base, plan_id, user_id, timeout=timeout)
    lesson_json = detail.get("lesson_json") or {}
    plan_payload = {
        "id": detail["id"],
        "user_id": detail["user_id"],
        "week_of": detail["week_of"],
        "status": detail.get("status") or plan_summary.get("status") or "completed",
        "output_file": detail.get("output_file") or plan_summary.get("output_file"),
        "error_message": detail.get("error_message")
        or plan_summary.get("error_message"),
        "week_folder_path": detail.get("week_folder_path"),
        "consolidated": int(bool(detail.get("consolidated"))),
        "total_slots": compute_total_slots(lesson_json),
        "processing_time_ms": detail.get("processing_time_ms"),
        "total_tokens": detail.get("total_tokens"),
        "total_cost_usd": detail.get("total_cost_usd"),
        "llm_model": detail.get("llm_model"),
        "generated_at": detail.get("generated_at")
        or plan_summary.get("generated_at")
        or datetime.utcnow().isoformat(),
        "lesson_json_str": json.dumps(lesson_json),
    }
    upsert_weekly_plan(conn, plan_detail=plan_payload)
    steps_inserted = 0
    if not skip_steps:
        pairs = day_slot_pairs(lesson_json)
        all_steps: List[Dict[str, Any]] = []

        # Fetch lesson steps in parallel for better performance
        if pairs:
            # NOW SAFE: Increasing concurrency since 500 errors (serialization bugs) are fixed.
            max_workers = 10
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all step fetch tasks
                future_to_pair = {
                    executor.submit(
                        fetch_lesson_steps,
                        api_base,
                        plan_id,
                        day_name,
                        slot_number,
                        user_id,
                        timeout,
                    ): (day_name, slot_number)
                    for day_name, slot_number in pairs
                }

                # Collect results as they complete
                for future in as_completed(future_to_pair):
                    day_name, slot_number = future_to_pair[future]
                    try:
                        steps = future.result()
                        if steps:
                            all_steps.extend(steps)
                    except Exception as exc:
                        print(
                            f"[WARN] Error fetching steps for {day_name} slot {slot_number}: {exc}"
                        )

        if all_steps:
            replace_lesson_steps(conn, plan_id, all_steps)
            steps_inserted = len(all_steps)
    return plan_payload["week_of"], steps_inserted


def main() -> None:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {db_path}. Run the desktop app once to create it."
        )

    # Create backup before syncing (if not dry-run)
    if not args.dry_run:
        backup_path = backup_database(db_path)
        print(f"  Backup created: {backup_path.name}\n")

    conn = sqlite3.connect(db_path)
    try:
        all_users = load_local_users(conn)
        target_users = resolve_users(all_users, args.users)
        if not target_users:
            raise RuntimeError("No users found to sync.")

        summary: List[str] = []
        for user_id, user_name in target_users.items():
            print(f"\n=== Syncing {user_name} ({user_id}) ===")
            remote_plans = load_remote_plans(
                args.api_base_url, user_id, args.plan_limit, timeout=args.timeout
            )
            if not remote_plans:
                print("  No plans returned by API.")
                continue
            print(f"  Found {len(remote_plans)} remote plan(s) from API")
            if len(remote_plans) >= args.plan_limit:
                print(
                    f"  WARNING: Hit plan limit of {args.plan_limit}. Some plans may be missing!"
                )
            existing = list_local_plan_ids(conn, user_id)
            targets = select_target_plans(
                remote_plans,
                args.weeks,
                existing,
                include_existing=args.include_existing,
            )
            if not targets:
                print(
                    f"  Nothing to sync (all {len(remote_plans)} remote plans already present locally)."
                )
                print(
                    f"  Remote plans: {[p.get('week_of', '?') for p in remote_plans[:5]]}..."
                )
                continue
            for plan in targets:
                plan_id = plan["id"]
                week_of = plan.get("week_of")
                print(f"  -> Syncing plan {plan_id} (week {week_of})")
                if args.dry_run:
                    continue
                synced_week, steps_count = sync_plan(
                    conn,
                    api_base=args.api_base_url,
                    plan_summary=plan,
                    user_id=user_id,
                    timeout=args.timeout,
                    skip_steps=args.skip_steps,
                )
                summary.append(
                    f"{user_name}: week {synced_week} (plan {plan_id}) "
                    f"{'+' if steps_count else ''}{steps_count} steps"
                )
                conn.commit()
        if args.dry_run:
            print("\nDry run complete. No changes were written to the database.")
        else:
            print("\nSync complete.")
            if summary:
                print("Imported plans:")
                for line in summary:
                    print(f"  - {line}")
            else:
                print("No plans were imported.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
