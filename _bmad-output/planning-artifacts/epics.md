---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories]
inputDocuments: [_bmad-output/planning-artifacts/prd.md, _bmad-output/planning-artifacts/architecture.md]
---

# Geo-Dash - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Geo-Dash, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-P1-01: The level must be rendered as a 2D grid of 1×1 tiles (solid blocks, spikes, air).
FR-P1-02: A scrolling camera must follow the player's horizontal position (no vertical scroll).
FR-P1-03: A persistent level editor must allow placing/removing blocks and spikes on a grid, with camera pan, tile selector, save/load, and play-test button.
FR-P1-05: The player must move automatically to the right at exactly 10.3761348998 blocks/second with no player horizontal control.
FR-P1-06: Gravity must apply constant downward acceleration; Space/Up arrow triggers a jump (vertical impulse, only when on ground, no double-jump).
FR-P1-07: AABB collision with solid tiles makes the player rest on top; spike triangle hitbox causes instant death; Y=0 floor prevents falling out of world.
FR-P1-08: Player appearance: red outer square (1×1 block) with inner square inset and thin black borders; continuous clockwise rotation when in-air; snaps to 0° when on ground.
FR-P1-09: Visual effects: glow/bloom around player, ground-contact particle burst, gradient trail (white→grey ~0.5s), vertical gradient sky, per-tile subtle lightness variation.
FR-P1-10: Spike tiles rendered as equilateral triangles filling 1×1 tile; same tint as blocks; contact with triangle hitbox kills player.
FR-P2-01: Neurons defined by (screen_x_offset, screen_y_offset) relative to player, type (block/spike/air), polarity (green=ON when tile matches / red=ON when tile does NOT match).
FR-P2-02: A network is a group of 1–N neurons + circle output node; fires (→ jump) when ALL neurons are active; multiple networks per brain evaluated independently each frame.
FR-P2-03: Brain = list of networks; serializable to/from JSON (position, type, polarity per neuron; network groupings).
FR-P2-04: 1 000 agents simulated simultaneously on same level; each has independent position/velocity/brain state; dead agents frozen; rendering disabled by default (toggle V).
FR-P2-05: Fitness = maximum X position reached before death or level end; agents completing level receive full level length as fitness.
FR-P2-06: Select top-10 brains (highest fitness); each produces 100 mutated children; mutation: move neurons N(0,1²) per axis (~70%), add/remove neuron (~25%), add/remove network (~5%); neuron positions are continuous floats.
FR-P2-07: Generation loop runs up to 100 generations automatically; early stop if agent completes level; saves best brain + stats after each generation.
FR-P2-08: Per-generation stats displayed: generation number, best/average/worst fitness; running chart; level completion indicator.
FR-P2-09: After each generation, best brain saved; replay UI allows selecting any past generation for visual playback with neuron activations shown.

### NonFunctional Requirements

NFR-01: 1 000 agents simulate at ≥60 sim-steps/s on a modern laptop.
NFR-02: Game renders at stable 60 FPS in play mode.
NFR-03: Level editor saves to disk; data survives process restart.
NFR-04: All 100 generation best-brains saved to disk in JSON.
NFR-05: Player speed = exactly 10.3761348998 blocks/s; physics at 240 Hz fixed timestep.
NFR-06: No external install steps beyond `pip install pygame numpy`.
NFR-07: Code separated into modules: engine/, editor/, ai/, renderer/.
NFR-08: Runs on macOS, Windows, Linux via Python 3.10+.

### Additional Requirements

From Architecture:

- **Project initialization**: `python -m venv .venv && pip install "pygame==2.6.*" "numpy>=1.26"` — first story in Epic 1.
- **Module structure**: `engine/`, `renderer/`, `editor/`, `ai/`, `ui/`, `data/`, `tests/` must be created as part of scaffolding.
- **Import rules (hard constraints for all stories)**:
  - `engine/` must NEVER import `pygame`, `renderer/`, or `ai/`
  - `ai/` must NEVER import `pygame` or `renderer/`
  - `renderer/` may import `engine/` and `ai/brain.py` only
