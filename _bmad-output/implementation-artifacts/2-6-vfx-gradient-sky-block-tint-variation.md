# Story 2.6: VFX — Gradient Sky & Block Tint Variation

Status: review

## Story

As a player,
I want the sky to show a vertical colour gradient and blocks to have subtle colour variation,
so that the level has visual depth and atmosphere.

## Acceptance Criteria

1. **Given** the game renderer draws the play scene **When** the background is drawn **Then** it shows a vertical gradient from `_SKY_TOP=(8,8,38)` (dark blue) to `_SKY_BOTTOM=(42,42,88)` (lighter blue) ✅
2. **And** the gradient is drawn using a series of horizontal lines ✅
3. **When** solid and spike tiles are drawn **Then** each tile has a unique, deterministic lightness offset seeded by `(col, row)` in the range ±10% ✅
4. **And** tint offsets are computed once (lazy cache) and never recalculated every frame ✅
5. **And** tile tints do not affect collision logic in `engine/world.py` ✅

## Tasks / Subtasks

- [x] Task 1 — `renderer/game_renderer.py` : constantes ciel + `_compute_tint()`
  - [x] 1.1 Supprimer `_BG_COLOR`; ajouter `_SKY_TOP=(8,8,38)` et `_SKY_BOTTOM=(42,42,88)`
  - [x] 1.2 `_compute_tint(base_color, col, row)` — fonction pure, hash Knuth multiplicatif, offset [-0.10, +0.10]
- [x] Task 2 — `GameRenderer` devient stateful (cache tint)
  - [x] 2.1 `__init__`: `self._tint_cache: dict[tuple[int,int], tuple[int,int,int]] = {}`
  - [x] 2.2 `draw()`: replace `surface.fill` par `self._draw_sky(surface)`
  - [x] 2.3 `_draw_sky(surface)`: boucle `screen_h` horizontal lines interpolées
  - [x] 2.4 `_draw_tiles()`: lookup lazy cache pour SOLID et SPIKE avant `pygame.draw.*`
- [x] Task 3 — `tests/test_renderer.py` : 9 tests headless sur `_compute_tint`
  - [x] 3.1 Déterminisme : même (col, row) → même couleur
  - [x] 3.2 Positions adjacentes → couleurs distinctes
  - [x] 3.3 Indépendance de l'ordre d'appel
  - [x] 3.4 Canaux SOLID dans [0, 255]
  - [x] 3.5 Canaux SPIKE dans [0, 255]
  - [x] 3.6 Offset ≤ 10% pour SOLID
  - [x] 3.7 Retourne un tuple de 3 ints
  - [x] 3.8 Grandes coordonnées → pas de overflow
  - [x] 3.9 Coordonnées négatives → pas de crash

## Dev Notes

### Design decisions
- **`_compute_tint` est une fonction pure module-level**, exportable et testable headless sans pygame.
- **Hash Knuth multiplicatif** : `(col * 2_654_435_761 ^ row * 22_695_477) & 0xFFFFFFFF` — pas de `random`, résultat stable cross-session.
- **Gradient dessiné ligne par ligne** (`pygame.draw.line` × screen_h). Sur un écran 600px, ~600 appels/frame. Optimisation possible avec numpy/Surface si besoin, mais négligeable à 60 FPS.
- **Cache lazy** : populé à la première rencontre de chaque tile. Compatible avec la modification dynamique de tuiles (éditeur Epic 3) — il suffira d'effacer le cache sur `set_tile`.

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Completion Notes List
- `_BG_COLOR` supprimé, remplacé par `_SKY_TOP` / `_SKY_BOTTOM`
- `_compute_tint()` ajoutée comme fonction module-level (pure, ~12 lignes)
- `GameRenderer` : `__init__` ajouté avec `_tint_cache`; `_draw_sky()` ajoutée; `_draw_tiles()` utilise le cache
- `tests/test_renderer.py` créé — 9 tests headless tous passants

### File List
- `renderer/game_renderer.py`
- `tests/test_renderer.py` (nouveau)

### Change Log
- 2026-03-05: Story 2.6 implémentée — 132 tests passing (123 → 132, +9). Epic 2 complète.
