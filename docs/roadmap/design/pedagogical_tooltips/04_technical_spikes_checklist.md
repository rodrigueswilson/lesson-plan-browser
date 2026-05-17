# Technical spikes checklist

**Status:** Spike results recorded (desk research + repo inspection)  
**Companion:** [README.md](./README.md), [05_decision_log.md](./05_decision_log.md)

Suggested time box: **2–4 hours per spike**; can be split across sessions.

---

## Spike S1 – Tooltip/popover library (React + Tailwind)

| Item | Detail |
|------|--------|
| Question | Use **Radix UI** (`@radix-ui/react-tooltip`, `@radix-ui/react-popover`) vs **Floating UI** (`@floating-ui/react`) for positioning only vs minimal custom layer? |
| Pass criteria | Document bundle impact, a11y story, and fit with existing Tailwind patterns; recommend one default for implementation phase |
| Date | 2025-03-20 |
| Result | **Radix** provides behavior many teams need out of the box: focus management, dismiss on Escape, pointer/focus guards for tooltips, and collision-aware positioning (see [Radix Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip), [Popover](https://www.radix-ui.com/primitives/docs/components/popover)). **Floating UI** is smaller if you only need coordinates and will implement ARIA and focus yourself ([Floating UI](https://floating-ui.com/)). Lesson-browser `package.json` currently has **no** Radix dependency—adding it is a deliberate bundle increase; measure with production build when implementing. |
| Follow-up | Run `npm run build` (or workspace equivalent) after adding deps and compare chunk sizes. |

**Online research (2025-03-20):** Radix builds on Floating UI for positioning; **shadcn/ui** Tooltip and Popover are thin Tailwind wrappers around the same Radix primitives. **React Aria** and **Base UI** are viable headless alternatives with their own APIs—compare learning curve and touch/tooltip notes. **Tippy.js** remains an integrated option but differs in model from Radix. See [06_online_research_notes.md](./06_online_research_notes.md) section 1 for links and matrix.

---

## Spike S2 – Markdown pipeline (`parseMarkdown`)

| Item | Detail |
|------|--------|
| Question | How do we attach interactive spans to text that passes through [`parseMarkdown`](../../../../shared/lesson-mode/src/utils/markdownUtils.tsx) (or equivalent)? |
| Pass criteria | One documented approach: preprocess tokens, postprocess DOM, or MDX-like component—pick least fragile |
| Date | 2025-03-20 |
| Result | **Pre-markdown:** Insert sentinel tokens or placeholder spans in raw string, then parse (risk: markdown breaks placeholders). **Post-markdown:** Render markdown to React tree, walk children to wrap text nodes (heavier). **Pre-segment:** Split by regex, render each segment as markdown or plain (simplest for narrow patterns like ELD codes). Recommendation: prototype **post-markdown segment split** for ELD regex first; use structured components for `ell_support` headers (no regex). |
| Follow-up | Implement one path in a throwaway branch when coding starts. |

---

## Spike S3 – Bundling SSOT JSON (offline Tauri)

| Item | Detail |
|------|--------|
| Question | How large are merged strategy JSON + `wida_framework_reference.json`, and can they live as static imports or `fetch` to `public`? |
| Pass criteria | Order-of-magnitude KB and note duplicate risk if backend also loads pack |
| Date | 2025-03-20 |
| Result | Strategy pack is modular (~15–25 KB per category per README; full pack modest). WIDA reference JSON is small. **Recommendation:** Vite-bundled static import or `import.meta.url` fetch from `public/` for clear caching; align with [verify_strategy_pack_ssot.py](../../../../tools/verify_strategy_pack_ssot.py) for id drift. |
| Follow-up | Generate a combined `strategy_lookup.json` build artifact if tree-shaking per category is needed. |

---

## Spike S4 – Tauri WebView behavior

| Item | Detail |
|------|--------|
| Question | Any WebView quirks for layered UI (portals, `position: fixed`, focus)? |
| Pass criteria | Smoke test: tooltip/popover visible above scroll containers in Lesson Browser |
| Date | 2025-03-20 |
| Result | Tauri 2 uses system WebView; **Radix portals** render to `document.body` and generally stack correctly. **Risk:** nested scroll areas in lesson detail—verify z-index and `overflow` on parent cards. No Tauri-specific API required (see [03](./03_ux_accessibility_and_platform_notes.md)). |
| Follow-up | Manual test on Windows target build. |

---

## Summary

| Spike | Outcome |
|-------|---------|
| S1 | Prefer **Radix** for primitives unless bundle budget forbids; then Floating UI + manual a11y |
| S2 | Prefer **segmented rendering** for regex-heavy fields; **structured UI** for `ell_support` |
| S3 | **Bundle JSON** in client; optional generated lookup file |
| S4 | **Portal + z-index** validation in real layout |
