# Using This Repository

This document explains how to use this Git repository as the main codebase for the **Bilingual Weekly Plan Builder** and how to keep creating lesson plans with it.

---

## What This Repo Is

- **Single source of truth** for the Bilingual Weekly Plan Builder application.
- **Remote:** `origin` → `https://github.com/rodrigueswilson/lesson-plan-browser.git`
- **Main branch:** `master` (you can rename to `main` on GitHub if you prefer; see below).

---

## 1. Get the Code and Keep It Updated

**First time (clone):**
```powershell
git clone https://github.com/rodrigueswilson/lesson-plan-browser.git LP
cd LP
```

**Already cloned (update before starting work):**
```powershell
cd D:\LP
git pull origin master
```

Always pull before a work session so you have the latest shared version.

---

## 2. Run the App to Create Lesson Plans

1. **Backend** (API + processing):
   ```powershell
   cd backend
   python -m uvicorn api:app --reload
   ```
   Leave this running (default: http://localhost:8000).

2. **Frontend** (desktop UI):
   ```powershell
   cd frontend
   npm run tauri dev
   ```
   Or use the standalone script from the repo root if you have one (e.g. `start-frontend.bat`).

3. **Use the app:** Upload your weekly DOCX, review, generate, and download the enhanced bilingual plan.  
   Details: **[Quick Start Guide](QUICK_START_GUIDE.md)** and **[User Training Guide](../training/USER_TRAINING_GUIDE.md)**.

---

## 3. Git Workflow for Day-to-Day Use

- **Before creating lesson plans or coding:** `git pull origin master`
- **After finishing a feature or fix:** commit and push:
  ```powershell
  git add <files>
  git commit -m "Short description"
  git push origin master
  ```
- **For big changes (e.g. refactoring BatchProcessor):** work on branch `refactor/batch-processor`, then merge when ready (see section 5).

---

## 4. Returning to the Stable Main Version

The **stable main version** (working state before refactors) is saved in two ways:

- **Branch:** `master` – the main line; keep it stable for lesson-plan work.
- **Tag:** `main-stable` – exact commit you can always check out:
  ```powershell
  git checkout main-stable   # detached HEAD at that commit
  # or create a branch from it:
  git checkout -b recovery main-stable
  ```
  To get back to `master`:
  ```powershell
  git checkout master
  ```

---

## 5. Refactoring on a Branch (e.g. batch_processor)

The branch **refactor/batch-processor** is for incremental refactor work. You are on it after setup.

**Switch between branches:**

- **Master to refactor branch:** `git checkout refactor/batch-processor`
- **Refactor branch to master:** `git checkout master`
- **See which branch you're on:** `git branch` — the current branch has an asterisk next to it.

- **Work on the refactor:** stay on `refactor/batch-processor`, edit `tools/batch_processor.py` (and related files), commit often.
- **Switch back to stable main:** use `git checkout master` for normal lesson-plan work. Tip: if you usually use the app for lesson plans, stay on `master` day to day and only switch to this branch when refactoring; then you never need to checkout master just to open the app.
- **When refactor is done:** merge into master and push:
  ```powershell
  git checkout master
  git merge refactor/batch-processor
  git push origin master
  ```
- **Update the stable tag (optional):** after merging, move the tag to the new tip of master:  
  `git tag -f -a main-stable -m "Stable after batch_processor refactor"` then `git push origin main-stable --force`.

---

## 6. Pushing the Main Version (One-Time Setup)

Your current **main version** is the latest commit on `master`. To make sure it is the one on GitHub:

1. **Fix any Git issues (if you had errors):**  
   The repo had a corrupted `.git/packed-refs`; it was repaired so `git status` and `git push` work again.

2. **Decide about uncommitted changes:**
   - You have many **uncommitted** changes (deleted/modified/untracked files).
   - **Option A – Push only what is already committed (recommended for a clean “main”):**  
     Do not add/commit. Just push:
     ```powershell
     git push -u origin master
     ```
     The “main version” on GitHub will be your last commit (e.g. “Add: Standalone frontend startup script”).
   - **Option B – Make current folder the new main version:**  
     If you want everything in your working tree to become the new main version:
     ```powershell
     git add -A
     git status   # review
     git commit -m "Main version: current state before refactor"
     git push -u origin master
     ```

3. **Optional – Use `main` instead of `master`:**
   - On GitHub: **Settings → General → Default branch** → rename `master` to `main`.
   - Locally:
     ```powershell
     git branch -m master main
     git push -u origin main
     ```
   - Then update default branch on GitHub to `main` if needed.

After this, **the main version is defined and pushed**; use the workflow in section 3 to keep creating lesson plans and updating the repo.
