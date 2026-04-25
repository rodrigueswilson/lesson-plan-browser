# UX, accessibility, and platform notes

**Status:** Living document  
**Companion:** [README.md](./README.md)

---

## 1. Tooltip vs popover vs link

| Pattern | Best for | Caveat |
|---------|----------|--------|
| **Native `title`** | Minimal cost; single line | Poor keyboard/touch; no rich formatting |
| **Tooltip** (hover + focus) | `short_en`, one-line WIDA gloss | Easy to trigger accidentally on trackpads; avoid dense hover-only |
| **Popover / disclosure** | `long_en`, lists (`look_fors`), multi-line WIDA | Prefer for classroom use if content is long |
| **"Learn more" link** | Jump to glossary panel or doc | Good escape hatch if inline UI is too busy |

**Recommendation (pre-decision):** Use **tooltip for under ~200 characters** and **popover or inline expand** for longer strategy text; always provide a **keyboard path** to the same content.

---

## 2. Tauri and WebView

- **In-lesson overlays are web UI** (HTML/CSS/React). Tauri does not provide special APIs for in-content tooltips; the WebView behaves like a browser for DOM events and CSS.
- **System tray** tooltips in Tauri apply to the **tray icon**, not lesson text—do not confuse the two.
- **Offline:** If lookups are bundled JSON, tooltips work offline; if fetched from a server, define fallback (cached bundle).

---

## 3. Touch and tablet (Lesson Mode / Browser)

- **Hover does not exist** on pure touch; design for **tap** to open rich content.
- Consider **first tap selects / opens**, **second tap** or outside dismisses (validate with users).
- Avoid tooltips that **move with cursor** on large touch targets; prefer anchored popovers.

---

## 4. Accessibility checklist (WCAG-oriented)

Use as a **minimum bar** for implementation; not a formal audit.

| Area | Check |
|------|--------|
| Keyboard | Triggers are focusable (`button` or `tabindex=0` with role); visible focus ring |
| Screen readers | Trigger has accessible name; popover content is in a **live region** or focus moves into dialog pattern |
| Motion | Respect `prefers-reduced-motion` for animations |
| Color | Do not rely on color alone for "has more info" (underline, icon, or text) |
| Timeout | Avoid auto-dismiss that steals focus while reading |

**References:** [WCAG 2.2 Understanding](https://www.w3.org/WAI/WCAG22/Understanding/) (non-normative); [Success Criterion 1.4.13 Content on Hover or Focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html); [APG Tooltip Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/). External synthesis: [06_online_research_notes.md](./06_online_research_notes.md) sections 2–3.

---

## 5. Teacher / classroom context

- Short **reading sessions**; avoid noisy flicker on every word.
- Prefer **predictable** placement (e.g. same corner) over cursor-following if it reduces distraction.
- Optional **global toggle** (see Q4 in [01_research_questions_and_success_criteria.md](./01_research_questions_and_success_criteria.md)) may reduce anxiety for power users.
