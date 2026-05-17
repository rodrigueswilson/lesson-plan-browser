# Repo evidence for pipeline outline (ten codebases)

**Date:** 2026-03-26  
**Updated:** 2026-03-26 (second pass: WordprocessingML tables doc, Tika `XWPFWordExtractorDecorator`, Docling/Unstructured/Mammoth/Pandoc test inventory; **extraction→DB** answer)  
**Method:** Read **primary source files** from GitHub (`raw.githubusercontent.com`) on each repo’s default branch (`main` or `master` as applicable). This fills [2026-03-26-pipeline-functions-vs-prior-art-outline.md](./2026-03-26-pipeline-functions-vs-prior-art-outline.md); it does **not** implement anything in LP.

**Legend:** §1 = Acquisition… through §8 = API (same as outline).

---

## 1. `dotnet/Open-XML-SDK` (OOSDK)

**Repo:** https://github.com/dotnet/Open-XML-SDK  

**Files reviewed**

- `src/DocumentFormat.OpenXml/Packaging/WordprocessingDocument.cs` — defines `WordprocessingDocument` as an `OpenXmlPackage` for Word.
- `src/DocumentFormat.OpenXml/Schema/Wordprocessing/Table.cs` — `Table` with `TableProperties`, `TableGrid`, `TableRows` collection.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§4** | **Ground-truth OOXML shape** for `w:tbl`: strongly typed `Table` / row / grid parts—use when reasoning about grid vs `python-docx` proxies. |
| **§4 (merge/grid)** | SDK encodes schema; **cell merge behavior** is in row/cell types elsewhere (`TableRow`, `TableCell` in same `Schema/Wordprocessing/` tree). Follow `TableRow`, `TableCell`, `VerticalMerge` from same package when debugging `vMerge`. |
| **§7** | Not applicable (no ingest reports). |

**Transferable takeaway:** Treat OOSDK as a **spec browser** in C#: navigate `DocumentFormat.OpenXml.Wordprocessing` for element names that match `python-docx`’s `lxml` layer.

---

## 2. `OfficeDev/open-xml-docs` (OXDOC)

**Repo:** https://github.com/OfficeDev/open-xml-docs  

**Files reviewed**

- `docs/about-the-open-xml-sdk.md` — OPC/ZIP packaging, parts, WordprocessingML “stories” (main doc, headers, footers, comments, etc.), SDK tasks (typed classes, validation).
- `docs/word/overview.md` — index of how-tos: **tables**, paragraphs, runs, styles, SAX text replace.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§4** | Conceptual map: **package = ZIP**, parts, relationships; links to **“Working with WordprocessingML tables”** and **structure of a WordprocessingML document**. |
| **§1 / §8** | No runtime code. |

**Transferable takeaway:** When fixing table or header/footer bugs, use OXDOC how-tos as **Microsoft’s** narrative over the same XML `python-docx` touches.

---

## 3. `googleworkspace/python-samples` (GWS)

**Repo:** https://github.com/googleworkspace/python-samples  

**Files reviewed**

- `docs/quickstart/quickstart.py` — `InstalledAppFlow`, `Credentials.from_authorized_user_file` / `refresh`, `build("docs", "v1", credentials=creds)`, `documents().get(documentId=...).execute()`.
- `docs/output-json/output_json.py` — `build("docs", "v1")`, `documents().get`, `json.dumps(result, indent=4, sort_keys=True)` for **full API JSON**.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§1** | Minimal **Credentials + build + get** pattern (mirrors your `DocsClient`; alternate auth via `google.auth.default()` in output-json sample). |
| **§3** | **Canonical JSON** dump pattern for comparing structure to your `GoogleDocsProcessor` expectations (tabs, body—see live JSON, not only code). |

**Transferable takeaway:** Use `output_json.py` as a **one-off debug harness** template: same API your crawler uses, to diff doc structure when export looks wrong.

---

## 4. `googleapis/google-api-python-client` (GAPC)

**Repo:** https://github.com/googleapis/google-api-python-client  

**Files reviewed**

- `googleapiclient/http.py` — `_should_retry_response` (retry **429**, **5xx**, selective **403** rate-limit reasons); `_retry_request` (**exponential** sleep `rand() * 2**retry_num`).

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§1** | **Concrete retry policy** your stack already inherits when using `googleapiclient`. Anything that bypasses `HttpRequest.execute()` may miss this—worth aligning custom export paths. |

