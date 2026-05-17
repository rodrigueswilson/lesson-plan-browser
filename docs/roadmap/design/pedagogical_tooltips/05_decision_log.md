# Decision log (pedagogical tooltips)

**Status:** Living document  
**Companion:** [README.md](./README.md)

Record decisions as they are made during research and implementation. Each row should point to evidence (spike id, PR, or doc section).

| Date | Decision | Rationale | Evidence |
|------|----------|-----------|----------|
| 2025-03-20 | Prefer **`strategy_id`** over free-text `strategy_name` for SSOT alignment when enriching `ell_support` rows | `strategy_name` can diverge from pack titles (see `valid_lesson_minimal.json`: "Graphic Organizers for Language Learning") | [02_data_inventory_and_matching.md](./02_data_inventory_and_matching.md) section 2 |
| 2025-03-20 | Default UI library direction: **Radix** Tooltip/Popover for first implementation unless bundle audit fails | Focus management and dismiss patterns reduce a11y risk vs raw Floating UI | [04_technical_spikes_checklist.md](./04_technical_spikes_checklist.md) S1 |
| 2025-03-20 | Markdown strategy: **segmented rendering** for regex-based WIDA/strategy spans; avoid fragile inline HTML in markdown source | `parseMarkdown` pipeline does not yet attach React wrappers | [04_technical_spikes_checklist.md](./04_technical_spikes_checklist.md) S2 |
| 2025-03-20 | Ship **strategy pack + WIDA JSON** with client for offline; optional slim lookup artifact later | Tauri offline expectation; small footprint | [04_technical_spikes_checklist.md](./04_technical_spikes_checklist.md) S3 |
| 2025-03-20 | **Defer** aggressive prose strategy matching until structured + ELD code paths ship | False positives and markdown edge cases | [01_research_questions_and_success_criteria.md](./01_research_questions_and_success_criteria.md) Q1, T2 |
| 2025-03-20 | **Rich** strategy text (`long_en`, lists) → **Popover** (or disclosure); **short** gloss → **Tooltip** | [WCAG 1.4.13](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html) content-on-hover/focus; [APG tooltip](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/) for brief associated description | [06_online_research_notes.md](./06_online_research_notes.md) sections 2–3 |
| 2025-03-20 | **Alternatives** to evaluate if Radix is rejected: **React Aria** (`@react-aria/tooltip`), **Base UI** tooltip/popover, or **shadcn** (Radix + Tailwind). **Floating UI** alone only if team implements a11y layer. | Industry practice; Radix uses Floating UI internally for positioning | [06_online_research_notes.md](./06_online_research_notes.md) section 1 |

**Pending (not decided)**

| Topic | Options | Next step |
|-------|---------|-----------|
| Global user toggle for inline help | On / Off in settings | User research |
| WIDA licensing for long excerpts | Short gloss only vs link out | Legal review if needed |
| Radix bundle size acceptability | Threshold TBD | Run build with deps |
