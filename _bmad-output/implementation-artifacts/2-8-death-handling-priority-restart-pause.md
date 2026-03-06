# Story 2.8: Death Handling — Priority Fix & Restart Pause

Status: review

## Story

As a human player,
I want the game to properly handle my death (no false victory, 2-second pause before restart),
so that the death experience is clear and polished.

## Context

### Bug: Victory shown after death
In `ui/play_scene.py`, `update()` checks `self._player.state.finished` BEFORE `self._player.alive`. If both flags trigger in the same resolution pass (e.g., near a FINISH tile while also hitting a wall or spike), the victory scene is shown even though the player is dead. Additionally, when replaying after a previous completion, if the finished flag somehow persists, the same bug occurs.

### Missing: Death restart pause
Currently when the player dies (human mode, no `return_scene`), the player is immediately recreated in the same `update()` tick — no visual feedback. The user expects a 2-second freeze (player disappears or stops, game pauses) then auto-restart from the beginning of the level.

## Acceptance Criteria

1. **Given** the player dies (`alive = False`) **When** `update()` runs in PlayScene **Then** the death state is detected BEFORE any victory check — `alive` takes priority over `finished`
2. **Given** the player dies **When** `finished` was also set to `True` in `_resolve_collision` **Then** `finished` is cleared (set to `False`) in the engine layer when `alive` becomes `False`, so there's no ambiguity
3. **Given** the player dies in human play mode (no `return_scene`) **When** 0 to 2 seconds have elapsed since death **Then** the game freezes (no physics update, camera and VFX stop), the player square disappears or shows a death visual
4. **Given** the player dies in human play mode **When** exactly 2 seconds have elapsed **Then** the level auto-restarts from the beginning with a fresh Player at `_START_X, _START_Y` and reset VFX
5. **Given** the player dies with `return_scene` set (editor test mode) **When** death occurs **Then** immediately return to editor (existing behaviour preserved)
6. **Given** the AI simulation **When** a simulated player dies (`alive = False`) **Then** no timer/pause logic is involved — the AI checks `alive` directly (engine layer only, no UI pause)
7. **Tests** verify death-before-victory priority and the 2-second restart timer

## Tasks / Subtasks

- [x] Task 1 — Engine layer: clear `finished` on death in `engine/player.py`
  - [x] 1.1 In `_resolve_collision()`, after setting `self.alive = False` (for spike or wall), also set `self.state.finished = False`
- [x] Task 2 — PlayScene: fix death/victory priority in `ui/play_scene.py`
  - [x] 2.1 In `update()`, check `not self._player.alive` BEFORE `self._player.state.finished`
  - [x] 2.2 Ensure death path is taken even if finished is True
- [x] Task 3 — PlayScene: add 2-second death pause timer
  - [x] 3.1 Add `_death_timer: float | None = None` attribute to PlayScene
  - [x] 3.2 On first detection of death: set `_death_timer = 2.0`, stop updating physics
  - [x] 3.3 Each `update()` call decrements timer: `_death_timer -= dt`
  - [x] 3.4 When `_death_timer <= 0`: reset player, reset VFX, clear timer
  - [x] 3.5 During death pause: `draw()` renders scene without player (None → renderer skips player)
- [x] Task 4 — Tests
  - [x] 4.1 `test_death_priority_over_victory` — player with alive=False and finished=True → no VictoryScene transition
  - [x] 4.2 `test_death_pause_timer` — after death, player is not reset until timer expires
  - [x] 4.3 `test_death_immediate_return_editor` — with return_scene, death still returns to editor immediately (regression)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (GitHub Copilot — Bob/Amelia)

### Completion Notes List
- Death priority: `ui/play_scene.py` — `alive` checked before `finished` in `update()`
- Death timer: `_death_timer` float, 2.0s countdown, then reset player
- Player hidden during death: `draw()` passes `None` to renderer when timer active
- Engine layer: `finished = False` on death (wall + spike) in `_resolve_collision()`
- 3 new tests in `tests/test_game_loop.py`

### File List
- `engine/player.py` (finished=False on death)
- `ui/play_scene.py` (death priority, death timer, player hidden during death)
- `renderer/game_renderer.py` (draw() already accepts Player|None)
- `tests/test_game_loop.py` (3 new death handling tests)

### Change Log
- 2026-03-06: Story 2.8 implemented — 231 tests passing

## Dev Notes

### Death timer implementation
The death timer should be a simple countdown float. During the death pause:
- `handle_events()` still processes QUIT/ESC but ignores SPACE (no jump during death)
- `update()` only decrements the timer, no physics
- `draw()` renders the frozen world without the player (or with a static death indicator)

### AI isolation
The 2-second pause is purely a UI concern (`PlayScene`). The engine-layer `Player.alive` flag is the sole death signal for both human and AI. AI simulation never goes through PlayScene — it reads `Player.alive` directly after `Player.update()`.

### Draw during death
During the death pause, the renderer should still draw the world and camera at their frozen positions. The player square should not be drawn (or could flash/fade — keep it simple: just don't draw the player). VFX particles can continue to decay but no new ones spawn.

### Architecture reference
- `ui/play_scene.py` — UI layer, owns human play loop
- `engine/player.py` — engine layer, owns `alive` and `finished` flags
- No cross-layer timer: UI timer stays in UI, engine death stays in engine
