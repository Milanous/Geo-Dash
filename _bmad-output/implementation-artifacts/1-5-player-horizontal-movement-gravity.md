# Story 1.5: Player Horizontal Movement & Gravity

Status: review

## Story

As a player,
I want my character to move automatically to the right and fall under gravity,
so that the game feels like Geometry Dash.

## Acceptance Criteria

1. **Given** `engine/player.py` exists with a `Player` class **When** `player.update(dt)` is called **Then** `player.state.x` increases by `PLAYER_SPEED * dt`
2. **And** `player.state.vy` decreases by `GRAVITY` each step (`vy += GRAVITY`, no dt scaling on gravity)
3. **And** `player.state.y` changes by `vy * dt` each step
4. **And** the player falls indefinitely with no floor
5. **And** `engine/player.py` does not import `pygame`
6. **And** a test in `tests/test_physics.py` verifies x advances by exactly `PLAYER_SPEED * DT` per step

## Tasks / Subtasks

- [ ] Task 1 — Implement engine/player.py (AC: 1-5) — combined with Story 1.6
  - [ ] 1.1 `Player.__init__` — holds `PlayerState` + `alive: bool`
  - [ ] 1.2 `Player.update(dt, world=None)` — x/vy/y update + collision dispatch
  - [ ] 1.3 `Player._resolve_collision(world)` — world boundary + tile SOLID/SPIKE
  - [ ] 1.4 `Player.jump()` — only on_ground, no double-jump
- [ ] Task 2 — Add player movement tests to tests/test_physics.py (AC: 6)
  - [ ] 2.1 x advances exactly PLAYER_SPEED * DT per step
  - [ ] 2.2 vy decreases by GRAVITY per step (no floor)
  - [ ] 2.3 y changes by vy * dt (falls without floor)

## Dev Notes

### Y-axis convention
- y=0 = world floor; higher y = higher up
- GRAVITY = -0.958 (negative = pulls y downward)
- `vy += GRAVITY` each step (no dt scale — per AC)
- `y += vy * dt` each step
- JUMP_VELOCITY = +12.36 → initial upward velocity

### Coordinate and collision design
- Player bounding box: 1×1 block at (x, y) — y is bottom-left
- `_resolve_collision`: world boundary first (y <= 0), then tile row check
- Tile col/row: `int(state.x)`, `int(state.y)` — check tile the player's bottom is in
- SOLID + vy <= 0 → snap y = row (integer), vy=0, on_ground=True
- SPIKE → alive = False

### References
- [Source: architecture.md#Catégorie 1] — physics constants, ax convention
- [Source: architecture.md#Catégorie 6] — PlayerState
- [Source: epics.md#Story 1.5] — ACs

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List

### File List

### Change Log
- 2026-03-05: Story file created — implemented together with Story 1.6 in engine/player.py
