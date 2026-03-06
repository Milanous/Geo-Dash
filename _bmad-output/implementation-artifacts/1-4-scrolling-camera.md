# Story 1.4: Scrolling Camera

Status: review

## Story

As a player,
I want the camera to follow my horizontal position so I can always see what is ahead,
so that the level scrolls as I move right.

## Acceptance Criteria

1. **Given** `engine/camera.py` exists with a `Camera` class **When** `Camera(x_offset=0)` is instantiated **Then** `camera.world_to_screen_x(bloc_x)` returns `World.to_px(bloc_x) - camera.x_offset`
2. **When** `camera.follow(player_x)` is called **Then** `camera.x_offset` is updated so the player appears at a fixed horizontal screen position (PLAYER_ANCHOR_PX = 200 px from left)
3. **And** `camera.x_offset` never goes below 0 (no negative scroll)
4. **And** `engine/camera.py` does not import `pygame`

## Tasks / Subtasks

- [x] Task 1 — Implement engine/camera.py (AC: 1-4)
  - [x] 1.1 Define `Camera` with `x_offset: int` initialised to 0
  - [x] 1.2 Implement `world_to_screen_x(bloc_x)` → `World.to_px(bloc_x) - self.x_offset`
  - [x] 1.3 Implement `follow(player_x)` — update x_offset to keep player at PLAYER_ANCHOR_PX
  - [x] 1.4 Clamp `x_offset` to >= 0
- [x] Task 2 — Write tests (AC: 1-4)
  - [x] 2.1 world_to_screen_x with zero offset
  - [x] 2.2 world_to_screen_x with non-zero offset
  - [x] 2.3 follow() positions player at anchor
  - [x] 2.4 follow() never sets x_offset below 0

## Dev Notes

### Camera Design
- `PLAYER_ANCHOR_PX = 200` — fixed horizontal screen position for the player
- `x_offset` is in **pixels** (int) — the pixel column of the world that appears at screen x=0
- `world_to_screen_x(bloc_x)` converts a world block coordinate to screen pixel x
- `follow(player_x)`:
  - `desired_offset = World.to_px(player_x) - PLAYER_ANCHOR_PX`
  - `self.x_offset = max(0, desired_offset)`

### Import Rules
- `engine/camera.py` imports only `engine.world.World` and stdlib
- Forbidden: `pygame`, `renderer`, `ai`

### References
- [Source: architecture.md#Catégorie 2] — World coordinate ownership
- [Source: epics.md#Story 1.4] — acceptance criteria

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List
- `PLAYER_ANCHOR_PX = 200` — player anchor at 200 px from left edge.
- `follow()` computes `desired = World.to_px(player_x) - PLAYER_ANCHOR_PX`, clamped to 0.
- `world_to_screen_x()` delegates to `World.to_px()` — no pixel math duplicated.
- 16 new tests; 75/75 total ✅

### File List
- engine/camera.py
- tests/test_camera.py
- _bmad-output/implementation-artifacts/1-4-scrolling-camera.md

### Change Log
- 2026-03-05: Story file created, status → in-progress
- 2026-03-05: Implementation complete, 75/75 tests pass, status → review