**Transferable takeaway:** Document **num_retries** defaults on `execute()` calls for long batch exports; match library behavior instead of duplicating backoff.

---

## 5. `python-openxml/python-docx` (PD)

**Repo:** https://github.com/python-openxml/python-docx (`master`, `src/docx/`)  

**Files reviewed**

- `src/docx/table.py` — `Table` proxy for `CT_Tbl`; **`_cells`** builds layout grid using `iter_tcs()`, **`vMerge` CONTINUE** (repeat cell from row above), **horizontal `grid_span`**; `_Row.cells` documents **grid_cols_before/after** and non-rectangular rows.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§4** | **Exact merge semantics** your parser inherits: vertical merge continuation, horizontal span expansion to “uniform matrix” cells. |
| **§5** | Cell/text extraction via `paragraphs`, `text`; nested `add_table` on `_Cell`. |
| **§6** | Indirect only (styles on paragraphs)—no curriculum routing. |

**Transferable takeaway:** Your **table fidelity bugs** should be cross-checked with **`_Row.cells` / `_cells`** behavior—library explicitly warns rows can differ in populated cell count.

---

## 6. `Unstructured-IO/unstructured` (UNS)

**Repo:** https://github.com/Unstructured-IO/unstructured  

**Files reviewed**

- `unstructured/partition/docx.py` — `partition_docx(...)`: loads **`docx.Document`**, options `include_page_breaks`, **`infer_table_structure`** → metadata **`text_as_html`** on tables; `DocxPartitionerOptions` documents **page number** limitations in DOCX; walks document with same types you use (`Paragraph`, `Table`, `Hyperlink`, `Run` imports at top of file).

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§4** | Same **python-docx** traversal stack; **`infer_table_structure`** flag is a ready-made pattern for **table → HTML string** alongside plain text. |
| **§5** | **Element stream** (`Element` types), page breaks, metadata attachment—pattern for “ordered emit” after parse. |
| **§2** | Only weakly (or via separate ingest repo); primary value is partition pipeline. |

**Transferable takeaway:** Compare your **table HTML** path to their **`text_as_html`** generation (uses `unstructured.common.html_table.htmlify_matrix_of_cell_texts` per imports in same module).

---

## 7. `docling-project/docling` (DCL)

**Repo:** https://github.com/docling-project/docling  

**Files reviewed**

- `docling/backend/msword_backend.py` — `MsWordDocumentBackend(DeclarativeDocumentBackend)`: imports **`from docx import Document`**, **`docx.table.Table`, `_Cell`**, builds **`DoclingDocument`** / `TableItem` / `RichTableCell` via **`docling_core`**; namespaces for DrawingML, OMML→LaTeX, image extraction.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§4** | **Second opinion** on “python-docx + extensions” (equations, images, tables) mapped into **one rich document graph**. |
| **§6** | **Reading order / layout** concerns addressed in backend (PDF side heavier); for DOCX still anchored on python-docx. |
| **§7** | `DocumentOrigin`, structured types—ideas for **metadata on parsed nodes**, not SQLite. |

**Transferable takeaway:** If you ever need **OMML math** or richer drawing extraction from DOCX, read this backend before writing custom XML walkers.

---

## 8. `mwilliamson/python-mammoth` (MM)

**Repo:** https://github.com/mwilliamson/python-mammoth  

**Files reviewed**

- `mammoth/conversion.py` — `convert_document_element_to_html`; **`_DocumentConverter`** visitor: **paragraphs**, **runs** (bold/italic/sup/sub), **hyperlinks**, **tables** (`thead`/`tbody` split using header row detection), **table cells** with **colspan/rowspan**; **`_find_html_path` / `_find_style`** uses **`style_map`** and warns on unrecognised styles.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§5** | **Visitor + HTML writer** pattern; collapses/strips empty nodes after visit. |
| **§6** | **Style map → output path** is the closest analogue to your **`SubjectConfig` anchors** (declarative mapping, not same domain). |
| **§3** | Different input (internal `documents.*` AST), same **recursive descent emit** idea as your JSON→MD. |

