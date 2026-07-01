# Rental Preferences Git Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist listing like/dislike choices to a repository JSON file and automatically commit and push the file to GitHub after each saved change.

**Architecture:** Replace the plain static server with a small Python HTTP service that still serves the existing HTML files, plus JSON API endpoints for reading and saving preferences. The browser keeps the instant `localStorage` behavior, then calls the local API to write `rental_preferences.json` and trigger git sync.

**Tech Stack:** Python 3.11 standard library, browser `fetch`, existing static HTML/JavaScript, git CLI.

## Global Constraints

- Do not put GitHub credentials or tokens into browser JavaScript.
- Only the local Python service may write files or run git commands.
- Git sync commits only `rental_preferences.json` for preference changes.
- Keep the existing page usable without the service by preserving `localStorage`, export, and import behavior.

---

### Task 1: Preference Storage And Git Sync Service

**Files:**
- Create: `rental_pref_service.py`
- Create: `tests/test_rental_pref_service.py`

**Interfaces:**
- Produces: `save_preference(repo_root: Path, payload: dict) -> dict`
- Produces: `git_commit_and_push(repo_root: Path, message: str, runner: Callable, push: bool = True) -> dict`

- [x] **Step 1: Write failing tests**
- [x] **Step 2: Run tests and verify missing module failure**
- [x] **Step 3: Implement the service helpers**
- [x] **Step 4: Run tests and verify they pass**

### Task 2: Browser Integration

**Files:**
- Modify: `zhangjiang_shortlist_15km_preview.html`

**Interfaces:**
- Consumes: `GET /api/preferences`
- Consumes: `POST /api/preferences`

- [x] **Step 1: Keep localStorage as the instant source for rendering**
- [x] **Step 2: Add a compact toolbar showing like/dislike counts and git sync state**
- [x] **Step 3: On each click, save locally, render immediately, then POST to the local service**
- [x] **Step 4: Keep JSON export/import controls for manual backup**

### Task 3: Runtime Switch

**Files:**
- Modify: local process only

**Interfaces:**
- Serves: `http://127.0.0.1:8766/zhangjiang_shortlist_15km_preview.html`

- [x] **Step 1: Stop the previous `python -m http.server` process**
- [x] **Step 2: Start `python rental_pref_service.py --host 127.0.0.1 --port 8766 --push`**
- [x] **Step 3: Verify HTTP page and API responses**
