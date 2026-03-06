# Story 2.3: Spike Tiles & Death Detection

Status: review

## Story

As a player,
I want spike tiles to be rendered as triangles and kill me on contact,
so that hazards are visually clear and gameplay consequences are immediate.

## Acceptance Criteria

1. **Given** a level with `TileType.SPIKE` tiles **When** the game renderer draws the scene **Then** each spike is drawn as a filled equilateral triangle occupying the full 1×1 tile area ✅
2. **When** the player's bounding box overlaps any spike tile **Then** `player.alive` is set to `False` ✅
3. **And** the play scene resets the player on next update after death ✅
4. **And** tests in `tests/test_world.py` verify spike collision detection headlessly ✅
5. **Note** Block-tint variation for spikes is deferred to Story 2.6 (gradient sky & tint)

## Tasks / Subtasks

- [x] Task 1 — Spike rendering as filled triangle in `renderer/game_renderer.py`
  - [x] 1.1 Triangle polygon points: bottom-left, bottom-right, apex-center
  - [x] 1.2 Orange spike colour constant `_SPIKE_COLOR = (255, 110, 40)`
- [x] Task 2 — Spike collision → `player.alive = False` in `engine/player.py`
  - [x] 2.1 `_resolve_collision` detects `TileType.SPIKE` → `self.alive = False`
  - [x] 2.2 No y-snap on spike (unlike SOLID)
- [x] Task 3 — Play scene resets player after death in `ui/play_scene.py`
  - [x] 3.1 `update()` checks `not self._player.alive` → new `Player(start_x, start_y)`
- [x] Task 4 — Tests in `tests/test_world.py`
  - [x] 4.1 `test_player_spike_sets_alive_false` — falls into row of spikes → dead
  - [x] 4.2 `test_spike_at_player_grid_cell_kills_in_one_step` — dies in 1 update
  - [x] 4.3 `test_spike_collision_does_not_snap_player_y` — no y-snap like SOLID

## Dev Notes

### Notes
- Spike rendering and collision were already implemented during Epic 1 (Stories 1.6 & 1.7) as part of the initial renderer and player setup. Story 2.3 formalizes and completes the test coverage.
- Block-tint variation for spikes (AC "spike tiles receive the same block-tint variation") is explicitly deferred to Story 2.6 which owns all tint logic.

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Completion Notes List
- Triangle rendering: `renderer/game_renderer.py` — `_draw_tiles()`, spike branch with `pygame.draw.polygon`
- Spike collision: `engine/player.py` — `_resolve_collision()`, `elif tile == TileType.SPIKE: self.alive = False`
- Scene reset: `ui/play_scene.py` — `update()` checks `not self._player.alive`
- 2 new tests added in `tests/test_world.py` (lines 289–310)

### File List
- `renderer/game_renderer.py` (spike triangle drawing — pre-existing from Story 1.7)
- `engine/player.py` (spike collision — pre-existing from Story 1.6)
- `ui/play_scene.py` (play scene reset — pre-existing from Story 1.7)
- `tests/test_world.py` (2 new tests: `test_spike_at_player_grid_cell_kills_in_one_step`, `test_spike_collision_does_not_snap_player_y`)

### Change Log
- 2026-03-05: Story 2.3 implemented and formalized — 107 tests passing
