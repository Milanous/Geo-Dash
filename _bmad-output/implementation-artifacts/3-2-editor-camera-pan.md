# Story 3.2: Editor Camera Pan

Status: review

## Story

As a level designer,
I want to pan the editor camera so I can work on any part of the level,
So that I am not limited to a fixed viewport.

## Acceptance Criteria

1. **Given** the editor scene is active **When** the user holds the middle mouse button and drags **Then** the camera pans in the corresponding direction *(event wiring in Story 3.4 — cette story livre la logique pan)*
2. **When** the user presses arrow keys **Then** the camera moves at a fixed pan speed (5 blocks/s) *(key event wiring en Story 3.4)*
3. **And** the camera offset is applied when converting screen coordinates to grid coordinates for tile placement → `EditorCamera.screen_to_world(sx, sy) -> (bx, by)`
4. **And** the camera cannot scroll to negative world coordinates (clamp à 0 en X et Y)

## Tasks / Subtasks

- [x] Task 1 — `editor/editor_camera.py` : class `EditorCamera`
  - [x] 1.1 `__init__(self, pan_speed: float = 5.0)` — `self.x_offset: float = 0.0`, `self.y_offset: float = 0.0` (en blocs), `self._pan_speed = pan_speed`
  - [x] 1.2 `pan_pixels(self, dx_px: int, dy_px: int) -> None` — convertit les pixels en blocs et déplace l'offset ; clamp à `>= 0.0`
  - [x] 1.3 `pan_blocks(self, dx_blk: float, dy_blk: float) -> None` — déplace l'offset directement en blocs ; clamp à `>= 0.0`
  - [x] 1.4 `screen_to_world(self, sx: int, sy: int, screen_h: int) -> tuple[float, float]` — convertit coordonnées écran (pixels) en coordonnées monde (blocs) en tenant compte de `x_offset`, `y_offset`, et du flip Y (Y écran = 0 en haut, Y monde = 0 en bas)
  - [x] 1.5 `step(self, dt: float, keys: dict[str, bool]) -> None` — avance le pan clavier : si `left` → `pan_blocks(-pan_speed * dt, 0)`, `right` → `+x`, `up` → `+y`, `down` → `-y`
  - [x] 1.6 Confirmer que ZERO import `pygame` dans `editor/editor_camera.py` (les keycodes sont passés en `dict[str, bool]`, pas d'import pygame direct)
- [x] Task 2 — `tests/test_editor_camera.py` : tests headless
  - [x] 2.1 Test : offset initial est `(0.0, 0.0)`
  - [x] 2.2 Test : `pan_pixels(30, 0)` déplace `x_offset` de 1 bloc (BLOCK_SIZE_PX=30)
  - [x] 2.3 Test : `pan_pixels(-999, 0)` ne descend pas sous 0 (clamp X)
  - [x] 2.4 Test : `pan_pixels(0, -999)` ne descend pas sous 0 (clamp Y)
  - [x] 2.5 Test : `pan_blocks(5.0, 2.0)` met `x_offset=5.0`, `y_offset=2.0`
  - [x] 2.6 Test : `screen_to_world(0, 0, screen_h=600)` avec offset nul → coin haut-gauche correct
  - [x] 2.7 Test : `screen_to_world` prend en compte `x_offset` et `y_offset`
  - [x] 2.8 Test : `step(dt=1.0, keys={"right": True})` déplace `x_offset` de `pan_speed * 1.0` blocs
  - [x] 2.9 Test : `step` avec aucune touche active → offset inchangé
  - [x] 2.10 Test : import guard — `editor_camera.py` n'importe pas `pygame`

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
editor/  →  peut importer engine/, stdlib
editor/  →  ne peut PAS importer renderer/, ai/, pygame
```
`EditorCamera` est un module de logique pure. Le mapping événements souris/clavier → appels `pan_pixels` / `step` vivra dans `ui/editor_scene.py` (Story 3.4).

### Interface attendue

```python
# editor/editor_camera.py
from __future__ import annotations
from engine.physics import BLOCK_SIZE_PX

PAN_SPEED_DEFAULT: float = 5.0  # blocks/second

class EditorCamera:
    x_offset: float  # blocks, always >= 0
    y_offset: float  # blocks, always >= 0

    def __init__(self, pan_speed: float = PAN_SPEED_DEFAULT) -> None: ...
    def pan_pixels(self, dx_px: int, dy_px: int) -> None: ...
    def pan_blocks(self, dx_blk: float, dy_blk: float) -> None: ...
    def screen_to_world(self, sx: int, sy: int, screen_h: int) -> tuple[float, float]: ...
    def step(self, dt: float, keys: dict[str, bool]) -> None: ...
```

### Coordonnées — convention projet

[Source: architecture.md#Naming Patterns]
- **Y monde** = 0 en bas, positif vers le haut (même convention que le moteur de jeu)
- **Y écran** = 0 en haut, positif vers le bas (convention pygame)
- Conversion `screen_to_world` :
  ```
  bx = sx / BLOCK_SIZE_PX + x_offset
  by = (screen_h - sy) / BLOCK_SIZE_PX + y_offset
  ```
  *(identique au rendu `game_renderer.py` : `sy = screen_h - (row+1)*bs`)*

### `step()` — keys dict

La touche `step()` reçoit un dict `{"left": bool, "right": bool, "up": bool, "down": bool}`. Cela permet les tests headless sans importer `pygame.key`. L'`EditorScene` (Story 3.4) sera responsable de construire ce dict à partir de `pygame.key.get_pressed()`.

Convention directions :
| Touche | Effet |
|---|---|
| `"right"` | `x_offset += pan_speed * dt` |
| `"left"` | `x_offset -= pan_speed * dt` (clamp ≥ 0) |
| `"up"` | `y_offset += pan_speed * dt` |
| `"down"` | `y_offset -= pan_speed * dt` (clamp ≥ 0) |

### Relation avec `engine/camera.py`

`engine/camera.py` est la caméra **play scene** (1D, suit le joueur en X uniquement). **Ne pas modifier `engine/camera.py`**. L'`EditorCamera` est une classe indépendante dans `editor/` qui gère la 2D (X + Y) et le pan manuel. Les deux classes sont distinctes et sans couplage.

### Relation avec `Editor` (Story 3.1)

`EditorCamera` est indépendante de `Editor`. Les deux sont instanciées séparément par `EditorScene` (Story 3.4) et composées là :
```python
# ui/editor_scene.py (Story 3.4)
self._editor = Editor()
self._editor_camera = EditorCamera()
# clic souris → screen_to_world → editor.place_tile / erase_tile
```

### `BLOCK_SIZE_PX`

Importé de `engine.physics` (valeur = 30 px). Utiliser cette constante dans `screen_to_world` et `pan_pixels`.

### Structure physique

```
editor/
    __init__.py
    editor.py              ← Story 3.1 (existant)
    editor_camera.py       ← À CRÉER dans cette story
tests/
    test_editor.py         ← Story 3.1 (existant)
    test_editor_camera.py  ← À CRÉER dans cette story
```

### Intelligence Story 3.1

- Pattern import guard : `re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE)` — éviter la correspondance dans les docstrings (bug découvert en 3.1)
- `World.set_tile()` gère les bounds silencieusement → même pattern : `EditorCamera` clamp l'offset sans crash
- Tests courts et explicites, nommage `test_<sujet>_<condition>`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Règles d'import]
- [Source: engine/camera.py] API Camera (jeu, référence pattern)
- [Source: engine/physics.py] `BLOCK_SIZE_PX = 30`
- [Source: engine/world.py] Convention coordonnées Y
- [Source: _bmad-output/implementation-artifacts/3-1-level-editor-core-grid-display-tile-placement.md] Leçons Story 3.1

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Debug Log References

Aucun bug rencontré. Implémentation propre au premier essai.

### Completion Notes List

- `pan_pixels(dx, dy)` : `dy_px > 0` = drag vers le bas = contenu monde monte → `y_offset` diminue (flip Y). Documenté explicitement dans la docstring.
- 20 tests créés (vs 10 prévus) — tests supplémentaires pour robustesse : drag up, combinaisons x+y offset, step up/down, all-false keys.
- `keys.get("right")` avec dict vide ne crash pas (`.get()` retourne `None` = falsy).
- 167 tests passing (147 → 167, +20).

### File List

- `editor/editor_camera.py` (nouveau)
- `tests/test_editor_camera.py` (nouveau)
