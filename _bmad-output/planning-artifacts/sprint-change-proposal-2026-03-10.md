# Sprint Change Proposal — Parametric Level Generator

**Date:** 2026-03-10
**Author:** Bob (Scrum Master)
**Status:** Approved & Implemented
**Scope:** Minor

---

## Section 1 — Issue Summary

### Problem Statement

The game currently requires using the level editor to create playable content, which limits
replayability and AI training variety. Milan wants to generate levels procedurally with
configurable parameters, accessible directly from the main menu, playable by a human or
trainable by the AI without going through the editor.

### Context

Identified before any related implementation was started. Epic 3 covers the persistent
level editor but contains no procedural generation story. This is a scope extension to
Epic 3 that adds infinite fresh content with zero editor overhead.

### Evidence

- `LevelSelectScene` only lists saved JSON files — no way to generate on-the-fly
- `editor/level_io.py` and `engine/world.py` are fully decoupled — trivial to produce a `World` without saving it
- `PlayScene` and `TrainConfigScene` both accept a `World` parameter — no integration changes needed

---

## Section 2 — Impact Analysis

### Epic Impact

| Epic | Impact |
|------|--------|
| Epic 1–2 | None — engine/renderer untouched |
| Epic 3 (Éditeur) | **Extended** — new Story 3.5 added |
| Epic 4 (Cerveaux IA) | None |
| Epic 5 (Entraînement) | None — `TrainConfigScene` reused as-is |

### Story Impact

| Story | Change | Type |
|-------|--------|------|
| 3.5 (NEW) | `engine/level_generator.py` — `GeneratorConfig` + `generate_level()` | New story |
| 3.5 (NEW) | `ui/gen_config_scene.py` — parameter form screen | New story |
| Existing 3.x | No change | Unchanged |
| `level_select_scene.py` | Add "🎲 Niveau Aléatoire" special entry + [G] shortcut | Modify |

### Technical Impact

- **New file:** `engine/level_generator.py` — pure stdlib + engine, no pygame
- **New file:** `ui/gen_config_scene.py` — pygame form scene, same pattern as `TrainConfigScene`
- **Modified:** `ui/level_select_scene.py` — special random entry at top of list, [G] key
- **0 changes** to engine/, renderer/, ai/, editor/, tests/

---

## Section 3 — Recommended Approach

**Direct Adjustment** — All changes contained within Epic 3 scope. No rollback needed.
No MVP modifications required. Effort: minimal (new files + 1 UI modification).

---

## Section 4 — Detailed Change Proposals

### 4.1 `engine/level_generator.py` (NEW)

`GeneratorConfig` dataclass with 15 parameters:

| Parameter | Default | Description |
|---|---|---|
| `length` | 1000 | Total level length in blocks |
| `height` | 20 | World height in blocks |
| `spike_density` | 0.15 | P(floor block → spike) |
| `gap_probability` | 0.10 | P(gap starts at this column) |
| `max_gap_width` | 3 | Max gap width in blocks |
| `platform_probability` | 0.08 | P(platform starts at this column) |
| `platform_min_width` | 2 | Min platform width |
| `platform_max_width` | 5 | Max platform width |
| `platform_min_height` | 3 | Min platform height above floor |
| `platform_max_height` | 6 | Max platform height above floor |
| `spike_under_platform` | True | SPIKE_DOWN tiles on underside |
| `stair_probability` | 0.06 | P(staircase starts at this column) |
| `stair_max_steps` | 5 | Max steps per staircase |
| `stair_step_height` | 1 | Height per step (1 or 2 blocks) |
| `seed` | None | RNG seed — None = random |

`generate_level(config) -> World` — builds fully populated World with:
- Safe start zone (6 cols) and safe end zone (4 cols + FINISH tile)
- Floor with gaps and spikes
- Floating platforms with optional SPIKE_DOWN underside
- Ascending staircase patterns

Import rule respected: no pygame, no renderer, no ai.

### 4.2 `ui/gen_config_scene.py` (NEW)

Two-column form grouped by category (Général / Dangers sol / Plateformes / Escaliers).
Each category has a distinct accent colour (cyan / red / purple / gold).
Actions: [Entrée] → Play, [T] → Train AI, [ESC] → Back.

### 4.3 `ui/level_select_scene.py` (MODIFIED)

**OLD:**
```
level_1
level_2
...
```

**NEW:**
```
🎲  Niveau Aléatoire  [G]   ← gold accent, always first
─────────────────────────────────
level_1
level_2
...
```

- Index 0 now reserved for the random entry (selected by default on scene entry)
- All existing keyboard navigation shifted by +1 (real levels start at index 1)
- [G] shortcut opens `GenConfigScene` from any selection position
- [E] and [R] disabled when random entry is selected (editing/replay not applicable)

---

## Section 5 — Implementation Handoff

**Scope classification:** Minor — implemented directly, no backlog reorganisation needed.

All deliverables are complete:
- `engine/level_generator.py` ✅ implemented & validated
- `ui/gen_config_scene.py` ✅ implemented & validated
- `ui/level_select_scene.py` ✅ modified & validated
- Story 3.5 added to `_bmad-output/planning-artifacts/epics.md` ✅
- 305 existing tests pass, 0 regressions introduced ✅