**Transferable takeaway:** Extract ideas from **`_find_html_path_for_paragraph`** and **`style_map`** for maintainable **template variance** (new unit headings) without growing `if/else` in one god function.

---

## 9. `apache/tika` (TIKA)

**Repo:** https://github.com/apache/tika  

**Files reviewed**

- `.../microsoft/ooxml/OOXMLParser.java` — `SUPPORTED_TYPES` includes **`wordprocessingml.document`**; **`OOXMLExtractorFactory.parse`**; static block tunes **`ZipSecureFile`** (zip bomb / file count) for POI.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§2** | **Facade routing**: one `Parser` interface, many MIME types—same *idea* as “type → handler” for ingest. |
| **§4** | Extraction via **POI/XWPF** stack (`XWPFWordExtractorDecorator` in same module tree per Tika layout)—**Java** reference if you need POI behavior hints. |
| **§1** | No Google API. |

**Transferable takeaway:** **`ZipSecureFile`** tuning is relevant if you ever parse raw OPC/ZIP from untrusted uploads (DoS surface).

---

## 10. `jgm/pandoc` (PAN)

**Repo:** https://github.com/jgm/pandoc  

**Files reviewed**

- `src/Text/Pandoc/Readers/Docx.hs` — module doc lists **implemented/partial** features (e.g. **Table**: column widths/alignments not fully implemented); uses **Zip** archive read; converts internal Docx type to **`Pandoc`** AST via `readDocx`.

### Answers by outline section

| Section | What this repo provides |
|--------|-------------------------|
| **§3** | Explicit **lossiness checklist** in source comments—good mental model for “what we refuse to preserve.” |
| **§4–§5** | Reader maps Word features into **simpler AST**—compare to your “lesson fields” shrinkage. |
| **§8** | None. |

**Transferable takeaway:** Use Pandoc’s **checkbox list in `Docx.hs`** as inspiration for a **parser capability matrix** in your own docs (what’s stable vs partial).

---

## Coverage matrix (outline § × repo)

| § | OOSDK | OXDOC | GWS | GAPC | PD | UNS | DCL | MM | TIKA | PAN |
|--|:-----:|:-----:|:---:|:----:|:--:|:---:|:---:|:--:|:----:|:---:|
| §1 | | | * | * | | | | | | |
| §2 | | | | | | * | | | * | |
| §3 | | | * | | | | | * | | * |
| §4 | * | * | | | * | * | * | * | * | * |
| §5 | | | | | * | * | | * | | * |
| §6 | | | | | | * | * | * | | |
| §7 | | | | | | * | * | | | |
| §8 | | | | | | | | | | |

`*` = this pass found **direct** source evidence useful for that section.

---

## Second pass — deeper §4 (tables / OOXML / extractors)

This pass adds **documentation + extractor implementation + tests** detail for **table-centric** work aligned with outline **§4** (and partially §5).

### OfficeDev/open-xml-docs

- **`docs/word/working-with-wordprocessingml-tables.md`** — ISO-framed explanation: `w:tbl`, **`tblPr`**, **`tblGrid` / `gridCol`**, **`tr`**, **`tc`**; maps each to Open XML SDK types (`TableProperties`, `TableGrid`, `GridColumn`, `TableRow`, `TableCell`). Includes sample XML for a minimal 1×3 table.
- **Use:** vocabulary match between **Word UI**, **raw XML**, and **OOSDK** names when reading `python-docx`’s underlying elements.

### dotnet/Open-XML-SDK

- **`test/.../Wordprocessing/TableTests.cs`** — xUnit tests for **`TableProperties`**, **`TableGrid`**, **`TableRows`** assembly (object graph shape), not merged-cell torture tests.

### Apache Tika

- **`.../ooxml/XWPFWordExtractorDecorator.java`** — decorator on **`XWPFWordExtractor`** (Apache POI): walks **`XWPFDocument`**, paragraphs, tables, hyperlinks, SDTs, etc.; emits via **`XHTMLContentHandler`** / **`ToTextContentHandler`** (SAX-style content extraction). **`LIST_DELIMITER`** comment references MS-DOC numbering behavior.
- **Use:** see how a **production** Java stack turns **XWPF*** into **linear text / XHTML** (different output shape than your JSON→HTML, same problem class).

