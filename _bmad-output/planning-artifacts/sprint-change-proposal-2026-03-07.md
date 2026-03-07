# Sprint Change Proposal — Configurable AI Hyperparameters

**Date:** 2026-03-07  
**Author:** Bob (Scrum Master)  
**Status:** Approved  
**Scope:** Moderate  

---

## Section 1 — Issue Summary

### Problem Statement

The current Epic 5 plan hardcodes all AI training hyperparameters directly in code:

- Population size: `1 000` (hardcoded in `PopulationSim.__init__`)
- Max generations: `100` (hardcoded in `AITrainScene`)
- Top-N selection: `10` (hardcoded in `select_top_n(n=10)`)
- Mutation sigma: `1.0` (hardcoded in `mutate()`)
- Max seconds per generation: `10.0` s (hardcoded as `PHYSICS_RATE * 10 = 2 400 steps`)
- Mutation probabilities: `70% / 25% / 5%` (hardcoded in `mutate()`)

### Context

This was identified **before any Epic 5 story was implemented** (all stories are `ready-for-dev`). The user (Milan) wants to experiment with different hyperparameter sets at runtime — without modifying code — as part of the learning/exploration goal of the project (see PRD §2, G-05/G-06).

### Evidence

- Story 5.1 `PopulationSim.__init__`: `np.full(self.n, ...)` initialized from hardcoded `brains` list of 1 000
- Story 5.3 `mutate()`: `r < 0.70`, `np.random.normal(0, 1.0)` hardcoded
- Story 5.4 `AITrainScene`: `MAX_STEPS_PER_GEN = PHYSICS_RATE * 10`, population `× 1 000` hardcoded

---

## Section 2 — Impact Analysis

### Epic Impact

| Epic | Impact |
|------|--------|
| Epic 1–3 | None |
| Epic 4 (Cerveaux IA) | None — `neuron.py`, `network.py`, `brain.py` unchanged |
| Epic 5 (Entraînement) | **Modified** — 5.1, 5.3, 5.4 updated; 2 new stories added |
| Epic 6 (Level/UX) | None |

### Story Impact

| Story | Change | Type |
|-------|--------|------|
| 5.0 (NEW) | `ai/training_config.py` — `TrainingConfig` dataclass | New story |
| 5.0b (NEW) | `ui/train_config_scene.py` — hyperparameter selection UI | New story |
| 5.1 | `PopulationSim(brains, level, config)` — signature update | Modify |
| 5.3 | `mutate(brain, config)` + `select_top_n(brains, fitness, n)` | Modify |
| 5.4 | `AITrainScene(config)` — drives all training parameters | Modify |
| 5.2, 5.5, 5.6 | No change | Unchanged |

### Artifact Conflicts

| Artifact | Change needed |
|----------|---------------|
| PRD §4 Journey 3 | Add config screen step before training launch |
| PRD FR-P2-04 | "config.population_size agents" instead of "1 000" |
| PRD FR-P2-06 | config-driven top-N, sigma, probabilities |
| PRD FR-P2-07 | "config.max_generations" instead of "100" |
| Architecture arborescence `ui/` | Add `train_config_scene.py` |
| Architecture §IA | Add `TrainingConfig` pattern description |

### Technical Impact

- New file: `ai/training_config.py` (no pygame, pure stdlib)
- New file: `ui/train_config_scene.py` (pygame UI, keyboard/mouse input)
- Modified: `ai/evolution.py` (function signatures)
- Modified: `ai/simulation.py` (constructor signature)
- Modified: `ui/ai_train_scene.py` (constructor + all hardcoded values)
- Import rule respected: `ai/training_config.py` imports nothing from pygame/renderer

---

## Section 3 — Recommended Approach

**Option 1 — Direct Adjustment** ✅ Selected

All Epic 5 stories are `ready-for-dev` (not yet implemented). The cost of this change is simply updating story files before any code is written. No rollback needed.

- **Effort:** Medium (2 new story files + 3 story updates + 2 artifact updates)
- **Risk:** Low — clean separation, no existing code to break
- **Timeline impact:** +1 story in Epic 5 sequence (story 5.0 + 5.0b prepend)

---

## Section 4 — Detailed Change Proposals

### Stories — New

---

#### Story 5.0 (NEW): `ai/training_config.py` — TrainingConfig dataclass

