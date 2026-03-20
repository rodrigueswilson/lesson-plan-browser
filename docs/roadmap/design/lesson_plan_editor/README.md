# Lesson Plan Editor (planned)

**Status:** Draft – research and architecture in progress  
**Location:** This folder under [docs/roadmap/design/](../)  
**Policy:** [docs/DOCUMENTATION_POLICY.md](../../../DOCUMENTATION_POLICY.md)

## Vision

A future **Edit** experience (dedicated tab or entry from the Lesson Plan Browser) where teachers can **review and change** generated lesson content in two ways:

1. **Manual edit** – a compact rich-text style editor (e.g. bold, italic, underline, highlight, copy/paste) with explicit save.
2. **Assistant edit** – conversational instructions to an LLM that proposes changes; the teacher **accepts or rejects** before persistence.

Both paths must converge on the same **persistence and export rules** so the database, DOCX outputs, and tablet-facing data stay consistent.

## Document map

| Document | Role |
|----------|------|
| [01_research_memo.md](./01_research_memo.md) | Phases B–D: library scan, spikes, decision log (evidence). |
| [02_architecture_dual_edit.md](./02_architecture_dual_edit.md) | Normative architecture (draft until research gate passes). |
| [03_mcp_agents_integration.md](./03_mcp_agents_integration.md) | MCP, agents, and backend boundary vs UI. |
| [04_data_export_sync.md](./04_data_export_sync.md) | `lesson_json`, DOCX regeneration, sync implications. |
| [05_ui_ux_spec.md](./05_ui_ux_spec.md) | UX scope, v1 non-goals, flows. |

## Phase A – Constraints and framing

### Stack facts (current codebase)

- **Desktop UI:** Tauri + React (see [README.md](../../../../README.md)); unified browser in [shared/lesson-browser](../../../../shared/lesson-browser/).
- **Backend:** FastAPI ([backend/api.py](../../../../backend/api.py)), plans API ([backend/routers/plans.py](../../../../backend/routers/plans.py)).
- **Canonical lesson payload:** `lesson_json` stored with weekly plans; validation and transforms under [backend/llm/](../../../../backend/llm/) (e.g. [transform_runner.py](../../../../backend/llm/transform_runner.py)).
- **DOCX output:** [tools/docx_renderer/](../../../../tools/docx_renderer/) renders from structured data; exports must remain aligned with stored JSON.
- **Storage:** Local-first SQLite; optional Supabase per project docs ([docs/roadmap/design/DATABASE_ARCHITECTURE_AND_SYNC.md](../DATABASE_ARCHITECTURE_AND_SYNC.md)).

### Non-negotiables

- **`lesson_json` (and related DB fields) remain SSOT** for lesson content; Word/PDF are **derived**, not authoritative after generation.
- **Privacy:** API keys via OS keychain where applicable; PII scrubbing before external LLM calls (existing project patterns).
- **Tablet / sync:** Edits must flow through the same persistence path the tablet or sync layer is expected to read; avoid duplicate sources of truth ([DATABASE_ARCHITECTURE_AND_SYNC.md](../DATABASE_ARCHITECTURE_AND_SYNC.md)).

### Research questions (must be answered before locking architecture)

1. **Rich text:** Plain strings only vs allowed HTML (or other) subset in JSON fields – and which fields?
2. **Assistant output shape:** Full `lesson_json` replacement vs JSON Patch (or similar) vs tool calls that the app applies?
3. **Runtime boundary:** LLM calls only through **FastAPI** (recommended) vs any direct WebView-to-provider calls?
4. **Paste / Word:** How much formatting from Word/Docs must survive, and how does sanitization work?
5. **Versioning:** What is stored per save (version row, audit metadata, chat transcript policy)?

### Success criteria (“research done”)

- Primary **manual editor** candidate chosen with **spike notes** (paste, bundle, a11y).
- **Assistant integration** pattern chosen (patch vs full document, human-in-the-loop).
- **Risks** documented for renderer, schema validation, and multi-device sync.
- [02_architecture_dual_edit.md](./02_architecture_dual_edit.md) updated from “pre-research draft” to **decision-aligned** draft.

## Related roadmap documents

- [LESSON_PLAN_BROWSER_MODULE.md](../LESSON_PLAN_BROWSER_MODULE.md) – navigation; mock `[Edit]` affordance.
- [AGENT_SKILLS_AND_CODE_EXECUTION.md](../AGENT_SKILLS_AND_CODE_EXECUTION.md) – skills, MCP, curriculum context direction.
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](../ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) – generation stack, teacher overrides (conceptual).
- [UI_PLANNING_DOCUMENT.md](../UI_PLANNING_DOCUMENT.md) – Browser and Lesson Mode UX context.

## Completion order (research-first)

1. This hub (Phase A) and [01_research_memo.md](./01_research_memo.md) template.
2. Phase B desk research and Phase C time-boxed spikes recorded in `01`.
3. Phase D synthesis and decision log in `01`; then finalize `02`–`05`.
4. Optional ADR under [docs/decisions/](../../../decisions/) if a contentious storage or security choice is made.
