# Story 1.6: Jump, Ground Collision & Floor Boundary

Status: review

## Story

As a player,
I want to be able to jump when on the ground and land on solid tiles,
so that I can navigate the level without falling through the world.

## Acceptance Criteria

1. **Given** a `World` with SOLID tiles at y=0 **When** the player falls onto y=0 **Then** `player.state.y == 0`, `vy == 0`, `on_ground == True`
2. **When** `player.jump()` called and `on_ground==True` **Then** `vy = JUMP_VELOCITY`, `on_ground = False`
3. **When** `player.jump()` called and `on_ground==False` **Then** vy unchanged (no double-jump)
4. **And** Y=0 world boundary catches the player even without a tile
5. **And** tests in `tests/test_world.py` verify collision and jump mechanics headlessly

## Tasks / Subtasks

- [ ] Task 1 — engine/player.py (see Story 1.5 — same file)
- [ ] Task 2 — Add collision and jump tests to tests/test_world.py (AC: 5)
  - [ ] 2.1 Landing on SOLID tiles at y=0 → y clamped, on_ground True
  - [ ] 2.2 World boundary (y<0) → clamped to 0 even without tile
  - [ ] 2.3 jump() when on_ground → vy=JUMP_VELOCITY, on_ground=False
  - [ ] 2.4 jump() when in air → vy unchanged (no double-jump)
  - [ ] 2.5 SPIKE tile contact → alive=False

## Dev Notes

### References
- [Source: architecture.md#Process Patterns] — collision resolution order
- [Source: epics.md#Story 1.6] — ACs

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List

### File List

### Change Log
- 2026-03-05: Story file created — implemented together with Story 1.5 in engine/player.py
