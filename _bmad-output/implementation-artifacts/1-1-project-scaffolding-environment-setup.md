# Story 1.1: Project Scaffolding & Environment Setup

Status: review

## Story

As a developer,
I want the project directory structure, virtual environment, and dependencies initialized,
so that all subsequent stories have a consistent, runnable foundation.

## Acceptance Criteria

1. **Given** an empty project directory **When** the developer runs the setup commands **Then** the full module skeleton exists: `main.py`, `requirements.txt`, `engine/`, `renderer/`, `editor/`, `ai/`, `ui/`, `data/levels/`, `data/brains/`, `tests/`
2. **And** `pip install -r requirements.txt` succeeds without errors (`pygame==2.6.*` + `numpy>=1.26`)
3. **And** `python main.py` runs without import errors (exits immediately / opens and closes window is acceptable)
4. **And** no module in `engine/` imports `pygame`, `renderer/`, or `ai/`
5. **And** a `.gitignore` excluding `.venv/`, `__pycache__/`, `*.pyc`, `*.pyd` is present

## Tasks / Subtasks

- [x] Task 1 — Create requirements.txt and .gitignore (AC: 1, 2, 5)
  - [x] 1.1 Write `requirements.txt` with `pygame==2.6.*` and `numpy>=1.26`
  - [x] 1.2 Write `.gitignore` covering `.venv/`, `__pycache__/`, `*.pyc`, `*.pyd`, `.DS_Store`
- [x] Task 2 — Create package skeleton (AC: 1)
  - [x] 2.1 Create `engine/__init__.py`, `renderer/__init__.py`, `editor/__init__.py`
  - [x] 2.2 Create `ai/__init__.py`, `ui/__init__.py`, `tests/__init__.py`
  - [x] 2.3 Create `data/levels/.gitkeep`, `data/brains/.gitkeep`
- [x] Task 3 — Create main.py (AC: 3)
  - [x] 3.1 Write `main.py`: init pygame, open 800×600 window, run event loop, exit cleanly on ESC or QUIT
- [x] Task 4 — Validate import isolation (AC: 4)
  - [x] 4.1 Confirm `engine/__init__.py` does not import pygame, renderer, or ai
- [x] Task 5 — Tests (AC: 1, 4)
  - [x] 5.1 Write `tests/test_scaffolding.py` that asserts all expected files and directories exist
  - [x] 5.2 Verify all `engine/` modules (`__init__.py`) import cleanly without pygame

## Dev Notes

### Architecture Context
- Project root IS the workspace root (repo: Milanous/Geo-Dash)
- All module paths are relative to workspace root
- `engine/` must remain headless (no pygame, no renderer, no ai imports) — enforced by import rules matrix [Source: architecture.md#Import Rules]
- Naming: `snake_case` files, `PascalCase` classes, `UPPER_SNAKE_CASE` constants [Source: architecture.md#Naming Patterns]
- Tests live in `tests/` at root — no co-location [Source: architecture.md#Tests]

### main.py Canonical Pattern
```python
# Game loop pattern from architecture.md#Catégorie 1
accumulator += delta_time
while accumulator >= DT:          # DT = 1/240
    physics_step(DT)
    accumulator -= DT
render(interpolation=accumulator / DT)
```
For Story 1.1 main.py only needs: init pygame → open window → event loop → exit. Full game loop in Story 1.7.

### Import Rules (enforced)
| Module   | Can import          | Cannot import              |
|----------|---------------------|----------------------------|
| engine/  | stdlib, numpy       | renderer/, ai/, pygame     |
| ai/      | engine/, numpy      | renderer/, pygame          |
| renderer/| engine/, ai/brain.py, pygame | ai/simulation.py  |
| editor/  | engine/, pygame     | ai/, renderer/             |
| ui/      | all except ai/simulation.py directly | —        |

### References
- [Source: architecture.md#Structure Projet Retenue] — full directory tree
- [Source: architecture.md#Catégorie 1] — game loop pattern
- [Source: architecture.md#Naming Patterns] — coding conventions
- [Source: architecture.md#Import Rules] — module isolation rules
- [Source: epics.md#Story 1.1] — acceptance criteria origin

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List

- All 5 tasks completed, 22 tests pass (0 failures).
- `main.py`: minimal pygame loop, exits on ESC/QUIT, 800×600 window. Full game loop deferred to Story 1.7.
- `requirements.txt`: `pygame==2.6.*`, `numpy>=1.26`, `pytest>=8.0`.
- Import isolation verified via AST analysis in tests — `engine/` contains zero forbidden imports.
- `.gitignore` excludes `.venv/`, `__pycache__/`, `*.pyc`, `*.pyd`, `.DS_Store`, `data/levels/*.gmd`.

### File List

- `main.py`
- `requirements.txt`
- `.gitignore`
- `engine/__init__.py`
- `renderer/__init__.py`
- `editor/__init__.py`
- `ai/__init__.py`
- `ui/__init__.py`
- `tests/__init__.py`
- `tests/test_scaffolding.py`
- `data/levels/.gitkeep`
- `data/brains/.gitkeep`
- `_bmad-output/implementation-artifacts/1-1-project-scaffolding-environment-setup.md`

### Change Log
- 2026-03-05: Story file created, status → in-progress
- 2026-03-05: All tasks implemented, 22/22 tests passed, status → review