- **Coordinate system**: All physics/AI code works in float blocks; pixel conversion only in `renderer/` via `World.to_px()`.
- **TileType enum**: `engine/world.py` — no raw tile strings in Python code.
- **JSON schemas**: versioned, `"version": 1` mandatory; coordinates in float blocks.
- **Physics constants**: `PHYSICS_RATE=240`, `DT=1/240`, `GRAVITY=-0.958`, `JUMP_VELOCITY=+12.36`, `PLAYER_SPEED=10.3761348998`, `BLOCK_SIZE_PX=30`.
- **Game loop pattern**: fixed accumulator timestep with render interpolation.
- **Pattern State**: `ui/scene.py` ABC with `handle_events()`, `update()`, `draw()`.
- **NumPy vectorised simulation**: `ai/simulation.py` uses `np.ndarray` for positions/velocities.
- **Tests**: headless, never import `pygame`; use `pytest`.

### FR Coverage Map

| FR | Épic | Résumé |
|---|---|---|
| FR-P1-01 | Epic 1 | Rendu grille tuilée |
| FR-P1-02 | Epic 1 | Caméra scrolling |
| FR-P1-05 | Epic 1 | Mouvement joueur horizontal |
| FR-P1-06 | Epic 1 | Gravité & saut |
| FR-P1-07 | Epic 1 | Collision AABB sol & mort |
| FR-P1-08 | Epic 2 | Apparence joueur & rotation |
| FR-P1-09 | Epic 2 | VFX glow, particules, traînée, sky, tint |
| FR-P1-10 | Epic 2 | Tuiles piques & mort |
| FR-P1-03 | Epic 3 | Éditeur de niveaux persistant |
| FR-P2-01 | Epic 4 | Neurones |
| FR-P2-02 | Epic 4 | Réseaux de neurones |
| FR-P2-03 | Epic 4 | Cerveau & sérialisation JSON |
| FR-P2-04 | Epic 5 | Simulation parallèle 1 000 agents |
| FR-P2-05 | Epic 5 | Évaluation fitness |
| FR-P2-06 | Epic 5 | Sélection top-10 & mutation gaussienne |
| FR-P2-07 | Epic 5 | Boucle 100 générations |
| FR-P2-08 | Epic 5 | Stats UI par génération |
| FR-P2-09 | Epic 5 | Replay meilleur agent |

## Epic List

### Epic 1: Foundation — Moteur de jeu & joueur basique
Milan peut lancer le jeu et voir un carré jouer sur un terrain tuilé avec gravité, saut et collision — la boucle de jeu core est fonctionnelle.
**FRs couvertes :** FR-P1-01, FR-P1-02, FR-P1-05, FR-P1-06, FR-P1-07

### Epic 2: Niveaux & visuels polished
Milan peut construire un niveau dans l’éditeur et le jouer avec des piques, un joueur stylé et des effets visuels complets.
**FRs couvertes :** FR-P1-08, FR-P1-09, FR-P1-10

### Epic 3: Éditeur de niveaux persistant
Milan peut concevoir et sauvegarder ses propres niveaux via une interface graphique avec placement de tuiles, caméra pan et play-test direct.
**FRs couvertes :** FR-P1-03

### Epic 4: Système de cerveaux IA
Le système peut créer, évaluer et sérialiser des cerveaux. Un cerveau observe le terrain et décide de sauter via ses réseaux de neurones.
**FRs couvertes :** FR-P2-01, FR-P2-02, FR-P2-03

### Epic 5: Entraînement évolutionnaire & replay
Milan peut lancer un entraînement de 100 générations, suivre la progression en temps réel, et rejouer le meilleur agent de n'importe quelle génération.
**FRs couvertes :** FR-P2-04, FR-P2-05, FR-P2-06, FR-P2-07, FR-P2-08, FR-P2-09

---

## Epic 1: Foundation — Moteur de jeu & joueur basique

### Story 1.1: Project Scaffolding & Environment Setup

As a developer,
I want the project directory structure, virtual environment, and dependencies initialized,
So that all subsequent stories have a consistent, runnable foundation.

**Acceptance Criteria:**

