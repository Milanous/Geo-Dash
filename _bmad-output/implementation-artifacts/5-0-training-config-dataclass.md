# Story 5.0: TrainingConfig — Hyperparameter Container

Status: ready-for-dev

## Story

As an AI trainer,
I want all training hyperparameters in a single dataclass,
So that I can configure them from the UI and pass them to all AI modules without hardcoded values.

## Acceptance Criteria

1. **Given** `ai/training_config.py` exists with `TrainingConfig` **When** it is imported **Then** it is a `@dataclass` with the following fields and default values:
   - `population_size: int = 1000`
   - `max_generations: int = 100`
   - `top_n: int = 10`
   - `mutation_sigma: float = 1.0`
   - `max_seconds_per_gen: float = 120.0`
   - `p_move: float = 0.70`
   - `p_neuron: float = 0.25`
2. **When** `TrainingConfig()` is instantiated with default values **Then** no exception is raised
3. **When** `TrainingConfig(p_move=0.80, p_neuron=0.30)` is instantiated **Then** a `ValueError` is raised (sum > 1.0)
4. **When** `TrainingConfig(top_n=50, population_size=10)` is instantiated **Then** a `ValueError` is raised (top_n >= population_size)
5. **When** `TrainingConfig(population_size=0)` is instantiated **Then** a `ValueError` is raised
6. **And** `ai/training_config.py` imports neither `pygame` nor any renderer module
7. **And** `tests/test_training_config.py` covers all above cases with passing tests

## Tasks / Subtasks

- [ ] Task 1 — `ai/training_config.py` : dataclass `TrainingConfig`
  - [ ] 1.1 Définir `@dataclass` avec les 7 champs listés ci-dessus et leurs valeurs par défaut
  - [ ] 1.2 `__post_init__(self)` — validations :
    - `if self.p_move + self.p_neuron > 1.0: raise ValueError(...)`
    - `if self.top_n >= self.population_size: raise ValueError(...)`
    - `if self.population_size < 1: raise ValueError(...)`
    - `if self.max_generations < 1: raise ValueError(...)`
    - `if self.mutation_sigma <= 0: raise ValueError(...)`
    - `if self.max_seconds_per_gen <= 0: raise ValueError(...)`
  - [ ] 1.3 ZERO import `pygame`, `renderer`, ou tout module non-stdlib

- [ ] Task 2 — `tests/test_training_config.py`
  - [ ] 2.1 Test : `TrainingConfig()` crée une instance avec toutes les valeurs par défaut correctes
  - [ ] 2.2 Test : `p_move + p_neuron > 1.0` → `ValueError`
  - [ ] 2.3 Test : `top_n >= population_size` → `ValueError`
  - [ ] 2.4 Test : `population_size < 1` → `ValueError`
  - [ ] 2.5 Test : `mutation_sigma <= 0` → `ValueError`
  - [ ] 2.6 Test : import guard — `training_config.py` n'importe pas `pygame`

## Dev Notes

### Rôle de TrainingConfig dans l'architecture

```
TrainConfigScene (ui/)
    └─ crée TrainingConfig avec valeurs saisies par l'utilisateur
            └─ passé à AITrainScene(config)
                    ├─ PopulationSim(brains, level, config)
                    ├─ select_top_n(brains, fitness, n=config.top_n)
                    └─ mutate(brain, config)
```

Aucune valeur d'hyperparamètre n'est hardcodée dans le code de production.

### Règle d'import

```
ai/training_config.py → stdlib uniquement (dataclasses, rien d'autre)
```

### p_network implicite

```python
# p_network = 1.0 - p_move - p_neuron  (implicite, pas stocké dans la dataclass)
# Utilisé dans mutate() comme : if r >= p_move + p_neuron → mutation réseau
```

### Structure fichier

```
ai/
    training_config.py   ← À CRÉER (prérequis de 5.0b, 5.1, 5.3, 5.4)
tests/
    test_training_config.py  ← À CRÉER
```

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-03-07.md]
- Prérequis pour : Story 5.0b, Story 5.1, Story 5.3, Story 5.4

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/training_config.py` (nouveau)
- `tests/test_training_config.py` (nouveau)
