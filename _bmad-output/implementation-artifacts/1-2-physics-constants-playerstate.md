# Story 1.2: Physics Constants & PlayerState

Status: review

## Story

As a developer,
I want all physics constants and the PlayerState dataclass defined in a single source-of-truth module,
so that every other module can import them without duplication or magic numbers.

## Acceptance Criteria

1. **Given** `engine/physics.py` exists **When** imported **Then** `PHYSICS_RATE == 240`
2. **And** `DT == 1.0 / 240`
3. **And** `GRAVITY == -0.958` (blocks/frame)
4. **And** `JUMP_VELOCITY == 12.36` (blocks/frame)
5. **And** `PLAYER_SPEED == 10.3761348998` (blocks/s)
6. **And** `BLOCK_SIZE_PX == 30`
7. **And** `PlayerState` dataclass has fields `x: float`, `y: float`, `vy: float`, `on_ground: bool`, `angle: float`
8. **And** `engine/physics.py` imports neither `pygame` nor any project module
9. **And** `tests/test_physics.py` asserts each constant to exact value and `DT == 1.0 / PHYSICS_RATE`

## Tasks / Subtasks

- [x] Task 1 — Implement engine/physics.py (AC: 1-8)
  - [x] 1.1 Define all 6 constants with exact values from architecture.md
  - [x] 1.2 Define `PlayerState` dataclass with 5 fields (x, y, vy, on_ground, angle)
  - [x] 1.3 Verify no pygame or project module imports
- [x] Task 2 — Write tests/test_physics.py (AC: 9)
  - [x] 2.1 Assert each constant to exact value
  - [x] 2.2 Assert `DT == 1.0 / PHYSICS_RATE`
  - [x] 2.3 Assert `PlayerState` can be instantiated with default fields
  - [x] 2.4 Assert `PlayerState` fields are correct types

## Dev Notes

### Constants (exact values from architecture.md#Catégorie 1)
```python
PHYSICS_RATE   = 240
DT             = 1.0 / 240
GRAVITY        = -0.958          # blocs/frame
JUMP_VELOCITY  = +12.36          # blocs/frame
PLAYER_SPEED   = 10.3761348998   # blocs/s
BLOCK_SIZE_PX  = 30              # px/bloc
```

### PlayerState (from architecture.md#Catégorie 6)
```python
@dataclass
class PlayerState:
    x: float; y: float; vy: float
    on_ground: bool; angle: float
```

### Import Rules
- `engine/physics.py` must import ONLY from stdlib (`dataclasses`)
- Forbidden: `pygame`, `renderer`, `ai`, any other project module

### References
- [Source: architecture.md#Catégorie 1] — physics constants
- [Source: architecture.md#Catégorie 6] — PlayerState definition
- [Source: architecture.md#Import Rules] — engine/ isolation
- [Source: epics.md#Story 1.2] — acceptance criteria

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List
- All 6 physics constants implemented with exact architecture values.
- `PlayerState` dataclass (not frozen) with default values — mutable for simulation.
- `DT` derived from `PHYSICS_RATE` (not hardcoded) ensuring consistency.
- No stdlib import beyond `dataclasses`; no pygame/project imports.
- 12 new tests + 23 regression tests: 35/35 ✅

### File List
- engine/physics.py
- tests/test_physics.py
- _bmad-output/implementation-artifacts/1-2-physics-constants-playerstate.md

### Change Log
- 2026-03-05: Story file created, status → in-progress
- 2026-03-05: Implementation complete, 35/35 tests pass, status → review
