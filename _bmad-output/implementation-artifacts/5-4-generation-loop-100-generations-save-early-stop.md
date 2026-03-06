# Story 5.4: Generation Loop — 100 Generations, Save & Early Stop

Status: ready-for-dev

## Story

As an AI trainer,
I want the training loop to run 100 generations automatically, saving after each, with early stop on level completion,
So that training requires minimal intervention.

## Acceptance Criteria

1. **Given** `ui/ai_train_scene.py` exists and the user selects "Train AI" from the menu **When** training starts **Then** a population of 1 000 random brains is generated
2. **And** each generation runs: simulate → evaluate fitness → select top-10 → mutate × 990 + elites × 10 = 1 000
3. **And** after each generation, the best brain is saved to `data/brains/gen_NNN_best.json`
4. **When** any agent completes the full level (fitness ≥ level length) **Then** training stops early and a "Level Completed!" indicator is shown
5. **When** 100 generations have run **Then** training stops and a summary is displayed
6. **And** the user can press `ESC` to abort training at any time

## Tasks / Subtasks

- [ ] Task 1 — `ui/ai_train_scene.py` : scene d'entraînement
  - [ ] 1.1 `AITrainScene(Scene)` avec `__init__` : charge le niveau courant, génère la population initiale via `generate_random_brain` × 1 000
  - [ ] 1.2 `update(dt)` : avance la simulation de `n_steps` steps par frame (ex. 4 steps/frame pour accélérer sans bloquer le rendu)
  - [ ] 1.3 Fin de génération détectée quand `np.all(~sim.alive)` ou que le compteur de steps max est atteint
  - [ ] 1.4 À chaque fin de génération : `select_top_n` → `mutate` → nouvelle `PopulationSim` → incrémenter `gen_num`
  - [ ] 1.5 Sauvegarde best brain : `data/brains/gen_{gen_num:03d}_best.json` via `json.dumps(brain.to_json())`
  - [ ] 1.6 Early stop : si `np.any(sim.fitness() >= level.width)` → stop avec message
  - [ ] 1.7 `ESC` → retour menu
  - [ ] 1.8 `draw(surface)` : appelle `StatsHUD.draw(surface, stats_dict)` (Story 5.5)
- [ ] Task 2 — Tests dans `tests/test_evolution.py`
  - [ ] 2.1 Test : la boucle génération produit 1 000 cerveaux à chaque itération
  - [ ] 2.2 Test : `gen_num` s'incrémente après chaque génération
  - [ ] 2.3 Test : le fichier `gen_001_best.json` est créé après la 1ère génération (tmp_path)

## Dev Notes

### Architecture obligatoire

```
ui/ai_train_scene.py  →  peut importer ai/, engine/, renderer/, pygame
```

### Population = 10 élites + 990 mutants

```python
elites = select_top_n(brains, fitness, n=10)
next_gen = elites[:]
while len(next_gen) < 1000:
    parent = random.choice(elites)
    next_gen.append(mutate(parent))
```

### Durée d'une génération

Limiter à `MAX_STEPS_PER_GEN = PHYSICS_RATE * 10` (= 2 400 steps = 10 s de jeu) pour éviter les générations infinies si des agents ne meurent jamais.

### Format fichier best brain

```json
{
  "version": 1,
  "generation": 1,
  "fitness": 42.3,
  "networks": [...]
}
```
Wrapper les données `brain.to_json()` avec `"generation"` et `"fitness"` avant d'écrire.

### Scene accélérée

Pour que l'entraînement soit rapide tout en gardant le rendu réactif, faire 4–8 steps par `update()`. Le rendu (draw) tourne à 60 FPS mais la simulation avance plus vite.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4]
- [Source: ai/simulation.py] PopulationSim (Story 5.1)
- [Source: ai/evolution.py] select_top_n, mutate, generate_random_brain (Story 5.3)
- [Source: ai/brain.py] to_json (Story 4.3)

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ui/ai_train_scene.py` (nouveau)
- `tests/test_evolution.py` (modifié)
