"""
Merge monolithic Grade 2 Science ingest (one unit, ~65 parser rows) into
6 modules and 20 canonical lessons per ``g2_science_canonical_ssot``.

Usage (repo root):
  python tools/db/canonicalize_g2_science_modules.py
  python tools/db/canonicalize_g2_science_modules.py --db path/to/curriculum.db --dry-run

Requires existing unit ``Science_2_U1_1SNRc-NF`` from ``ingest_wave_unit``.
Removes that unit after successful merge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.database.curriculum import CurriculumDatabase
from tools.db.g2_science_canonical_ssot import (
    G2ScienceCanonicalLessonSpec,
    G2ScienceModuleSpec,
    g2_science_modules,
    monolithic_science_unit_id,
    validate_ssot_covers_monolithic_ingest,
)
from tools.db.ingest_wave_unit import _delete_unit_rows, _seed_unit

_HTML_MERGE_FIELDS = (
    "narrative_html",
    "lesson_narrative",
    "learning_intentions",
    "daily_instructional_task",
    "success_criteria",
    "essential_questions",
    "procedure",
    "materials",
    "instructional_resources",
    "purpose",
    "mlr",
    "objectives_student",
    "procedure_html",
    "vocabulary",
    "practices",
    "procedures",
    "differentiation",
)


def _merge_html(parts: Sequence[str]) -> str:
    chunks = [p.strip() for p in parts if p and str(p).strip()]
    return "\n\n".join(chunks)


def _merge_science_payloads(
    payloads: List[Dict[str, Any]],
    *,
    doc_lesson_number: int,
) -> Dict[str, Any]:
    segments_out: List[Dict[str, Any]] = []
    for p in payloads:
        for seg in p.get("segments") or []:
            if isinstance(seg, dict):
                segments_out.append(dict(seg))
    return {
        "schema_version": 2,
        "source": "science_canonical_merge@v1",
        "doc_lesson_number": int(doc_lesson_number),
        "segments": segments_out,
    }


def _parse_science_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw or not str(raw).strip():
        return None
    try:
        o = json.loads(raw)
        return o if isinstance(o, dict) else None
    except json.JSONDecodeError:
        return None


def _merge_standards_structured(rows: List[Dict[str, Any]]) -> str:
    out: List[Any] = []
    for r in rows:
        raw = r.get("standards_structured")
        if not raw:
            continue
        try:
            arr = json.loads(raw)
            if isinstance(arr, list):
                out.extend(arr)
        except json.JSONDecodeError:
            continue
    return json.dumps(out, ensure_ascii=False)


def _content_hash(lesson: Dict[str, Any]) -> str:
    key = "\n".join(
        [
            lesson.get("title") or "",
            lesson.get("procedure_html") or "",
            lesson.get("science_li_sc_day_structured") or "",
        ]
    )
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def _load_monolithic_lesson_map(
    conn: sqlite3.Connection, unit_id: str
) -> Dict[int, Dict[str, Any]]:
    cur = conn.execute(
        "SELECT * FROM lessons WHERE unit_id = ? ORDER BY lesson_number",
        (unit_id,),
    )
    by_num: Dict[int, Dict[str, Any]] = {}
    for row in cur.fetchall():
        d = dict(row)
        n = int(d["lesson_number"])
        by_num[n] = d
    return by_num


def _collect_sources(
    by_num: Dict[int, Dict[str, Any]], nums: Tuple[int, ...]
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for n in nums:
        if n not in by_num:
            raise KeyError(f"Parser lesson_number {n} missing in monolithic unit")
        out.append(by_num[n])
    return out


def _build_canonical_lesson_row(
    *,
    module: G2ScienceModuleSpec,
    spec: G2ScienceCanonicalLessonSpec,
    sources: List[Dict[str, Any]],
    source_url: str,
    source_doc_id: str,
    ingest_meta: Dict[str, Any],
) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for f in _HTML_MERGE_FIELDS:
        merged[f] = _merge_html([str(s.get(f) or "") for s in sources])

    payloads = []
    for s in sources:
        p = _parse_science_json(s.get("science_li_sc_day_structured"))
        if p:
            payloads.append(p)
    science_json: Optional[str] = None
    if payloads:
        combined = _merge_science_payloads(
            payloads, doc_lesson_number=spec.lesson_in_module
        )
        science_json = json.dumps(combined, ensure_ascii=False)

    new_id = f"{module.unit_id}_L{spec.lesson_in_module}"
    row = {
        "id": new_id,
        "unit_id": module.unit_id,
        "lesson_number": spec.lesson_in_module,
        "title": spec.title,
        "science_doc_lesson_number": spec.lesson_in_module,
        "science_li_sc_day_structured": science_json,
        "standards_structured": _merge_standards_structured(sources),
        "source_url": source_url,
        "source_doc_id": source_doc_id,
        "ingested_at": ingest_meta.get("ingested_at"),
        "ingest_run_id": ingest_meta.get("ingest_run_id"),
        "ingest_parser_version": str(ingest_meta.get("ingest_parser_version", ""))
        + "+canonical_merge@v1",
    }
    for k in (
        "ela_key_learning_summary",
        "ela_lesson_plan_structured",
    ):
        row[k] = sources[0].get(k) if sources else None

    row["content_hash"] = _content_hash(row)
    return row


def _snapshot_union_links(
    conn: sqlite3.Connection, old_ids: Sequence[str]
) -> Tuple[List[str], List[str], List[str]]:
    """Collect distinct standard codes, vocab item ids, resource ids before source rows are deleted."""
    std: List[str] = []
    voc: List[str] = []
    res: List[str] = []
    for oid in old_ids:
        std.extend(
            r[0]
            for r in conn.execute(
                "SELECT standard_code FROM lesson_standards WHERE lesson_id = ?",
                (oid,),
            )
        )
        voc.extend(
            r[0]
            for r in conn.execute(
                "SELECT vocab_item_id FROM lesson_vocabulary WHERE lesson_id = ?",
                (oid,),
            )
        )
        res.extend(
            r[0]
            for r in conn.execute(
                "SELECT resource_id FROM lesson_resources WHERE lesson_id = ?",
                (oid,),
            )
        )
    return (
        list(dict.fromkeys(std)),
        list(dict.fromkeys(voc)),
        list(dict.fromkeys(res)),
    )


def _apply_snapshot_links(
    conn: sqlite3.Connection,
    new_id: str,
    stds: Sequence[str],
    voc_ids: Sequence[str],
    res_ids: Sequence[str],
) -> None:
    for code in stds:
        conn.execute(
            "INSERT OR IGNORE INTO lesson_standards (lesson_id, standard_code) VALUES (?, ?)",
            (new_id, code),
        )
    for vid in voc_ids:
        conn.execute(
            "INSERT OR IGNORE INTO lesson_vocabulary (lesson_id, vocab_item_id) VALUES (?, ?)",
            (new_id, vid),
        )
    for rid in res_ids:
        conn.execute(
            "INSERT OR IGNORE INTO lesson_resources (lesson_id, resource_id) VALUES (?, ?)",
            (new_id, rid),
        )


def run_canonicalize_g2_science_modules(db_path: str, *, dry_run: bool = False) -> int:
    validate_ssot_covers_monolithic_ingest(expect_rows=65)

    db_path = os.path.abspath(db_path)
    mono_id = monolithic_science_unit_id()

    if not os.path.isfile(db_path):
        print(f"ERROR: database not found: {db_path}", flush=True)
        return 1

    conn = sqlite3.connect(db_path, timeout=60.0)
    conn.row_factory = sqlite3.Row
    n_mono = conn.execute(
        "SELECT COUNT(*) FROM lessons WHERE unit_id = ?", (mono_id,)
    ).fetchone()[0]
    if n_mono == 0:
        print(
            f"ERROR: no lessons for monolithic unit {mono_id!r}; run ingest_wave_unit first.",
            flush=True,
        )
        conn.close()
        return 1

    urow = conn.execute("SELECT * FROM units WHERE id = ?", (mono_id,)).fetchone()
    if not urow:
        print(f"ERROR: unit row missing: {mono_id}", flush=True)
        conn.close()
        return 1
    urow = dict(urow)
    source_url = urow.get("source_url") or ""
    source_doc_id = urow.get("source_doc_id") or ""
    ingest_meta = {
        "ingested_at": urow.get("ingested_at"),
        "ingest_run_id": urow.get("ingest_run_id"),
        "ingest_parser_version": urow.get("ingest_parser_version"),
    }

    by_num = _load_monolithic_lesson_map(conn, mono_id)
    if len(by_num) != 65:
        print(
            f"WARNING: expected 65 monolithic lessons, found {len(by_num)}; SSOT assumes 65.",
            flush=True,
        )

    curriculum = CurriculumDatabase(db_path)
    plans: List[
        Tuple[
            G2ScienceModuleSpec,
            G2ScienceCanonicalLessonSpec,
            List[Dict[str, Any]],
            Tuple[List[str], List[str], List[str]],
        ]
    ] = []

    for mod in g2_science_modules():
        for les in mod.lessons:
            sources = _collect_sources(by_num, les.source_parser_lesson_numbers)
            old_ids = [s["id"] for s in sources]
            snap = _snapshot_union_links(conn, old_ids)
            plans.append((mod, les, sources, snap))

    if dry_run:
        print(f"DRY RUN: would create 6 units, 20 lessons, delete {mono_id}", flush=True)
        for mod, les, srcs, _snap in plans:
            print(
                f"  {mod.unit_id} L{les.lesson_in_module} {les.title!r} <- {les.source_parser_lesson_numbers}",
                flush=True,
            )
        conn.close()
        return 0

    conn.close()

    for mod in g2_science_modules():
        _delete_unit_rows(db_path, mod.unit_id)

    _delete_unit_rows(db_path, mono_id)

    for mod in g2_science_modules():
        _seed_unit(
            db_path,
            mod.unit_id,
            2,
            "Science",
            mod.module_number,
            mod.unit_title,
        )

    conn = sqlite3.connect(db_path, timeout=60.0)
    conn.row_factory = sqlite3.Row
    for mod in g2_science_modules():
        conn.execute(
            """INSERT OR IGNORE INTO units_intro (unit_id, essential_questions, enduring_understandings)
               VALUES (?, '[]', '[]')""",
            (mod.unit_id,),
        )
        conn.execute(
            """
            UPDATE units SET source_doc_id = ?, source_url = ?, ingested_at = ?,
            ingest_run_id = ?, ingest_parser_version = ?
            WHERE id = ?
            """,
            (
                source_doc_id,
                source_url,
                ingest_meta.get("ingested_at"),
                ingest_meta.get("ingest_run_id"),
                str(ingest_meta.get("ingest_parser_version", "")) + "+canonical_merge@v1",
                mod.unit_id,
            ),
        )
    conn.commit()

    for mod, les, sources, snap in plans:
        row = _build_canonical_lesson_row(
            module=mod,
            spec=les,
            sources=sources,
            source_url=source_url,
            source_doc_id=source_doc_id,
            ingest_meta=ingest_meta,
        )
        curriculum.upsert_lesson(row)
        conn.execute(
            "DELETE FROM science_lesson_day_segments WHERE lesson_id = ?", (row["id"],)
        )
        conn.commit()
        _apply_snapshot_links(conn, row["id"], snap[0], snap[1], snap[2])
        conn.commit()
        if row.get("science_li_sc_day_structured"):
            curriculum.replace_science_lesson_day_segments(
                row["id"],
                json.loads(row["science_li_sc_day_structured"]),
            )

    conn.close()
    print(
        f"Canonicalized Grade 2 Science: 6 modules, 20 lessons in {db_path}. Removed {mono_id}.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--db",
        default="",
        help="curriculum.db path (default: CURRICULUM_DB_PATH or data/curriculum.db)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    db_path = (args.db or "").strip() or os.environ.get(
        "CURRICULUM_DB_PATH", str(_REPO_ROOT / "data" / "curriculum.db")
    )
    return run_canonicalize_g2_science_modules(db_path, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