**Given** an empty project directory
**When** the developer runs the setup commands
**Then** the following structure exists:
```
geo-dash/
├── main.py
├── requirements.txt        # pygame==2.6.*, numpy>=1.26
├── engine/__init__.py
├── renderer/__init__.py
├── editor/__init__.py
├── ai/__init__.py
├── ui/__init__.py
├── data/levels/.gitkeep
├── data/brains/.gitkeep
└── tests/__init__.py
```
**And** `pip install -r requirements.txt` succeeds without errors
**And** `python main.py` runs without import errors (can exit immediately)
**And** no module in `engine/` imports `pygame`, `renderer/`, or `ai/`

---

### Story 1.2: Physics Constants & PlayerState

As a developer,
I want all physics constants and the PlayerState dataclass defined in a single source-of-truth module,
So that every other module can import them without duplication or magic numbers.

**Acceptance Criteria:**

**Given** `engine/physics.py` exists
**When** it is imported
**Then** the following constants are accessible:
- `PHYSICS_RATE = 240`
- `DT = 1.0 / 240`
- `GRAVITY = -0.958` (blocks/frame)
- `JUMP_VELOCITY = 12.36` (blocks/frame)
- `PLAYER_SPEED = 10.3761348998` (blocks/s)
- `BLOCK_SIZE_PX = 30`
**And** `PlayerState` is a dataclass with fields: `x: float`, `y: float`, `vy: float`, `on_ground: bool`, `angle: float`
**And** `engine/physics.py` imports neither `pygame` nor any project module
**And** `tests/test_physics.py` asserts each constant to its exact value and `DT == 1.0 / PHYSICS_RATE`

---

### Story 1.3: Tile Grid World & Coordinate System

As a developer,
I want a `World` class that stores the level tile grid and converts between block and pixel coordinates,
So that all modules share a single coordinate system.

**Acceptance Criteria:**

**Given** `engine/world.py` exists with `TileType(Enum)` and `World`
**When** `TileType` is imported
**Then** it has members: `AIR`, `SOLID`, `SPIKE`
**When** `World(width, height)` is instantiated (default all `AIR`)
**Then** `world.tile_at(bx, by)` returns `TileType.AIR` for any in-bounds position
**And** `world.set_tile(bx, by, TileType.SOLID)` then `world.tile_at(bx, by)` returns `TileType.SOLID`
**And** `World.to_px(1.0) == 30` (BLOCK_SIZE_PX)
**And** `World.to_bloc(30) == 1.0`
**And** `World.to_px(0.5) == 15`
**And** `engine/world.py` does not import `pygame`
**And** `tests/test_world.py` covers all above with passing tests

---

### Story 1.4: Scrolling Camera

As a player,
I want the camera to follow my horizontal position so I can always see what is ahead,
So that the level scrolls as I move right.

**Acceptance Criteria:**

**Given** `engine/camera.py` exists with a `Camera` class
**When** `Camera(x_offset=0)` is instantiated
**Then** `camera.world_to_screen_x(bloc_x)` returns `World.to_px(bloc_x) - camera.x_offset`
**When** `camera.follow(player_x)` is called with a player X position in blocks
**Then** `camera.x_offset` is updated so the player appears at a fixed horizontal screen position (e.g. 200 px from left)
**And** `camera.x_offset` never goes below 0 (no negative scroll)
**And** `engine/camera.py` does not import `pygame`

---

### Story 1.5: Player Horizontal Movement & Gravity

As a player,
I want my character to move automatically to the right and fall under gravity,
So that the game feels like Geometry Dash.

**Acceptance Criteria:**

**Given** `engine/player.py` exists with a `Player` class that holds a `PlayerState`
**When** `player.update(dt)` is called each physics step
**Then** `player.state.x` increases by `PLAYER_SPEED * dt` each step
**And** `player.state.vy` decreases by `GRAVITY` (i.e. `vy += GRAVITY`) each step (gravity pulls down)
**And** `player.state.y` decreases by `vy * dt` each step (or increases depending on axis convention — must be consistent with GRAVITY sign)
**And** the player falls infinitely if no floor is present
**And** `engine/player.py` does not import `pygame`
**And** a test in `tests/test_physics.py` verifies x advances by exactly `PLAYER_SPEED * DT` per step

---

### Story 1.6: Jump, Ground Collision & Floor Boundary

As a player,
I want to be able to jump when on the ground and land on solid tiles,
So that I can navigate the level without falling through the world.

**Acceptance Criteria:**

