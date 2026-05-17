# ELA "Summary of Key Learning" table structure (SSOT)

This document describes the **unit-level** matrix that [`tools/scraper/ela_summary_table.py`](../../tools/scraper/ela_summary_table.py) detects when `ingest_to_curriculum` runs with **`subject="ELA"`**. Header strings are also defined on [`SubjectConfig.ELA_SUMMARY_TABLE`](../../tools/scraper/subject_config.py).

It is **not** the same as per-lesson **detailed** teacher-guide tables later in the DOCX; those are still ingested via the normal semantic stream.

## Grid layout

| Row | Column A | Column B | Column C | Column D |
|-----|----------|----------|----------|----------|
| 0 (title) | **Merged / single logical cell** | (same) | (same) | (same) |
| 1 (headers) | Lesson | Learning Intentions and Success Criteria | Daily Instructional Task | Content and Learning Strategies |
| 2+ (data) | Lesson number only (e.g. `1`, `2`) | See below | See below | See below |

**Title row:** Cell text must match **Summary of Key Learning** (spacing/punctuation normalized; see `is_summary_key_learning_table`).

**Detector:** Requires at least **three** rows (title, headers, one data row). Merged cells in DOCX may appear as one physical cell with content in the first column and empty siblings; the parser accepts that pattern.

## Column B — Learning Intentions and Success Criteria

1. A line starting with **`Learning Intention:`** or **`Learning Intentions:`** (case-insensitive) opens the intention block.
2. A line starting with **`Success Criteria:`** (case-insensitive) ends the intention block and opens the criteria block.
3. Between and after these labels, teachers use **multiple lines** (e.g. several “I am learning…” / “We are learning…” sentences, then several “I can…” lines).

**Extracted fields (JSON):**

- `learning_intention` — plain text between the first intention label and the success criteria label.
- `success_criteria` — plain text after the success criteria label.
- `learning_intentions_success_html` — full column HTML from paragraph runs (bold, links preserved when present in DOCX).

## Column C — Daily Instructional Task

Typical shape:

1. **Task type title** in **bold** at the start (e.g. *Oral Explanatory Task*, *Explanatory Writing*).
2. A short **narrative** (paragraph(s)).
3. **Bulleted** steps where Word uses list formatting.
4. Optional **Rubric** label (often bold) plus **hyperlink** text to a resource.

**Extracted fields:**

- `daily_task_title` — from the **first contiguous bold run sequence** in the cell; if none, a **fallback** uses the first substantial plain-text line of the cell.
- `daily_task_body` — remainder of the cell as HTML (`json_to_html` from the parser).

## Column D — Content and Learning Strategies

Line-oriented **activity labels** with **standards and codes** grouped at the **end** of each line (comma-separated), for example:

- `Unit Introduction: Essential Question`
- `Preview SL.PE.2.1A-C`
- `Vocabulary L.VL.2.2` (source docs may contain stray spaces or double dots, e.g. `L .VL.2..2`)
- `Read Aloud and Text Dependent Questions RI.CR.2.1, ...`
- `Daily Instructional Task: Partner Discussions ... RI.CR.2.1, ...`

**Extracted fields:**

- `content_and_strategies` — full column HTML.
- `standards_mentions` — deduplicated list of code-like tokens from **plain** cell text after **spacing normalization** (spaces around dots removed so regex can match district typos). Patterns live in `SubjectConfig.ELA["patterns"]["standards_summary_mentions"]` (NJ ELA-style `RL.|RI.|SL.|W.|L.` codes, optional letter suffix ranges like `2.1A-C`, and NJ social studies-style `6.1.n.*` segments).

## Lesson count

The number of data rows is **defined by the document** (e.g. one unit tab may have 12, 15, or other counts). Parsers must not assume a fixed lesson count.

## Related code

- Detection and parsing: [`tools/scraper/ela_summary_table.py`](../../tools/scraper/ela_summary_table.py)
- Stream skip + merge into `lessons.ela_key_learning_summary`: [`tools/scraper/table_extractor.py`](../../tools/scraper/table_extractor.py) (`_stream_docx_for_curriculum_ingest`)
- Architecture overview: [CURRICULUM_EXTRACTION_ARCHITECTURE.md](./CURRICULUM_EXTRACTION_ARCHITECTURE.md)
