# Runbook 06 — License hygiene and regression

This runbook is **Step 6** (ongoing): **copyleft awareness**, **no blind paste** rules, and **revisiting** pinned commits when upstream or your needs change.

**Prerequisites:** At least Pass 1 complete; preferably a full wave through [05_research_to_product_backlog.md](05_research_to_product_backlog.md).

---

## Copyleft and high-friction licenses (reference repos)

Treat the master table in [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) as the checklist. Known items to double-check in **your** Pass 1 notes:

| Repo | Typical license concern | Practical LP stance |
|------|-------------------------|----------------------|
| **firecrawl** | **AGPL-3.0** | Pattern-only, sidecar service, or legal review before embedding or modifying code in the app. **Do not** paste substantial snippets into `tools/scraper` without review. |
| **marker** | **GPL-3.0** + model / weight terms | Treat as **dependency or subprocess** only with compliance review; understand commercial/model restrictions in their LICENSE. |
| Others (MIT, Apache-2.0) | Lower friction | Still prefer **PyPI dependency** over vendoring; attribute per license. |

This table is **guidance**, not legal advice. Record **your** reading of the actual `LICENSE` file at pinned SHA in deep notes when uncertainty affects a spike.

---

## No-paste policy (engineering)

- **OK:** New code **you** write, informed by API shapes, CLI flags, or architecture diagrams you saw upstream.  
- **OK:** Quoting **small** fair-use snippets in **internal** research notes with citation (repo, file, SHA).  
- **Not OK:** Copying substantial modules from AGPL/GPL projects into LP without explicit approval.  
- **Prefer:** Import library from PyPI in an isolated tool or document **why** a subprocess boundary is used.

---

## Permissive libraries

MIT/Apache/BSD rows still warrant:

- **Dependency budget** — extra install size, CI time, and security surface  
- **Overlap** — e.g. two markdown converters with no clear owner

Update **Verdict** to **Out-of-scope** when a permissive project is redundant with existing LP code.

---

## Revisit cadence

- **Quarterly** (or before a **major ingest redesign**): for each row still **Dependency-candidate** or **Adopt**, run `git fetch` in the clone (or re-clone shallow), compare **LICENSE** and **CHANGELOG** / release notes, update **Pinned SHA** and re-skim Pass 1 questions in **15–20 minutes** per repo.
- If **verdict** flips (e.g. license change, deprecation), add **one dated line** to **Deep notes**: `YYYY-MM-DD: verdict X→Y because …`

---

## Regression of research notes

Stale notes hurt more than no notes. When SHAs drift:

- Refresh **Pinned SHA** in the index  
- If bullets in the index contradict current upstream behavior, **strike through** or replace with dated clarification—do not leave contradictory SSOT in committed docs  

---

## Optional: wave close-out checklist

- [ ] All index rows have current **Pinned SHA** for repos still **Adopt** / **Dependency-candidate**  
- [ ] AGPL/GPL rows have explicit **Pattern-only** / **sidecar** / **legal TBD** in **Verdict** or **Deep notes**  
- [ ] No large pasted upstream code in `tools/scraper` from this wave without ticket reference  

---

## Definition of done (Step 6)

- Copyleft and model-license risks for **firecrawl** and **marker** (minimum) are **explicit** in index or linked deep note.  
- Revisit policy adopted (quarterly or event-driven) and documented here or in index footer.  
- Research wave closed with **no silent** stale SHA on active dependencies.
