import os
import sys
import json
import hashlib
import re
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union

from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl, CT_Row, CT_Tc
from docx.oxml.ns import qn
try:
    from tools.scraper.subject_config import SubjectConfig
except ImportError:
    from subject_config import SubjectConfig
try:
    from tools.scraper.docs_client import DocsClient
except ImportError:
    from docs_client import DocsClient

try:
    from tools.scraper.ingest_failure_codes import apply_ingest_failure_code
except ImportError:
    from ingest_failure_codes import apply_ingest_failure_code

# Add parent directory to path for backend imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database.sqlite_impl import SQLiteDatabase
from backend.database.curriculum import CurriculumDatabase

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_source_doc_id(source_url: str) -> Optional[str]:
    if not source_url:
        return None
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", source_url)
    return m.group(1) if m else None


_LESSON_START_TO_INGEST_WARN_RATIO = 2.0


def _looks_like_equation_token_loss(text: str) -> bool:
    """Heuristic: detect standards lines where math/equation placeholders appear blank."""
    t = (text or "").lower()
    if not t:
        return False
    signals = (
        "as a multiple of .",
        "as the product ,",
        "by the equation .",
        "in general, .",
        "will eat  of a pound",
    )
    return any(s in t for s in signals)


def _xml_local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _omml_node_to_text(node: Any) -> str:
    """Best-effort OMML -> text for curriculum fidelity (fractions, superscripts, roots)."""
    name = _xml_local_name(getattr(node, "tag", ""))
    if name in {"oMath", "oMathPara", "r", "box", "d"}:
        return "".join(_omml_node_to_text(c) for c in node)
    if name == "t":
        return (node.text or "").strip()
    if name == "f":
        num = ""
        den = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "num":
                num = _omml_node_to_text(c)
            elif c_name == "den":
                den = _omml_node_to_text(c)
        if num and den:
            return f"{num}/{den}"
        return "".join(_omml_node_to_text(c) for c in node)
    if name == "sSup":
        base = ""
        sup = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "e":
                base = _omml_node_to_text(c)
            elif c_name == "sup":
                sup = _omml_node_to_text(c)
        if base and sup:
            return f"{base}^{sup}"
    if name == "sSub":
        base = ""
        sub = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "e":
                base = _omml_node_to_text(c)
            elif c_name == "sub":
                sub = _omml_node_to_text(c)
        if base and sub:
            return f"{base}_{sub}"
    if name == "rad":
        deg = ""
        expr = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "deg":
                deg = _omml_node_to_text(c)
            elif c_name == "e":
                expr = _omml_node_to_text(c)
        if expr:
            return f"root({deg},{expr})" if deg else f"sqrt({expr})"
    if name == "nary":
        op = ""
        body = ""
        lower = ""
        upper = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "chr":
                op = c.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "")
            elif c_name == "sub":
                lower = _omml_node_to_text(c)
            elif c_name == "sup":
                upper = _omml_node_to_text(c)
            elif c_name == "e":
                body = _omml_node_to_text(c)
        if op or body:
            lim = ""
            if lower and upper:
                lim = f"_({lower})^({upper})"
            elif lower:
                lim = f"_({lower})"
            elif upper:
                lim = f"^({upper})"
            return f"{op}{lim}{body}"
    if name == "d":
        begin = ""
        end = ""
        expr = ""
        for c in node:
            c_name = _xml_local_name(getattr(c, "tag", ""))
            if c_name == "begChr":
                begin = c.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "")
            elif c_name == "endChr":
                end = c.get("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "")
            elif c_name == "e":
                expr = _omml_node_to_text(c)
        if expr:
            return f"{begin}{expr}{end}"
    if name == "m":
        rows: List[str] = []
        for c in node:
            if _xml_local_name(getattr(c, "tag", "")) == "mr":
                cells = []
                for cc in c:
                    if _xml_local_name(getattr(cc, "tag", "")) == "e":
                        cells.append(_omml_node_to_text(cc))
                if cells:
                    rows.append(",".join(cells))
        if rows:
            return "[" + ";".join(rows) + "]"
    return "".join(_omml_node_to_text(c) for c in node)


def _join_runs_for_paragraph_text(runs: List[Dict[str, Any]]) -> str:
    """Join run text while avoiding token glue around recovered math expressions."""
    out: List[str] = []
    prev_last = ""
    for run in runs:
        text = run.get("text") or ""
        if not text:
            continue
        cur_first = text[0]
        # Insert a spacer when two alphanumeric boundaries collide (e.g., "a/bas").
        if out and prev_last.isalnum() and cur_first.isalnum():
            out.append(" ")
        out.append(text)
        prev_last = text[-1]
    return "".join(out).strip()


def _annotate_ingest_report(
    report: Dict[str, Any],
    ingest_stats: Dict[str, Any],
    ingested_count: int,
) -> None:
    lessons_started_raw = int(ingest_stats.get("lessons_started") or 0)
    lessons_started_unique = int(ingest_stats.get("lessons_started_unique") or lessons_started_raw)
    report["ingest_stats"] = {
        "lessons_started": lessons_started_raw,
        "lessons_started_unique": lessons_started_unique,
        "paragraphs_appended": ingest_stats.get("paragraphs_appended"),
        "section_hits": dict(ingest_stats.get("section_hits") or {}),
        "suspected_equation_token_loss_standards": ingest_stats.get(
            "suspected_equation_token_loss_standards", 0
        ),
    }
    if ingested_count == 0 and lessons_started_unique == 0:
        apply_ingest_failure_code(report, "ANCHOR_MISS")
        report["warnings"].append("Ingest: no lesson titles matched the subject lesson pattern.")
    elif ingested_count == 0:
        apply_ingest_failure_code(report, "EMPTY_FIELD")
        report["warnings"].append(
            "Ingest: lessons started in stream but none had persistable body fields."
        )
    elif ingested_count > 0:
        start_to_ingest_ratio = lessons_started_unique / float(ingested_count)
        report["ingest_stats"]["lessons_started_to_ingested_ratio"] = round(
            start_to_ingest_ratio, 3
        )
        if start_to_ingest_ratio > _LESSON_START_TO_INGEST_WARN_RATIO:
            apply_ingest_failure_code(report, "ANCHOR_MISS")
            report["warnings"].append(
                "Ingest: lessons_started_unique/lessons_ingested ratio exceeds "
                f"{_LESSON_START_TO_INGEST_WARN_RATIO:.1f} "
                f"({lessons_started_unique}/{ingested_count}); review lesson title/anchor matching."
            )
    eq_loss_hits = int(ingest_stats.get("suspected_equation_token_loss_standards") or 0)
    if eq_loss_hits > 0:
        apply_ingest_failure_code(report, "EXPORT_LOSS")
        report["warnings"].append(
            "Ingest: detected standards lines with likely equation-token loss "
            f"({eq_loss_hits} hit(s)); review Docs/Export math fidelity."
        )


def _build_ingest_report(
    run_id: str,
    target_unit: str,
    source_doc_id: Optional[str],
    source_url: Optional[str],
    started_at: str,
    ended_at: str,
    parser_version: str,
    lessons_ingested: int,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "target_unit": target_unit,
        "source_doc_id": source_doc_id,
        "source_url": source_url,
        "started_at": started_at,
        "ended_at": ended_at,
        "parser_version": parser_version,
        "lessons_ingested": lessons_ingested,
        "primary_failure_code": None,
        "secondary_failure_codes": [],
        "warnings": [],
        "fidelity_checks": {
            "sample_lines_checked": 0,
            "mismatches": 0,
        },
    }


def _write_ingest_report(report: Dict[str, Any]) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "ingest_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report['run_id']}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return str(out_path)


def _normalize_anchor_text(text: str) -> str:
    t = (text or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _resolve_field_from_anchors(
    normalized_text: str,
    field_map: Dict[str, str],
    max_len_for_substring: int = 120,
    short_key_len: int = 8,
) -> Optional[str]:
    if not normalized_text:
        return None
    if normalized_text in field_map:
        return field_map[normalized_text]
    if len(normalized_text) > max_len_for_substring:
        return None
    best_field: Optional[str] = None
    best_key_len = -1
    for key, field in field_map.items():
        if not key:
            continue
        if len(key) < short_key_len:
            if normalized_text == key:
                matched = True
            elif (
                normalized_text.startswith(key + " ")
                or normalized_text.startswith(key + ":")
                or normalized_text.startswith(key + "(")
                or normalized_text.startswith(key + ".")
            ):
                matched = True
            else:
                matched = False
        else:
            matched = key in normalized_text
        if matched and len(key) > best_key_len:
            best_key_len = len(key)
            best_field = field
    return best_field

def _extract_vocab_terms(text: str) -> List[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    # Remove common bullet glyphs/prefixes and split lightweight term lists.
    cleaned = re.sub(r"^[\u2022\-\*\u25CF\u25A0\s]+", "", cleaned)
    parts = re.split(r"[,\n;]+", cleaned)
    return [p.strip() for p in parts if p and p.strip()]

def _is_procedure_subheader(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    return bool(
        re.match(
            r"^(warm-?up|lesson\s+activity|activity\s*\d+|cool-?down|lesson synthesis|activity synthesis)\b",
            t,
        )
    )

def _is_non_standard_heading(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    return bool(
        re.match(
            r"^(warm-?up|lesson\s+activity|activity\s*\d+|cool-?down|lesson synthesis|activity synthesis|math workshop resources|homework|suggested centers|gifted and talented|amplify desmos math)\b",
            t,
        )
    )

_STANDARDS_SECTION_META: Dict[str, Dict[str, str]] = {
    "new jersey state learning standards": {
        "panel": "left",
        "section": "New Jersey State Learning Standards",
    },
    "mathematical practice standards": {
        "panel": "left",
        "section": "Mathematical Practice Standards",
    },
    "national council of teachers of mathematics content standards": {
        "panel": "right",
        "section": "National Council of Teachers of Mathematics Content Standards",
    },
    "national council of teachers of mathematics process standards": {
        "panel": "right",
        "section": "National Council of Teachers of Mathematics Process Standards",
    },
}


def _ends_with_sentence_terminal(text: str) -> bool:
    t = (text or "").rstrip()
    if not t:
        return False
    return bool(re.search(r"(?:\.{3}|[.!?]|\u2026)\s*[\)\]\"'”’]*\s*$", t))


def _starts_with_lowercase_continuation(text: str) -> bool:
    s = (text or "").lstrip()
    if not s:
        return False
    return s[0].isalpha() and s[0].islower()


def _should_merge_docx_soft_break(prev: Dict[str, Any], nxt: Dict[str, Any]) -> bool:
    if prev.get("type") != "paragraph" or nxt.get("type") != "paragraph":
        return False
    if prev.get("is_bullet") and nxt.get("is_bullet"):
        return False
    p = (prev.get("text") or "").strip()
    n = (nxt.get("text") or "").strip()
    if not p or not n:
        return False
    if len(p) > 6000 or len(n) > 6000:
        return False
    if _ends_with_sentence_terminal(p):
        return False
    if not _starts_with_lowercase_continuation(n):
        return False
    if _is_procedure_subheader(n) or _is_non_standard_heading(n):
        return False
    nh = _normalize_anchor_text(n)
    if nh in _STANDARDS_SECTION_META:
        return False
    return True


def _merge_two_paragraph_items(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    text_a = (a.get("text") or "").rstrip()
    text_b = (b.get("text") or "").lstrip()
    merged_text = f"{text_a} {text_b}".strip()
    runs_a = list(a.get("runs") or [])
    runs_b = list(b.get("runs") or [])
    runs: List[Dict[str, Any]] = []
    runs.extend(runs_a)
    if runs_a and runs_b and text_a and text_b:
        runs.append({"type": "run", "text": " ", "style": None})
    runs.extend(runs_b)
    return {
        "type": "paragraph",
        "text": merged_text,
        "is_bullet": False,
        "ilvl": 0,
        "runs": runs,
    }


# Lesson fields where DOCX often inserts a stray paragraph break mid-sentence.
_SOFT_BREAK_MERGE_SECTIONS: frozenset = frozenset({
    "narrative_html",
    "purpose",
    "procedure_html",
    "learning_intentions",
    "objectives_student",
    "mlr",
    "materials",
    "vocabulary",
    "instructional_resources",
    "daily_instructional_task",
    "success_criteria",
    "essential_questions",
    "lesson_narrative",
})


def merge_docx_soft_break_paragraphs(buffer: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Join adjacent paragraphs that Word split mid-sentence (stray Enter).
    Heuristic: previous chunk lacks sentence-ending punctuation; next starts with a lowercase letter.
    """
    if not buffer:
        return buffer
    out: List[Dict[str, Any]] = []
    i = 0
    while i < len(buffer):
        item = buffer[i]
        if item.get("type") != "paragraph":
            out.append(item)
            i += 1
            continue
        cur: Dict[str, Any] = item
        j = i + 1
        while j < len(buffer):
            nxt = buffer[j]
            if not _should_merge_docx_soft_break(cur, nxt):
                break
            cur = _merge_two_paragraph_items(cur, nxt)
            j += 1
        out.append(cur)
        i = j
    return out


class RecursiveTableParser:
    """
    Extracted data from complex and nested tables in .docx files.
    Identifies 'Lesson X' structures for curriculum ingestion.
    """
    
    FRIENDLY_NAMES = {
        "p": "paragraph",
        "tbl": "table",
        "tr": "table-row",
        "tc": "table-cell",
        "r": "run",
        "t": "text"
    }

    def __init__(self, db_path: str = r"d:\LP\data\curriculum.db"):
        self.db_path = db_path
        self.db = SQLiteDatabase(db_path=db_path) # Always initialize db
        self.depth_limit = 10
        self.doc = None
        self._current_lesson = None
        self._current_section = None
        self._buffer = []
        self._docs_client = None # Lazy-load docs client

    def parse_document(self, docx_path: str) -> List[Dict[str, Any]]:
        """Entry point for parsing a document."""
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"File not found: {docx_path}")
            
        doc = Document(docx_path)
        self.doc = doc
        content = []
        
        # In docx, top-level elements can be paragraphs or tables
        for element in doc.element.body:
            parsed = self.parse_element(element)
            if parsed:
                content.append(parsed)
                
        return content

    def parse_element(self, element: Any, depth: int = 0) -> Optional[Dict[str, Any]]:
        """Generic recursive handler for Docx elements."""
        if depth > self.depth_limit:
            return None
            
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag_name == "p":
            return self._parse_paragraph(element)
        elif tag_name == "tbl":
            return self._parse_table(element, depth)
        
        return None

    def _parse_paragraph(self, p_element: Any) -> Dict[str, Any]:
        """Parses a paragraph element into JSON with bullet detection and link extraction."""
        p = Paragraph(p_element, None)
        
        # Bullet/Numbering detection
        ilvl = 0
        num_pr = p._element.xpath('.//w:numPr')
        if num_pr:
            ilvl_xpath = num_pr[0].xpath('./w:ilvl/@w:val')
            if ilvl_xpath:
                try: ilvl = int(ilvl_xpath[0])
                except ValueError: ilvl = 0
            
        runs = []
        # XML Traversal for high-fidelity link and run extraction
        for child in p._element:
            tag = child.tag.split('}')[-1]
            
            if tag == "hyperlink":
                r_id = child.get(qn('r:id'))
                url = self.doc.part.rels[r_id].target_ref if self.doc and r_id in self.doc.part.rels else None
                
                # Extract text within hyperlink (can have multiple runs)
                link_text = "".join([t.text for t in child.xpath('.//w:t')])
                
                style = {"link": True}
                if url:
                    style["url"] = url
                    # Extract Google ID if applicable
                    g_id_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
                    if g_id_match:
                        style["google_id"] = g_id_match.group(1)

                runs.append({
                    "type": "run",
                    "text": link_text,
                    "style": style
                })
            elif tag == "r":
                # Standard run
                run_obj = None
                # Low-level run extraction to keep it simple but accurate
                for r in p.runs:
                    if r._element is child:
                        run_obj = r
                        break
                
                if run_obj:
                    style = {}
                    if run_obj.bold: style["bold"] = True
                    if run_obj.italic: style["italic"] = True
                    runs.append({
                        "type": "run",
                        "text": run_obj.text,
                        "style": style if style else None
                    })
            elif tag in {"oMath", "oMathPara"}:
                eq_text = _omml_node_to_text(child)
                if eq_text:
                    runs.append({
                        "type": "run",
                        "text": eq_text,
                        "style": {"equation": True}
                    })
        paragraph_text = _join_runs_for_paragraph_text(runs)
        return {
            "type": "paragraph",
            # Use run-composed text so OMML equations are preserved for ingest and LLM feed.
            "text": paragraph_text or p.text,
            "is_bullet": bool(num_pr),
            "ilvl": ilvl,
            "runs": runs
        }

    def _parse_table(self, tbl_element: CT_Tbl, depth: int) -> Dict[str, Any]:
        """Parses a table element recursively with robust merge handling."""
        rows = []
        
        # 1. Get max grid columns (Bypassing python-docx Twips conversion error)
        try:
            grid_cols = [int(float(gc.get(qn('w:w')))) for gc in tbl_element.tblGrid.gridCol_lst if gc.get(qn('w:w'))]
            total_grid_width = sum(grid_cols)
        except Exception as e:
            log(f"DEBUG: Grid parsing failed. {e}", "WARNING")
            grid_cols = []
            total_grid_width = 0
        
        for tr_xml in tbl_element.tr_lst:
            row_cells = []
            for tc_xml in tr_xml.tc_lst:
                v_merge = tc_xml.vMerge
                
                cell_json = {
                    "type": "table-cell",
                    "grid_span": tc_xml.grid_span,
                    "v_merge": v_merge,
                    "content": []
                }
                
                # Recurse through cell elements
                for child in tc_xml:
                    child_parsed = self.parse_element(child, depth + 1)
                    if child_parsed:
                        cell_json["content"].append(child_parsed)
                
                row_cells.append(cell_json)
                
            rows.append({
                "type": "table-row",
                "cells": row_cells
            })
            
        return {
            "type": "table",
            "rows": rows,
            "depth": depth
        }

    def flatten_for_llm(self, content: List[Dict[str, Any]]) -> str:
        """Converts structured JSON to a flattened text representation.

        NOTE (fidelity): keep raw Unicode/math-like tokens as-is here.
        Do not normalize/remove special characters in this path, because LLM
        prompts rely on exact curriculum text fidelity when symbols are present.
        """
        lines = []
        for item in content:
            if item["type"] == "paragraph":
                lines.append(item["text"])
            elif item["type"] == "table":
                lines.append(self._table_to_text(item))
        return "\n".join(lines)

    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """Flatten table to a Markdown-style string."""
        if not table.get("rows"):
            return ""
            
        lines = []
        for row in table["rows"]:
            cells = []
            for cell in row["cells"]:
                cell_text = []
                for item in cell.get("content", []):
                    if item["type"] == "paragraph":
                        cell_text.append(item["text"])
                    elif item["type"] == "table":
                        cell_text.append(self._table_to_text(item))
                
                content = " ".join(cell_text).replace("\n", " ").strip()
                cells.append(content if content else " ")
            
            lines.append("| " + " | ".join(cells) + " |")
            
        return "\n".join(lines)
    def json_to_html(self, elements: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Converts structured JSON back to basic HTML, now with nested list support."""
        if isinstance(elements, list):
            html = ""
            list_stack = [] # Stack of current ilvl
            
            for e in elements:
                if e.get("is_bullet"):
                    target_lvl = e.get("ilvl", 0)
                    
                    # Handle level changes
                    if not list_stack:
                        html += "<ul>"
                        list_stack.append(target_lvl)
                    elif target_lvl > list_stack[-1]:
                        while target_lvl > list_stack[-1]:
                            html += "<ul>"
                            # Small hack to handle skips like 0 -> 2
                            list_stack.append(list_stack[-1] + 1)
                        # Ensure the last one matches target
                        list_stack[-1] = target_lvl
                    elif target_lvl < list_stack[-1]:
                        while list_stack and target_lvl < list_stack[-1]:
                            html += "</ul>"
                            list_stack.pop()
                        if not list_stack: # Should not happen if well-formed
                            html += "<ul>"
                            list_stack.append(target_lvl)
                    
                    # Add List Item
                    html += f"<li>{self._get_paragraph_inner_html(e)}</li>"
                else:
                    # Close all lists before non-bullet content
                    while list_stack:
                        html += "</ul>"
                        list_stack.pop()
                    html += self.json_to_html(e)
            
            # Close any remaining lists
            while list_stack:
                html += "</ul>"
                list_stack.pop()
            return html
        
        type = elements.get("type")
        if type == "paragraph":
            inner = self._get_paragraph_inner_html(elements)
            # If it's a bullet, we don't wrap it in <p> because it's in <li>
            if elements.get("is_bullet"):
                return inner
            return f"<p>{inner}</p>" if inner else ""
        
        elif type == "table":
            html = '<table border="1">'
            for row in elements.get("rows", []):
                html += "<tr>"
                for cell in row.get("cells", []):
                    span = f' colspan="{cell["grid_span"]}"' if cell.get("grid_span") and cell["grid_span"] > 1 else ""
                    html += f"<td{span}>"
                    html += self.json_to_html(cell.get("content", []))
                    html += "</td>"
                html += "</tr>"
            html += "</table>"
            return html
        
        return ""

    def _get_paragraph_inner_html(self, p_json: Dict[str, Any]) -> str:
        """Helper to get HTML inside a paragraph (handles runs and links)."""
        inner = ""
        for run in p_json.get("runs", []):
            text = run["text"]
            if not text: continue
            style = run.get("style") or {}
            
            # Apply wrapping
            if style.get("bold"): text = f"<b>{text}</b>"
            if style.get("italic"): text = f"<i>{text}</i>"
            
            # Link wrapping
            if style.get("link") and style.get("url"):
                url = style["url"]
                g_id = style.get("google_id")
                # Add data-resource-id for the local-first logic
                attr = f' data-resource-id="{g_id}"' if g_id else ""
                # Open external curriculum links in a new tab (Drive, ePro, Amplify, etc.)
                text = (
                    f'<a href="{url}" target="_blank" rel="noopener noreferrer"{attr}>'
                    f"{text}</a>"
                )
                
            inner += text
        return inner

    def flatten_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively flattens all paragraphs and sub-tables into a single sequence."""
        flat = []
        for e in elements:
            if e["type"] == "paragraph":
                flat.append(e)
            elif e["type"] == "table":
                flat.append(e)
                for row in e.get("rows", []):
                    for cell in row.get("cells", []):
                        flat.extend(self.flatten_elements(cell.get("content", [])))
        return flat

    def parse_to_stream(self, docx_path: str):
        """Generates a linearized stream of semantic elements from the document."""
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"File not found: {docx_path}")
            
        doc = Document(docx_path)
        self.doc = doc
        for element in doc.element.body:
            tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            
            if tag_name == "p":
                yield self._parse_paragraph(element)
            elif tag_name == "tbl":
                table_json = self._parse_table(element, 0)
                for item in self._table_to_semantic_items(table_json):
                    yield item

    def _table_to_semantic_items(self, table_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts a table into a sequence of elements, handling side-by-side metadata."""
        items = []
        rows = table_json.get("rows", [])
        
        # Known headers that can appear side-by-side
        HEADERS = ["supplemental resources", "formative assessment", "materials", "vocabulary", "standards"]
        
        for row in rows:
            cells = row.get("cells", [])
            is_processed = False
            
            if len(cells) == 2:
                c0_cont = cells[0].get("content", [])
                c1_cont = cells[1].get("content", [])
                c0_text = "".join([p.get("text", "") for p in c0_cont if p["type"] == "paragraph"]).strip()
                c1_text = "".join([p.get("text", "") for p in c1_cont if p["type"] == "paragraph"]).strip()
                
                # Check if both cells are headers
                is0 = any(h in c0_text.lower() for h in HEADERS) and len(c0_text) < 60
                is1 = any(h in c1_text.lower() for h in HEADERS) and len(c1_text) < 60
                
                if is0 and is1:
                    # Both are headers, but they might contain the values too
                    items.append({"type": "property", "key": c0_text, "content": c0_cont})
                    items.append({"type": "property", "key": c1_text, "content": c1_cont})
                    is_processed = True
                elif is0:
                    items.append({"type": "property", "key": c0_text, "content": c1_cont})
                    is_processed = True
            
            if not is_processed:
                for cell in cells:
                    for content_item in cell.get("content", []):
                        if content_item["type"] == "table":
                            items.extend(self._table_to_semantic_items(content_item))
                        else:
                            items.append(content_item)
        return items

    def flush_buffer(self, lesson_data: Dict[str, Any]):
        """Flushes the current buffer into the appropriate section of the lesson."""
        if not self._buffer or not lesson_data: return
        section = lesson_data.get("_current_section") or "procedure_html"
        buf_for_html: List[Dict[str, Any]] = self._buffer
        if section in _SOFT_BREAK_MERGE_SECTIONS:
            buf_for_html = merge_docx_soft_break_paragraphs(list(self._buffer))
        lesson_data[section] += self.json_to_html(buf_for_html)
        
        # Extract links and standards from buffer
        standards_section_headers = set(_STANDARDS_SECTION_META.keys())

        current_standard_code: Optional[str] = None
        current_structured_entry: Optional[Dict[str, Any]] = None
        current_structured_section = lesson_data.get("_standards_section", "")
        current_structured_panel = lesson_data.get("_standards_panel", "")
        for b in self._buffer:
            if b["type"] == "paragraph":
                p_text = (b.get("text") or "").strip()
                if p_text:
                    # Standards + descriptions
                    config = SubjectConfig.get_config(lesson_data["subject"]) # Assuming subject is available
                    standard_pattern = config["patterns"]["standards"]
                    normalized_line = _normalize_anchor_text(p_text)
                    if normalized_line in standards_section_headers:
                        section_meta = _STANDARDS_SECTION_META[normalized_line]
                        current_structured_section = section_meta["section"]
                        current_structured_panel = section_meta["panel"]
                        current_standard_code = None
                        current_structured_entry = None
                        continue
                    found_codes = standard_pattern.findall(p_text)

                    if found_codes:
                        current_standard_code = None
                        current_structured_entry = None
                        for code in found_codes:
                            normalized_code = (code or "").strip()
                            if not normalized_code:
                                continue
                            if normalized_code not in lesson_data["_standards"]:
                                lesson_data["_standards"][normalized_code] = ""

                            # Handle one-line forms like "MP3. Construct viable arguments..."
                            inline = re.match(
                                rf"^\s*{re.escape(normalized_code)}[\.\:\-\s]*(.+)$",
                                p_text,
                                flags=re.IGNORECASE,
                            )
                            if inline:
                                desc = inline.group(1).strip()
                                if desc:
                                    prev = lesson_data["_standards"].get(normalized_code, "")
                                    lesson_data["_standards"][normalized_code] = (
                                        f"{prev}\n{desc}".strip() if prev else desc
                                    )
                            entry: Dict[str, Any] = {
                                "panel": current_structured_panel or "left",
                                "section": current_structured_section or "Standards",
                                "code": normalized_code,
                                "description_lines": [],
                            }
                            if inline:
                                desc = inline.group(1).strip()
                                if desc:
                                    entry["description_lines"].append(desc)
                            lesson_data["_standards_structured"].append(entry)
                            current_structured_entry = entry
                            current_standard_code = normalized_code
                    elif (
                        current_standard_code
                        and normalized_line not in standards_section_headers
                    ):
                        if _is_non_standard_heading(p_text):
                            current_standard_code = None
                            current_structured_entry = None
                            continue
                        # Continuation line for the most recent standard code.
                        prev = lesson_data["_standards"].get(current_standard_code, "")
                        lesson_data["_standards"][current_standard_code] = (
                            f"{prev}\n{p_text}".strip() if prev else p_text
                        )
                        if current_structured_entry is not None:
                            current_structured_entry["description_lines"].append(p_text)

                # Standards
                # Links / Resources
                for run in b.get("runs", []):
                    style = run.get("style") or {}
                    if style.get("link"):
                        res = {
                            "url": style["url"],
                            "google_id": style.get("google_id"),
                            "text": run["text"]
                        }
                        lesson_data["_resources"].append(res)
        lesson_data["_standards_section"] = current_structured_section
        lesson_data["_standards_panel"] = current_structured_panel
        self._buffer.clear()

    def ingest_to_curriculum(
        self,
        docx_path: str,
        unit_id: str,
        subject: str = "Math",
        source_url: Optional[str] = None,
        ingest_run_id: Optional[str] = None,
        parser_version: str = "table_extractor@v1",
    ):
        """Specialized ingestion using the Semantic Stream."""
        curr_db = CurriculumDatabase()
        started_at = _utc_now_iso()
        run_id = ingest_run_id or f"{started_at.replace(':', '-').replace('.', '-')}_{uuid.uuid4().hex[:8]}"
        source_doc_id = _extract_source_doc_id(source_url or "")
        stream = self.parse_to_stream(docx_path)
        
        lessons_data = []
        current_lesson = None
        
        config = SubjectConfig.get_config(subject)
        lesson_pattern = config["patterns"]["lesson_title"]
        standard_pattern = config["patterns"]["standards"]
        
        # Build reverse field map from anchors (normalized keys)
        FIELD_MAP: Dict[str, str] = {}
        for field, anchors in config["anchors"].items():
            for a in anchors:
                FIELD_MAP[_normalize_anchor_text(a)] = field

        # Special internal buffers for standards/vocab if not explicitly in anchors
        if "standards" not in FIELD_MAP:
            FIELD_MAP[_normalize_anchor_text("standards")] = "_standards_temp"
        if "vocabulary" not in FIELD_MAP:
            FIELD_MAP[_normalize_anchor_text("vocabulary")] = "_vocab_temp"

        ingest_stats: Dict[str, Any] = {
            "lessons_started": 0,
            "lessons_started_unique": 0,
            "paragraphs_appended": 0,
            "section_hits": Counter(),
            "suspected_equation_token_loss_standards": 0,
        }
        seen_lesson_numbers: Set[int] = set()

        for item in stream:
            item_type = item.get("type")
            if item_type == "paragraph":
                text = item.get("text", "").strip()
                lesson_match = lesson_pattern.match(text)
                if lesson_match:
                    lnum_str = lesson_match.group(1) or lesson_match.group(2)
                    lnum = int(lnum_str.split('.')[-1]) if '.' in lnum_str else int(lnum_str)
                    ltitle = lesson_match.group(3).strip().split("   ")[0]
                    ingest_stats["lessons_started"] += 1
                    if lnum not in seen_lesson_numbers:
                        seen_lesson_numbers.add(lnum)
                        ingest_stats["lessons_started_unique"] += 1
                    # Store current links before starting new lesson
                    lesson_links = []
                    if current_lesson:
                        lesson_links = [
                            r["url"] for r in current_lesson.get("_resources", [])
                            if "docs.google.com/document/d/" in r.get("url", "")
                        ]
                    
                    self.flush_buffer(current_lesson)
                    
                    # Recursive ingestion for the PREVIOUS lesson before moving to next
                    if current_lesson and lesson_links:
                        self.process_recursive_links(current_lesson, lesson_links, subject)
                    
                    if current_lesson: lessons_data.append(current_lesson)
                    current_lesson = {
                        "id": f"{unit_id}_L{lnum}", "unit_id": unit_id, "lesson_number": lnum, "title": ltitle,
                        "subject": subject,
                        "narrative_html": "", "lesson_narrative": "", "learning_intentions": "", "procedure_html": "",
                        "instructional_resources": "", "materials": "", "objectives_student": "", "purpose": "", "mlr": "",
                        "vocabulary": "", "standards_structured": "",
                        "source_doc_id": source_doc_id,
                        "source_url": source_url,
                        "ingested_at": started_at,
                        "ingest_run_id": run_id,
                        "ingest_parser_version": parser_version,
                        "_current_section": None, "_standards": {}, "_standards_structured": [], "_vocabulary": [], "_resources": [],
                        "_standards_section": "", "_standards_panel": "",
                        "_standards_temp": "", "_vocab_temp": ""
                    }
                    continue

                if not current_lesson: continue
                low_text = _normalize_anchor_text(text)
                new_section = _resolve_field_from_anchors(low_text, FIELD_MAP)
                if not new_section and _is_procedure_subheader(text):
                    new_section = "procedure_html"
                if new_section:
                    self.flush_buffer(current_lesson)
                    if new_section == "_standards_temp" and low_text in _STANDARDS_SECTION_META:
                        section_meta = _STANDARDS_SECTION_META[low_text]
                        current_lesson["_standards_section"] = section_meta["section"]
                        current_lesson["_standards_panel"] = section_meta["panel"]
                    current_lesson["_current_section"] = new_section
                    ingest_stats["section_hits"][new_section] += 1
                    # Preserve activity headers (e.g., "Warm-up: ...") as visible content.
                    if new_section == "procedure_html" and _is_procedure_subheader(text):
                        self._buffer.append(item)
                        ingest_stats["paragraphs_appended"] += 1
                    continue
                if current_lesson.get("_current_section") in {"_vocab_temp", "vocabulary"}:
                    current_lesson["_vocabulary"].extend(_extract_vocab_terms(text))
                    continue
                self._buffer.append(item)
                ingest_stats["paragraphs_appended"] += 1

            elif item_type == "property":
                if not current_lesson: continue
                key = _normalize_anchor_text(item.get("key", ""))
                field = _resolve_field_from_anchors(key, FIELD_MAP, max_len_for_substring=200)
                if not field:
                    field = next((f for k, f in FIELD_MAP.items() if k in key), None)
                if field:
                    self.flush_buffer(current_lesson)
                    if field in {"_vocab_temp", "vocabulary"}:
                        txt = "".join([p.get("text", "") for p in item["content"] if p["type"] == "paragraph"])
                        current_lesson["_vocabulary"].extend(_extract_vocab_terms(txt))
                    elif field == "instructional_resources":
                        current_lesson["instructional_resources"] += self.json_to_html(item["content"])
                    else:
                        current_lesson[field] += self.json_to_html(item["content"])
                else:
                    current_lesson["procedure_html"] += self.json_to_html(item["content"])
            
            # Note: item_type == "table" is no longer yielded by parse_to_stream
            # Contents are streamed as paragraphs/properties with table_context

        self.flush_buffer(current_lesson)
        if current_lesson:
            # Ensure the final lesson also gets recursive link enrichment.
            final_links = [
                r["url"] for r in current_lesson.get("_resources", [])
                if "docs.google.com/document/d/" in r.get("url", "")
            ]
            if final_links:
                self.process_recursive_links(current_lesson, final_links, subject)
            lessons_data.append(current_lesson)

        log(
            "INGEST_STATS: lessons_started=%s paragraphs_buffered=%s section_hits=%s"
            % (
                ingest_stats["lessons_started"],
                ingest_stats["paragraphs_appended"],
                dict(ingest_stats["section_hits"]),
            ),
        )

        unique_lessons = {
            l["id"]: l for l in lessons_data
            if any([
                l.get("narrative_html"),
                l.get("procedure_html"),
                l.get("instructional_resources"),
                l.get("learning_intentions"),
                l.get("daily_instructional_task"),
                l.get("success_criteria"),
                l.get("materials"),
                l.get("purpose"),
                l.get("mlr"),
                l.get("objectives_student"),
                l.get("vocabulary"),
                l.get("_standards"),
                l.get("_vocabulary"),
                l.get("_resources"),
            ])
        }
        
        ingested_count = 0
        with curr_db._get_conn() as conn:
            conn.execute(
                """
                UPDATE units
                SET source_doc_id = ?,
                    source_url = ?,
                    ingested_at = ?,
                    ingest_run_id = ?,
                    ingest_parser_version = ?
                WHERE id = ?
                """,
                (source_doc_id, source_url, started_at, run_id, parser_version, unit_id),
            )
            conn.commit()
        for data in unique_lessons.values():
            log(f"Upserting Lesson {data['lesson_number']}: {data['title']}")
            data["standards_structured"] = json.dumps(
                data.get("_standards_structured", []),
                ensure_ascii=False,
            )
            
            # 1. Clear existing links (individual transactions or one per lesson)
            with curr_db._get_conn() as conn:
                conn.execute("DELETE FROM lesson_standards WHERE lesson_id = ?", (data["id"],))
                conn.execute("DELETE FROM lesson_vocabulary WHERE lesson_id = ?", (data["id"],))
                conn.execute("DELETE FROM lesson_resources WHERE lesson_id = ?", (data["id"],))
                conn.commit()
                
            # 2. Save Standards
            for code, desc in data["_standards"].items():
                if _looks_like_equation_token_loss(desc):
                    ingest_stats["suspected_equation_token_loss_standards"] += 1
                try:
                    curr_db.upsert_standard(code, desc, subject)
                except TypeError:
                    curr_db.upsert_standard(code, desc)
                curr_db.link_lesson_to_standard(data["id"], code)
            
            # 3. Save Vocabulary
            for term in data["_vocabulary"]:
                curr_db.link_lesson_to_vocabulary(data["id"], term)
            
            # 4. Save Resources (Double Strategy)
            for res in data["_resources"]:
                curr_db.upsert_lesson_resource(data["id"], res)

            # 5. Save Lesson Core
            clean_data = {k: v for k, v in data.items() if not k.startswith("_")}
            curr_db.upsert_lesson(clean_data)
            ingested_count += 1
        ended_at = _utc_now_iso()
        report = _build_ingest_report(
            run_id=run_id,
            target_unit=unit_id,
            source_doc_id=source_doc_id,
            source_url=source_url,
            started_at=started_at,
            ended_at=ended_at,
            parser_version=parser_version,
            lessons_ingested=ingested_count,
        )
        _annotate_ingest_report(report, ingest_stats, ingested_count)
        report_path = _write_ingest_report(report)
        log(f"Ingest report written: {report_path}")
        return ingested_count

    def ingest_to_db(self, docx_path: str, metadata: Dict[str, Any]) -> str:
        """Parses DOCX and stores extraction cache in original_lesson_plans."""
        required = ["user_id", "week_of", "slot_number", "subject", "grade"]
        missing = [k for k in required if metadata.get(k) in (None, "")]
        if missing:
            raise ValueError(f"Missing required metadata for ingestion: {', '.join(missing)}")

        content = self.parse_document(docx_path)
        full_text = self.flatten_for_llm(content)
        content_hash = hashlib.md5(full_text.encode("utf-8")).hexdigest() if full_text else None

        source_file_path = os.path.abspath(docx_path)
        source_file_name = os.path.basename(source_file_path)
        identity = f"{metadata['user_id']}|{metadata['week_of']}|{metadata['slot_number']}|{source_file_path}"
        plan_id = hashlib.md5(identity.encode("utf-8")).hexdigest()

        plan_data = {
            "id": plan_id,
            "user_id": metadata["user_id"],
            "week_of": metadata["week_of"],
            "slot_number": int(metadata["slot_number"]),
            "subject": metadata["subject"],
            "grade": metadata["grade"],
            "homeroom": metadata.get("homeroom"),
            "source_file_path": source_file_path,
            "source_file_name": source_file_name,
            "primary_teacher_name": metadata.get("primary_teacher_name"),
            "content_json": content,
            "full_text": full_text,
            "available_days": metadata.get("available_days"),
            "has_no_school": bool(metadata.get("has_no_school", False)),
            "content_hash": content_hash,
            "status": metadata.get("status", "extracted"),
            "error_message": metadata.get("error_message"),
        }

        # original_lesson_plans lives on the app lesson-plans DB, not curriculum.db
        db = SQLiteDatabase()
        return db.create_original_lesson_plan(plan_data)

    def process_recursive_links(self, lesson: Dict[str, Any], links: List[str], subject: str):
        """Processes external links to fetch detailed content."""
        if not self._docs_client:
            try:
                self._docs_client = DocsClient()
            except Exception as e:
                print(f"[WARN] Failed to init DocsClient: {e}")
                return

        seen = set()
        for link in links:
            if link in seen:
                continue
            seen.add(link)
            # Extract Google Doc ID
            match = re.search(r"/d/([a-zA-Z0-9_-]+)", link)
            if not match:
                continue
            doc_id = match.group(1)

            print(f"[RECURSION] Fetching details for {lesson['title']} from ID: {doc_id}")

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                success = self._docs_client.export_document(
                    doc_id,
                    tmp_path,
                    mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )

                if success:
                    # Parse the detailed doc
                    # We create a new parser instance to avoid state pollution, or reset state
                    sub_parser = RecursiveTableParser(self.db_path)
                    detailed_stream = list(sub_parser.parse_to_stream(tmp_path))

                    # Merge content into our current lesson
                    # We primarily want the 'Procedure' from the detailed doc
                    detailed_html = ""
                    for item in detailed_stream:
                        if item["type"] == "paragraph":
                            detailed_html += self.json_to_html(item)
                        elif item["type"] == "property":
                            # If the detailed doc has its own headers/anchors, process them
                            key = item["key"].lower()
                            # Check if matches procedure anchors
                            if any(anchor in key for anchor in ["activity", "step", "procedure", "synthesis", "launch", "cool-down"]):
                                detailed_html += f"<h3>{item['key']}</h3>"
                                detailed_html += self.json_to_html(item["content"])

                    if detailed_html:
                        print(f"  -> Merged {len(detailed_html)} chars of detailed procedure.")
                        lesson["procedure_html"] = (lesson["procedure_html"] or "") + detailed_html
            except Exception as e:
                print(f"[WARN] Recursive link processing failed for {link}: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        # Mode: curriculum
        docx_path = sys.argv[1]
        unit_id = sys.argv[2]
        parser = RecursiveTableParser()
        count = parser.ingest_to_curriculum(docx_path, unit_id)
        log(f"Successfully processed {count} lessons into curriculum.db")
    elif len(sys.argv) > 1:
        # Mode: test/print
        path = sys.argv[1]
        parser = RecursiveTableParser()
        result = parser.parse_document(path)
        print(json.dumps(result, indent=2))
