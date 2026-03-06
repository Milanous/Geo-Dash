# Story 3.3: Level Save & Load (JSON)

Status: review

## Story

As a level designer,
I want to save my level to disk and reload it,
So that my work persists between sessions.

## Acceptance Criteria

1. **Given** `editor/level_io.py` exists with `save_level(path, world)` and `load_level(path) -> World` **When** `save_level("data/levels/my_level.json", world)` is called **Then** a JSON file is written matching the schema `{"version": 1, "name": "...", "tiles": [{"x": int, "y": int, "type": "solid"|"spike"}]}`
2. **And** only non-AIR tiles are written (AIR is implicit)
3. **When** `load_level("data/levels/my_level.json")` is called **Then** it returns a `World` with tiles at the correct positions
4. **And** a round-trip (save then load) produces an identical `World`
5. **And** `tests/test_world.py` includes a round-trip test for save/load *(ajouter dans `test_world.py` ou `test_level_io.py` — voir dev notes)*
6. **And** `level_io.py` does not import `pygame`

## Tasks / Subtasks

- [x] Task 1 — `editor/level_io.py` : fonctions `save_level` / `load_level`
  - [x] 1.1 `save_level(path: str | Path, world: World, name: str = "untitled") -> None`
    - Sérialise uniquement les tiles non-AIR dans la liste `"tiles"`
    - Schéma obligatoire : `{"version": 1, "name": str, "width": int, "height": int, "tiles": [{"x": int, "y": int, "type": "solid"|"spike"}]}`
    - Inclure `"width"` et `"height"` pour reconstruire le `World` exact à l'identique
    - Crée les répertoires parents si nécessaires (`Path(path).parent.mkdir(parents=True, exist_ok=True)`)
    - Écriture atomique via `json.dumps` + `write_text` (ou équivalent)
  - [x] 1.2 `load_level(path: str | Path) -> World`
    - Lit et parse le JSON
    - Crée `World(width, height)` depuis les champs `"width"` et `"height"`
    - Itère sur `"tiles"` et appelle `world.set_tile(x, y, TileType.SOLID|SPIKE)`
    - Lève `ValueError` si `"version"` != 1
    - Lève `FileNotFoundError` naturellement si le fichier est absent
  - [x] 1.3 ZERO import `pygame` dans `editor/level_io.py`
- [x] Task 2 — `tests/test_level_io.py` : tests headless (fichiers temporaires via `tmp_path`)
  - [x] 2.1 Test : `save_level` crée un fichier JSON valide
  - [x] 2.2 Test : JSON contient `version=1`, `width`, `height`, `name`, `tiles`
  - [x] 2.3 Test : seuls les tiles non-AIR sont écrits
  - [x] 2.4 Test : `load_level` retourne un `World` avec les tiles aux bonnes positions
  - [x] 2.5 Test : round-trip — `save_level` puis `load_level` → `World` identique (même dimensions, mêmes tiles)
  - [x] 2.6 Test : world vide (tout AIR) → `"tiles": []`
  - [x] 2.7 Test : `load_level` sur un fichier `version=2` lève `ValueError`
  - [x] 2.8 Test : `load_level` sur fichier absent lève `FileNotFoundError`
  - [x] 2.9 Test : import guard — `level_io.py` n'importe pas `pygame`
  - [x] 2.10 Test : `save_level` crée les répertoires parents si absents

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
editor/  →  peut importer engine/, stdlib
editor/  →  ne peut PAS importer renderer/, ai/, pygame
```
`level_io.py` est fichier pur stdlib + `engine/world.py`. Aucun import pygame.

### Interface attendue

```python
# editor/level_io.py
from __future__ import annotations
import json
from pathlib import Path
from engine.world import TileType, World

