#!/usr/bin/env python3
"""
Analyze a Python file for refactor planning: public API and suggested extractions.

Used by start_refactor.py to pre-fill plan sections. Uses AST only (stdlib).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple


class PlanAnalysis(NamedTuple):
    """Result of analyzing a file for refactor plan content."""

    public_api_lines: list[str]
    extraction_bullets: list[str]


def _get_package_all(init_path: Path) -> list[str] | None:
    """Get __all__ from a package __init__.py if present."""
    if not init_path.is_file():
        return None
    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                names.append(elt.value)
                            elif isinstance(elt, ast.Str):
                                names.append(elt.s)
                        return names
    return None


def _analyze_python_file(file_path: Path, rel_path_str: str) -> PlanAnalysis:
    """Parse Python file and derive public API lines and extraction suggestions."""
    public_api_lines: list[str] = []
    extraction_bullets: list[str] = []

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except (OSError, SyntaxError):
        return PlanAnalysis(public_api_lines=[], extraction_bullets=[])

    package_all: list[str] | None = None
    parent_init = file_path.parent / "__init__.py"
    if parent_init.is_file():
        package_all = _get_package_all(parent_init)
    if package_all:
        public_api_lines.append("- **Package `__all__`** (from sibling `__init__.py`): " + ", ".join(package_all))

    class_methods: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in node.body
                if isinstance(n, ast.FunctionDef)
            ]
            if methods:
                class_methods[node.name] = methods

    for class_name, methods in class_methods.items():
        public_methods = [m for m in methods if not m.startswith("_") and m != "run"]
        private_methods = [m for m in methods if m.startswith("_") and not m.startswith("__")]
        if public_methods:
            public_api_lines.append(f"- **Class `{class_name}`** (public methods): " + ", ".join(public_methods))
        if not private_methods:
            continue
        prefix_to_names: dict[str, list[str]] = {}
        for m in private_methods:
            if m.startswith("_"):
                rest = m[1:]
                if "_" in rest:
                    prefix = rest.split("_")[0]
                else:
                    prefix = rest or "private"
                prefix_to_names.setdefault(prefix, []).append(m)
        for i, (prefix, names) in enumerate(
            sorted(prefix_to_names.items(), key=lambda x: -len(x[1])), start=1
        ):
            if len(names) >= 2:
                sample = "`, `".join(sorted(names)[:5])
                suffix = " ..." if len(names) > 5 else ""
                extraction_bullets.append(
                    f"{i}. **`{prefix}_*`** helpers ({len(names)} methods): `{sample}`{suffix}"
                    f" -> consider new module `.../{prefix}_*.py` or keep in facade and delegate."
                )

    if not extraction_bullets and class_methods:
        for class_name, methods in class_methods.items():
            private = [m for m in methods if m.startswith("_") and not m.startswith("__")]
            if len(private) >= 3:
                extraction_bullets.append(
                    f"1. **Class `{class_name}`** has {len(private)} private methods; group by responsibility (fill, format, placement, media) and extract to sibling modules."
                )
                break

    if not public_api_lines and class_methods:
        main_class = max(class_methods.keys(), key=lambda c: len(class_methods[c]))
        public_api_lines.append(f"- **Main class:** `{main_class}` (preserve constructor and public method signatures).")

    return PlanAnalysis(public_api_lines=public_api_lines, extraction_bullets=extraction_bullets)


def analyze_for_plan(file_path: Path, rel_path_str: str) -> PlanAnalysis:
    """
    Analyze a source file for refactor plan content.

    For .py files: uses AST to list public API and suggest extractions by method prefix.
    For other files: returns empty lines (plan will use placeholders).
    """
    if file_path.suffix != ".py":
        return PlanAnalysis(public_api_lines=[], extraction_bullets=[])
    return _analyze_python_file(file_path, rel_path_str)
