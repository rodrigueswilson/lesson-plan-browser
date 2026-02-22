# Refactoring Study: tools/docx_renderer/renderer.py (2,240 lines)

**Goal:** Reduce `renderer.py` size and clarify boundaries by extracting table/cell and optionally media logic into dedicated modules, without changing public API or behavior.

---

## 1. Current structure (renderer.py)

### 1.1 Method list and approximate line ranges

| Method | Line range | Est. lines | Role |
|--------|------------|------------|------|
| `__init__` | 67-92 | 26 | Template load, structure init |
| `_reset_state` | 93-105 | 13 | Per-render state reset |
| `_initialize_structure` | 106-148 | 43 | Detect daily-plans table, structure metadata |
| `_get_row_index` | 149-157 | 9 | Row index from structure |
| `_get_col_index` | 158-164 | 7 | Column index from structure |
| **`render`** | 165-495 | **331** | Orchestration: load doc, fill metadata, fill days, normalize, save |
| **`_fill_metadata`** | 496-624 | **129** | Fill metadata table (teacher, grade, homeroom, etc.) |
| `_extract_unique_teachers` | 625-645 | 21 | Multi-slot: unique teachers |
| `_extract_unique_subjects` | 646-664 | 19 | Multi-slot: unique subjects |
| `_abbreviate_content` | 665-712 | 48 | Truncate content for multi-slot cells |
| `_fill_day` | 713-787 | 75 | Dispatch to single- or multi-slot day fill |
| **`_fill_single_slot_day`** | 788-953 | **166** | One slot per day: fill each row/section |
| **`_fill_multi_slot_day`** | 954-1190 | **237** | Multiple slots per day: combine per row |
| **`_fill_cell`** | 1191-1879 | **689** | Fill one cell: text, inline hyperlinks, images, formatting |
| `_format_objective` | 1880-1901 | 22 | Objective section text |
| `_format_anticipatory_set` | 1902-1920 | 19 | Anticipatory set text |
| `_filter_valid_vocabulary_pairs` | 1921-1932 | 12 | Filter vocab for display |
| `_filter_valid_sentence_frames` | 1933-1943 | 11 | Filter sentence frames |
| **`_format_tailored_instruction`** | 1944-2061 | **118** | Instruction + co-teaching + ELL + vocab/frames |
| `_format_misconceptions` | 2062-2084 | 23 | Misconceptions text |
| `_format_assessment` | 2085-2116 | 32 | Assessment section text |
| `_try_structure_based_placement` | 2117-2166 | 50 | Image: row_label + cell_index match |
| **`_calculate_match_confidence`** | 2167-2283 | **117** | Fuzzy match score for hyperlinks/images |
| _inject_hyperlink_inline ... _add_hyperlink | 2284-2477 | (delegates) | Delegated to hyperlink_placement |
| **`_inject_image_inline`** | 2304-2333 | 30 | Insert image in cell |
| **`_append_unmatched_media`** | 2335-2406 | 72 | Referenced Links + Attached Images sections |
| **`_insert_images`** | 2408-2460 | 53 | Legacy: attach images at end of doc |
| `_format_homework` | 2478-2500 | 23 | Homework section text |
| `main()` | 2503-2529 | 27 | CLI entry |

**Total in renderer:** ~2,240 lines. The heaviest blocks are: `render` (~331), `_fill_cell` (~689), `_fill_multi_slot_day` (~237), `_fill_single_slot_day` (~166), `_fill_metadata` (~129), `_format_tailored_instruction` (~118), `_calculate_match_confidence` (~117).

---

## 2. Proposed extractions

### 2.1 Option A: Extract table_cell (recommended first step)

**Module:** `tools/docx_renderer/table_cell.py`

**Move from renderer into table_cell (as functions taking `renderer` as first argument):**

- `fill_metadata(renderer, doc, json_data)`
- `extract_unique_teachers(renderer, json_data)`
- `extract_unique_subjects(renderer, json_data)`
- `abbreviate_content(renderer, content, num_slots, max_length)`
- `fill_day(renderer, doc, day_name, day_data, ...)` (uses `_get_col_index`; note: `_fill_day` uses `DAY_TO_COL` in current code but that constant is not defined in the class—likely dead path or bug; use `renderer._get_col_index(day_name)` in extracted code)
- `fill_single_slot_day(renderer, table, col_idx, day_data, ...)`
- `fill_multi_slot_day(renderer, table, col_idx, slots, ...)`
- `fill_cell(renderer, table, row_idx, col_idx, text, ...)`
- `format_objective(renderer, objective)`
- `format_anticipatory_set(renderer, anticipatory)`
- `filter_valid_vocabulary_pairs(renderer, vocabulary_cognates)`
- `filter_valid_sentence_frames(renderer, sentence_frames)`
- `format_tailored_instruction(renderer, instruction, vocabulary_cognates, sentence_frames)`
- `format_misconceptions(renderer, misconceptions)`
- `format_assessment(renderer, assessment)`
- `format_homework(renderer, homework)`
- `try_structure_based_placement(renderer, image, day_name, section_name, col_idx)`
- `calculate_match_confidence(renderer, cell_text, media, day_name, section_name)`

