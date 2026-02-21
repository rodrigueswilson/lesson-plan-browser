# Prioritized Task Roadmap for Next Session

This document details the critical investigation and remediation tasks identified following the latest deployment. All tasks focus on Hyperlink Integrity, Document Generation Reliability, and Formatting Consistency.

## 1. Hyperlink Integrity & Leakage Analysis

### Task 1.1: Create Hyperlink Comparison Script
**Objective:** Programmatically verify that hyperlinks in the transformed output match the original source in terms of *count*, *location*, and *day*.
- **Input:** Original extracted JSON (or DOCX) and Transformed Output JSON (or DOCX).
- **Logic:**
    - Iterate through every cell (Day/Slot).
    - Extract all hyperlinks from the Original.
    - Extract all hyperlinks from the Transformed output.
    - **Pass Condition:** 
        - Total link count matches.
        - Every link in Original exists in Transformed.
        - No "alien" links (links belonging to other days) appear in the cell.
- **Output:** A report highlighting specific cells with discrepancies (missing links, extra links, or displaced links).

### Task 1.2: Enforce Hyperlink Whitespace
**Objective:** Ensure every hyperlink in the final DOCX is surrounded by spaces to prevent text merging.
- **Problem:** Links are sometimes glued to surrounding text (e.g., `word[Link](url)` instead of `word [Link](url)`).
- **Implementation:**
    - Modified `docx_renderer.py` -> `_fill_cell`.
    - In the "Smart Inline Replacement" logic, ensure that the replacement formatting `f" {match} "` explicitly includes shielding spaces if they don't already exist.
    - Check regex lookbehinds/lookaheads to avoid double spacing.

### Task 1.3: Deep Dive into Persistent Leakage
**Objective:** Solve why links like "02 - Second Grade Unit Description..." appear repeatedly on days they don't belong (e.g., Tuesday link showing up on Monday).
- **Hypothesis:**
    - The "Smart Inline Replacement" might be matching text globally across the whole string without respecting the `day_hint` constraint (Partial fix applied, verification needed).
    - The "Fuzzy Matcher" (`_calculate_match_confidence`) might be too aggressive (Strategy 3 or Context Match) and overriding the day hint.
- **Action:** Use the script from Task 1.1 to isolate specific failure cases and trace the `_fill_cell` decision path for those specific links.

---

## 2. Document Generation Issues

### Task 2.1: Debug Partial Missing `combined_originals.docx`
**Objective:** Identify why the `combined_originals.docx` file is sometimes missing from the `originals/` directory.
- **Context:** This file is supposed to be generated immediately after parallel extraction (Phase 1).
- **Potential Causes:**
    - Race condition in `BatchProcessor` where the file generation task is cancelled or fails silently.
    - Integration issue with `docxcompose` (merging library) failing on specific file types.
    - Permission or path error in the Docker/Local environment.
- **Action:** Add robust logging around `_generate_combined_original_docx` and check for exception swallowing.

---

## 3. Formatting & Metadata Regressions

### Task 3.1: Header Metadata Corruption
**Objective:** Fix critical bug where teacher names and grades are swapped (e.g., "Donna Savoca/Grade 2" becoming "Kelsey Lang/Grade 3").
- **Context:** This suggests a **Slot Index Mismatch** or **Template Contamination**.
- **Investigation:**
    - Check `BatchProcessor._merge_week_plans`. Are slots being re-ordered or mis-indexed when merging parallel results?
    - Check `BaseParser.extract_metadata`. Is it picking up metadata from a previous file in the batch?
    - Verify if the "Template" DOCX used for rendering has residual metadata that isn't being overwritten.

### Task 3.2: Content Concatenation & "Merged" Text
**Objective:** Fix issue where Title and Description are merged into a single line with the URL, instead of being distinct paragraphs.
- **Example:** 
    - *Original:* 
        > Refer to guide
        > 
        > **Title**
    - *Output:* `Refer to guide: Title (URL)`
- **Cause:** The `MarkdownToDocx` or `DOCXRenderer` might be stripping newlines aggressively when injecting hyperlinks, or the "Inline Replacement" is replacing a large block of text (including newlines) with a single link string.

### Task 3.3: Missing Bold Formatting
**Objective:** Restore bold styling for keywords, strategy names, and labels.
- **Problem:** Text that was bold in the source (e.g., **Key Question:**) is rendering as plain text.
- **Hypothesis:** 
    - `MarkdownToDocx` might be failing to parse `**bold**` syntax correctly in complex nested structures.
    - The "Smart Inline Replacement" might be wiping out existing run properties (like Bold) when it replaces text with a hyperlink.
- **Action:** Review `_add_formatted_text` in `markdown_to_docx.py` and ensure it preserves or re-applies bold styling after link injection.

---

## 4. Verification

### Task 4.1: Verify Day Leakage Fix
- **Context:** A fix was applied to `docx_renderer.py` to enforce strict day matching during inline replacement.
- **Action:** Run the "Link Comparison Script" (Task 1.1) on a newly generated plan to confirm zero leakage.
