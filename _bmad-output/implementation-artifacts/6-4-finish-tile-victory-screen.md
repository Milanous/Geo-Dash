# Story 6.4: Finish Tile & Victory Screen

Status: dev-complete

## Story

As a player,
I want a visible finish line in the level and a victory screen when I reach it,
So that levels have a clear objective and end.

## Acceptance Criteria

1. **Given** `TileType.FINISH` is added to `engine/world.py` **When** the player's bounding box overlaps a FINISH tile **Then** `player.finished = True` and physics stops updating that player
2. **When** the edge of the world is reached (`player.x >= world.width - 1`) **Then** the same `player.finished = True` is set
3. **When** `player.finished == True` in `PlayScene` **Then** `VictoryScene` activates
4. **And** `VictoryScene` displays: "LEVEL COMPLETE!", the level name, and options "Play Again" / "Level Select"
5. **And** `TileType.FINISH` renders as a **bright green vertical bar** in both `game_renderer.py` and `editor_renderer.py`
6. **And** `TileType.FINISH` is serialised as `"finish"` in level JSON (backward-compatible — old files without FINISH still load correctly)
7. **And** the editor toolbar gains a "FINISH" button (3rd tile type)
8. **And** `tests/test_finish.py` covers finish detection (tile + world edge) and JSON round-trip

## Tasks / Subtasks

- [x] Task 1 — `engine/world.py` : ajouter `TileType.FINISH`
  - [x] 1.1 Ajouter `FINISH = auto()` à l'enum `TileType`
- [x] Task 2 — `engine/player.py` : ajouter `finished` à `PlayerState`
  - [x] 2.1 Ajouter `self.finished: bool = False` à `PlayerState.__init__`
  - [x] 2.2 Dans `Player.update()` : ne pas appeler la physique si `self.state.finished`
  - [x] 2.3 Détection finish tile : si `world.tile_at(self.state.x, self.state.y) == TileType.FINISH` → `self.state.finished = True`
  - [x] 2.4 Détection bord monde : si `self.state.x >= world.width - 1` → `self.state.finished = True`
- [x] Task 3 — `editor/level_io.py` : sérialisation `FINISH`
  - [x] 3.1 Ajouter `TileType.FINISH: "finish"` dans `_TYPE_TO_STR`
  - [x] 3.2 Ajouter `"finish": TileType.FINISH` dans `_STR_TO_TYPE`
  - [x] 3.3 Les anciens fichiers sans tile `"finish"` chargent sans erreur (aucune migration nécessaire)
- [x] Task 4 — `renderer/game_renderer.py` : rendu FINISH
  - [x] 4.1 Couleur `_FINISH_COLOR = (50, 220, 80)` (vert vif)
  - [x] 4.2 Dans `_draw_tiles()` : case `TileType.FINISH` → rectangle vertical centré (largeur = 4 px, hauteur = 1 bloc)
- [x] Task 5 — `renderer/editor_renderer.py` : rendu FINISH dans l'éditeur
  - [x] 5.1 Même rendu que game_renderer pour FINISH
  - [x] 5.2 Ajouter bouton "FINISH" dans la toolbar (`_BTN_FINISH_IDX = 2`)
- [x] Task 6 — `ui/editor_scene.py` : sélection tile FINISH
  - [x] 6.1 Ajouter `TileType.FINISH` comme tile sélectionnable dans `_handle_toolbar_click`
- [x] Task 7 — `ui/victory_scene.py` : écran de victoire
  - [x] 7.1 `VictoryScene(Scene)` avec `__init__(level_name: str = "", return_scene: Scene | None = None)`
  - [x] 7.2 Affiche "LEVEL COMPLETE!" + `level_name` en grand
  - [x] 7.3 Options : `[R] Rejouer` → `PlayScene` avec même niveau ; `[Enter/ESC] Sélection niveaux` → `LevelSelectScene`
  - [x] 7.4 `handle_events()` : `R` → rejouer, `Enter`/`ESC` → LevelSelectScene
- [x] Task 8 — `ui/play_scene.py` : déclenchement VictoryScene
  - [x] 8.1 Dans `update()` : si `self._player.state.finished` → `self.next_scene = VictoryScene(level_name=..., return_scene=level_select)`
  - [x] 8.2 Stocker `level_name` en paramètre de `PlayScene.__init__`