**Given** a `World` with a row of `SOLID` tiles at `y=0`
**When** the player falls onto `y=0`
**Then** `player.state.y` is clamped to 0 (or tile top surface)
**And** `player.state.vy` is set to 0
**And** `player.state.on_ground` is `True`
**When** `player.jump()` is called and `on_ground` is `True`
**Then** `player.state.vy` is set to `JUMP_VELOCITY`
**And** `player.state.on_ground` becomes `False`
**When** `player.jump()` is called and `on_ground` is `False`
**Then** `player.state.vy` is unchanged (no double-jump)
**And** a Y=0 floor catches the player even without a tile (world boundary)
**And** tests in `tests/test_world.py` verify collision and jump mechanics headlessly

---

### Story 1.7: Game Loop, Basic Renderer & Play Scene

As a player,
I want to see the game running at 60 FPS with the player moving on a tiled level,
So that the core game loop is functional and visible.

**Acceptance Criteria:**

**Given** `main.py` exists with a Pygame window (800×600 default)
**When** the game starts
**Then** a fixed-timestep loop runs at 240 Hz physics with 60 FPS rendering
**And** the accumulator pattern is used: `while accumulator >= DT: physics_step(); accumulator -= DT`
**And** `ui/scene.py` defines the `Scene` ABC with `handle_events()`, `update(dt)`, `draw(surface)`
**And** `ui/play_scene.py` implements `PlayScene` loading a simple hardcoded level (flat floor of SOLID tiles)
**And** `renderer/game_renderer.py` draws solid tiles as grey rectangles and the player as a red square (1 block)
**And** the camera follows the player horizontally
**And** pressing `ESC` exits the game cleanly
**And** the game maintains ≥55 FPS on the dev machine (monitored via `pygame.Clock`)

---

## Epic 2: Niveaux & visuels polished

### Story 2.3: Spike Tiles & Death Detection

As a player,
I want spike tiles to be rendered as triangles and kill me on contact,
So that hazards are visually clear and gameplay consequences are immediate.

**Acceptance Criteria:**

**Given** a level loaded with `TileType.SPIKE` tiles
**When** the game renderer draws the scene
**Then** each spike is drawn as a filled equilateral triangle occupying the full 1×1 tile area
**And** spike tiles receive the same block-tint variation as solid tiles (subtle lightness offset)
**When** the player's bounding box overlaps any spike tile's triangle hitbox
**Then** the player's `alive` flag is set to `False` and the play scene resets
**And** a test in `tests/test_world.py` verifies spike collision detection headlessly using a mock `PlayerState`

---

### Story 2.4: Player Visual Polish — Styled Square & In-Air Rotation

As a player,
I want my character to look like the Geometry Dash cube with smooth rotation while airborne,
So that the game feels visually authentic.

**Acceptance Criteria:**

**Given** the player is rendered by `renderer/game_renderer.py`
**When** the player sprite is drawn
**Then** it consists of a red outer square (1×1 block, thin black border) and a smaller red inner square (centered, ~60% size, thin black border)
**When** `player.state.on_ground` is `False`
**Then** `player.state.angle` increases by a fixed rate per physics step (clockwise rotation)
**And** the sprite is drawn rotated by `player.state.angle` degrees
**When** `player.state.on_ground` is `True`
**Then** `player.state.angle` snaps to 0°
**And** the rotation logic lives in `engine/player.py` (pure, no pygame)
**And** the drawing with rotation uses `pygame.transform.rotate`

---

### Story 2.5: VFX — Glow, Ground Particles & Trail

As a player,
I want visual effects around my character (glow, particles on landing, movement trail),
So that the game feels polished and satisfying.

**Acceptance Criteria:**

**Given** `renderer/vfx.py` exists with `VFXSystem`
**When** `vfx_system.update(player_state, dt)` is called each frame
**Then** the trail deque records the last ~30 player positions (≈0.5 s at 60 FPS)
**And** particles created by `on_land()` are updated (position, lifetime decreasing)
**When** `vfx_system.draw(surface, camera_offset)` is called
**Then** the trail is drawn as a gradient line from white (head) to grey (tail)
**And** active particles are drawn as small filled circles
**And** a soft glow/bloom halo is drawn behind the player using a semi-transparent surface
**When** `PlayerState.on_ground` transitions from `False` to `True`
**Then** `vfx_system.on_land(px, py)` is called, spawning a burst of ≥5 particles
**And** `VFXSystem` never imports from `engine/player.py` directly — it receives `PlayerState` only

