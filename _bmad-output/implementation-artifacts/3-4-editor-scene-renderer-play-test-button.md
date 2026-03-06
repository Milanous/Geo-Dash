# Story 3.4: Editor Scene, Renderer & Play-test Button

Status: review

## Story

As a level designer,
I want a complete editor interface with a play-test button,
So that I can immediately try the level I am building.

## Acceptance Criteria

1. **Given** `ui/editor_scene.py` and `renderer/editor_renderer.py` exist **When** the editor scene is active **Then** the grid, tiles, toolbar, and cursor highlight are drawn by `editor_renderer.py`
2. **And** a "Play-test" button is visible in the toolbar
3. **When** the play-test button is clicked (or `P` key pressed) **Then** the current editor `World` is passed to `PlayScene` and the play scene activates
4. **When** the player dies or `ESC` is pressed in play-test mode **Then** control returns to the editor scene with the same state
5. **And** the editor scene is reachable from the main menu

## Tasks / Subtasks

- [x] Task 1 — `renderer/editor_renderer.py` : rendu de l'éditeur
  - [x] 1.1 `EditorRenderer` class avec méthode `draw(surface, world, editor_camera, cursor_bx, cursor_by, selected_tile_type)`
  - [x] 1.2 Fond uni (couleur neutre, pas de gradient sky)
  - [x] 1.3 Grille : dessiner les lignes de grille pour toutes les cellules visibles (viewport calculé via `editor_camera`)
  - [x] 1.4 Tiles : SOLID en gris, SPIKE en orange — même palette que `game_renderer.py` (`_SOLID_COLOR`, `_SPIKE_COLOR`)
  - [x] 1.5 Highlight curseur : rect semi-transparent sur le bloc pointé par la souris
  - [x] 1.6 Toolbar : bande en bas (ou haut) avec boutons SOLID / SPIKE / Play-test — sélection active mise en évidence
  - [x] 1.7 Invalider `GameRenderer._tint_cache` si besoin via appel externe (note : le cache est propre à chaque instance `GameRenderer`)
- [x] Task 2 — `ui/editor_scene.py` : scene ABC + intégration événements
  - [x] 2.1 `EditorScene(Scene)` avec `__init__` : instancie `Editor()`, `EditorCamera()`, `EditorRenderer()`, charge un niveau si `level_path` fourni
  - [x] 2.2 `update(dt)` : appelle `editor_camera.step(dt, keys_dict)` — construit `keys_dict` depuis `pygame.key.get_pressed()`
  - [x] 2.3 `handle_event(event)` : clic gauche → `screen_to_world` → `editor.place_tile()` ; clic droit → `erase_tile()` ; bouton milieu drag → `pan_pixels()`; `P` ou clic Play-test → basculer en play-test
  - [x] 2.4 Play-test : passer `editor.world` à `PlayScene` ; capturer retour (mort ou ESC) → restaurer `EditorScene`
  - [x] 2.5 `draw(surface)` : appelle `editor_renderer.draw(...)` avec curseur actuel
  - [x] 2.6 Accessible depuis `main.py` / `MenuScene` (ajouter route si nécessaire)
- [x] Task 3 — `tests/test_editor_scene.py` : tests headless de la logique (pas du rendu)
  - [x] 3.1 Test : `EditorScene` s'instancie sans erreur (pas d'affichage)
  - [x] 3.2 Test : `editor_camera.screen_to_world` + `editor.place_tile` → tile correcte dans le world
  - [x] 3.3 Test : `erase_tile` via coordonnées écran → AIR

## Dev Notes

### Architecture obligatoire

