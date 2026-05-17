# Research spikes (agentic doc extraction)

Small, **optional** scripts for Wave 2 validation. Not imported by production code.

| Spike | Purpose |
|-------|---------|
| [instructor_curriculum_smoke](instructor_curriculum_smoke/) | `OPENAI_API_KEY` / `LLM_API_KEY` / `GPT5_API_KEY` — Pydantic lesson stub extraction |
| [docling_curriculum_smoke](docling_curriculum_smoke/) | Local PDF/DOCX/URL → Markdown (layout / tables / links sanity) |
| [langextract_curriculum_smoke](langextract_curriculum_smoke/) | `LANGEXTRACT_API_KEY` (Gemini) in repo-root `.env`; `LANGEXTRACT_SMOKE_INPUT_FILE` or `export_lesson_text_from_db.py` for real lesson text |
| [lp_parser_hyperlink_dump](lp_parser_hyperlink_dump/) | Same DOCX → LP `RecursiveTableParser` hyperlink JSON (compare to Docling MD); see [../repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](../repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md) |

## Isolated venv (recommended)

Conda/global installs may hit resolver conflicts (`typer`, `anyio`, etc.):

```powershell
cd d:\LP
python -m venv .venv-research
.\.venv-research\Scripts\activate
pip install instructor openai pydantic langextract "docling>=2.0"
```

Run scripts from repo root as documented in each README.

## Evidence

Log outcomes in [../repos/wave_2_evidence.md](../repos/wave_2_evidence.md).
