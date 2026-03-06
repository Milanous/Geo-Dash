# Story 5.6: Best Agent Replay

Status: ready-for-dev

## Story

As an AI trainer,
I want to select any past generation and watch its best agent play the level,
So that I can understand how the AI improved over time.

## Acceptance Criteria

1. **Given** `ui/replay_scene.py` exists and at least one `gen_NNN_best.json` exists **When** the user selects "Replay" from the main menu **Then** a generation selector is shown listing available saved generations
2. **When** the user selects a generation **Then** the best brain is loaded via `Brain.from_json()` and a single-agent simulation runs at 60 FPS
3. **And** the player sprite is rendered with the standard game visuals
4. **When** `brain.should_jump()` fires **Then** a visual indicator (circle outline glow) is shown on the active network
5. **And** neuron positions are shown as small coloured dots (green/red) around the player
6. **And** `ESC` returns to the main menu ; `R` restarts the current replay

## Tasks / Subtasks

- [ ] Task 1 — `ui/replay_scene.py` : scene de replay
  - [ ] 1.1 `ReplayScene(Scene)` avec `__init__` : scanner `data/brains/` pour les fichiers `gen_*_best.json` disponibles ; présenter la liste
  - [ ] 1.2 Sélection génération : interface simple (flèches + Entrée, ou clic)
  - [ ] 1.3 `_load_gen(gen_num: int) -> None` : charge le fichier JSON via `Brain.from_json()`, instancie un `Player` seul à la position de départ
  - [ ] 1.4 `update(dt)` : avance la physique du joueur (utiliser `player.update(dt, world)`), évalue `brain.should_jump()` et déclenche le saut
  - [ ] 1.5 `draw(surface)` : rendu via `GameRenderer`, puis overlay de debug (neurones + indicateur jump)
  - [ ] 1.6 `ESC` → retour menu ; `R` → `_load_gen` avec la génération courante
- [ ] Task 2 — Rendu debug neurones
  - [ ] 2.1 Pour chaque neurone du brain : dessiner un petit cercle à `(player_x + neuron.dx, player_y + neuron.dy)` en coordonnées écran — vert si actif, rouge si inactif
  - [ ] 2.2 Si `brain.should_jump()` vient de virer à True : flash/glow sur le joueur pendant 0.1 s
- [ ] Task 3 — Test minimal
  - [ ] 3.1 Test : `ReplayScene` scan de répertoire vide → liste vide, pas de crash

## Dev Notes

### Architecture obligatoire

```
ui/replay_scene.py  →  peut importer ai/, engine/, renderer/, pygame
```

### Réutiliser `Player` et `GameRenderer`

```python
from engine.player import Player
from renderer.game_renderer import GameRenderer
from engine.camera import Camera

self._player = Player(start_x=5.0, start_y=2.0)
self._camera = Camera()
self._renderer = GameRenderer()
```
`player.update(dt, world)` gère la physique. `brain.should_jump()` → si True → simuler un appui espace (injecter un jump).

### Jump depuis brain

`Player` ne prend pas de brain en paramètre. Le replay injecte le saut en appelant la même logique que le clavier : vérifier si `player.state.on_ground` et `brain.should_jump()` → `player.state.vy = JUMP_VELOCITY`.

### Coordonnées écran pour les neurones

```python
from engine.world import World
screen_x = World.to_px(player.state.x + neuron.dx) - camera.x_offset
screen_y = screen_h - World.to_px(player.state.y + neuron.dy)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.6]
- [Source: ai/brain.py] Brain.from_json (Story 4.3)
- [Source: engine/player.py] Player, PlayerState
- [Source: renderer/game_renderer.py] GameRenderer
- [Source: data/brains/] format fichier gen_NNN_best.json (Story 5.4)

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ui/replay_scene.py` (nouveau)
