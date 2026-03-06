# Story 5.2: Fitness Evaluation

Status: ready-for-dev

## Story

As an AI trainer,
I want each agent scored by the maximum distance it reached,
So that better agents can be identified and selected.

## Acceptance Criteria

1. **Given** a `PopulationSim` that has run to completion **When** `sim.fitness()` is called **Then** it returns a `np.ndarray` of shape `(n,)` where each value is the agent's maximum X position reached in blocks
2. **And** an agent that reached the end of the level receives the full level length as fitness
3. **And** agents that never moved (died at start) have fitness ≈ 0
4. **And** `fitness()` is a pure read — it does not modify simulation state
5. **And** `tests/test_evolution.py` verifies fitness values for mock simulation results

## Tasks / Subtasks

- [ ] Task 1 — Améliorer `PopulationSim` dans `ai/simulation.py`
  - [ ] 1.1 Ajouter `self.max_x: np.ndarray` — array de shape `(n,)` initialisé à `self.x.copy()`, mis à jour à chaque step : `self.max_x = np.maximum(self.max_x, self.x)`
  - [ ] 1.2 `fitness(self) -> np.ndarray` retourne `self.max_x.copy()` (distance max atteinte, pas la position courante)
  - [ ] 1.3 Agents qui atteignent `world.width` → leur fitness est capée à `world.width` et leur `alive[i]` peut rester True (fin de niveau)
- [ ] Task 2 — Ajouter tests dans `tests/test_evolution.py`
  - [ ] 2.1 Test : `fitness()` après 0 steps retourne les positions initiales
  - [ ] 2.2 Test : si un agent avance puis meurt, `fitness()` retourne sa position max (pas sa position de mort si elle est plus faible)
  - [ ] 2.3 Test : `fitness()` est pure — deux appels successifs retournent le même résultat
  - [ ] 2.4 Test : agent mort au départ → fitness ≈ position initiale (5.0)

## Dev Notes

### Fitness = distance maximale, pas distance finale

Un agent peut avancer loin puis être repoussé... non, le déplacement est unidirectionnel (X augmente toujours). Mais un agent peut mourir et sa position est gelée. `max_x` capture le meilleur moment.

En pratique dans ce projet : `x` ne diminue jamais (`PLAYER_SPEED > 0`), donc `max_x == x_at_death` pour les agents morts. Néanmoins, tracker `max_x` est meilleure pratique et prépare à des variantes futures.

### Modification de `PopulationSim` — note

Story 5.1 livre `fitness() = self.x.copy()`. Cette story **remplace** cette implémentation par `self.max_x.copy()` et ajoute le tracking. Ne pas casser les tests 5.1 existants — vérifier que le comportement reste cohérent.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.2]
- [Source: ai/simulation.py] `PopulationSim` (Story 5.1)
- [Source: tests/test_evolution.py] tests existants Story 5.1

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/simulation.py` (modifié — max_x tracking + fitness update)
- `tests/test_evolution.py` (modifié — tests fitness ajoutés)