```
Story 5.0: TrainingConfig — Hyperparameter Container

As an AI trainer,
I want all training hyperparameters in a single dataclass,
So that I can configure them from the UI and pass them to all AI modules.

Acceptance Criteria:
- ai/training_config.py contains TrainingConfig @dataclass with:
    population_size: int = 1000
    max_generations: int = 100
    top_n: int = 10
    mutation_sigma: float = 1.0
    max_seconds_per_gen: float = 120.0
    p_move: float = 0.70
    p_neuron: float = 0.25
    # p_network = 1.0 - p_move - p_neuron (implicit)
- __post_init__ validates:
    p_move + p_neuron <= 1.0  (else ValueError)
    top_n < population_size   (else ValueError)
    population_size >= 1      (else ValueError)
- Zero import pygame
- tests/test_training_config.py validates default values and all error conditions

File list:
  - ai/training_config.py (new)
  - tests/test_training_config.py (new)
```

---

#### Story 5.0b (NEW): `ui/train_config_scene.py` — Hyperparameter Selection UI

```
Story 5.0b: TrainConfigScene — Hyperparameter Selection UI

As a user,
I want to configure training hyperparameters from the interface before
launching AI training,
So that I can experiment without modifying the code.

Acceptance Criteria:
1. Given Select "Train AI" from main menu
   When TrainConfigScene loads
   Then 6 editable fields displayed with default values:
     - Population size       (default: 1000)
     - Max generations       (default: 100)
     - Top-N selection       (default: 10)
     - Mutation sigma        (default: 1.0)
     - Max seconds/gen       (default: 120.0)
     - P(move) / P(neuron)   (default: 0.70 / 0.25)

2. When user clicks a field and types
   Then field shows new value (digits, dot, backspace supported)

3. When user presses Enter or clicks "Launch Training"
   Then TrainingConfig is constructed from entered values
   And scene transitions to AITrainScene(config=that_config)

4. When values are invalid (p_move + p_neuron > 1.0, top_n >= population, etc.)
   Then inline error message displayed
   And training does not launch

5. When user presses ESC
   Then scene returns to main menu

Tasks:
- Task 1: ui/train_config_scene.py — TrainConfigScene(Scene)
  - Field list: [(label, attr_name, type, default), ...]
  - Active field selection by mouse click
  - Keyboard input: digits, dot, backspace
  - Validation on submit via TrainingConfig.__post_init__
  - Transition to AITrainScene(config)
- Task 2: tests/test_train_config_scene.py (headless)
  - Test: default values correct at init
  - Test: validation rejects p_move + p_neuron > 1.0
  - Test: validation rejects top_n >= population_size

File list:
  - ui/train_config_scene.py (new)
  - tests/test_train_config_scene.py (new)
```

---

### Stories — Modified

---

#### Story 5.1: `PopulationSim` — signature update

```
Section: Acceptance Criteria 1
OLD: PopulationSim(brains, level)
NEW: PopulationSim(brains: list[Brain], level: World, config: TrainingConfig)

Section: Task 1.1
OLD: __init__(self, brains: list[Brain], level: World)
NEW: __init__(self, brains: list[Brain], level: World, config: TrainingConfig)
     → self.config = config
     → self.max_steps = int(config.max_seconds_per_gen * PHYSICS_RATE)

Section: Task 1.2 — step() timeout
OLD: MAX_STEPS_PER_GEN = PHYSICS_RATE * 10  (2 400 steps)
NEW: self.max_steps = int(config.max_seconds_per_gen * PHYSICS_RATE)  (28 800 at default)

Section: Test 2.6
OLD: 1 000 agents × 2 400 steps (10 s) < 60 s
NEW: 1 000 agents × 7 200 steps (30 s simulé, sous-ensemble) < 60 s

Imports added: from ai.training_config import TrainingConfig
```

---

#### Story 5.3: `evolution.py` — signature update

```
Section: Acceptance Criteria 1
OLD: select_top_n(brains, fitness, n=10)
NEW: select_top_n(brains, fitness, n: int)  — no default

Section: Acceptance Criteria 2
OLD: mutate(brain) → proba 70/25/5, sigma=1.0
NEW: mutate(brain, config: TrainingConfig) → Brain
     r < config.p_move     → move neurons (N(0, config.mutation_sigma²))
     r < config.p_move + config.p_neuron  → add/remove neuron
     else                  → add/remove network

Section: Task 1.1
OLD: select_top_n(brains: list[Brain], fitness: np.ndarray, n: int = 10)
NEW: select_top_n(brains: list[Brain], fitness: np.ndarray, n: int)

Section: Task 1.2
OLD: mutate(brain: Brain) -> Brain
     r < 0.70, r < 0.95, np.random.normal(0, 1.0)
NEW: mutate(brain: Brain, config: TrainingConfig) -> Brain
     r < config.p_move
     r < config.p_move + config.p_neuron
     np.random.normal(0, config.mutation_sigma)

Imports added: from ai.training_config import TrainingConfig
```

---

#### Story 5.4: `AITrainScene` — config-driven

