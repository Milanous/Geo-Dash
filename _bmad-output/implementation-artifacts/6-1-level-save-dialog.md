# Story 6.1: Level Save Dialog — Custom Name & Confirmation

Status: done

## Story

As a level designer,
I want to save my level with a custom name and receive confirmation,
So that I can maintain a library of distinct named levels.

## Acceptance Criteria

1. **Given** the editor is open and the user presses `S` **When** no filename is set yet **Then** a text-input overlay appears asking for a level name
2. **When** the user types a name and confirms (Enter) **Then** the level is saved to `data/levels/{sanitise_name(name)}.json` via `save_level(path, world, name=level_name)`
3. **When** the user presses `ESC` in the dialog **Then** the save is cancelled and the editor is restored
4. **When** the level was already saved once (name known) **Then** pressing `S` saves directly without dialog, and a brief "Saved!" label flashes on screen (1.5 s)
5. **When** `Shift+S` is pressed **Then** the save-as dialog always appears (rename or overwrite)
6. **And** the name is sanitised (alphanumeric + dash/underscore only) before writing to filesystem
7. **And** `tests/test_level_io.py` covers name sanitisation
8. **When** `EditorScene(level_path=...)` loads an existing level **Then** `_level_name` is initialised from the JSON `"name"` field (no dialog on first `S`)
9. **And** if `data/levels/{name}.json` already exists, it is overwritten silently (no confirmation prompt)

## Cross-Story Dependencies

- **Story 6.2** (Level Library) will scan `data/levels/*.json` and read the `"name"` field from each file. The filename MUST match `{sanitise_name(name)}.json` and the JSON `"name"` field MUST contain the human-readable name passed by the user.
- **Story 6.4** will add `TileType.FINISH` to `_TYPE_TO_STR` / `_STR_TO_TYPE` in `level_io.py` — do NOT hardcode tile type sets.

## Tasks / Subtasks

- [x] Task 1 — `editor/level_io.py` : ajouter `sanitise_name` + helper `load_level_name`
  - [x] 1.1 `sanitise_name(raw: str) -> str` : spaces→`_`, strip non `[a-zA-Z0-9_-]`, truncate 64 chars, fallback `"untitled"` if empty (also if result is only dashes/underscores with no alphanumeric → `"untitled"`)
  - [x] 1.2 `load_level_name(path: str | Path) -> str` : reads JSON, returns `data["name"]` (lightweight — does NOT build a World). Used by `EditorScene.__init__` when loading existing level.
- [x] Task 2 — `ui/save_dialog.py` : overlay de saisie de nom
  - [x] 2.1 `SaveDialog` : overlay pygame semi-transparent (fond 50% opaque), champ de saisie de texte
  - [x] 2.2 `update(event) -> str | None | False` : retourne le nom saisi (str) sur Enter, `False` sur ESC, `None` si en cours
  - [x] 2.3 Affiche le texte courant dans le champ, curseur clignotant (toggle 0.5 s)
  - [x] 2.4 Backspace supprime le dernier caractère ; seuls `[a-zA-Z0-9 _-]` sont acceptés en frappe
  - [x] 2.5 `SaveDialog` ne doit pas importer depuis `ai/`
- [x] Task 3 — Intégration dans `ui/editor_scene.py`
  - [x] 3.1 Ajouter `self._level_name: str | None = None` et `self._save_flash: float = 0.0`
  - [x] 3.2 Si `level_path` fourni au constructeur : `self._level_name = load_level_name(level_path)` (récupérer le nom depuis le JSON)
  - [x] 3.3 `S` → si `_level_name` est None : ouvrir `SaveDialog` ; sinon : `save_level("data/levels/" + sanitise_name(self._level_name) + ".json", self._editor.world, name=self._level_name)` + flash 1.5 s
  - [x] 3.4 `Shift+S` → toujours ouvrir `SaveDialog`
  - [x] 3.5 Supprimer `_DEFAULT_SAVE_PATH` et `self._level_path` — remplacés par `_level_name` + chemin dynamique
  - [x] 3.6 Flash "Saved!" : dans `EditorScene.draw()`, APRÈS `self._renderer.draw(...)`, afficher le label via `pygame.font.Font(None, 24)` si `_save_flash > 0`
  - [x] 3.7 Décrémenter `_save_flash` dans `update(dt)`, pas dans `draw()`
- [x] Task 4 — `tests/test_level_io.py` : tests `sanitise_name` + `load_level_name`
  - [x] 4.1 Test : nom alphanumérique normal → inchangé (`"my_level"` → `"my_level"`)
  - [x] 4.2 Test : espaces → remplacés par `_` (`"Mon Niveau"` → `"Mon_Niveau"`)
  - [x] 4.3 Test : caractères spéciaux (`*`, `/`, `?`, `!`) → supprimés (`"Level!01?"` → `"Level01"`)
  - [x] 4.4 Test : nom vide `""` → `"untitled"`
  - [x] 4.5 Test : nom > 64 chars → tronqué à 64
  - [x] 4.6 Test : nom uniquement tirets/underscores `"---"` → `"untitled"` (pas de contenu alphanumérique)
  - [x] 4.7 Test : `load_level_name` retourne le champ `"name"` du JSON existant
- [x] Task 5 — Tests headless `ui/save_dialog.py`
  - [x] 5.1 Test : `SaveDialog` s'instancie sans display (guard)
  - [x] 5.2 Test : `update(KEYDOWN Enter)` avec texte saisi → retourne le nom (str)
  - [x] 5.3 Test : `update(KEYDOWN ESC)` → retourne `False`