def save_level(path: str | Path, world: World, name: str = "untitled") -> None: ...
def load_level(path: str | Path) -> World: ...
```

### Schéma JSON — format exact

```json
{
  "version": 1,
  "name": "my_level",
  "width": 100,
  "height": 20,
  "tiles": [
    {"x": 3, "y": 0, "type": "solid"},
    {"x": 7, "y": 2, "type": "spike"}
  ]
}
```

- `"version": 1` — obligatoire, entier
- `"width"` / `"height"` — dimensions du `World` (nécessaires pour reconstruire les bounds exactes)
- `"tiles"` — seulement les non-AIR ; les AIR sont **implicites**
- `"type"` — valeurs autorisées : `"solid"` et `"spike"` (lowercase strings) — jamais les noms d'enum Python
- Coordonnées `x`, `y` — entiers (indices grille), cohérents avec `World._grid[y][x]`

[Source: architecture.md#Format Patterns] — champs en `snake_case`, `"version": 1` obligatoire, coordonnées en blocs.

### Mapping TileType ↔ chaîne JSON

```python
_TYPE_TO_STR = {TileType.SOLID: "solid", TileType.SPIKE: "spike"}
_STR_TO_TYPE = {"solid": TileType.SOLID, "spike": TileType.SPIKE}
```

Ne jamais utiliser `.name.lower()` directement — les valeurs JSON sont un contrat de format indépendant des noms Python.

### Pourquoi `width` et `height` dans le JSON

Sans ces champs, `load_level` ne peut pas reconstruire un `World` identique si les dimensions ne sont pas inférées. Un fichier avec seulement des tiles en `x<50` ne permettrait pas de savoir si `width=50` ou `width=100`. Le round-trip doit être parfait.

### `tmp_path` — fixture pytest

Utiliser la fixture `tmp_path: Path` (pytest builtin) pour les tests de fichiers :
```python
def test_save_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    w = World(10, 5)
    save_level(path, w)
    assert path.exists()
```
Pas de fichiers dans `data/levels/` lors des tests — tout dans le répertoire temporaire.

### Round-trip — critère d'égalité

`World` ne surcharge pas `__eq__`. Pour vérifier l'identité après round-trip :
```python
def worlds_equal(w1: World, w2: World) -> bool:
    if w1.width != w2.width or w1.height != w2.height:
        return False
    for y in range(w1.height):
        for x in range(w1.width):
            if w1.tile_at(x, y) != w2.tile_at(x, y):
                return False
    return True
```
Utiliser cette fonction helper dans `test_level_io.py`.

### Chemin `data/levels/`

`save_level` doit créer les répertoires parents automatiquement. Cela permet de sauvegarder dans `data/levels/mon_niveau.json` même si `data/levels/` n'existe pas encore. Utiliser `Path(path).parent.mkdir(parents=True, exist_ok=True)`.

### Structure physique

```
editor/
    __init__.py
    editor.py              ← Story 3.1 ✅
    editor_camera.py       ← Story 3.2 ✅
    level_io.py            ← À CRÉER dans cette story
tests/
    test_editor.py         ← Story 3.1 ✅
    test_editor_camera.py  ← Story 3.2 ✅
    test_level_io.py       ← À CRÉER dans cette story
data/
    levels/                ← répertoire existant (à créer si absent)
```

### Intelligence stories précédentes

- Import guard pattern (Stories 3.1/3.2) : `re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE)`
- Tests courts, nommage `test_<sujet>_<condition>`, fixture `tmp_path` de pytest (builtin, pas d'import supplémentaire)
- `World.set_tile()` et `World.tile_at()` gèrent les bounds silencieusement — pas de guard supplémentaire dans `level_io.py` pour les coordonnées en bounds (les tiles sauvegardés proviennent toujours du même World)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Règles d'import]
- [Source: engine/world.py] API World (TileType, set_tile, tile_at, width, height)
- [Source: _bmad-output/implementation-artifacts/3-1-level-editor-core-grid-display-tile-placement.md] Leçons 3.1
- [Source: _bmad-output/implementation-artifacts/3-2-editor-camera-pan.md] Leçons 3.2

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (GitHub Copilot — Amelia)

### Debug Log References

Aucun blocage — implémentation directe.

### Completion Notes List

- Task 1 : `editor/level_io.py` créé — `save_level` sérialise uniquement les tiles non-AIR avec schéma `{version, name, width, height, tiles}` ; `load_level` reconstruit le World exact, lève ValueError si version≠1 et FileNotFoundError si fichier absent. Mapping explicite `_TYPE_TO_STR` / `_STR_TO_TYPE` indépendant des noms d'enum Python.
- Task 2 : `tests/test_level_io.py` créé — 11 tests (10 AC + 1 extra lowercase) ; tous passent. Suite complète : 178 tests, 0 régression.

### File List

- `editor/level_io.py` (nouveau)
- `tests/test_level_io.py` (nouveau)

### Change Log

- 2026-03-05 : Story 3.3 implémentée — `editor/level_io.py` + `tests/test_level_io.py` (11 tests). Total suite : 178 tests.
