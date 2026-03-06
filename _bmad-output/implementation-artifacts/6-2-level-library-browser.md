# Story 6.2: Level Library — Browse, Select & Delete

Status: done

## Story

As a player or level designer,
I want to see all saved levels and pick one to play or edit,
So that I can maintain a library of levels without using the filesystem manually.

## Acceptance Criteria

1. **Given** `editor/level_library.py` exists **When** `LevelLibrary.scan()` is called **Then** it returns a list of `LevelEntry` objects (name, path, modified_at) for every `.json` file in `data/levels/`
2. **And** entries are sorted by `modified_at` descending (most recent first)
3. **When** `data/levels/` does not exist **Then** `scan()` returns an empty list (no crash)
4. **When** `LevelLibrary.delete(entry)` is called **Then** the corresponding JSON file is removed from disk
5. **And** `tests/test_level_library.py` covers scan, sort, delete and empty-folder cases

## Tasks / Subtasks

- [x] Task 1 — `editor/level_library.py` : scan + delete
  - [x] 1.1 `@dataclass LevelEntry(name: str, path: Path, modified_at: float)` — `name` est le stem du fichier (`Path.stem`)
  - [x] 1.2 `class LevelLibrary` avec méthode statique `scan(folder: str | Path = "data/levels") -> list[LevelEntry]`
    - `Path(folder).glob("*.json")` → liste des fichiers
    - Construit un `LevelEntry` par fichier (`stat().st_mtime` pour `modified_at`)
    - Trie par `modified_at` décroissant
    - Si dossier absent : retourne `[]`
  - [x] 1.3 `LevelLibrary.delete(entry: LevelEntry) -> None` : `entry.path.unlink(missing_ok=True)`
  - [x] 1.4 ZERO import `pygame`
- [x] Task 2 — `tests/test_level_library.py` : tests headless
  - [x] 2.1 Test : `scan()` sur dossier vide → liste vide
  - [x] 2.2 Test : `scan()` sur dossier absent → liste vide, pas d'exception
  - [x] 2.3 Test : `scan()` retourne autant d'entrées que de fichiers `.json`
  - [x] 2.4 Test : tri décroissant — le fichier le plus récent est en premier
  - [x] 2.5 Test : `delete()` supprime le fichier
  - [x] 2.6 Test : `delete()` sur fichier déjà absent → pas d'exception
  - [x] 2.7 Test : import guard — `level_library.py` n'importe pas `pygame`
- [x] Review Follow-ups (AI)
  - [x] [AI-Review][High] Handle FileNotFoundError in `scan()` for concurrently deleted files
  - [x] [AI-Review][Medium] Remove unused imports in `level_library.py` and `test_level_library.py`
  - [x] [AI-Review][Low] Improved type hint for `scan` signature (`os.PathLike[str]`)

## Dev Notes

### Architecture obligatoire

```
editor/level_library.py  →  stdlib uniquement
```
Pas de pygame, pas d'engine, pas d'ai. Juste pathlib + dataclasses.

### `name` vs filename

`entry.name` = `Path(file).stem` (sans `.json`). Exemple : `data/levels/mon_niveau.json` → `name = "mon_niveau"`.

### Dossier par défaut

Utiliser `Path("data/levels")` comme valeur par défaut. Le chemin est relatif au `cwd` au moment de l'exécution (racine du projet avec `python main.py`). Dans les tests, passer `tmp_path` comme argument.

### References

- [Source: editor/level_io.py] `save_level`, `load_level` (Story 3.3)
- [Source: _bmad-output/implementation-artifacts/6-1-level-save-dialog.md] Story 6.1

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References

### Completion Notes List
- `LevelEntry` dataclass: `name` (stem), `path` (Path), `modified_at` (float mtime)
- `LevelLibrary.scan()`: globs `*.json`, sorts by `modified_at` desc, returns `[]` if folder absent
- `LevelLibrary.delete()`: `unlink(missing_ok=True)`
- Zero pygame imports — stdlib only (pathlib + dataclasses)
- 7 tests all passing, full suite 206 passed
- **[AI Code Review Fixes]**: Fixed concurrent deletion crash via `try/except FileNotFoundError` on `stat()`. Cleaned up unused imports (pytest, time, importlib). Improved `scan` signature typehint with `os.PathLike[str]`.

### File List

- `editor/level_library.py` (nouveau)
- `tests/test_level_library.py` (nouveau)
