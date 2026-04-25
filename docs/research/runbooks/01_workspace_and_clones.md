# Runbook 01 — Workspace and shallow clones

This runbook is **Step 1** of the agentic document research workflow. It prepares `research/agentic_doc_extraction/` for local reference clones only. **Do not** install Python dependencies across all repositories in this step.

**Next:** [02_pass1_all_repositories.md](02_pass1_all_repositories.md)

---

## Prerequisites

- **Git** installed and on `PATH` (2.30+ recommended for consistent shallow clone behavior).
- **Disk space:** Ten shallow clones typically land in the **hundreds of MB to a few GB** depending on repo history blobs and submodules. Large monorepos (e.g. LlamaIndex) are still smaller shallow than full clones. Free **5–10 GB** before cloning if possible.
- **Network:** Public HTTPS clones; no auth required for the listed GitHub repos.
- **Git LFS:** These ten projects are usually **ordinary Git**; upstream may add LFS for assets. If `git clone` warns about LFS or fails on large objects, read **that repository’s** README and install [Git LFS](https://git-lfs.com/) only if required. **Marker** may reference model weights or downloads in docs—check its README *before* assuming you need GPU weights for Pass 1 (reading the repo does not require full model download).

---

## Directory layout and git policy

From the **repository root** (`LP/`):

- [research/agentic_doc_extraction/README.md](../../../research/agentic_doc_extraction/README.md) — **committed**; quick rules and clone URLs.
- `research/agentic_doc_extraction/clones/` — **gitignored**; place all shallow clones here.
- `research/agentic_doc_extraction/spikes/` — **gitignored**; used in Runbook 04, not in this step.

Only `clones/` and `spikes/` are ignored; the README and this `docs/research/` tree are tracked.

---

## Bootstrap directories

Run from **repository root** (`d:\LP` or equivalent).

**POSIX (bash):**

```bash
mkdir -p research/agentic_doc_extraction/clones
mkdir -p research/agentic_doc_extraction/spikes
```

**Windows PowerShell:**

```powershell
New-Item -ItemType Directory -Force -Path research/agentic_doc_extraction/clones
New-Item -ItemType Directory -Force -Path research/agentic_doc_extraction/spikes
```

---

## Clone working directory (critical)

All `git clone` commands in this project assume **current working directory** is:

```text
research/agentic_doc_extraction
```

So clone targets are `clones/docling`, `clones/unstructured`, etc., matching [README.md](../../../research/agentic_doc_extraction/README.md).

**Example (POSIX):**

```bash
cd research/agentic_doc_extraction
git clone --depth 1 https://github.com/docling-project/docling.git clones/docling
```

**Example (PowerShell):**

```powershell
Set-Location research\agentic_doc_extraction
git clone --depth 1 https://github.com/docling-project/docling.git clones/docling
```

If you clone from the repo root without `clones/` in the path, fix with re-clone or move the folder so paths stay consistent for team notes.

---

## Study order and clone commands

Use **`--depth 1`** unless you have a specific need for full history.

1. **Layout / normalization:** docling, unstructured, marker, markitdown  
2. **Structured extraction:** langextract, instructor  
3. **Crawl / extract:** firecrawl, crawl4ai, scrapegraph-ai  
4. **Orchestration:** llama_index  

Full one-liners live in [README.md](../../../research/agentic_doc_extraction/README.md); duplicate here for convenience after `cd research/agentic_doc_extraction`:

```bash
git clone --depth 1 https://github.com/docling-project/docling.git clones/docling
git clone --depth 1 https://github.com/Unstructured-IO/unstructured.git clones/unstructured
git clone --depth 1 https://github.com/datalab-to/marker.git clones/marker
git clone --depth 1 https://github.com/microsoft/markitdown.git clones/markitdown
git clone --depth 1 https://github.com/google/langextract.git clones/langextract
git clone --depth 1 https://github.com/567-labs/instructor.git clones/instructor
git clone --depth 1 https://github.com/firecrawl/firecrawl.git clones/firecrawl
git clone --depth 1 https://github.com/unclecode/crawl4ai.git clones/crawl4ai
git clone --depth 1 https://github.com/ScrapeGraphAI/Scrapegraph-ai.git clones/scrapegraph-ai
git clone --depth 1 https://github.com/run-llama/llama_index.git clones/llama_index
```

---

## After each clone: pin the SHA

For [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md):

```bash
cd clones/<name>
git rev-parse HEAD
```

Record the full SHA in the **Pinned SHA** column when you complete Pass 1 for that row (Runbook 02). You may copy SHA immediately after clone if the row is ready for tracking; update again if you later `git pull`.

---

## Verification

- **Listing:** `ls clones` / `Get-ChildItem clones` — expect ten directories when done (or fewer if you clone incrementally).
- **Sanity:** `cd clones/docling && git rev-parse --is-inside-work-tree` should print `true`.
- **Shallow check:** `git rev-parse --git-dir` then inspect `.git/shallow` exists or `git log --oneline | wc -l` shows very few commits.

---

## Failure modes and fixes

| Symptom | Likely cause | Action |
|--------|---------------|--------|
| `repository not found` | Typo, network, or GitHub outage | Retry; verify URL in browser |
| Clone stuck / huge download | Submodules or unexpected blobs | Cancel; read upstream README; try `--depth 1` again; consider `--recurse-submodules=no` (default) |
| Wrong path | CWD not `research/agentic_doc_extraction` | Remove bad folder; re-clone into `clones/<name>` |
| SSL errors | Corporate proxy | Configure Git SSL/proxy per IT policy |

---

## What not to do in Step 1

- Do **not** run `pip install -e .` or full dev setup in every clone (slow, easy dependency conflicts). Install only inside a **spike** venv (Runbook 04) when you execute code.
- Do **not** commit anything under `clones/` or `spikes/`.

---

## Step 1 definition of done

- `research/agentic_doc_extraction/clones/` exists and contains the repos you need for the current research wave (typically **all ten**).
- You can `cd` into each clone and run `git rev-parse HEAD` successfully.
- You are ready to start Runbook 02 (Pass 1) in the **study order** above.
