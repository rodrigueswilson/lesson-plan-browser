# GitHub repositories: DOCX / Docs API extraction and complexity

**Date:** 2026-03-26  
**Purpose:** Compare how major open codebases handle **document extraction complexity**—what code they center, **which libraries** they compose, and **what OOXML / DOCX structure knowledge** they encode (vs delegating).  
**Not evaluated here:** fitness for adoption in this repo (SSOT remains in architecture docs); this is a landscape survey.

**URLs:** Every repository below is public on GitHub. License names are high level; confirm before reuse.

---

## 1. `dotnet/Open-XML-SDK`

**URL:** https://github.com/dotnet/Open-XML-SDK  
**Maintainer:** Microsoft (described as “Open XML SDK by Microsoft”; lives under `dotnet` org).  
**Language / runtime:** C# / .NET (`DocumentFormat.OpenXml` on NuGet).

### What code

Low-level toolkit: **read/write OPC packages**, **WordprocessingML**, SpreadsheetML, PresentationML per **ECMA-376 / ISO 29500**. Strongly typed element classes + packaging APIs for performance-oriented generation and modification.

### Libraries / stack

- **`System.IO.Packaging`** for ZIP/package parts  
- No “magic” high-level curriculum model—callers must know **part names**, **relationships**, and element semantics.

### DOCX / OOXML knowledge encoded

**Very deep:** the SDK is essentially a typed surface over the standard. Complexity is **pushed to the caller** (correct `w:tbl`, `w:tc`, `w:gridSpan`, `w:vMerge`, headers/footers, styles). Best for teams that want **full control** and can invest in spec literacy.

**License:** MIT.

---

## 2. `OfficeDev/open-xml-docs`

**URL:** https://github.com/OfficeDev/open-xml-docs  
**Maintainer:** Microsoft / OfficeDev.  
**Language:** Documentation source (Markdown / tooling; not an application runtime).

### What code

**Documentation repository** for Open XML SDK and formats—not a parser product. Explains **concepts**, migration (e.g. v2→v3 SDK), and how formats fit together.

### Libraries / stack

N/A (docs only).

### DOCX / OOXML knowledge encoded

**Conceptual SSOT companion** to the SDK: explains *why* the object model looks the way it does and what the **standard** expects. Use alongside `Open-XML-SDK` when reasoning about tricky structures (tables, merges, document parts).

**License:** MIT.

---

## 3. `googleworkspace/python-samples` (Docs API)

**URL:** https://github.com/googleworkspace/python-samples  
**Relevant paths:** e.g. `docs/quickstart/`, `docs/output-json/`, `docs/mail-merge/`.

### What code

Official **small samples**: OAuth, `googleapiclient.discovery.build("docs", "v1")`, `documents.get`, batch updates, exporting structure as **API JSON** (not binary DOCX parsing in-repo).

### Libraries / stack

Typically **`google-api-python-client`**, **`google-auth`**, **`google-auth-oauthlib`**.

### DOCX / OOXML knowledge encoded

**None for OOXML bytes.** Knowledge is **Google Docs’ REST document model**: `StructuralElement`, `Table`, `TableRow`, `TableCell`, `Paragraph`, `TextRun`, requests like `MergeTableCells`. That is the right reference when comparing **Docs JSON fidelity** vs **Drive-exported DOCX** for the same doc.

**License:** Apache 2.0 (Google samples; verify file headers).

---

## 4. `googleapis/google-api-python-client`

**URL:** https://github.com/googleapis/google-api-python-client  

### What code

**Discovery-based** client for all Google REST APIs: builds typed accessors from discovery documents (cached in v2+). Maintenance mode for new features; still widely used for Docs/Drive.

### Libraries / stack

**`httplib2`**, **`uritemplate`**, **`google-auth`** ecosystem. Large wheel size because discovery docs are bundled.

### DOCX / OOXML knowledge encoded

**None.** It is transport + API surface. Complexity handling is **HTTP retries, auth refresh, batching**—not paragraph/table semantics.

**License:** Apache 2.0.

---

## 5. `python-openxml/python-docx`

**URL:** https://github.com/python-openxml/python-docx  

### What code

High-level Python API: **`Document`**, **`paragraphs`**, **`tables`**, runs, styles, merges—implemented over **lxml**-backed **OOXML** element trees.

### Libraries / stack

Core: **`python-docx`** (depends on **lxml** for XML). No separate rendering engine.

### DOCX / OOXML knowledge encoded

**Medium–high for “common Word”:** maps familiar Word concepts to XML (`w:p`, `w:r`, `w:tbl`, merge protocol documented in project docs). **Gaps** show up on **pathological merges, nested tables, and revision-heavy** files (see project issues). Complexity is **centralized in one library**, so consumers inherit both ergonomics and limits.

**License:** MIT.

---

## 6. `Unstructured-IO/unstructured`

**URL:** https://github.com/Unstructured-IO/unstructured  

### What code