### python-docx (recall from first pass, §4 anchor)

- **`src/docx/table.py`** — **`_cells`**: `iter_tcs()`, **`vMerge == CONTINUE`** handling, **`grid_span`**; **`_Row.cells`** documents **`grid_cols_before` / `grid_cols_after`** (non-rectangular visual rows). This is the **logic your parser inherits** when using the library.

### Docling

- **`tests/test_backend_msword.py`** — builds **`DocumentConverter(..., DOCX)`**, converts every file under **`tests/data/docx/`**, then:
  - **`verify_export`** on **Markdown**, **indented text**, and (for `word_tables.docx`) **HTML** against files named like **`*.md`**, **`*.json`** under **`groundtruth/docling_v2/`**;
  - **`verify_document`** against **`*.json`** (full **`DoclingDocument`** snapshot).
- **Use:** strongest **E2E “ingest to structured model”** pattern in this set—still **JSON/Markdown ground truth in-repo**, not **SQL**.

### Unstructured

- **`test_unstructured/partition/test_docx.py`** — **`partition_docx`** from file/spooled file; **`infer_table_structure`** toggles presence of **`metadata.text_as_html`** on **`Table`** elements (parametrized test); fixtures under shared **`example_doc_path`**; uses **`assert_round_trips_through_JSON`** helper for element serialization.

### Mammoth

- **`tests/mammoth_tests.py`** — **`test_word_tables_are_converted_to_html_tables`** compares full HTML string to expected for **`tables.docx`**; many tests use **`tests/test-data/*.docx`** fixtures.

### Pandoc

- **`test/docx/`** (directory in repo) — golden **`.docx`** inputs and expected command outputs for the Docx reader pipeline (regression suite); not database-backed.

---

## Do these repos test “extraction → database ingestion”?

**Short answer: no.** None of the ten repositories are built to prove that **parsed fields** land correctly in **your** (or any fixed) **application `curriculum.db` / lesson rows**. Their scope stops at:

| Repo | What tests actually assert | DB / SQL? |
|------|----------------------------|-----------|
| **OOSDK** | CLR object graph / schema behavior (`TableTests`, etc.) | No |
| **OXDOC** | Docs + included samples (not a CI suite in that repo) | No |
| **GWS** | Samples only; no extraction→DB contract | No |
| **GAPC** | HTTP client, retry logic, discovery docs | No |
| **python-docx** | Library behavior on `.docx` (tables, paragraphs, etc.) | No |
| **UNS** | **Element list** equality, **metadata** (`text_as_html`), JSON round-trip of elements | No |
| **DCL** | **`DoclingDocument`** vs **checked-in ground truth** (`.json`, `.md`, `.html`); rich tables, comments, headings | No |
| **MM** | **HTML (or markdown) string** vs expected for fixture **`.docx`** | No |
| **TIKA** | **Parser output** (text/XHTML/metadata), integration tests | No |
| **PAN** | **Reader golden tests** under **`test/docx/`** | No |

**Closest analogue to your “extraction → persistence” gate:** **Docling**’s **`verify_document` / `verify_export`** (structured document ↔ files) and **Unstructured**’s **element snapshots**—they are **fixtures + diff**, not **SQL assertions**. **Your** project’s equivalent is **`verify_curriculum_db.py`**, **`tests/test_curriculum_gaps.py`**, ingest reports, and the **quality gate** rubric—not something to import wholesale from these repos.

---

## Gaps and limits

- **§8 (FastAPI)** — none of the ten repos address HTTP/OpenAPI; outline remains correct.
- **§6 full “lesson compiler”** — only **Mammoth style maps** and **Unstructured element categories** partially overlap; no repo encodes curriculum semantics.
- First and second passes were **targeted** (not every Pandoc submodule, every Tika `XWPF*` branch, or every OOSDK merge test).

---

## Related

- [2026-03-26-pipeline-functions-vs-prior-art-outline.md](./2026-03-26-pipeline-functions-vs-prior-art-outline.md) — problem mapping.
- [2026-03-26-github-repos-extraction-complexity-survey.md](./2026-03-26-github-repos-extraction-complexity-survey.md) — high-level survey.