## Dev Notes

### Architecture obligatoire

```
ui/save_dialog.py  →  peut importer pygame (ui/ peut importer tous sauf ai/simulation.py)
editor/level_io.py →  stdlib + engine/ seulement — ajouter sanitise_name + load_level_name ici
```

[Source: architecture.md#Règles d'import]

| Module | Peut importer | Ne peut PAS importer |
|---|---|---|
| `editor/` | `engine/`, `pygame` | `ai/`, `renderer/` |
| `ui/` | tous sauf `ai/simulation.py` | — |

### Sanitise — règle (définitive)

1. Remplacer les espaces par `_`
2. Supprimer tout caractère non `[a-zA-Z0-9_-]`
3. Tronquer à 64 caractères
4. Si le résultat est vide OU ne contient aucun caractère alphanumérique → `"untitled"`

Exemple : `"Mon Niveau! 01"` → `"Mon_Niveau_01"`
Exemple : `"---"` → `"untitled"`
Exemple : `""` → `"untitled"`

### Existing code to modify in `ui/editor_scene.py`

**Replace** `_DEFAULT_SAVE_PATH = "data/levels/current.json"` and `self._level_path` with dynamic path from `_level_name`.

**Replace** `_save_current_level()` method (currently line ~192):
```python
# CURRENT (Story 3.4):
def _save_current_level(self) -> None:
    try:
        save_level(self._level_path, self._editor.world)
    except OSError:
        pass

# NEW (Story 6.1): must pass name= param and use dynamic path
```

**When loading existing level** (constructor `level_path is not None` block ~line 60):
```python
# CURRENT:
if level_path is not None:
    world = load_level(level_path)
    ...

# ADD after load:
    self._level_name = load_level_name(level_path)
```

### `save_level()` — pass `name` parameter

`save_level(path, world, name="untitled")` stores `name` in JSON `"name"` field. Always pass `name=self._level_name` when saving — otherwise default `"untitled"` ends up in JSON, breaking Story 6.2 library scan.

### Flash "Saved!"

In `EditorScene.draw()`, AFTER `self._renderer.draw(...)`:
```python
if self._save_flash > 0:
    font = pygame.font.Font(None, 24)
    label = font.render("Saved!", True, (50, 220, 80))
    surface.blit(label, (surface.get_width() - label.get_width() - 10, 10))
```
Decrement `_save_flash` in `update(dt)` (NOT in `draw()`). Initial value: `1.5`.

### `SaveDialog` — headless guard

Tests instantiate `SaveDialog` without pygame display. `__init__` must NOT call `pygame.Surface` / `pygame.font` — initialise pygame resources lazily in a `draw()` or `open()` method, not in constructor.

### Overwrite behaviour

If `data/levels/{name}.json` already exists, `save_level()` overwrites silently. No confirmation prompt needed — this is intentional.

### References

- [Source: editor/level_io.py] `save_level(path, world, name)`, `load_level(path)` (Story 3.3)
- [Source: ui/editor_scene.py] `EditorScene`, `_save_current_level()`, `_DEFAULT_SAVE_PATH` (Story 3.4 — to replace)
- [Source: engine/world.py] `World`, `TileType`
- [Source: renderer/editor_renderer.py] `EditorRenderer.draw()` — called by `EditorScene.draw()`, renders grid/tiles/toolbar

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (GitHub Copilot)

### Debug Log References
- RED phase: import error confirmed for `sanitise_name`, `load_level_name` (not yet defined)
- RED phase: `ModuleNotFoundError: No module named 'ui.save_dialog'` confirmed
- GREEN phase: 20/20 level_io tests pass, 3/3 save_dialog tests pass
- Full regression: 199/199 tests pass (187 existing + 12 new)

### Completion Notes List
- `sanitise_name()`: spaces→`_`, regex strip `[^a-zA-Z0-9_-]`, max 64 chars, fallback "untitled" if empty or no alphanumeric
- `load_level_name()`: lightweight JSON read returning `data["name"]` without building World
- `SaveDialog`: headless-safe (no pygame in `__init__`), modal overlay with blinking cursor, Enter→name, ESC→False
- `EditorScene`: removed `_DEFAULT_SAVE_PATH` / `_level_path`, added `_level_name` + `_save_flash` + `_save_dialog`
- S key: dialog if first save, direct save+flash if name known; Shift+S: always dialog
- Loading existing level now reads `"name"` field from JSON via `load_level_name()`
- Flash "Saved!" rendered in top-right corner for 1.5s, decremented in `update(dt)`

### Change Log
- 2026-03-05: Story 6.1 implemented — save dialog, sanitise_name, load_level_name, flash confirmation (12 new tests, 199 total)
- 2026-03-05: Code Review fixes applied — fixed save cancel on empty string, prevented camera pan while dialog is open, optimized font creation, updated `_level_name` fallback.

### File List

- `editor/level_io.py` (modifié — `sanitise_name` + `load_level_name` + `import re`)
- `ui/save_dialog.py` (nouveau — `SaveDialog` class)
- `ui/editor_scene.py` (modifié — dialog + flash + suppression `_DEFAULT_SAVE_PATH` / `_level_path`)
- `tests/test_level_io.py` (modifié — 9 nouveaux tests sanitise_name + load_level_name)
- `tests/test_save_dialog.py` (nouveau — 3 tests headless SaveDialog)
