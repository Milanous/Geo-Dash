# Story 5.0b: TrainConfigScene — Hyperparameter Selection UI

Status: complete

## Story

As a user,
I want to configure training hyperparameters from the interface before launching AI training,
So that I can experiment with different settings without modifying the code.

## Acceptance Criteria

1. **Given** the user selects "Train AI" from the main menu **When** `TrainConfigScene` loads **Then** a Pygame screen displays 6 editable fields with their default values:
   - Population size (default: 1000)
   - Max generations (default: 100)
   - Top-N selection (default: 10)
   - Mutation sigma (default: 1.0)
   - Max seconds/gen (default: 120.0)
   - P(move) / P(neuron) (default: 0.70 / 0.25)
2. **When** the user clicks a field **Then** the field becomes active (visually highlighted)
3. **When** the user types in an active field **Then** the field accepts digits, dot, and backspace
4. **When** the user presses Enter or clicks "Launch Training" **Then** a `TrainingConfig` is constructed with the entered values **And** the scene transitions to `AITrainScene(config=that_config)`
5. **When** entered values are invalid (e.g. `p_move + p_neuron > 1.0`, `top_n >= population_size`) **Then** an inline error message is displayed below the offending field **And** the training does not launch
6. **When** the user presses ESC **Then** the scene returns to the main menu

## Tasks / Subtasks

- [x] Task 1 — `ui/train_config_scene.py` : `TrainConfigScene(Scene)`
  - [x] 1.1 Définir la liste des champs :
    ```python
    FIELDS = [
        ("Population size",   "population_size", int,   1000),
        ("Max generations",   "max_generations", int,   100),
        ("Top-N selection",   "top_n",           int,   10),
        ("Mutation sigma",    "mutation_sigma",  float, 1.0),
        ("Max seconds/gen",   "max_seconds_per_gen", float, 120.0),
        ("P(move)",           "p_move",          float, 0.70),
        ("P(neuron)",         "p_neuron",        float, 0.25),
    ]
    ```
  - [x] 1.2 `__init__` : initialiser `self.values = {attr: str(default) for ...}` ; `self.active_field = None` ; `self.error_msg = ""`
  - [x] 1.3 `handle_events(events)` :
    - `MOUSEBUTTONDOWN` → déterminer quel champ est cliqué → `self.active_field = attr`
    - `KEYDOWN` sur champ actif :
      - chiffres / point → append à `self.values[active_field]`
      - BACKSPACE → retirer dernier caractère
      - RETURN/KP_ENTER → appeler `_try_launch()`
      - ESCAPE → retour menu
  - [x] 1.4 `_try_launch(self)` :
    - Convertir `self.values` vers les types corrects (int/float)
    - Tenter `TrainingConfig(**kwargs)`
    - Si `ValueError` → afficher message dans `self.error_msg`, ne pas changer de scène
    - Si succès → `self.next_scene = AITrainScene(config=config)`
  - [x] 1.5 `draw(surface)` :
    - Fond noir, titre "AI Training Configuration"
    - Pour chaque champ : label à gauche, rectangle de saisie à droite
    - Champ actif : bordure colorée
    - `self.error_msg` en rouge sous les champs si non vide
    - Bouton "Launch Training" en bas

- [x] Task 2 — `tests/test_train_config_scene.py` (headless)
  - [x] 2.1 Test : valeurs par défaut correctes à l'init (`self.values` contient les bonnes valeurs string)
  - [x] 2.2 Test : `_try_launch()` avec `p_move=0.8, p_neuron=0.3` → `error_msg` non vide, pas de `next_scene`
  - [x] 2.3 Test : `_try_launch()` avec `top_n=50, population_size=10` → `error_msg` non vide
  - [x] 2.4 Test : `_try_launch()` avec valeurs valides → `next_scene` est une instance de `AITrainScene`

## Dev Notes

### Règle d'import

```
ui/train_config_scene.py  →  peut importer pygame, ai/, engine/
```

### Pattern Scene

```python
from ui.scene import Scene
from ai.training_config import TrainingConfig
from ui.ai_train_scene import AITrainScene   # import local pour la transition

class TrainConfigScene(Scene):
    def __init__(self) -> None: ...
    def handle_events(self, events): ...
    def update(self, dt: float): ...
    def draw(self, surface): ...
```

### Tests headless

Les tests **ne doivent pas** instancier de surface Pygame ni appeler `pygame.init()`. Tester uniquement la logique de validation via `_try_launch()` en mockant ou en testant directement l'état des attributs.

```python
# Exemple test headless
def test_invalid_probabilities():
    scene = TrainConfigScene.__new__(TrainConfigScene)
    scene.values = {
        "population_size": "1000", "max_generations": "100", "top_n": "10",
        "mutation_sigma": "1.0", "max_seconds_per_gen": "120.0",
        "p_move": "0.80", "p_neuron": "0.30"
    }
    scene.error_msg = ""
    scene.next_scene = None
    scene._try_launch()
    assert scene.error_msg != ""
    assert scene.next_scene is None
```

### Entrée numérique

Accepter uniquement : chiffres `0-9`, `.` (une seule fois par champ), backspace.  
Bloquer les lettres et caractères spéciaux.

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-03-07.md]
- Dépend de : Story 5.0 (`TrainingConfig`)
- Précède : Story 5.4 (`AITrainScene`)
- [Source: ui/scene.py] interface Scene ABC

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (Copilot Agent — Amelia)

### Debug Log References
None

### Completion Notes List
- All 7 FIELDS defined with (label, attr, type, default)
- `__init__` sets `values`, `active_field`, `error_msg`; lazy-inits fonts
- `handle_events` handles MOUSEBUTTONDOWN (field click + button click), KEYDOWN (digits, dot, backspace, Enter, Esc)
- `_try_launch` converts values, constructs `TrainingConfig`, catches `ValueError` for inline error; uses `try/except ImportError` for `AITrainScene` (Story 5.4 not yet implemented)
- `draw` renders title, labelled input fields, active-field highlight, error in red, Launch button with hover
- 9 headless tests: 2 default-values, 2 invalid-probabilities, 2 invalid-top_n, 1 valid-launch (mocked AITrainScene), 1 empty-field, 1 non-numeric
- Full suite: 262 passed, 0 failed

### File List

- `ui/train_config_scene.py` (nouveau)
- `tests/test_train_config_scene.py` (nouveau)
