# Lesson Plan Editor – Research memo

**Status:** Living document (Phases B–D)  
**Companion:** [README.md](./README.md) (Phase A framing)

## 1. Phase A echo

Copy or summarize constraints, non-negotiables, research questions, and success criteria from [README.md](./README.md) when this file is filled in, so spikes always point back to explicit questions.

## 2. Phase B – Library and pattern scan

### 2.1 Rich text editors (React + WebView)

| Criterion | TipTap / ProseMirror | Lexical | Slate | Notes |
|-----------|----------------------|---------|-------|-------|
| Maintenance / adoption | TBD | TBD | TBD | Add npm trends, last release date |
| Bundle size (approx.) | TBD | TBD | TBD | |
| TypeScript | TBD | TBD | TBD | |
| Paste from Word / Google Docs | TBD | TBD | TBD | |
| Content model (HTML / JSON) | TBD | TBD | TBD | Maps to `lesson_json` strategy |
| Accessibility | TBD | TBD | TBD | |
| License | TBD | TBD | TBD | |

**Sanitization:** Document chosen approach (e.g. DOMPurify, allowlist) and what is stripped on paste.

### 2.2 Tauri / desktop

- Clipboard APIs and limitations (if any) for the target OS.
- WebView behavior with large documents (scroll, focus).
- Whether LLM traffic should use `invoke` to backend only (default hypothesis: yes).

### 2.3 Assistant patterns

- Structured output / JSON schema / tool use from the provider SDK.
- JSON Patch (RFC 6902) vs custom `{ path, old, new }` vs full document replace.
- Human-in-the-loop: single “Apply” vs per-hunk review.

### 2.4 MCP and curriculum context

- Confirm **backend gateway** pattern: UI calls FastAPI; FastAPI (or worker) exposes MCP tools or wraps context service.
- List which planned tools from [AGENT_SKILLS_AND_CODE_EXECUTION.md](../AGENT_SKILLS_AND_CODE_EXECUTION.md) apply to **edit** vs **generate** only.

**Citations:** Add links to docs, blog posts, or official READMEs for each row above.

## 3. Phase C – Spike checklist

Time-box each spike (suggest 2–4 hours each); record date and outcome.

| Spike | Question | Pass criteria | Date | Result |
|-------|----------|---------------|------|--------|
| C1 – Editor | Can we bind one `lesson_json` text field with acceptable paste? | Paste from Word/Docs documented; sanitization list | | |
| C2 – Assistant | Can we apply a validated patch to `lesson_json`? | Validator runs clean after merge (mock LLM OK) | | |
| C3 – API boundary (optional) | Does a stub backend round-trip match production intent? | Single `invoke` or HTTP path documented | | |

## 4. Phase D – Synthesis

### 4.1 Decision log

| Date | Decision | Rationale | Source (spike id / link) |
|------|----------|-----------|---------------------------|
| | | | |

### 4.2 Risks and mitigations

- Schema drift between editor fields and `schemas/lesson_output_schema.json` (or successor).
- HTML in JSON breaking DOCX renderer – mitigation TBD.
- Token cost and latency for assistant – mitigation TBD.
- Concurrent edit (PC + tablet) – align with [DATABASE_ARCHITECTURE_AND_SYNC.md](../DATABASE_ARCHITECTURE_AND_SYNC.md).

### 4.3 Deferred (YAGNI)

Explicitly list what v1 will **not** do (e.g. real-time collaborative editing).

## 5. Gate

Do not treat [02_architecture_dual_edit.md](./02_architecture_dual_edit.md) as **approved** until Phase D rows are filled and this memo links to the finalized decisions.