---

### Story 2.6: VFX — Gradient Sky & Block Tint Variation

As a player,
I want the sky to show a vertical colour gradient and blocks to have subtle colour variation,
So that the level has visual depth and atmosphere.

**Acceptance Criteria:**

**Given** the game renderer draws the play scene
**When** the background is drawn
**Then** it shows a vertical gradient from a top colour to a bottom colour (configurable constants, e.g. dark blue → lighter blue)
**And** the gradient is drawn using a series of horizontal lines or a Surface fill
**When** solid and spike tiles are drawn
**Then** each tile has a unique, deterministic lightness offset (seeded by tile grid position) in the range ±10% of the base tile colour
**And** the tint offsets are computed once at level load and cached (not recalculated every frame)
**And** tile tints do not affect collision logic in `engine/world.py`

---

## Epic 3: Éditeur de niveaux persistant

### Story 3.1: Level Editor Core — Grid Display & Tile Placement

As a level designer,
I want to click on a grid to place and remove tiles,
So that I can build a custom level interactively.

**Acceptance Criteria:**

**Given** `editor/editor.py` exists with an `Editor` class wrapping a `World`
**When** the editor is active
**Then** the grid is displayed with tile outlines visible
**And** a toolbar shows at least two tile type buttons: `SOLID` and `SPIKE`
**And** left-click on a grid cell places the currently selected tile type
**And** right-click on a grid cell sets the cell to `TileType.AIR` (erase)
**And** the tile type selector updates on toolbar button click
**And** `editor/editor.py` does not import `pygame` (event handling lives in `ui/editor_scene.py`)

---

### Story 3.2: Editor Camera Pan

As a level designer,
I want to pan the editor camera so I can work on any part of the level,
So that I am not limited to a fixed viewport.

**Acceptance Criteria:**

**Given** the editor scene is active
**When** the user holds the middle mouse button and drags
**Then** the camera pans in the corresponding direction
**When** the user presses arrow keys
**Then** the camera moves at a fixed pan speed (e.g. 5 blocks/s)
**And** the camera offset is applied when converting screen coordinates to grid coordinates for tile placement
**And** the camera cannot scroll to negative world coordinates

---

### Story 3.3: Level Save & Load (JSON)

As a level designer,
I want to save my level to disk and reload it,
So that my work persists between sessions.

**Acceptance Criteria:**

**Given** `editor/level_io.py` exists with `save_level(path, world)` and `load_level(path) -> World`
**When** `save_level("data/levels/my_level.json", world)` is called
**Then** a JSON file is written matching the schema `{"version": 1, "name": "...", "tiles": [{"x": int, "y": int, "type": "solid"|"spike"}]}`
**And** only non-AIR tiles are written (AIR is implicit)
**When** `load_level("data/levels/my_level.json")` is called
**Then** it returns a `World` with tiles at the correct positions
**And** a round-trip (save then load) produces an identical `World`
**And** `tests/test_world.py` includes a round-trip test for save/load
**And** `level_io.py` does not import `pygame`

---

### Story 3.4: Editor Scene, Renderer & Play-test Button

As a level designer,
I want a complete editor interface with a play-test button,
So that I can immediately try the level I am building.

**Acceptance Criteria:**

**Given** `ui/editor_scene.py` and `renderer/editor_renderer.py` exist
**When** the editor scene is active
**Then** the grid, tiles, toolbar, and cursor highlight are drawn by `editor_renderer.py`
**And** a "Play-test" button is visible in the toolbar
**When** the play-test button is clicked (or `P` key pressed)
**Then** the current editor `World` is passed to `PlayScene` and the play scene activates
**When** the player dies or `ESC` is pressed in play-test mode
**Then** control returns to the editor scene with the same state
**And** the editor scene is reachable from the main menu

---

## Epic 4: Système de cerveaux IA

### Story 4.1: Neuron — Definition, Sensing & Tests