**Renderer keeps:** `__init__`, `_reset_state`, `_initialize_structure`, `_get_row_index`, `_get_col_index`, `render()` (orchestration), `_inject_image_inline`, `_append_unmatched_media`, `_insert_images`, plus the existing one-line delegates for hyperlink and style. In `renderer.py`, each moved method becomes a one-liner that calls the table_cell function (e.g. `def _fill_metadata(self, doc, json_data): table_cell.fill_metadata(self, doc, json_data)`).

**Dependencies:**

- table_cell needs: `renderer` (for `_get_row_index`, `_get_col_index`, `structure_metadata`, `placement_stats`, `UNIT_LESSON_ROW`, `logger`, `is_originals`), and must call:
  - `_style_module.sanitize_xml_text`, `_style_module.force_font_tnr8`, `_style_module.force_font_arial10`
  - `_hyperlink_module.inject_hyperlink_inline`, `_hyperlink_module.place_hyperlink_hybrid`
  - `renderer._inject_image_inline` (stays on renderer to avoid table_cell depending on image logic in another module)
- table_cell must **not** import `renderer` (would create a circular import). So: `renderer` imports `table_cell`; `table_cell` receives `renderer` as argument and uses it as an object (no import of the renderer module).

**Estimated line move:** ~1,850 lines from renderer into table_cell. After extraction: renderer.py ~390 lines (orchestration + init + image/fallback + delegates), table_cell.py ~1,850 lines.

### 2.2 Option B: Extract media/fallback (optional second step)

**Module:** `tools/docx_renderer/media.py` (or `images.py`)

**Move:**

- `inject_image_inline(renderer, cell, image, max_width)` — decode base64, add picture + caption in cell
- `append_unmatched_media(renderer, doc, hyperlinks, images)` — Referenced Links + Attached Images sections (uses `renderer._add_hyperlink`)
- `insert_images(renderer, doc, images)` — legacy “Attached Images” at end of doc

**Renderer:** Keeps one-line delegates to media module. No new concepts; just moves ~155 lines out of renderer.

**Estimated after Option B:** renderer.py ~235 lines (orchestration + init + delegates only), table_cell.py ~1,850, media.py ~155.

### 2.3 Option C: Split table_cell into submodules (only if table_cell.py becomes hard to navigate)

Possible split:

- `table_cell/fill.py` — fill_metadata, fill_day, fill_single_slot_day, fill_multi_slot_day, fill_cell
- `table_cell/format.py` — format_objective, format_anticipatory_set, format_tailored_instruction, format_misconceptions, format_assessment, format_homework, filter_valid_*
- `table_cell/placement.py` — try_structure_based_placement, calculate_match_confidence, abbreviate_content, extract_unique_*

Only do this if a single table_cell.py (~1,850 lines) proves too large to work with; otherwise one file is simpler.

### 2.4 Option A+C: table_cell as a package (combined approach)

**Package:** `tools/docx_renderer/table_cell/` with submodules instead of a single `table_cell.py`.

| Submodule | Contents | Est. lines |
|-----------|----------|------------|
| `table_cell/fill.py` | fill_metadata, fill_day, fill_single_slot_day, fill_multi_slot_day, fill_cell | ~1,300 |
| `table_cell/format.py` | format_objective, format_anticipatory_set, format_tailored_instruction, format_misconceptions, format_assessment, format_homework, filter_valid_vocabulary_pairs, filter_valid_sentence_frames | ~280 |
| `table_cell/placement.py` | try_structure_based_placement, calculate_match_confidence, abbreviate_content, extract_unique_teachers, extract_unique_subjects | ~270 |
| `table_cell/__init__.py` | Re-export public functions so renderer can `from .table_cell import fill_metadata, fill_cell, ...` or call `table_cell.fill.fill_metadata(renderer, ...)` | ~20 |

**Internal dependencies:** `fill.py` will call functions in `format.py` (e.g. fill_cell uses format_objective, format_tailored_instruction) and in `placement.py` (e.g. calculate_match_confidence). So: fill imports format and placement; format and placement do not import fill. No cycles.

**Renderer:** Same as Option A: thin methods that call into the table_cell package, e.g. `table_cell.fill.fill_metadata(self, doc, json_data)` or, if __init__ re-exports, `table_cell.fill_metadata(self, doc, json_data)`.

**Benefits of combining A+C (package from the start):**

- **Single responsibility:** Each file has a clear role (fill vs format vs placement), aligned with SOLID.
- **Smaller files:** ~270–1,300 lines per file instead of one ~1,850-line file; easier to navigate and test.
- **One refactor:** No follow-up “split table_cell.py” step; structure is right from the start.
- **Consistency:** Matches the existing `docx_renderer` package pattern (style, hyperlink_placement, renderer as separate modules).

**Costs:**

- More files to add and wire (four files under `table_cell/` and dependency direction to respect).
- Need to decide export style: either renderer uses `table_cell.fill.fill_metadata(...)`, `table_cell.format.format_objective(...)`, or __init__.py re-exports and renderer uses `table_cell.fill_metadata(...)` (simpler call sites, but __init__.py must import from fill/format/placement).