**Import rules** [Source: architecture.md#Règles d'import] :
```
renderer/editor_renderer.py  →  peut importer engine/, pygame
ui/editor_scene.py           →  peut importer editor/, engine/, renderer/, pygame
```

### Intégration des modules Stories 3.1–3.3

```python
# ui/editor_scene.py
from editor.editor import Editor
from editor.editor_camera import EditorCamera
from editor.level_io import save_level, load_level
from renderer.editor_renderer import EditorRenderer
from ui.play_scene import PlayScene

class EditorScene(Scene):
    def __init__(self, level_path: str | None = None) -> None:
        self._editor = Editor()
        self._camera = EditorCamera()
        self._renderer = EditorRenderer()
        if level_path:
            world = load_level(level_path)
            self._editor = Editor.__new__(Editor)
            self._editor._world = world
            self._editor._selected = TileType.SOLID
```

### Conversion événements souris → monde

```python
# Dans handle_event
mx, my = pygame.mouse.get_pos()
screen_h = surface.get_height()
bx, by = self._camera.screen_to_world(mx, my, screen_h)
```

### Play-test — pattern de basculement de scène

L'architecture BMAD utilise un pattern `Scene` avec `Scene.next_scene` ou un SceneManager. Adapter selon le pattern déjà établi dans `main.py` et `ui/play_scene.py`.

### Toolbar — coordonnées fixes (pixels)

La toolbar est dessinée en coordonnées écran fixes (overlay), pas en coordonnées monde. Elle ne scrolle pas avec la caméra.

### Palette cohérente avec `game_renderer.py`

Réutiliser les mêmes constantes de couleur :
- `_SOLID_COLOR = (160, 160, 160)`
- `_SPIKE_COLOR = (255, 110, 40)`
- Grille : lignes fines gris sombre `(50, 50, 50)`
- Fond éditeur : `(30, 30, 30)` (neutre, différent du sky gradient)

### `GameRenderer._tint_cache`

Si le joueur en play-test puis retour éditeur entraîne une nouvelle `GameRenderer`, le cache est recréé vide — pas de problème. Si `GameRenderer` est partagée, vider le cache sur retour éditeur. Dans tous les cas, **ne pas modifier `game_renderer.py`** dans cette story.

### Structure physique

```
renderer/
    game_renderer.py   ✅
    vfx.py             ✅
    editor_renderer.py ← À CRÉER
ui/
    play_scene.py      ✅
    editor_scene.py    ← À CRÉER
tests/
    test_editor_scene.py ← À CRÉER (logique headless uniquement)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Catégorie 1 — Pattern Scene]
- [Source: editor/editor.py] interface Editor (Story 3.1)
- [Source: editor/editor_camera.py] interface EditorCamera (Story 3.2)
- [Source: editor/level_io.py] interface level_io (Story 3.3)
- [Source: renderer/game_renderer.py] palette couleurs à réutiliser
- [Source: ui/play_scene.py] pattern Scene à suivre

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Debug Log References

Aucun blocage.

### Completion Notes List

- Task 1 : `renderer/editor_renderer.py` créé — `EditorRenderer.draw()` : fond (30,30,30), tiles SOLID/SPIKE avec même palette game_renderer, lignes de grille (50,50,50), highlight curseur SRCALPHA, toolbar 40px avec boutons SOLID/SPIKE/PLAY.
- Task 2 : `ui/editor_scene.py` créé — clic gauche/droit placement/érasure, drag milieu pan, touche P → `PlayScene(world=..., return_scene=self)` via pattern `next_scene`. `ui/scene.py` + `ui/play_scene.py` + `main.py` mis à jour.
- Task 3 : `tests/test_editor_scene.py` créé — 9 tests. Suite complète : 187 tests, 0 régression.

### File List

- `renderer/editor_renderer.py` (nouveau)
- `ui/editor_scene.py` (nouveau)
- `tests/test_editor_scene.py` (nouveau)
- `ui/scene.py` (modifié — ajout `next_scene` via `__init__`)
- `ui/play_scene.py` (modifié — params `world`, `return_scene`, gestion ESC/mort play-test)
- `main.py` (modifié — démarre avec EditorScene, support scene switching)

### Change Log

- 2026-03-05 : Story 3.4 implémentée — EditorRenderer + EditorScene + play-test (9 tests). Total suite : 187 tests.
