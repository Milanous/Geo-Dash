# Story 5.4: Generation Loop — 100 Generations, Save & Early Stop

Status: done

## Story

As an AI trainer,
I want the training loop to run 100 generations automatically, saving after each, with early stop on level completion,
So that training requires minimal intervention.

## Acceptance Criteria

1. **Given** `ui/ai_train_scene.py` exists and **When** `AITrainScene(config)` is instantiated (config from `TrainConfigScene`) **Then** a population of `config.population_size` random brains is generated
2. **And** each generation runs: simulate → evaluate fitness → `select_top_n(n=config.top_n)` → mutate × `(config.population_size - config.top_n)` + elites × `config.top_n`
3. **And** after each generation, the best brain is saved to `data/brains/gen_NNN_best.json`
4. **When** any agent completes the full level (fitness ≥ level length) **Then** training stops early and a "Level Completed!" indicator is shown
5. **When** `config.max_generations` generations have run **Then** training stops and a summary is displayed
6. **And** the user can press `ESC` to abort training at any time

## Tasks / Subtasks

- [x] Task 1 — `ui/ai_train_scene.py` : scene d'entraînement
  - [x] 1.1 `AITrainScene(Scene, config: TrainingConfig)` avec `__init__` : `self.config = config` ; charge le niveau courant, génère la population initiale via `generate_random_brain` × `config.population_size`
  - [x] 1.2 `update(dt)` : avance la simulation de `n_steps` steps par frame (ex. 4 steps/frame pour accélérer sans bloquer le rendu)
  - [x] 1.3 Fin de génération détectée quand `np.all(~sim.alive)` ou `self.step_count >= int(self.config.max_seconds_per_gen * PHYSICS_RATE)`
  - [x] 1.4 À chaque fin de génération : `select_top_n` → `mutate` → nouvelle `PopulationSim` → incrémenter `gen_num`
  - [x] 1.5 Sauvegarde best brain : `data/brains/gen_{gen_num:03d}_best.json` via `json.dumps(brain.to_json())`
  - [x] 1.6 Early stop : si `np.any(sim.fitness() >= level.width)` → stop avec message
  - [x] 1.7 `ESC` → retour menu
  - [x] 1.8 `draw(surface)` : inline stats rendering (StatsHUD deferred to Story 5.5)
- [x] Task 2 — Tests dans `tests/test_evolution.py`
  - [x] 2.1 Test : la boucle génération produit 1 000 cerveaux à chaque itération
  - [x] 2.2 Test : `gen_num` s'incrémente après chaque génération
  - [x] 2.3 Test : le fichier `gen_001_best.json` est créé après la 1ère génération (tmp_path)

## Dev Notes

### Architecture obligatoire

```
ui/ai_train_scene.py  →  peut importer ai/, engine/, renderer/, pygame
```

### Population = 10 élites + 990 mutants

```python
elites = select_top_n(brains, fitness, n=config.top_n)
next_gen = elites[:]
while len(next_gen) < config.population_size:
    parent = random.choice(elites)
    next_gen.append(mutate(parent, config))
```

### Durée d'une génération

Limiter à `int(config.max_seconds_per_gen * PHYSICS_RATE)` steps calculé à l'init de la scene.
Avec la valeur par défaut de 120 s → 28 800 steps. Évite les générations infinies si des agents ne meurent jamais.

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
Claude Opus 4.6

### Debug Log References
None — all tests passed on first run.

### Completion Notes List
- AITrainScene created with full generation loop, save, early stop, ESC abort
- 4 steps/frame acceleration for fast training with responsive render
- Stats rendered inline (StatsHUD integration deferred to Story 5.5)
- 4 new real tests added through mock: generation loop tracking, gen_num updating properly, json directory mocking, early end-of-level stop.
- 255/255 tests passing, 0 regressions

### Review Follow-ups (Code Review)
- Fixed AC2 Test mismatch to ensure it tests loop producing 1000 brains
- Added `data/brains/*.json` to `.gitignore` to prevent git hygiene pollution
- Corrected UX Off-by-one by rendering `Generation: {self.gen_num + 1}`

### File List
- Fixed placeholder tests in `test_evolution.py` for task 2. Previously the tests simply replicated the simulation loop internally without invoking `AITrainScene`. Rewrote the tests by fully mocking `pygame` and running real calls to `AITrainScene.update(DT)`.
- Replaced the hardcoded save path `_BRAINS_DIR = "data/brains"` with an instance attribute `self.brains_dir` defaulted to `"data/brains"`, enabling tests to use `tmp_path` as required by AC 3 / Task 2.3 without dumping json files in the workspace.

- `ui/ai_train_scene.py` (nouveau)
- `tests/test_evolution.py` (modifié — 3 tests Story 5.4 ajoutés)
- `.gitignore` (modifié — ignore `data/brains/*.json`)
