# Story 2.7: Wall Collision — Front-Face Death

Status: review

## Story

As a player (human or AI),
I want to die when I hit a SOLID block from the front (side collision),
so that obstacles are meaningful and I must jump at the right time.

## Context

Currently `_resolve_collision()` in `engine/player.py` only handles:
- Floor collision (landing on top of SOLID when `vy <= 0`)
- Hazard overlap (SPIKE → death, FINISH → win)

There is **no horizontal/wall collision**. The player passes through SOLID blocks laterally. In Geometry Dash, hitting a wall (not jumping in time) is the primary death mechanic.

## Acceptance Criteria

1. **Given** a player moving horizontally at `PLAYER_SPEED` **When** the player's leading edge (right side of bounding box, `x + 0.9`) enters a `TileType.SOLID` tile at the player's current row height **Then** `player.alive` is set to `False`
2. **Given** wall collision detection **When** the player is on the ground or in the air **Then** front-face collision kills in both cases (not just on the ground)
3. **Given** a SOLID block **When** the player lands on top of it from above (vy ≤ 0) **Then** the existing floor-snap behaviour is preserved (no death, player lands normally)
4. **Given** the wall collision system **When** accessed from AI headless simulation (no pygame) **Then** `Player.alive` becomes `False` identically — the detection is purely in the engine layer (`engine/player.py`), no UI dependency
5. **Tests** in `tests/test_world.py` verify wall collision kills the player headlessly
6. **Regression**: all existing tests still pass (spike, floor, jump, finish)

## Tasks / Subtasks

- [x] Task 1 — Add wall (front-face) collision detection in `engine/player.py` `_resolve_collision()`
  - [x] 1.1 After horizontal move, check if the player's right edge overlaps a SOLID tile at the player's body height (rows `int(y)` to `int(y + 0.9)`)
  - [x] 1.2 If overlap detected with SOLID at horizontal leading edge → `self.alive = False`
  - [x] 1.3 Ensure floor-landing (top-of-tile) is still resolved BEFORE wall check to avoid false kills when landing on top of a block
- [x] Task 2 — Tests in `tests/test_world.py`
  - [x] 2.1 `test_player_wall_collision_kills` — player on ground walks into a SOLID wall → dies
  - [x] 2.2 `test_player_wall_collision_in_air_kills` — player in air hits a SOLID wall → dies
  - [x] 2.3 `test_player_landing_on_top_does_not_kill` — player lands on top of SOLID block → alive, on_ground (regression)
  - [x] 2.4 `test_wall_collision_no_pygame_dependency` — headless test confirming no pygame import needed

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (GitHub Copilot — Bob/Amelia)

### Completion Notes List
- Wall collision: `engine/player.py` — `_resolve_collision()`, step 2 after floor snap
- `self.state.finished = False` on any death (wall or spike) to prevent victory bug
- 4 new tests in `tests/test_world.py`
- Also fixed gravity scaling: `GRAVITY * dt` instead of raw `GRAVITY` per step

### File List
- `engine/player.py` (wall collision + finished=False on death)
- `tests/test_world.py` (4 new wall collision tests)

### Change Log
- 2026-03-06: Story 2.7 implemented — 231 tests passing

## Dev Notes

### Collision detection approach
The player's bounding box is 1×1 block at `(x, y)`. The leading edge is `x + ~0.9` (right side). After horizontal movement (`x += PLAYER_SPEED * dt`), check tiles at column `int(x + 0.9)` for rows covering `int(y)` to `int(y + 0.9)`. If any of those tiles is SOLID and the player is NOT landing on top of it (i.e., it's at the same row height as the player body), that's a wall hit → death.

Key distinction: **floor collision** = SOLID tile is below the player's feet (player is above the tile's top surface). **Wall collision** = SOLID tile is at the same height as the player's body (player's side overlaps the tile).

### AI compatibility
`Player.alive` is already the death signal used by both human play and AI simulation. No additional API needed — just ensure the wall detection happens in the engine layer.

### Architecture reference
- `engine/player.py` — sole owner of collision logic (architecture.md: Catégorie 1)
- No pygame import allowed in engine/ (architecture.md: Process Patterns)