**Recommendation:** Combining A and C and making **table_cell a package** is beneficial if you want clear boundaries and smaller files in one go. Prefer the package when:
- You value SRP and navigability over minimal file count.
- You are already doing one extraction pass and want to avoid a second split later.

Use a **single table_cell.py** (Option A only) when:
- You want the smallest change set and the fewest new files.
- You are okay with one large module and can split later (Option C) if needed.

So: **yes, combining A+C and creating a package is better for long-term maintainability;** a single table_cell.py is simpler for the first pass. Choose the package if you are comfortable with the extra wiring in one go.

---

## 3. Dependency and import rules

- **renderer.py** imports: `table_cell`, `style`, `hyperlink_placement`, and (if Option B) `media`. It does not get imported by those modules.
- **table_cell.py** imports: `style`, `hyperlink_placement`, and backend/tools (logger, config, metadata_utils, sorting_utils, table_structure, markdown_to_docx). It receives `renderer` as the first argument to every function; it must **not** `from .renderer import DOCXRenderer` (circular).
- **hyperlink_placement.py** (existing) imports: `style`. It receives `renderer` for `_calculate_match_confidence` and for style (add_hyperlink uses style.force_font_tnr8).
- **media.py** (if added) would import nothing from the package except by receiving `renderer`; it would call `renderer._add_hyperlink` for links in fallback sections.

So the dependency graph is: renderer → table_cell, renderer → hyperlink_placement, renderer → style [, renderer → media]. table_cell → style, table_cell → hyperlink_placement (for inject_hyperlink_inline / place_hyperlink_hybrid). No cycles.

**If table_cell is a package (A+C):** renderer → table_cell.fill, table_cell.format, table_cell.placement (or table_cell __init__). table_cell.fill → table_cell.format, table_cell.fill → table_cell.placement; format and placement do not import fill. table_cell.* → style, hyperlink_placement. Same no-cycle rule: table_cell never imports renderer.

---

## 4. Suggested order of work

1. **Branch:** From current `refactor/docx-renderer` (or from master if merged), create a branch e.g. `refactor/docx-renderer-table-cell`.
2. **Extract table_cell (Option A or A+C):**
   - **Option A (single module):** Implement `table_cell.py` with the 18 functions above. Each function body is the current method body, with `self` replaced by `renderer` and any call to another extracted method replaced by a call to the corresponding table_cell function (e.g. `self._format_objective(...)` → `format_objective(renderer, ...)`). For `_fill_cell` calling `self._inject_image_inline`, call `renderer._inject_image_inline(...)` (stays on renderer).
   - **Option A+C (package):** Create `table_cell/` with `fill.py`, `format.py`, `placement.py`, and `__init__.py`. Move the 18 functions into the three submodules as in 2.4; fill.py imports from format and placement. In renderer.py, replace each extracted method with a one-liner delegating to the table_cell package (e.g. `table_cell.fill.fill_metadata(self, doc, json_data)` or, if __init__ re-exports, `table_cell.fill_metadata(self, doc, json_data)`).
   - In both cases: run DOCX-related tests; fix any missing attributes or call-site errors.
3. **Optional:** Extract media (Option B) in the same branch or a follow-up.
4. **Update docs:** REFACTORING_PRIORITIES_AND_TOOLS.md Section 0.5 line counts and 1.4 if merged.

---

## 5. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Circular import (table_cell imports renderer) | table_cell never imports renderer; it only receives the renderer instance as an argument. |
| Missing attribute on renderer | After extraction, ensure renderer still has all attributes that table_cell uses (e.g. `placement_stats`, `structure_metadata`, `UNIT_LESSON_ROW`, `logger`, `is_originals`, `_get_row_index`, `_get_col_index`, `_inject_image_inline`). |
| _fill_day and DAY_TO_COL | Current code uses `self.DAY_TO_COL[day_name.lower()]` in `_fill_day` but `DAY_TO_COL` is not defined on the class. In the extracted path, use `renderer._get_col_index(day_name)` and handle -1 (skip day) instead of relying on DAY_TO_COL. |
| Test patches | Tests that patch `tools.docx_renderer.renderer.DOCXRenderer` or methods on it continue to work; no change to public API. |
| Debug print statements | Consider removing or gating the `print(f"DEBUG: _fill_cell(...)")` (and similar) in `_fill_cell` when moving to table_cell, to avoid noisy stdout. |

---

## 6. Summary

- **Largest gain:** Move table/cell and format/placement logic into `table_cell` (either one module ~1,850 lines or a package with fill/format/placement submodules), reducing renderer.py to ~390 lines (orchestration, init, image/fallback, delegates).
- **A+C (package):** Combining A and C and making table_cell a package gives clearer SRP and smaller files in one pass; choose it if you want better long-term structure. Single table_cell.py is simpler for a minimal first pass.
- **Optional:** Move image and fallback-media logic into `media.py` (~155 lines), bringing renderer down to ~235 lines.
- **No new public API;** `from tools.docx_renderer import DOCXRenderer` unchanged. All extraction is internal to the package with renderer delegating to new modules.
