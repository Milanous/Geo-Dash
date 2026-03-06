# Story 3.1: Level Editor Core — Grid Display & Tile Placement

Status: review

## Story

As a level designer,
I want to click on a grid to place and remove tiles,
So that I can build a custom level interactively.

## Acceptance Criteria

1. **Given** `editor/editor.py` exists with an `Editor` class wrapping a `World` **When** the editor is active **Then** the grid is displayed with tile outlines visible *(display verified in Story 3.4 — this story delivers the logic layer)*
2. **And** a toolbar shows at least two tile type buttons: `SOLID` and `SPIKE` *(toolbar state managed by `Editor.selected_tile_type` — rendering in Story 3.4)*
3. **And** left-click on a grid cell places the currently selected tile type *(event → `Editor.place_tile(bx, by)`, event wiring in Story 3.4)*
4. **And** right-click on a grid cell sets the cell to `TileType.AIR` (erase) → `Editor.erase_tile(bx, by)`
5. **And** the tile type selector updates on toolbar button click → `Editor.set_selected_tile_type(tile_type)`
6. **And** `editor/editor.py` does **not** import `pygame` (event handling lives in `ui/editor_scene.py`)

## Tasks / Subtasks

- [x] Task 1 — `editor/editor.py` : class `Editor`
  - [x] 1.1 `__init__(self, width: int = 100, height: int = 20)` — crée `self._world = World(width, height)` et `self._selected: TileType = TileType.SOLID`
  - [x] 1.2 Propriété `world` → retourne `self._world` (lecture seule via property)
  - [x] 1.3 Propriété `selected_tile_type` → retourne `self._selected`
  - [x] 1.4 `set_selected_tile_type(tile_type: TileType) -> None` — met à jour `self._selected` (valider que c'est pas `AIR`)
  - [x] 1.5 `place_tile(bx: float, by: float) -> None` — appelle `self._world.set_tile(bx, by, self._selected)` (bounds guard : ignorer si hors limites)
  - [x] 1.6 `erase_tile(bx: float, by: float) -> None` — appelle `self._world.set_tile(bx, by, TileType.AIR)` (bounds guard)
  - [x] 1.7 Confirmer que ZERO import `pygame` dans `editor/editor.py`
- [x] Task 2 — `tests/test_editor.py` : tests headless
  - [x] 2.1 Test : `Editor` initialise un `World` vide (tout `AIR` au départ)
  - [x] 2.2 Test : `place_tile()` pose `selected_tile_type` à la bonne position
  - [x] 2.3 Test : `erase_tile()` remet `AIR` à la position
  - [x] 2.4 Test : `set_selected_tile_type(TileType.SPIKE)` change la sélection
  - [x] 2.5 Test : `place_tile()` hors-limites ne crash pas
  - [x] 2.6 Test : `set_selected_tile_type(TileType.AIR)` doit être refusé (ValueError ou ignore — doc le choix)
  - [x] 2.7 Test : `editor/editor.py` n'importe pas `pygame` (import guard)
  - [x] 2.8 Test : `place_tile()` default SOLID (sélection initiale)
  - [x] 2.9 Test : round-trip place→erase remet `AIR`

## Dev Notes

### Architecture obligatoire

**Import rule for `editor/`** [Source: architecture.md#Règles d'import] :
```
editor/  →  peut importer engine/, stdlib
editor/  →  ne peut PAS importer renderer/, ai/, pygame
```
`editor/editor.py` est un module de logique pure — ZERO `import pygame`.  
Le mapping événements souris → coordonnées bloc est fait dans `ui/editor_scene.py` (Story 3.4).

### Classe `Editor` — interface attendue

```python
# editor/editor.py
from __future__ import annotations
from engine.world import TileType, World

class Editor:
    def __init__(self, width: int = 100, height: int = 20) -> None: ...
    @property
    def world(self) -> World: ...
    @property
    def selected_tile_type(self) -> TileType: ...
    def set_selected_tile_type(self, tile_type: TileType) -> None: ...
    def place_tile(self, bx: float, by: float) -> None: ...
    def erase_tile(self, bx: float, by: float) -> None: ...
```

### World — API disponible [Source: engine/world.py]

```python
World(width: int, height: int)           # constructeur
world.tile_at(bx: float, by: float)      # -> TileType (hors limites → AIR, sans crash)
world.set_tile(bx: float, by: float, t)  # -> None
world.width, world.height                # int
World.to_px(bloc: float) -> int          # conversion (non utilisé dans editor.py)
World.to_bloc(px) -> float
```

**`set_tile()` hors-limites** : vérifier le comportement actuel de `World.set_tile()` avant l'implémentation. S'il ne guarde pas déjà les bounds → ajouter un guard dans `Editor.place_tile()` / `Editor.erase_tile()` pour éviter `IndexError`.

### Dimensions par défaut

- `width=100` blocs × `height=20` blocs : taille cohérente avec les niveaux GD classiques
- `BLOCK_SIZE_PX=30` px → viewport = 100×30 = 3 000 px de large (scroll nécessaire → Story 3.2)

### TileType.AIR comme sélection

`set_selected_tile_type(TileType.AIR)` **ne doit pas être autorisé** — l'effet "effacer" passe par `erase_tile()`, pas par la sélection. Choisir `ValueError` ou ignorer silencieusement ; documenter dans la docstring.

### Patterns de test établis dans le projet

Référence : `tests/test_world.py` (Story 1.3)
```python
from engine.world import TileType, World
# Headless — jamais import pygame
# Pas de fixture complexe, tests courts et explicites
# Nommage : test_<ce_qui_est_testé>_<condition>
```

Test import guard (pattern utilisé dans Stories 2.3/2.5) :
```python
def test_editor_does_not_import_pygame() -> None:
    import importlib, sys
    # Retirer le module du cache s'il y est
    sys.modules.pop("editor.editor", None)
    import editor.editor as mod
    assert "pygame" not in sys.modules or "editor.editor" not in repr(sys.modules.get("pygame", ""))
    # Alternative simple : inspecter le source
    import inspect
    src = inspect.getsource(mod)
    assert "import pygame" not in src
```

### Limitations de scope de cette story

| Responsabilité | Story |
|---|---|
| `Editor` logique (place/erase/select) | **3.1 (cette story)** |
| Camera pan + screen→bloc conversion | 3.2 |
| Save/Load JSON | 3.3 |
| `ui/editor_scene.py`, `renderer/editor_renderer.py`, toolbar rendu, play-test | 3.4 |

**Ne pas créer** `ui/editor_scene.py` ni `renderer/editor_renderer.py` dans cette story.

### Contexte précédent (Story 2.6 → 3.1)

Les dernières stories ont établi ces patterns :
- **Séparation logique/rendu** : `engine/player.py` sans pygame, événements dans `ui/play_scene.py` → même pattern pour `editor/editor.py` vs `ui/editor_scene.py`
- **Tests headless** : `tests/test_vfx.py`, `tests/test_renderer.py` montrent comment tester sans display pygame
- **Import guard tests** : vérification dans `tests/test_vfx.py` que `renderer/vfx.py` n'importe pas `engine.player`
- **VFX tint cache** : `GameRenderer._tint_cache` devra être invalidé si `world.set_tile()` est appelé — **signaler à Amelia** mais ne pas implémenter dans cette story (Story 3.4 scope)

### Structure physique actuelle

```
editor/
    __init__.py       ← existe déjà (vide ou minimal)
    editor.py         ← À CRÉER dans cette story
tests/
    test_editor.py    ← À CRÉER dans cette story
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Règles d'import]
- [Source: _bmad-output/planning-artifacts/architecture.md#Mapping FRs → Fichiers] FR-P1-03
- [Source: _bmad-output/planning-artifacts/architecture.md#Flux éditeur]
- [Source: engine/world.py] API World
- [Source: tests/test_world.py] Patterns de test headless

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Debug Log References

- Test `test_editor_does_not_import_pygame` : première version trop large (matchait le substring dans la docstring). Corrigée avec `re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE)` pour cibler uniquement les véritables instructions d'import.

### Completion Notes List

- `World.set_tile()` gère déjà les bounds silencieusement → pas de double guard nécessaire dans `Editor`. Les bounds guards dans `place_tile()`/`erase_tile()` sont délégués à `World`.
- `set_selected_tile_type(TileType.AIR)` lève `ValueError` avec message explicite.
- 15 tests créés (vs 9 prévus) — tests supplémentaires pour la robustesse (SPIKE round-trip, sélection retour SOLID, erase hors-limites, etc.).
- 147 tests passing (132 → 147, +15).

### File List

- `editor/editor.py` (nouveau)
- `tests/test_editor.py` (nouveau)
