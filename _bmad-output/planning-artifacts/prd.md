---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
inputDocuments: []
workflowType: prd
---

# Product Requirements Document — Geo-Dash

**Author:** Milan  
**Date:** 2026-03-03  
**Version:** 1.3  
**Status:** Finalized — All OQs resolved

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Goals](#2-vision--goals)
3. [Success Criteria](#3-success-criteria)
4. [User Journeys](#4-user-journeys)
5. [Domain Model](#5-domain-model)
6. [Project Scope](#6-project-scope)
7. [Functional Requirements — Phase 1: Game](#7-functional-requirements--phase-1-game)
8. [Functional Requirements — Phase 2: AI](#8-functional-requirements--phase-2-ai)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Technical Constraints & Stack](#10-technical-constraints--stack)
11. [Out of Scope](#11-out-of-scope)
12. [Resolved Decisions](#12-resolved-decisions)
13. [Open Questions](#13-open-questions)

---

## 1. Executive Summary

**Geo-Dash** is a Geometry Dash clone built in Python/Pygame with two distinct phases:

1. **Phase 1 — Playable Game**: A faithful side-scrolling platformer with a level editor, physics, and polished visual effects.
2. **Phase 2 — Evolutionary AI**: A population-based neuro-evolutionary system where 1 000 agent "brains" are tested in parallel each generation, with the fittest surviving and mutating over 100 generations to learn to complete a level.

The project is both a technical learning exercise (game development, evolutionary algorithms) and a personal creative project for Milan.

---

## 2. Vision & Goals

### Vision Statement
> Create a Geometry Dash clone that can be played by a human or by an AI that learns autonomously — using a unique visual neuron-network system — through evolutionary selection.

### Primary Goals

| # | Goal | Phase |
|---|------|-------|
| G-01 | Deliver a playable Geometry Dash-like game in Python/Pygame | 1 |
| G-02 | Provide a persistent level editor for custom level creation | 1 |
| G-04 | Implement polished visuals: gradient sky, glow, particles, trail | 1 |
| G-05 | Implement an evolutionary AI with visual neuron-network brains | 2 |
| G-06 | Evolve 1 000 brains per generation over 100 generations in parallel | 2 |
| G-07 | Visualize AI progress: live stats + replay of best agent per generation | 2 |

---

## 3. Success Criteria

| ID | Criterion | Measurable Signal |
|----|-----------|-------------------|
| SC-02 | Level editor saves and reloads a level exactly | Saved file + loaded scene are pixel-identical |
| SC-03 | Physics match official GD speed and feel | Player moves at 10.3761348998 b/s; gravity = -0.958 b/frame @ 240Hz |
| SC-04 | AI maximizes distance on the loaded level within 100 generations | Best agent distance increases monotonically; ideally completes the level |
| SC-05 | All 1 000 agents run in parallel without frame drops | Full generation simulation completes in < 60 s on dev machine |
| SC-06 | User can watch the best agent of any past generation | Replay mode accessible from generation stats UI |

---

## 4. User Journeys

### Journey 1 — Human Player

```
Launch game
  → Select "Play Level"
  → Level loads from editor
  → Player navigates with Space/Up (jump)
  → Player dies on spike or completes level
  → Score screen displays
```

### Journey 2 — Level Editor

```
Launch game
  → Select "Level Editor"
  → Camera pan (arrow keys / mouse drag)
  → Place / remove blocks and spikes on grid
  → Save level to JSON format
  → Play-test level directly from editor
```

### Journey 3 — AI Training

```
Launch game
  → Select "Train AI"
  → System generates 1 000 random brains
  → All 1 000 agents simulate in parallel on selected level
  → Fitness (distance) computed per agent
  → Generation stats displayed (best, average, worst distance)
  → Best brain mutated 1 000× → next generation
  → After 100 generations, show best brain replay
  → User can replay best agent of any generation
```

---

## 5. Domain Model

### 5.1 World / Level

- **Grid**: 2D tile grid, each tile = 1 block unit
- **Block types**: Empty (air), Solid block, Spike
- **Camera**: scrolls horizontally following player X position
- **Level format**: JSON (custom save format)

### 5.2 Player

- **Appearance**: Red square (1×1 block), inner square inset, thin black border
- **State**: On-ground / In-air
- **Velocity**: Constant horizontal = 10.3761348998 blocks/s; vertical governed by gravity
- **Actions**: Jump (Space or Up key)
- **Rotation**: Continuous clockwise rotation when in-air
- **VFX**: Glow/bloom effect, ground-contact particle burst, gradient trail (white → grey)

### 5.3 Physics

- **Gravity**: Constant downward acceleration (tuned to match GD feel)
- **Jump**: Instantaneous vertical impulse (cancels current vertical velocity)
- **Collision**: AABB against solid blocks and spike hitboxes; death on spike contact
- **Floor**: Y=0 baseline prevents falling through world

### 5.4 Spike

- **Shape**: Triangle occupying full 1×1 block tile
- **Hitbox**: Triangle approximation for collision
- **Effect**: Instant player death on contact

### 5.5 Brain (AI)

- **Neuron**: A point placed at a fixed screen-space (relative to player) position.
  - **Type**: `block`, `spike`, or `air` → defines which tile type activates it
  - **Polarity**: `green` (ON when standing on matching tile) or `red` (ON always EXCEPT when on matching tile)
  - **State**: Active / Inactive
- **Network**: A named group of 1–N neurons connected to a circle node.
  - **Activation rule**: ALL neurons in group must be active → network fires → player jumps
  - A brain may contain multiple independent networks.
- **Brain**: The complete set of networks for one agent.
- **Generation**: A population of 1 000 brains evaluated simultaneously.

### 5.6 Evolution

- **Fitness**: Horizontal distance traveled before death (or level completion)
- **Selection**: Keep the single best brain of the generation
- **Mutation variants** (applied 1 000× to produce next generation):
  - Move one or more neuron positions (common)
  - Add or remove a neuron from a network (common)
  - Add or remove an entire network (rare)
- **Termination**: After 100 generations or level completion

---

## 6. Project Scope

### In Scope

| ID | Item | Phase |
|----|------|-------|
| S-01 | Tile-based level renderer | 1 |
| S-02 | Scrolling camera following player | 1 |
| S-03 | Level editor with grid, block/spike placement, save/load | 1 |
| S-05 | Player physics: horizontal speed, gravity, jump, collision | 1 |
| S-06 | Player visuals: styled square, glow, particles, trail | 1 |
| S-07 | Spike tiles with death detection | 1 |
| S-08 | Gradient sky background + block tint variation | 1 |
| S-09 | Visual neuron-network brain representation | 2 |
| S-10 | Parallel simulation of 1 000 agents | 2 |
| S-11 | Genetic algorithm: selection + mutation | 2 |
| S-12 | Generation stats UI | 2 |
| S-13 | Best-agent replay per generation | 2 |

### Out of Scope (v1)

- Online multiplayer
- Full GD level pack library / server
- Custom music or audio synchronization
- Mobile build
- Full GD level editor feature-parity (portals, orbs, triggers)
- Neural network weights (only positional/structural genome)

---

## 7. Functional Requirements — Phase 1: Game

### FR-P1-01 — Tile Grid Renderer
**As a** player,  
**I want** the level to be rendered as a grid of 1×1 tiles,  
**so that** all objects are spatially consistent.

- Tile size configurable (pixels per block)
- Solid blocks rendered with slight color tint variation per tile for relief
- Grid origin at world (0, 0)

---

### FR-P1-02 — Scrolling Camera
**As a** player,  
**I want** the camera to follow my horizontal position,  
**so that** I can always see what's ahead.

- Camera locks Y-axis (no vertical scroll)
- Camera offset tracks player X with no lag

---

### FR-P1-03 — Level Editor
**As a** level designer,  
**I want** a persistent editor where I can place blocks and spikes on a grid,  
**so that** I can build and iterate on custom levels.

- LMB click → place selected tile type (block or spike)
- RMB click → remove tile
- Camera pan via arrow keys or middle-mouse drag
- Toolbar: tile type selector (Block / Spike / Eraser)
- Save to file (JSON or `.gmd`-compatible)
- Load from file
- Play-test button → launches game from editor state

---

### FR-P1-05 — Player Movement
**As a** player,  
**I want** the character to move automatically to the right at the official GD speed,  
**so that** the game feels authentic.

- Constant horizontal velocity = **10.3761348998 blocks/second**
- No player control over horizontal movement

---

### FR-P1-06 — Gravity & Jump
**As a** player,  
**I want** gravity to pull me down and be able to jump,  
**so that** I can navigate obstacles.

- Gravity: constant downward acceleration (tuned to GD feel)
- Jump: Space or Up arrow → vertical impulse (only when on ground)
- One jump per ground contact (no double-jump)

---

### FR-P1-07 — Collision Detection
**As a** player,  
**I want** the game to detect when I stand on a block or hit a spike,  
**so that** physics and death work correctly.

- AABB collision with solid tiles → player rests on top
- Spike triangle hitbox → instant death on contact
- Floor (Y=0) → prevents falling out of world

---

### FR-P1-08 — Player Appearance
**As a** player,  
**I want** a visually styled character,  
**so that** the game looks polished.

- Outer square: red fill, thin black border, size = 1 block
- Inner square: smaller red square inset with black border (concentric)
- Rotation: continuous clockwise when in-air; snaps to 0° when on ground

---

### FR-P1-09 — Visual Effects
**As a** player,  
**I want** the game to have visual polish,  
**so that** it feels satisfying to play.

- **Glow/Bloom**: soft luminous halo around the player
- **Ground particles**: burst of small particles on each landing contact
- **Trail**: gradient line behind player (white at head → grey at tail), length ~0.5 s
- **Sky**: vertical gradient (top color to bottom color, configurable)
- **Block tint**: each solid tile gets a subtle random lightness offset for visual depth

---

### FR-P1-10 — Spikes
**As a** player,  
**I want** spike obstacles to be visually distinct and kill me on contact,  
**so that** hazards are clear.

- Rendered as equilateral triangle filling 1×1 tile
- Same tint variation as blocks for consistency
- Contact with any part of triangle hitbox → death

---

## 8. Functional Requirements — Phase 2: AI

### FR-P2-01 — Neuron Definition
**As an** AI designer,  
**I want** to define neurons by position, type, and polarity,  
**so that** they can sense the environment.

- Neuron has: `(screen_x_offset, screen_y_offset)` relative to player, `type ∈ {block, spike, air}`, `polarity ∈ {green, red}`
- Green neuron: active when the tile at its position matches its type
- Red neuron: active when the tile at its position does NOT match its type
- Neuron rendered as small colored circle at its position during visualization

---

### FR-P2-02 — Network Definition
**As an** AI designer,  
**I want** to group neurons into networks that trigger a jump,  
**so that** complex conditions can be represented.

- Network = ordered list of 1–N neurons + a circle output node
- Network fires (→ jump) when ALL neurons in the group are active simultaneously
- Multiple networks per brain are evaluated independently each frame
- If any network fires → player jumps (subject to ground constraint)

---

### FR-P2-03 — Brain Representation
**As an** AI designer,  
**I want** each AI agent to have a brain (genome),  
**so that** it can be stored, mutated, and compared.

- Brain = list of networks
- Brain serializable to JSON (position, type, polarity per neuron; network groupings)
- Brain can be loaded back to recreate exact behavior

---

### FR-P2-04 — Parallel Agent Simulation
**As an** AI trainer,  
**I want** 1 000 agents to be simulated simultaneously on the same level,  
**so that** training is fast.

- All 1 000 agents share the same level geometry
- Each has independent position, velocity, and brain state
- Dead agents stop advancing (distance frozen at death point)
- Rendering of all agents is **disabled by default** for performance; activatable via a debug toggle key (e.g. `V`) at runtime

---

### FR-P2-05 — Fitness Evaluation
**As an** AI trainer,  
**I want** each agent scored by distance traveled,  
**so that** better agents are selected.

- Fitness = maximum X position reached before death or level end
- Agents completing the level receive full level length as fitness

---

### FR-P2-06 — Selection & Mutation
**As an** AI trainer,  
**I want** the top brains to survive and produce 1 000 mutated children,  
**so that** each generation improves.

- Select: **top 10 brains** (highest fitness) — each produces 100 mutated children (10 × 100 = 1 000)
- Neuron positions are **continuous floats** (not grid-snapped); a neuron can sit anywhere in screen space
- Mutation operators:

| Mutation | Probability | Detail |
|----------|-------------|--------|
| Displace 1–3 neuron positions | High (~70%) | Offset drawn from **N(0, 1²)** (mean=0, σ=1 block) independently per axis |
| Add or remove a neuron in a network | Medium (~25%) | New neuron position drawn uniformly from sensor window |
| Add or remove an entire network | Low (~5%) | — |

- Mutations are applied independently per child (not accumulated)
- All 10 parent brains are preserved unchanged into the next generation (elitism)

---

### FR-P2-07 — Generation Loop
**As an** AI trainer,  
**I want** the system to run up to 100 generations automatically,  
**so that** training requires minimal intervention.

- Loop: generate population → simulate → evaluate → select → mutate → next generation
- Early stop if an agent completes the full level
- After each generation, save: best brain, generation stats

---

### FR-P2-08 — Generation Stats UI
**As an** AI trainer,  
**I want** to see stats after each generation,  
**so that** I can monitor progress.

- Displayed per generation: generation number, best fitness, average fitness, worst fitness
- Running chart of best fitness over generations
- Indicator when level is completed

---

### FR-P2-09 — Best Agent Replay
**As an** AI trainer,  
**I want** to watch the best agent of any past generation play the level,  
**so that** I can understand how the AI improved.

- After each generation, best brain is saved
- Replay UI: generation selector → launches visual playback at normal speed
- Neuron activations and network firings shown during replay

---

## 9. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | 1 000 agents simulate at ≥60 sim-steps/s on a modern laptop |
| NFR-02 | Performance | Game renders at stable 60 FPS in play mode |
| NFR-03 | Persistence | Level editor saves to disk; data survives process restart |
| NFR-04 | Persistence | All 100 generation best-brains saved to disk in JSON |
| NFR-05 | Accuracy | Player speed = exactly 10.3761348998 blocks/s; physics at 240 Hz fixed timestep |
| NFR-06 | Usability | No external install steps beyond `pip install pygame` |
| NFR-07 | Maintainability | Code separated into modules: `engine/`, `editor/`, `ai/`, `renderer/` |
| NFR-08 | Portability | Runs on macOS, Windows, Linux via Python 3.10+ |

---

## 10. Technical Constraints & Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Game/Rendering | Pygame 2.x |
| Level format storage | JSON (internal save format for editor) |
| AI genome | JSON serialization |
| Parallelism (AI) | Pure Python loop (no multiprocessing required at 1 000 agents / headless sim) |
| VFX | Pygame surfaces + per-pixel alpha (glow), particle system (custom) |

> **Physics constants** (resolved — see RD-02 in Section 12): Fixed 240 Hz timestep, `GRAVITY = -0.958 blocks/frame`, `JUMP_VELOCITY = +12.36 blocks/frame`, `PLAYER_SPEED = 10.3761348998 blocks/s`. Source: `engine/physics.py`.

---

## 11. Out of Scope

- Audio / music synchronization
- Online features, leaderboards, account system
- Mobile or browser build
- Full GD level editor feature-parity (portals, orbs, triggers)
- Wave / Ship / Ball / UFO / Robot gamemodes (cube only in v1)
- Wave portal section gameplay in `Nine Circles.gmd` (agent stops or passes through in v1)
- Neural network weights (genome is structural/positional only)
- Complex crossover/recombination between brains (single parent mutation only)
- Level pack management beyond single-level play

---

## 12. Resolved Decisions

### RD-02 — Jump Physics Constants (formerly OQ-04)

**Decision**: Option C — Official GD physics values + fixed 240 Hz physics timestep.

**Rationale**: GD levels are designed around exact physics. Any deviation makes `.gmd` levels unplayable as intended. The 240 Hz fixed timestep architecture also benefits the AI simulation (deterministic, delta-time independent).

**Implemented constants**:

```python
# engine/physics.py
PHYSICS_RATE    = 240          # Internal physics steps per second
DT              = 1.0 / 240    # Fixed physics delta time

GRAVITY         = -0.958       # blocks/frame @ 240fps  (= -229.92 blocks/s²)
JUMP_VELOCITY   = +12.36       # blocks/frame @ 240fps  (= +296.64 blocks/s)
PLAYER_SPEED    = 10.3761348998  # blocks/second (horizontal, constant)

BLOCK_SIZE_PX   = 30           # pixels per block (1 GD unit = 30 px)
```

**Game loop architecture** (fixed timestep with render interpolation):

```python
accumulator += delta_time
while accumulator >= DT:
    physics_step(DT)
    accumulator -= DT
render(interpolation=accumulator / DT)  # smooth rendering at 60fps
```

**Advantage for AI**: All 1 000 agents share the same fixed-step simulation — results are 100% deterministic regardless of frame rate or machine speed.

### RD-04 — Sélection multi-parents (anciennement OQ-02)

**Décision** : Conserver les **10 meilleurs cerveaux** de chaque génération (au lieu d'un seul).

**Rationale** : La diversité génétique est préservée en maintenant 10 parents ; chacun produit 100 enfants mutés, soit exactement 1 000 agents par génération. Les 10 parents sont également conservés tels quels (élitisme) pour éviter la régression.

**Implémentation** (`ai/evolution.py`) :

```python
ELITE_COUNT = 10        # parents survivants
POPULATION  = 1000     # taille de la population
CHILDREN_PER_PARENT = POPULATION // ELITE_COUNT  # = 100

def next_generation(population: list[Brain]) -> list[Brain]:
    ranked = sorted(population, key=lambda b: b.fitness, reverse=True)
    elites = ranked[:ELITE_COUNT]
    children = [mutate(random.choice(elites)) for _ in range(POPULATION - ELITE_COUNT)]
    return elites + children
```

---

### RD-05 — Mode visualisation IA (anciennement OQ-03)

**Décision** : La visualisation des 1 000 agents est **désactivée par défaut** ; elle peut être activée/désactivée via une touche de debug (ex. `V`) en cours de simulation.

**Rationale** : Afficher 1 000 sprites simultanément à 60 FPS représente une charge GPU/CPU significative. En mode headless (visualisation OFF), la simulation d'une génération complète doit tenir en < 60 s sur un laptop standard (NFR-01). La touche toggle permet d'observer le comportement émergent sans pénaliser les performances nominales.

---

### RD-06 — Amplitude de mutation des neurones (anciennement OQ-05)

**Décision** : Les positions des neurones sont des **flottants continus** (non alignés sur la grille). La mutation de déplacement suit une **loi normale N(0, 1²)** — centrée en 0, écart-type σ = 1 bloc — appliquée indépendamment sur chaque axe (x et y).

**Rationale** : Une distribution gaussienne permet des micro-ajustements fréquents (|Δ| < 1 bloc) et des déplacements plus larges occasionnels, ce qui est favorable à l'exploration locale tout en autorisant des sauts de configuration. Le choix σ = 1 bloc équivaut à ~68 % des mutations restant dans un rayon d'un bloc, ce qui est cohérent avec la résolution du gameplay GD.

**Implémentation** (`ai/evolution.py`) :

```python
import random, math

def mutate_position(x: float, y: float, sigma: float = 1.0) -> tuple[float, float]:
    """Déplace un neurone selon N(0, sigma²) sur chaque axe."""
    return (
        x + random.gauss(0, sigma),
        y + random.gauss(0, sigma),
    )
```

> **Note** : `sigma` est exprimé en **blocs** (1 bloc = `BLOCK_SIZE_PX` pixels). La conversion px ↔ blocs est appliquée au moment du rendu, pas dans le génome.

---

## 13. Open Questions

*Toutes les questions ouvertes sont résolues. Voir Section 12 (RD-02, RD-04, RD-05, RD-06).*

---

*Document generated by John (PM Agent) — BMAD Method v6.0.4 — 2026-03-03*  
*Updated by John (PM Agent) — 2026-03-05 — v1.4: .gmd import removed (strategic pivot), RD-01/RD-03/FR-P1-04/G-03 deleted*