**Partition** pipeline: normalize many file types into **`Element`** streams (titles, narrative, tables, etc.). DOCX path lives under `unstructured/partition/docx.py` (uses **`python-docx`** heavily: paragraphs, tables, sections, hyperlinks, html table helper).

### Libraries / stack

For DOCX extra: **`python-docx`**, optional **`libreoffice`**, **`pypandoc` / pandoc** in broader installs; **`lxml`-class** HTML table building; many other deps for PDF/images when using `all-docs`.

### DOCX / OOXML knowledge encoded

**Composition, not a new OOXML kernel:** DOCX complexity is handled by **reusing python-docx** plus **heuristics** (bullets, chunking, metadata). Good reference for “**element stream**” design and **table→HTML matrix** patterns—not for low-level merge semantics.

**License:** Apache 2.0.

---

## 7. `docling-project/docling`

**URL:** https://github.com/docling-project/docling  

### What code

End-to-end **document converter**: PDF-centric layout models, but **DOCX/PPTX/XLSX** listed as supported formats; outputs Markdown, HTML, JSON **`DoclingDocument`**, etc. Pipelines mix classical parsing with **layout / VLM** options for scanned content.

### Libraries / stack

**Python**, **`pydantic`**, optional **deep learning** models; heavy dependency tree when full features enabled.

### DOCX / OOXML knowledge encoded

**Unified internal document model** (abstract away per-format quirks). DOCX-specific detail is **inside format backends**; public surface emphasizes **cross-format** structure (tables, reading order) rather than exposing `w:*` details. Complexity is managed by **normalizing to one graph** and optional ML for messy PDFs.

**License:** MIT (project); model weights may have separate terms.

---

## 8. `mwilliamson/python-mammoth`

**URL:** https://github.com/mwilliamson/python-mammoth  

### What code

**DOCX → HTML** focused on **semantic** output: map Word styles (e.g. `Heading 1` → `h1`) rather than cloning typography.

### Libraries / stack

Pure Python over **ZIP + XML** (custom DOCX interpretation, not `python-docx`).

### DOCX / OOXML knowledge encoded

**Opinionated subset:** explicitly acknowledges **mismatch** between DOCX and HTML; avoids chasing pixel-perfect layout. Encodes rules for headings, lists, tables (content + text formatting; not table borders), footnotes, images, links. Good study for **“acceptable loss”** tradeoffs and **style-map** extensibility.

**License:** BSD-2-Clause.

---

## 9. `apache/tika`

**URL:** https://github.com/apache/tika  

### What code

Java **detection + parsing façade**: routes files to **specialized parsers** (including Office formats via **Apache POI** and related components), returns text/metadata.

### Libraries / stack

**Maven** modules, **`tika-parsers-standard-package`**, **Java 17+** in current generation.

### DOCX / OOXML knowledge encoded

**Indirect:** Tika orchestrates; **POI** carries much Word OOXML knowledge. Complexity is handled by **pluggable parsers** + **unified `Metadata`/content API**. Useful reference for **“single ingress, many formats”** service design (contrast with in-process Python-only pipelines).

**License:** Apache 2.0.

---

## 10. `jgm/pandoc`

**URL:** https://github.com/jgm/pandoc  

### What code

Haskell **readers** / **writers** around a **single intermediate AST**. Includes **`docx` reader and writer** (Office Open XML as input/output).

### Libraries / stack

Haskell ecosystem; optional **Lua filters** to transform the AST between read and write.

### DOCX / OOXML knowledge encoded

**AST-centric:** maps DOCX into **pandoc’s document model**; README explicitly warns **lossiness** for formats richer than that model (e.g. complex tables). Complexity is managed by **narrowing expressiveness** and documenting **known limitations**—a pattern comparable to Mammoth’s semantic stance, but broader across many formats.

**License:** GPL-2.0 or later (linking/copying constraints for proprietary stacks).

---

## Cross-cutting: how these projects manage complexity

| Strategy | Examples |
|----------|----------|
| **Expose the standard** | `Open-XML-SDK` (+ `open-xml-docs`) |
| **API-native model (no OOXML)** | `googleworkspace` samples + Discovery client |
| **One good high-level library** | `python-docx`, `Unstructured` (wraps it) |
| **Semantic simplification / lossy conversion** | `python-mammoth`, `pandoc` |
| **Normalize many formats to one graph** | `docling`, `tika` |

For **this** project (curriculum tables, merges, linked docs), the most transferable lessons are usually: **`python-docx`-level ergonomics with custom guards**, **explicit handling of Drive/Docs limits**, and (when researching JSON parity) **Google’s Docs JSON table model**—not necessarily adopting a second full stack.

---

## Suggested local deep reads (next step)

If you clone for study (no dependency commitment):

1. `unstructured/partition/docx.py` — pragmatic **table + paragraph** decomposition with **`python-docx`**.  
2. `OfficeDev/open-xml-docs` — passages on **tables and merge** behavior relative to the standard.  
3. `googleworkspace/python-samples/docs/output-json` — **JSON shape** of a real Doc.  
4. `python-mammoth` — **style maps** and documented **limitations**.
