# Lesson Plan Editor – MCP and agents integration

**Status:** Outline (align with [01_research_memo.md](./01_research_memo.md) and [02_architecture_dual_edit.md](./02_architecture_dual_edit.md))

## 1. Goal

Reuse the same **authoritative context** planned for generation (WIDA slices, curriculum registry, strategy pack) when the teacher asks the **edit assistant** to align or improve text—without introducing a second copy of that context in the client.

## 2. Recommended boundary

- **Tauri WebView:** Renders lesson content, chat UI, and calls **FastAPI** (or existing `invoke` surface) only.
- **FastAPI / backend:** Holds API keys (or orchestrates keychain access), PII scrubbing, rate limits, and any **MCP tool** or **curriculum context service** invocations.
- **MCP:** Treated as a **server-side or sidecar** capability the backend calls—not something the browser connects to directly unless a future ADR says otherwise.

This matches the direction in [AGENT_SKILLS_AND_CODE_EXECUTION.md](../AGENT_SKILLS_AND_CODE_EXECUTION.md) and [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](../ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) (local metadata-driven document access).

## 3. Skill / tool mapping (template)

Fill as implementation approaches:

| Capability | Generate flow | Edit assistant | Notes |
|------------|---------------|----------------|-------|
| Curriculum context lookup | TBD | TBD | Same tool, different prompt |
| Strategy pack reference | TBD | TBD | |
| Validation / schema check | TBD | TBD | Should be shared code path |

## 4. Security and privacy

- Reference existing patterns: key storage, scrubbing before LLM, logging policy.
- Define whether **chat transcripts** are persisted, truncated, or ephemeral (product + legal).

## 5. TBD

- Exact endpoints: e.g. `POST /api/plans/{id}/edit-assistant` vs reuse of existing LLM service modules.
- Whether edit assistant shares **one** agent definition with generation or a narrower skill set (YAGNI: start narrow).
