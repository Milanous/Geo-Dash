# Story 6.3: Level Select Scene — Play, Edit & Train AI

Status: dev-complete

## Story

As a player,
I want a level selection screen as the main entry point,
So that I can choose a level to play, edit or train the AI on.

## Acceptance Criteria

1. **Given** the game launches **When** `main.py` starts **Then** `LevelSelectScene` is displayed (not `EditorScene` directly)
2. **And** the scene lists all levels found in `data/levels/` via `LevelLibrary.scan()`
3. **When** zero levels exist **Then** only a "New Level" option is shown
4. **When** a level is selected and "Play" is pressed **Then** the level is loaded and `PlayScene(world=..., return_scene=level_select)` activates
5. **When** a level is selected and "Edit" is pressed **Then** `EditorScene(level_path=...)` activates
6. **When** a level is selected and "Train AI" is pressed **Then** `AITrainScene(world=..., level_name=...)` activates
7. **When** "New Level" is pressed **Then** `EditorScene()` (empty) activates
8. **And** keyboard navigation: `↑`/`↓` selects entries, `Enter` → Play, `E` → Edit, `T` → Train AI, `N` → New Level, `DEL` → delete selected with confirmation
9. **And** returning from Play / Edit / TrainAI re-opens `LevelSelectScene` (via `return_scene` / `next_scene`)

## Tasks / Subtasks

- [x] Task 1 — `ui/level_select_scene.py` : scene de sélection
  - [x] 1.1 `LevelSelectScene(Scene)` avec `__init__` : appelle `LevelLibrary.scan()`, stocke `self._entries`, `self._selected_idx = 0`
  - [x] 1.2 `handle_events()` :
    - `↑` / `↓` : déplacer `_selected_idx` (clamp entre 0 et len-1)
    - `Enter` : Play avec niveau sélectionné
    - `E` : Edit avec niveau sélectionné
    - `T` : Train AI avec niveau sélectionné
    - `N` : New Level (EditorScene vide)
    - `DEL` : `LevelLibrary.delete(entry)` + `scan()` + ajuster index
    - `ESC` : quitter l'application (retour False)
  - [x] 1.3 `update(dt)` : vérifier `next_scene` revenu de Play/Edit — rescanner si retour d'Edit (niveau potentiellement modifié)
  - [x] 1.4 `draw(surface)` : fond dark, liste centrée, entrée sélectionnée en surbrillance, instructions clavier en bas
  - [x] 1.5 `_load_and_play(entry)` : `load_level(entry.path)` → `PlayScene(world=..., return_scene=self)`
  - [x] 1.6 `_load_and_edit(entry)` : `EditorScene(level_path=str(entry.path))` avec `next_scene`
  - [x] 1.7 `_load_and_train(entry)` : `AITrainScene(world=..., level_name=entry.name)` avec `next_scene`
  - [x] 1.8 `_new_level()` : `EditorScene()` vide avec `next_scene`
- [x] Task 2 — Mise à jour `main.py`
  - [x] 2.1 Remplacer `EditorScene()` par `LevelSelectScene()` comme scène initiale
- [ ] Task 3 — Mise à jour `ui/ai_train_scene.py` (Story 5.4) — DEFERRED: AITrainScene n'existe pas encore
  - [ ] 3.1 Ajouter paramètre `level_name: str = "unknown"` à `AITrainScene.__init__`
  - [ ] 3.2 Utiliser `level_name` dans le chemin de sauvegarde : `data/brains/{level_name}/gen_{n:03d}_best.json`
- [x] Task 4 — Tests headless `tests/test_level_select.py`
  - [x] 4.1 Test : `LevelSelectScene` s'instancie (dossier vide)
  - [x] 4.2 Test : `_selected_idx` reste dans les bornes avec ↑/↓
  - [x] 4.3 Test : `next_scene` est None à l'init

## Dev Notes

### Architecture obligatoire

```
ui/level_select_scene.py  →  peut importer editor/, engine/, renderer/, pygame
```

### Rendu — simplicité

Pas de sprites ni assets. Fond `(15, 15, 25)`, entrées en texte blanc, sélection surlignée en `(60, 120, 200)`. Instructions en bas : `"[↑↓] Sélectionner  [Enter] Jouer  [E] Éditer  [T] Entraîner IA  [N] Nouveau  [DEL] Supprimer"`.

### Rescan après retour d'Edit

Lorsque `EditorScene` est la `next_scene` active et que le joueur revient (next_scene = LevelSelectScene), il faut rescanner `data/levels/` pour refléter les nouveaux fichiers sauvegardés.

Pattern :
```python
def update(self, dt):
    # Si on vient de revenir d'une sous-scene
    if self._came_from_edit:
        self._entries = LevelLibrary.scan()
        self._came_from_edit = False
```

### AITrainScene — dossier brain par level

Chaque niveau a son propre dossier de cerveaux pour ne pas mélanger les entraînements :
`data/brains/{level_name}/gen_001_best.json`

### References

- [Source: editor/level_library.py] LevelLibrary, LevelEntry (Story 6.2)
- [Source: editor/level_io.py] load_level (Story 3.3)
- [Source: ui/editor_scene.py] EditorScene (Story 3.4)
- [Source: ui/play_scene.py] PlayScene + return_scene pattern (Story 3.4)
- [Source: ui/scene.py] Scene.next_scene pattern (Story 3.4)
- [Source: main.py] entrée principale (Story 3.4)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (GitHub Copilot)

### Debug Log References
None — all tests passed on first run (213 passed).

### Completion Notes List
- `LevelSelectScene` created with full keyboard navigation (↑↓ Enter E T N DEL ESC)
- `main.py` now starts with `LevelSelectScene` instead of `EditorScene`
- Task 3 (AITrainScene `level_name` param) deferred: `ui/ai_train_scene.py` does not exist yet (Story 5.4 not implemented). `_load_and_train` uses `try/except ImportError` to handle gracefully.
- Rescan-after-edit pattern implemented via `_came_from_edit` flag
- 7 headless tests added covering instantiation, index bounds, next_scene, rescan, delete
- **[Code Review Fix]** Added `return_scene` support to `EditorScene` to allow gracefully returning to the level select scene using ESC.
- **[Code Review Fix]** Injected `self` as `return_scene` inside `LevelSelectScene._load_and_edit()` and `_new_level()`.

### File List

- `ui/level_select_scene.py` (nouveau)
- `main.py` (modifié — LevelSelectScene comme scène initiale)
- `tests/test_level_select.py` (nouveau)