As an AI designer,
I want neurons that can sense the environment around the player and report active/inactive state,
So that brains can perceive the level.

**Acceptance Criteria:**

**Given** `ai/neuron.py` exists with a `Neuron` dataclass
**When** `Neuron(dx=2.0, dy=-1.0, type=TileType.SPIKE, polarity="green")` is created
**Then** `neuron.dx` and `neuron.dy` are `float` values (not grid-snapped integers)
**When** `neuron.is_active(player_x, player_y, world)` is called
**And** the tile at `(player_x + dx, player_y + dy)` is `TileType.SPIKE`
**Then** a green neuron returns `True`
**And** a red neuron (`polarity="red"`) returns `False`
**When** the tile does NOT match the neuron's type
**Then** a green neuron returns `False`, a red neuron returns `True`
**And** `ai/neuron.py` does not import `pygame`
**And** `tests/test_brain.py` covers all four polarity × match combinations

---

### Story 4.2: Network — Grouping & Firing Logic

As an AI designer,
I want a network that groups neurons and fires when all are active,
So that complex conditions can trigger a jump.

**Acceptance Criteria:**

**Given** `ai/network.py` exists with a `Network` class
**When** `Network(neurons=[n1, n2])` is created
**And** `network.should_fire(player_x, player_y, world)` is called
**Then** it returns `True` only if ALL neurons in the list return `True` from `is_active()`
**When** any one neuron returns `False`
**Then** `should_fire()` returns `False`
**And** a `Network` with a single neuron fires if that neuron is active
**And** `Network` with empty neuron list never fires
**And** `ai/network.py` does not import `pygame`
**And** `tests/test_brain.py` covers all-active, one-inactive, and empty-network cases

---

### Story 4.3: Brain — Genome & JSON Serialization

As an AI designer,
I want a Brain that aggregates networks and triggers a jump when any network fires,
So that the full decision logic is encapsulated in a serializable genome.

**Acceptance Criteria:**

**Given** `ai/brain.py` exists with a `Brain` class
**When** `Brain(networks=[net1, net2])` is created
**And** `brain.should_jump(player_x, player_y, world)` is called
**Then** it returns `True` if ANY network fires
**And** returns `False` only if NO network fires
**When** `brain.to_json()` is called
**Then** it returns a dict matching the schema:
```json
{"version": 1, "networks": [{"neurons": [{"dx": float, "dy": float, "type": "spike"|"solid"|"air", "polarity": "green"|"red"}]}]}
```
**When** `Brain.from_json(data)` is called with the above dict
**Then** it returns an equivalent `Brain` that behaves identically
**And** a round-trip (to_json → from_json) produces a brain with identical `should_jump()` results for any input
**And** `ai/brain.py` does not import `pygame`
**And** `tests/test_brain.py` covers should_jump (any fires, none fires) and round-trip serialization

---

## Epic 5: Entraînement évolutionnaire & replay

### Story 5.1: PopulationSim — NumPy Vectorised Simulation

As an AI trainer,
I want 1 000 agents simulated simultaneously using NumPy vectorised operations,
So that a full generation completes in under 60 seconds.

**Acceptance Criteria:**

**Given** `ai/simulation.py` exists with `PopulationSim`
**When** `PopulationSim(brains, level)` is instantiated with 1 000 brains
**Then** `self.x`, `self.y`, `self.vy`, `self.alive` are `np.ndarray` of shape `(1000,)`
**When** `sim.step(DT)` is called once
**Then** `self.x[i]` increases by `PLAYER_SPEED * DT` for all alive agents
**And** `self.vy[i]` decreases by `GRAVITY` for all alive agents
**And** agents with `alive[i] == False` do not move (position frozen)
**When** an agent's bounding box overlaps a `SPIKE` tile
**Then** `alive[i]` is set to `False`
**And** `ai/simulation.py` does not import `pygame`
**And** a benchmark test in `tests/test_evolution.py` verifies 1 000 agents × 67 blocks simulation completes in < 60 s

---

### Story 5.2: Fitness Evaluation

As an AI trainer,
I want each agent scored by the maximum distance it reached,
So that better agents can be identified and selected.

**Acceptance Criteria:**

