# Story 2.4: Player Visual Polish — Styled Square & In-Air Rotation

Status: review

## Story

As a player,
I want my character to look like the Geometry Dash cube with smooth rotation while airborne,
so that the game feels visually authentic.

## Acceptance Criteria

1. **Given** the player is rendered by `renderer/game_renderer.py` **When** the player sprite is drawn **Then** it consists of a red outer square (1×1 block, thin black border) and a smaller red inner square (centered, ~55% size, thin black border) ✅
2. **When** `player.state.on_ground` is `False` **Then** `player.state.angle` increases by `ROTATION_SPEED_DEG_PER_STEP` per physics step ✅
3. **And** the sprite is drawn rotated by `player.state.angle` degrees (clockwise, via `pygame.transform.rotate`) ✅
4. **When** `player.state.on_ground` is `True` **Then** `player.state.angle` snaps to 0° ✅
5. **And** the rotation logic lives in `engine/player.py` (pure, no pygame) ✅

## Tasks / Subtasks

- [x] Task 1 — `engine/physics.py`: constante `ROTATION_SPEED_DEG_PER_STEP = 1.875` (450°/s ÷ 240Hz)
- [x] Task 2 — `engine/player.py`: rotation après `_resolve_collision()`
  - [x] 2.1 Import `ROTATION_SPEED_DEG_PER_STEP`
  - [x] 2.2 Si `on_ground` → `angle = 0.0`; sinon → `angle = (angle + ROTATION_SPEED) % 360.0`
- [x] Task 3 — `renderer/game_renderer.py`: rendu joueur stylé
  - [x] 3.1 Surface `bs×bs` SRCALPHA
  - [x] 3.2 Carré extérieur rouge + bordure noire 2px
  - [x] 3.3 Carré intérieur rouge centré (55% de bs) + bordure noire 1px
  - [x] 3.4 `pygame.transform.rotate(sprite, -angle)` → blit centré
- [x] Task 4 — `tests/test_physics.py`: 4 tests headless
  - [x] 4.1 `test_rotation_constant_value` — valeur 1.875
  - [x] 4.2 `test_angle_increases_when_airborne` — 1 step in-air → angle == 1.875
  - [x] 4.3 `test_angle_snaps_to_zero_on_landing` — atterrissage → angle == 0.0
  - [x] 4.4 `test_angle_stays_zero_while_grounded` — plusieurs steps au sol → angle constant 0.0

## Dev Notes

### References
- [Source: epics.md#Story 2.4]
- `pygame.transform.rotate` is counter-clockwise → pass `-state.angle` for clockwise rotation
- `ROTATION_SPEED_DEG_PER_STEP = 450°/s ÷ 240Hz = 1.875°/step` (matches official GD cube spin)
- Sprite blit uses `get_rect(center=...)` to keep the rotated surface centered on the player block

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Completion Notes List
- `engine/physics.py`: ajout de `ROTATION_SPEED_DEG_PER_STEP = 1.875`
- `engine/player.py`: import de la constante + 5 lignes de logic rotation en fin de `update()`
- `renderer/game_renderer.py`: `_draw_player` entièrement réécrit — surface SRCALPHA, carré outer + inner, rotate + blit centré; ajout constantes `_PLAYER_BORDER_COLOR`, `_INNER_RATIO`, `_BORDER_OUTER`, `_BORDER_INNER`
- `tests/test_physics.py`: import `ROTATION_SPEED_DEG_PER_STEP` + 4 nouveaux tests

### File List
- `engine/physics.py`
- `engine/player.py`
- `renderer/game_renderer.py`
- `tests/test_physics.py`

### Change Log
- 2026-03-05: Story 2.4 implémentée — 111 tests passing (107 → 111, +4)
