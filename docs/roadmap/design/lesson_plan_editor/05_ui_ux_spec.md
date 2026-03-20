# Lesson Plan Editor – UI/UX spec (v1 draft)

**Status:** Draft – product shape for first implementation wave  
**Related:** [LESSON_PLAN_BROWSER_MODULE.md](../LESSON_PLAN_BROWSER_MODULE.md) (mock `[Edit]` in browser chrome)

## 1. Placement

- **Option A:** Dedicated **Edit** tab alongside Browser (shared week/day/slot navigation where possible).
- **Option B:** **Edit** opened from Browser’s `[Edit]` only.

Pick one for v1 in a later revision (solo decider: record choice here when decided).

## 2. Manual edit mode

- Toolbar: **bold, italic, underline, highlight**, copy, paste; paste sanitization per research memo.
- **Save** explicit (optional autosave later—YAGNI unless needed).
- **Discard** or revert to last saved (TBD: scope per field vs whole lesson).

## 3. Assistant edit mode

- Chat thread + clear **scope** (current lesson / current field set).
- Model proposals shown as **preview or diff**; **Apply** commits through the shared save pipeline; **Reject** drops proposal.
- API key configuration follows app-wide settings (keychain).

## 4. v1 non-goals (suggested defaults)

- Real-time collaborative editing (two cursors).
- Full Word feature parity (styles, track changes, comments).
- Assistant editing **without** validation gate.
- Direct MCP connection from the browser WebView.

## 5. Open UX questions

- Full-screen edit vs split view with Browser preview.
- How much of `lesson_json` is exposed as editable blocks vs single narrative field (depends on schema).
