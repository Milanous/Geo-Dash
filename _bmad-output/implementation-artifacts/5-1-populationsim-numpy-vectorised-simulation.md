# Story 5.1: PopulationSim — NumPy Vectorised Simulation

Status: done

## Story

As an AI trainer,
I want 1 000 agents simulated simultaneously using NumPy vectorised operations,
So that a full generation completes in under 60 seconds.

## Acceptance Criteria

1. **Given** `ai/simulation.py` exists with `PopulationSim` **When** `PopulationSim(brains, level, config)` is instantiated **Then** `self.x`, `self.y`, `self.vy`, `self.alive` are `np.ndarray` of shape `(config.population_size,)`
2. **When** `sim.step(DT)` is called once **Then** `self.x[i]` increases by `PLAYER_SPEED * DT` for all alive agents
3. **And** `self.vy[i]` decreases by `GRAVITY` for all alive agents (gravity = negative → vy decreases)
4. **And** agents with `alive[i] == False` do not move (position frozen)
5. **When** an agent's bounding box overlaps a `SPIKE` tile **Then** `alive[i]` is set to `False`
6. **And** `ai/simulation.py` does not import `pygame`
7. **And** a benchmark test in `tests/test_evolution.py` verifies 1 000 agents × simulation completes in < 60 s

## Tasks / Subtasks

- [x] Task 1 — `ai/simulation.py` : class `PopulationSim`
  - [x] 1.1 `__init__(self, brains: list[Brain], level: World, config: TrainingConfig)` — initialise les arrays NumPy : `x`, `y`, `vy` de shape `(n,)` float64 ; `alive` de shape `(n,)` bool
    - `self.config = config`
    - `self.max_steps = int(config.max_seconds_per_gen * PHYSICS_RATE)`
  - [x] 1.2 `step(self, dt: float) -> None`
    - Gravité vectorisée : `self.vy[self.alive] += GRAVITY * dt` *(attention : `GRAVITY` est négatif dans le projet — `vy` diminue)*
    - Position Y : `self.y[self.alive] += self.vy[self.alive] * dt`
    - Position X : `self.x[self.alive] += PLAYER_SPEED * dt`
    - Sol clamp : `self.y = np.maximum(self.y, 0.0)` ; si `y[i]` était < 0 → `vy[i] = 0`
    - Détection spike : `_resolve_spikes()` — vectorisée autant que possible
    - Évaluation cerveaux : `_evaluate_brains()` — boucle Python sur `np.where(self.alive)[0]`
  - [x] 1.3 `_resolve_spikes(self) -> None` — pour chaque agent alive, vérifier la tile à `(x[i], y[i])` ; si SPIKE → `alive[i] = False`
  - [x] 1.4 `_evaluate_brains(self) -> None` — pour chaque agent alive, appeler `brain.should_jump(x[i], y[i], level)` ; si True → `vy[i] = JUMP_VELOCITY`
  - [x] 1.5 `fitness(self) -> np.ndarray` — retourne `self.x.copy()` (distance = fitness)
  - [x] 1.6 ZERO import `pygame`
- [x] Task 2 — `tests/test_evolution.py` : tests headless
  - [x] 2.1 Test : `PopulationSim` initialise arrays de bonne forme
  - [x] 2.2 Test : agents morts ne se déplacent pas après `step()`
  - [x] 2.3 Test : agent vivant avance de `PLAYER_SPEED * dt` en X à chaque step
  - [x] 2.4 Test : agent touche SPIKE → `alive=False`
  - [x] 2.5 Test : `fitness()` retourne les positions X courantes
  - [x] 2.6 Test benchmark : 1 000 agents × 7 200 steps (30 s de jeu simulé avec config par défaut) < 60 s
  - [x] 2.7 Test : import guard — `simulation.py` n'importe pas `pygame`

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
ai/simulation.py  →  peut importer engine/, numpy
ai/simulation.py  →  ne peut PAS importer renderer/, pygame
```

### Constantes physiques à importer

```python
from engine.physics import GRAVITY, PLAYER_SPEED, JUMP_VELOCITY, DT, PHYSICS_RATE
```

Valeurs : `GRAVITY = -0.958`, `PLAYER_SPEED = 10.3761348998`, `JUMP_VELOCITY = 12.36`, `DT = 1/240`

**Attention `GRAVITY`** : la constante est négative dans ce projet. `vy += GRAVITY` fait diminuer la vitesse (chute). Ne pas inverser le signe.

### Structure vectorisée [Source: architecture.md#Catégorie 5]

```python
import numpy as np
from engine.physics import GRAVITY, PLAYER_SPEED, JUMP_VELOCITY
from engine.world import TileType, World
from ai.brain import Brain

class PopulationSim:
    def __init__(self, brains: list[Brain], level: World) -> None:
        self.n = len(brains)
        self.x     = np.full(self.n, 5.0)           # départ x=5 blocs
        self.y     = np.full(self.n, 2.0)           # départ y=2 blocs
        self.vy    = np.zeros(self.n)
        self.alive = np.ones(self.n, dtype=bool)
        self.brains = brains
        self.level = level
```

### Boucle `_evaluate_brains` — performance

La boucle Python sur 1 000 cerveaux est inévitable (la logique neuronale n'est pas vectorisable sans compilation). Elle est acceptable car : `world.tile_at()` est O(1), les neurones sont peu nombreux par cerveau, et l'essentiel de la charge (physique) est vectorisé.

### Benchmark < 60 s

Utiliser `time.perf_counter()` pour le test benchmark. Si le test échoue systématiquement sur machine lente → ajuster le seuil ou décorer avec `@pytest.mark.slow` et documenter.

### Structure physique

```
ai/
    neuron.py    ← 4.1 ✅
    network.py   ← 4.2 ✅
    brain.py     ← 4.3 ✅
    simulation.py ← À CRÉER
tests/
    test_evolution.py ← À CRÉER (accueillera aussi 5.2, 5.3)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Catégorie 5]
- [Source: engine/physics.py] constantes physiques
- [Source: ai/brain.py] interface Brain (Story 4.3)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
- Spike test: agent falls to y=0 before reaching spike at y=2 → moved spike to floor level (row 0)
- Import guard: docstring containing "import pygame" text triggered false positive → switched to AST-based check
- np.False_ identity: `np.False_ is False` returns False → use `not sim.alive[0]` instead

### Completion Notes List
- Stories 4.1-4.3 (neuron, network, brain) implemented as prerequisites — they were not yet in the codebase
- All 290 tests pass with 0 regressions
- Benchmark: 1000 agents × 7200 steps completes in ~5s

### File List

- `ai/neuron.py` (nouveau — prerequisite 4.1)
- `ai/network.py` (nouveau — prerequisite 4.2)
- `ai/brain.py` (nouveau — prerequisite 4.3)
- `ai/simulation.py` (nouveau)
- `tests/test_brain.py` (nouveau — tests 4.1-4.3)
- `tests/test_evolution.py` (nouveau)