```
Section: Acceptance Criteria 1
OLD: population of 1 000 random brains is generated
NEW: population of config.population_size random brains generated from
     TrainingConfig passed by TrainConfigScene

Section: Acceptance Criteria 2
OLD: select top-10 → mutate × 990 + elites × 10 = 1 000
NEW: select_top_n(brains, fitness, n=config.top_n)
     elites × config.top_n + mutate × (config.population_size - config.top_n)

Section: Acceptance Criteria 4
OLD: 100 generations → stop
NEW: config.max_generations generations → stop

Section: Task 1.1
OLD: AITrainScene(Scene) __init__: génère population × 1 000
NEW: AITrainScene(Scene, config: TrainingConfig) __init__
     self.config = config
     génère population × config.population_size
     MAX_STEPS = int(config.max_seconds_per_gen * PHYSICS_RATE)

Section: Task 1.3
OLD: compteur de steps max = PHYSICS_RATE * 10
NEW: self.step_count >= int(self.config.max_seconds_per_gen * PHYSICS_RATE)

Section: Dev Notes population snippet
OLD: select_top_n(brains, fitness, n=10) / while len(next_gen) < 1000
NEW: select_top_n(brains, fitness, n=config.top_n)
     while len(next_gen) < config.population_size

Imports added: from ai.training_config import TrainingConfig
```

---

### Artifacts — Modified

#### PRD §4 Journey 3

```
OLD:
  Launch game → Select "Train AI"
  → System generates 1 000 random brains
  → All 1 000 agents simulate in parallel…

NEW:
  Launch game → Select "Train AI"
  → Config screen: user sets hyperparameters
    (population size, max generations, top-N, mutation sigma,
     max seconds/gen, mutation probabilities) — defaults pre-filled
  → User clicks "Launch Training"
  → System generates config.population_size random brains
  → All agents simulate in parallel…
```

#### PRD FR-P2-04, FR-P2-06, FR-P2-07

```
FR-P2-04: "config.population_size agents" (default 1 000, configurable from UI)
FR-P2-06: top-N = config.top_n (default 10); sigma = config.mutation_sigma (default 1.0);
          probabilities = config.p_move / config.p_neuron
FR-P2-07: up to config.max_generations (default 100)
```

#### Architecture — arborescence `ui/`

```
OLD:
├── ui/
│   ├── hud.py
│   └── menu.py

NEW:
├── ui/
│   ├── hud.py
│   ├── menu.py
│   └── train_config_scene.py   ← nouveau
```

#### Architecture — nouvelle note §IA

```
TrainingConfig (ai/training_config.py) — dataclass centralisée contenant
tous les hyperparamètres d'entraînement. Instanciée par TrainConfigScene,
passée à AITrainScene → PopulationSim, mutate(), select_top_n().
Aucun hyperparamètre d'entraînement n'est hardcodé dans le code de prod.
Import rule: ai/training_config.py n'importe ni pygame ni renderer/.
```

---

## Section 5 — Implementation Handoff

**Scope classification: Moderate**

### Nouvelle séquence Epic 5

```
5.0   TrainingConfig dataclass          → dev (prérequis de tout le reste)
5.0b  TrainConfigScene UI               → dev (dépend de 5.0)
5.1   PopulationSim (modifié)           → dev (dépend de 5.0)
5.2   Fitness evaluation                → dev (inchangé)
5.3   Evolution top-N + mutate (modifié)→ dev (dépend de 5.0)
5.4   Generation loop (modifié)         → dev (dépend de 5.0, 5.0b, 5.1, 5.3)
5.5   Generation stats HUD              → dev (inchangé)
5.6   Best agent replay                 → dev (inchangé)
```

### Responsabilités

| Rôle | Action |
|------|--------|
| SM (Bob) | Mettre à jour sprint-status.yaml, créer story files 5.0 et 5.0b, mettre à jour 5.1/5.3/5.4 |
| Dev (Amelia) | Implémenter dans l'ordre 5.0 → 5.0b → 5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 5.6 |
| PM | Mettre à jour PRD §4 et FR-P2-04/06/07 |
| Architect | Mettre à jour architecture §arborescence ui/ et §IA |

### Success criteria

- [ ] `TrainingConfig` importable depuis `ai/training_config.py` avec valeurs par défaut correctes
- [ ] `TrainConfigScene` s'affiche au clic "Train AI" avec tous les champs pré-remplis
- [ ] Valeurs invalides bloquent le lancement avec message d'erreur
- [ ] `AITrainScene` reçoit et utilise le `config` pour toutes ses constantes
- [ ] Aucune valeur hardcodée dans `evolution.py`, `simulation.py`, `ai_train_scene.py`
- [ ] Tous les tests passent en headless

---

*Généré par Bob (Scrum Master) — Workflow Correct Course — 2026-03-07*