**Given** a `PopulationSim` that has run to completion (all agents dead or level end reached)
**When** `sim.fitness()` is called
**Then** it returns a `np.ndarray` of shape `(1000,)` where each value is the agent's maximum X position reached in blocks
**And** an agent that reached the end of the level receives the full level length as fitness
**And** agents that never moved (died at start) have fitness ≈ 0
**And** `fitness()` is a pure read — it does not modify simulation state
**And** `tests/test_evolution.py` verifies fitness values for mock simulation results

---

### Story 5.3: Evolution — Top-10 Selection & Gaussian Mutation

As an AI trainer,
I want the top-10 brains selected and mutated to produce the next generation,
So that each generation improves on the previous one.

**Acceptance Criteria:**

**Given** `ai/evolution.py` exists with `select_top_n(brains, fitness, n=10)` and `mutate(brain)`
**When** `select_top_n` is called with 1 000 brains and their fitness scores
**Then** it returns the 10 brains with the highest fitness values
**When** `mutate(brain)` is called
**Then** it returns a new `Brain` (original unchanged) with one of the following applied:
- (~70%) 1–3 neuron positions displaced by `Δ ~ N(0, 1.0²)` independently per axis (in blocks)
- (~25%) a neuron added to or removed from a randomly chosen network
- (~5%) an entire network added or removed
**And** neuron positions after mutation remain as `float` (not snapped to grid)
**And** mutation never produces a `Brain` with zero networks
**And** `tests/test_evolution.py` verifies select_top_n returns 10 items, and that mutate returns a different object with valid structure

---

### Story 5.4: Generation Loop — 100 Generations, Save & Early Stop

As an AI trainer,
I want the training loop to run 100 generations automatically, saving after each, with early stop on level completion,
So that training requires minimal intervention.

**Acceptance Criteria:**

**Given** `ui/ai_train_scene.py` exists and the user selects "Train AI" from the menu
**When** training starts
**Then** a population of 1 000 random brains is generated
**And** each generation runs: simulate → evaluate fitness → select top-10 → mutate × 990 + elites × 10 = 1 000
**And** after each generation, the best brain is saved to `data/brains/gen_NNN_best.json`
**And** generation stats (number, best/avg/worst fitness) are logged/displayed
**When** any agent completes the full level (fitness ≥ level length)
**Then** training stops early and a "Level Completed!" indicator is shown
**When** 100 generations have run
**Then** training stops and a summary is displayed
**And** the user can press `ESC` to abort training at any time

---

### Story 5.5: Generation Stats HUD

As an AI trainer,
I want a live stats overlay showing generation progress,
So that I can monitor whether the AI is improving.

**Acceptance Criteria:**

**Given** `ui/hud.py` exists with a `StatsHUD` widget
**When** `StatsHUD.draw(surface, stats)` is called
**Then** the following are displayed on screen:
- Current generation number (e.g. "Gen 42 / 100")
- Best fitness in current generation (in blocks, 1 decimal)
- Average fitness in current generation
- Worst fitness in current generation
**And** a running line chart shows best fitness over all completed generations
**And** an "ALIVE: NNN" counter shows how many agents are still running in the current generation
**And** a "Press V to toggle agent view" hint is displayed
**When** `V` is pressed
**Then** alive agents are rendered as semi-transparent red squares (debug mode toggle)
**And** `StatsHUD` does not import from `ai/simulation.py` directly — it receives a plain stats dict

---

### Story 5.6: Best Agent Replay

As an AI trainer,
I want to select any past generation and watch its best agent play the level,
So that I can understand how the AI improved over time.

**Acceptance Criteria:**

**Given** `ui/replay_scene.py` exists and at least one `gen_NNN_best.json` file exists
**When** the user selects "Replay" from the main menu
**Then** a generation selector is shown listing available saved generations
**When** the user selects a generation
**Then** the best brain from that generation is loaded via `Brain.from_json()`
**And** a single-agent simulation runs at normal game speed (60 FPS visual)
**And** the player sprite is rendered with the standard game visuals
**When** the `brain.should_jump()` fires
**Then** a visual indicator (e.g. circle outline glow) is shown on the active network's output node
**And** neuron positions are shown as small coloured dots (green/red) around the player
**And** pressing `ESC` returns to the main menu
**And** pressing `R` restarts the current replay from the beginning
