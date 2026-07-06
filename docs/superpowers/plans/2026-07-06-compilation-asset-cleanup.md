# Compilation Asset Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete day-level generated image assets after a full compilation upload and Drive backup succeed.

**Architecture:** Reuse the existing per-DAY `asset_manifest` stored in upload logs instead of reconstructing word assignments from CSV. Add one cleanup helper for compilation ranges, call it only after compilation upload and Drive backup succeed, and cover the behavior with focused `unittest` cases.

**Tech Stack:** Python, Streamlit, unittest, existing upload log and cleanup helpers

---

### Task 1: Range Cleanup Tests

**Files:**
- Modify: `D:\backup\jlpt_word\tests\test_ops_helpers.py`
- Test: `D:\backup\jlpt_word\tests\test_ops_helpers.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cleanup_generated_assets_for_compilation_range_deletes_manifest_images(self):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m unittest D:\backup\jlpt_word\tests\test_ops_helpers.py`
Expected: FAIL because the new cleanup helper does not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
def cleanup_generated_assets_for_compilation_range(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m unittest D:\backup\jlpt_word\tests\test_ops_helpers.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_ops_helpers.py src/cleanup/asset_cleanup.py
git commit -m "feat: cleanup compilation source assets"
```

### Task 2: Streamlit Full Compilation Hookup

**Files:**
- Modify: `D:\backup\jlpt_word\streamlit_app.py`
- Modify: `D:\backup\jlpt_word\deploy_policy_update.py`

- [ ] **Step 1: Write the failing test**

Use the Task 1 regression to define the helper contract before wiring the UI flow.

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m unittest D:\backup\jlpt_word\tests\test_ops_helpers.py`
Expected: FAIL before helper implementation

- [ ] **Step 3: Write minimal implementation**

```python
cleanup_generated_assets_for_compilation_range(...)
```

Call it after:
- `upload_compilation_video(...)`
- `backup_compilation_assets(..., delete_local=True)`
- before or alongside `delete_compilation_source_day_videos(...)`

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m unittest D:\backup\jlpt_word\tests\test_ops_helpers.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py deploy_policy_update.py
git commit -m "feat: cleanup compilation images after backup"
```

### Task 3: Verification and Deployment

**Files:**
- Modify: `C:\Users\admin\Documents\언어 쇼츠 생성기\deploy_policy_update.py`

- [ ] **Step 1: Run local verification**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m unittest D:\backup\jlpt_word\tests\test_ops_helpers.py`
Expected: PASS

- [ ] **Step 2: Run syntax verification**

Run: `D:\backup\jlpt_word\venv\Scripts\python.exe -m py_compile streamlit_app.py src\cleanup\asset_cleanup.py`
Expected: PASS

- [ ] **Step 3: Deploy and verify remotely**

Run the existing deployment helper and confirm:
- remote `unittest` passes
- `systemctl is-active jlpt-word` returns `active`
- `curl -I https://jlpt.hyoku.cloud --max-time 20` returns `200`

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-07-06-compilation-asset-cleanup.md
git commit -m "docs: add compilation cleanup plan"
```
