# Wave 1 — Pass 2 traces (top three repos)

Happy-path traces for **docling**, **instructor**, **langextract** after Pass 1 (see Runbook 03).

## docling

| Step | Detail |
|------|--------|
| Input | Path or stream: PDF / DOCX / other supported formats |
| Trigger | Python: `docling` package / CLI per [getting started](https://docling-project.github.io/docling/) (local clone: `docling` examples in repo) |
| Output | `DoclingDocument` serialized to Markdown, JSON, HTML, etc. |
| Module chain (conceptual) | ingest file → format-specific backend → layout/table analysis → `DoclingDocument` → export serializers |

## instructor

| Step | Detail |
|------|--------|
| Input | Natural language string + `messages` list |
| Trigger | `instructor.from_provider(...)` then `client.chat.completions.create(response_model=MyModel, ...)` |
| Output | Validated Pydantic instance (`MyModel`) |
| Module chain (conceptual) | provider client → instructor patch → completion → parse/validate → retry hooks per library config |

## langextract

| Step | Detail |
|------|--------|
| Input | Long unstructured text + extraction prompt / examples |
| Trigger | Library API per README Quick Start (`langextract` package) |
| Output | Structured extractions with source grounding metadata; optional visualization HTML |
| Module chain (conceptual) | text chunker → parallel LLM calls → merge grounded spans → schema validation → viz export |

**Selection rationale:** Layout IR (docling), extraction control plane (instructor), grounded LLM extract (langextract) cover A2 + A1/A3 + A4 audit needs without committing to web crawlers.
