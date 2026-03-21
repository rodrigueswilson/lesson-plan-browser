#!/usr/bin/env python3
"""
Verify strategies_pack_v2/_index.json and wida/wida_strategy_enhancements.json
stay aligned with category JSON files (single source of truth: strategies[].id).

Run from repository root:
  python tools/verify_strategy_pack_ssot.py

Exit code 0 if OK, 1 if any mismatch (prints details on stderr).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def verify() -> list[str]:
    errors: list[str] = []
    root = _root()
    pack_dir = root / "strategies_pack_v2"
    index_path = pack_dir / "_index.json"
    if not index_path.is_file():
        return [f"Missing {index_path}"]

    index = _load_json(index_path)
    categories = index.get("categories") or {}
    meta = index.get("_meta") or {}

    all_file_ids: set[str] = set()

    for cat_key, cmeta in categories.items():
        rel = (cmeta or {}).get("file")
        if not rel:
            errors.append(f"Category {cat_key!r} has no 'file' in _index.json")
            continue
        path = pack_dir / str(rel).replace("\\", "/")
        if not path.is_file():
            errors.append(f"Category {cat_key}: missing file {path}")
            continue
        data = _load_json(path)
        file_ids = []
        for s in data.get("strategies") or []:
            if isinstance(s, dict) and s.get("id"):
                file_ids.append(str(s["id"]).strip())
        file_set = set(file_ids)
        if len(file_ids) != len(file_set):
            errors.append(
                f"Category {cat_key}: duplicate id in {path.name}: {sorted(file_ids)}"
            )
        index_list = [str(x).strip() for x in (cmeta.get("strategies") or [])]
        index_set = set(index_list)
        if len(index_list) != len(index_set):
            errors.append(
                f"Category {cat_key}: duplicate id in _index.json strategies list"
            )
        if file_set != index_set:
            only_file = sorted(file_set - index_set)
            only_index = sorted(index_set - file_set)
            errors.append(
                f"Category {cat_key}: _index.json strategies mismatch vs {path.name}. "
                f"Only in JSON file: {only_file}. Only in index: {only_index}."
            )
        count = cmeta.get("count")
        if count is not None and int(count) != len(file_ids):
            errors.append(
                f"Category {cat_key}: count={count} but file has {len(file_ids)} strategies"
            )
        overlap = all_file_ids & file_set
        if overlap:
            errors.append(
                f"Category {cat_key}: ids also present in another category: {sorted(overlap)}"
            )
        all_file_ids |= file_set

    declared_total = meta.get("total_strategies")
    if declared_total is not None and int(declared_total) != len(all_file_ids):
        errors.append(
            f"_index.json _meta.total_strategies={declared_total} but distinct ids "
            f"from category files = {len(all_file_ids)}"
        )

    wida_path = root / "wida" / "wida_strategy_enhancements.json"
    if not wida_path.is_file():
        errors.append(f"Missing {wida_path}")
        return errors

    wida = _load_json(wida_path)
    adaptations = wida.get("strategy_adaptations") or {}
    wida_keys = {k for k in adaptations if isinstance(k, str) and not k.startswith("_")}
    missing_wida = sorted(all_file_ids - wida_keys)
    if missing_wida:
        errors.append(
            f"Pack ids missing from wida strategy_adaptations: {missing_wida}"
        )
    extra_wida = sorted(wida_keys - all_file_ids)
    if extra_wida:
        errors.append(
            f"wida strategy_adaptations keys not in pack: {extra_wida}"
        )

    wmeta = wida.get("_meta") or {}
    wt = wmeta.get("total_strategies")
    if wt is not None and int(wt) != len(all_file_ids):
        errors.append(
            f"wida _meta.total_strategies={wt} but pack has {len(all_file_ids)} distinct ids"
        )

    return errors


def main() -> int:
    errs = verify()
    if errs:
        print("strategy_pack_ssot verification FAILED:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("strategy_pack_ssot OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
