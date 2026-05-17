# Online research notes (libraries and open questions)

**Status:** Living document  
**Last updated:** 2025-03-20  
**Companion:** [01_research_questions_and_success_criteria.md](./01_research_questions_and_success_criteria.md), [04_technical_spikes_checklist.md](./04_technical_spikes_checklist.md)

This file captures **external** sources (docs, patterns, articles) gathered to inform implementation. It does not replace spike measurements (e.g. real bundle-size diffs) in CI or local builds.

---

## 1. Library and stack options (React + Tailwind)

### 1.1 Relationship: Radix and Floating UI

Radix Tooltip and Popover use **Floating UI** (`@floating-ui/react-dom`) internally for collision-aware positioning. Choosing Radix is not an alternative to Floating UI for geometry—it adds **ARIA roles, focus behavior, portals, and interaction defaults** on top of the same positioning core.

Sources:

- [Radix Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip), [Radix Popover](https://www.radix-ui.com/primitives/docs/components/popover)
- [Floating UI – React](https://floating-ui.com/docs/react)
- Comparative overview: [Floating UI vs Tippy.js vs Radix Tooltip (PkgPulse)](https://www.pkgpulse.com/blog/floating-ui-vs-tippyjs-vs-radix-tooltip-popover-positioning-2026)

### 1.2 Comparison matrix (high level)


| Option                                                           | Role                                           | Strengths                                                                                                                     | Trade-offs                                                                                                                                                                                                       |
| ---------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Radix** (`@radix-ui/react-tooltip`, `@radix-ui/react-popover`) | Headless React primitives                      | WAI-ARIA–oriented patterns; Popover for **rich** content; tree-shake per primitive                                            | Extra JS vs raw Floating UI; app needs `TooltipProvider` where documented                                                                                                                                        |
| **Floating UI** (`@floating-ui/react`)                           | Positioning + interaction hooks                | Smallest abstraction if you own **all** a11y and ARIA                                                                         | More implementation work for production-grade overlays                                                                                                                                                           |
| **shadcn/ui** (Tooltip, Popover)                                 | **Copy-paste** components styled with Tailwind | Same Radix behavior; matches Tailwind-heavy codebases                                                                         | Not a separate runtime—still Radix under the hood ([shadcn Tooltip](https://ui.shadcn.com/docs/components/radix/tooltip), [Popover](https://ui.shadcn.com/docs/components/radix/popover))                        |
| **React Aria** (`@react-aria/tooltip`, overlays)                 | Adobe hooks + components                       | Strong accessibility focus; `useTooltipTrigger` and related APIs ([React Aria Tooltip](https://react-aria.adobe.com/Tooltip)) | Different API surface than Radix; team learning curve                                                                                                                                                            |
| **Base UI** (MUI)                                                | Unstyled primitives                            | Alternative headless family; Tooltip documented as unstyled ([Base UI Tooltip](https://base-ui.com/react/components/tooltip)) | Evaluate touch/tooltip notes in their docs vs product needs                                                                                                                                                      |
| **Tippy.js**                                                     | All-in-one tooltip                             | Mature; many options                                                                                                          | Different model than Radix; compare bundle and React integration if considered ([Floating UI vs Tippy vs Radix](https://www.pkgpulse.com/blog/floating-ui-vs-tippyjs-vs-radix-tooltip-popover-positioning-2026)) |
| **Native `title`**                                               | Browser default                                | Zero dependency                                                                                                               | Poor keyboard/touch story; not suitable for rich content                                                                                                                                                         |


**Recommendation for this project (pre-implementation):** Prefer **Radix Tooltip + Popover** (or **shadcn** wrappers if the team wants ready-made Tailwind markup) so **long strategy text** can use Popover/dialog patterns while short glosses use Tooltip. Use **Floating UI alone** only if bundle audits rule Radix out and the team commits to implementing WCAG-aligned behavior by hand.

### 1.3 Bundle size

Public posts often compare patterns; **exact KB** depends on versions, bundler, and tree-shaking. The spike “pass” remains: add candidate deps to the **lesson-browser** (or shared UI package), run production build, and record before/after. Radix documents tree-shakeable installs per package ([Radix Introduction](https://www.radix-ui.com/primitives/docs/overview/introduction)).

---

## 2. Accessibility patterns (relevant to Q3 and success criteria S4–S5)

### 2.1 WCAG 1.4.13 – Content on Hover or Focus

Additional content triggered by hover or focus should be **dismissible**, **hoverable** (pointer can move to the content without it vanishing), and **persistent** until dismissed or invalid—see [Understanding 1.4.13](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html) (WCAG 2.2 link; 2.1 understanding is similar).

This supports the product direction: **do not put mission-critical information only in a hover tooltip** without a keyboard-equivalent path; **Escape** dismissal aligns with [APG Tooltip Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/).

### 2.2 Tooltip vs popover / dialog

APG: a **tooltip** is typically brief, associated with `role="tooltip"` and `aria-describedby`; **interactive content** belongs in patterns that allow focus inside (e.g. popover/dialog), not inside a classic tooltip—see [Tooltip pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/) and general [CSS-Tricks tooltip practices](https://css-tricks.com/tooltip-best-practices/).

Maps to our split: `**short_en`** → tooltip-style; `**long_en` / lists** → popover or disclosure.

### 2.3 Touch devices

Touch has no hover; product success criterion **S5** requires **tap** to open rich help. Libraries may disable or alter tooltip behavior on touch; verify in chosen primitives (e.g. Base UI notes touch limitations in their tooltip docs—re-validate before relying on any single sentence).

---

## 3. Answers to questions in `01_research_questions_and_success_criteria.md`


| ID                                       | Direction from sources / practice                                                                                                                                                                                    |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1** (structured first)                | **Yes, strongly recommended for v1.** Structured `strategy_id` avoids false positives; prose matching is a known NLP/UX hazard (paraphrase, overlap). Aligns with SSOT in [02](./02_data_inventory_and_matching.md). |
| **Q2** (WIDA v1 scope)                   | **Regex-friendly fragments + `wida_framework_reference.json`** are sufficient for v1; full PDF-sourced sentences belong with [WIDA_FRAMEWORK_INGESTION_AND_USE.md](../WIDA_FRAMEWORK_INGESTION_AND_USE.md).          |
| **Q3** (hover vs click for rich content) | **Prefer click/focus for long content**; keep hover for short gloss. Supported by WCAG 1.4.13 and APG (avoid hover-only critical paths).                                                                             |
| **Q4** (user toggle)                     | No universal library feature—**app-level setting** (e.g. suppress annotations) if implemented; defer to v2 unless user research demands it.                                                                          |
| **Q5** (aliases)                         | **Yes for matching**, if prose matching is added: strategy pack `aliases[]` should map to the same lookup entry as `strategy_id` to reduce missed matches.                                                           |
| **T1** (markdown + spans)                | No single “best” library: options remain **segment-then-markdown**, **markdown-then-walk React tree**, or **MDX/custom components**; see [04](./04_technical_spikes_checklist.md) S2.                                |
| **T2** (LLM paraphrase)                  | **No tooltip** unless above confidence threshold, or show **generic “Strategy definitions”** link—avoids wrong gloss.                                                                                                |
| **T3** (overlap)                         | **Prefer longest match** among dictionary phrases, or **priority order** by `strategy_id`; multi-pattern matchers (e.g. Aho-Corasick) find occurrences; tie-breaking policy is product-defined.                      |
| **T4** (offline)                         | **Ship JSON in app bundle** for Tauri offline; same as spike S3—no web search dependency.                                                                                                                            |


---

## 4. Markdown / annotation (T1)

Popular stacks for rich text with components include **MDX** (embed React in markdown) and **unified/remark** pipelines; both imply build and security considerations (allowlist). For **annotating existing lesson strings**, the team’s **segment-and-render** approach avoids full MDX migration—see [04](./04_technical_spikes_checklist.md) spike S2.

---

## 5. Follow-ups (measurable)

1. Add Radix (or shadcn) to the target package and record **gzip bundle delta** from `vite build` / analyzer.
2. Prototype one **ELD code** regex field with Tooltip vs Popover split and run **keyboard + VoiceOver/NVDA** smoke test.
3. Re-read **Base UI** / **React Aria** tooltip touch behavior if the team prefers those stacks over Radix.

---

## 6. Document index update


| File                     | Role                                                   |
| ------------------------ | ------------------------------------------------------ |
| [README.md](./README.md) | Add link to this file under document index when stable |