- [x] Task 9 — `tests/test_finish.py` : tests headless
  - [x] 9.1 Test : `TileType.FINISH` existe dans l'enum
  - [x] 9.2 Test : `PlayerState.finished` est False à l'init
  - [x] 9.3 Test : joueur sur tile FINISH → `player.state.finished == True` après `player.update(dt, world)`
  - [x] 9.4 Test : joueur à `x >= world.width - 1` → `player.state.finished == True`
  - [x] 9.5 Test : round-trip JSON avec tile FINISH → `TileType.FINISH` restauré
  - [x] 9.6 Test : charger un ancien fichier JSON (sans tile FINISH) → pas d'erreur
  - [x] 9.7 Test : import guard — `player.py` n'importe pas `pygame`

## Dev Notes

### Architecture obligatoire

```
engine/world.py     →  stdlib uniquement — ajouter FINISH à TileType
engine/player.py    →  stdlib + engine/ — ajouter détection finish
editor/level_io.py  →  stdlib + engine/ — ajouter FINISH à mapping
renderer/           →  engine/ + pygame — rendu FINISH
ui/victory_scene.py →  engine/ + renderer/ + pygame
```

### Compatibilité JSON — préserver version 1

On reste en `"version": 1`. FINISH est simplement un nouveau `type` possible dans le tableau `tiles`. Les anciens fichiers chargent normalement car ils n'ont pas de tile de type `"finish"` — aucun changement de comportement.

### Détection finish dans `player.py`

```python
# Dans Player.update() — après mise à jour de position
if world.tile_at(self.state.x, self.state.y) == TileType.FINISH:
    self.state.finished = True
if self.state.x >= world.width - 1:
    self.state.finished = True
# Si finished : ne pas appliquer la physique
if self.state.finished:
    return
```

### `PlayScene` — stocker `level_name`

```python
class PlayScene(Scene):
    def __init__(
        self,
        world: World | None = None,
        return_scene: Scene | None = None,
        level_name: str = "",
    ) -> None:
        ...
        self._level_name = level_name
```

### VictoryScene — rendu sans font heavy

Utiliser `pygame.font.Font(None, 48)` pour le titre, `pygame.font.Font(None, 28)` pour les options. Fond dark + texte blanc, vert pour "LEVEL COMPLETE!".

### Impact sur PopulationSim (Story 5.1 — futur)

Dans `ai/simulation.py`, la condition de victoire sera `player.state.finished` ou `player.x >= world.width - 1`. La story 5.4 early-stop utilisera cette même logique. **Ne pas modifier `ai/simulation.py` dans cette story** — noter dans les Completion Notes que 5.4 devra tenir compte de `TileType.FINISH`.

### References

- [Source: engine/world.py] TileType (Stories 1.3+)
- [Source: engine/player.py] Player, PlayerState (Story 1.5)
- [Source: editor/level_io.py] _TYPE_TO_STR, _STR_TO_TYPE (Story 3.3)
- [Source: renderer/game_renderer.py] _draw_tiles (Story 1.7)
- [Source: renderer/editor_renderer.py] _draw_tiles, toolbar (Story 3.4)
- [Source: ui/play_scene.py] update() mort/return_scene pattern (Story 3.4)
- [Source: ui/level_select_scene.py] LevelSelectScene (Story 6.3)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (GitHub Copilot)

### Debug Log References
- FINISH tile detection moved to `_resolve_collision` (alongside SPIKE) to catch tile overlap pre-snap
- World-edge detection kept in `update()` post-collision
- `_BTN_FINISH_IDX = 2`, PLAY shifted to index 3
- `VictoryScene.__init__` accepts `world` param for replay support
- `PlayScene.update()` walks up `return_scene` to find `LevelSelectScene` for VictoryScene

### Completion Notes List
- Story 5.4 (AI early-stop) should use `player.state.finished` or `player.x >= world.width - 1` — `TileType.FINISH` is now available
- `_STR_TO_TYPE` is auto-derived from `_TYPE_TO_STR` via dict comprehension — adding FINISH to `_TYPE_TO_STR` was sufficient

### File List

- `engine/world.py` (modifié — TileType.FINISH)
- `engine/physics.py` (modifié — PlayerState.finished field)
- `engine/player.py` (modifié — finished guard, finish tile + world edge detection)
- `editor/level_io.py` (modifié — FINISH in _TYPE_TO_STR)
- `renderer/game_renderer.py` (modifié — _FINISH_COLOR, green vertical bar render)
- `renderer/editor_renderer.py` (modifié — FINISH render + toolbar button at idx 2)
- `ui/editor_scene.py` (modifié — FINISH tile in _handle_toolbar_click)
- `ui/victory_scene.py` (nouveau — VictoryScene with replay/level-select)
- `ui/play_scene.py` (modifié — level_name param, VictoryScene trigger on finish)
- `ui/level_select_scene.py` (modifié — pass level_name to PlayScene)
- `tests/test_finish.py` (nouveau — 8 tests)
