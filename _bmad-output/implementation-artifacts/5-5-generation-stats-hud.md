# Story 5.5: Generation Stats HUD

Status: done

## Story

As an AI trainer,
I want a live stats overlay showing generation progress,
So that I can monitor whether the AI is improving.

## Acceptance Criteria

1. **Given** `ui/hud.py` exists with a `StatsHUD` widget **When** `StatsHUD.draw(surface, stats)` is called **Then** the following are displayed: generation number, best/avg/worst fitness, alive count
2. **And** a running line chart shows best fitness over all completed generations
3. **And** an "ALIVE: NNN" counter shows how many agents are still running
4. **And** a "Press V to toggle agent view" hint is displayed
5. **When** `V` is pressed **Then** alive agents are rendered as semi-transparent red squares
6. **And** `StatsHUD` does not import from `ai/simulation.py` directly — it receives a plain stats dict

## Tasks / Subtasks

- [x] Task 1 — `ui/hud.py` : class `StatsHUD`
  - [x] 1.1 `StatsHUD.__init__()` : initialise la liste `self.history: list[float]` (best fitness par génération)
  - [x] 1.2 `update(stats: dict) -> None` : met à jour `self.history` avec `stats["best_fitness"]` si génération terminée
  - [x] 1.3 `draw(surface: pygame.Surface, stats: dict) -> None`
    - Affiche : `"Gen {gen} / 100"`, `"Best: {best:.1f}"`, `"Avg: {avg:.1f}"`, `"Worst: {worst:.1f}"`, `"ALIVE: {alive}"`
    - Dessine le line chart de `self.history` dans un mini-panneau (50×100 px env.)
    - Affiche le hint `"V: toggle agents"`
  - [x] 1.4 `debug_agents: bool` — toggle V ; `AITrainScene` lit cette propriété pour activer le rendu des agents
- [x] Task 2 — Tests headless dans `tests/test_evolution.py` ou nouveau `tests/test_hud.py`
  - [x] 2.1 Test : `StatsHUD` s'instancie sans erreur (headless)
  - [x] 2.2 Test : `update()` ajoute bien à `history`
  - [x] 2.3 Test : `StatsHUD` n'importe pas `ai.simulation`

## Dev Notes

### Stats dict format

```python
stats = {
    "gen": int,           # numéro de génération courante
    "best_fitness": float,
    "avg_fitness": float,
    "worst_fitness": float,
    "alive": int,         # nombre d'agents encore vivants
    "gen_complete": bool, # True si génération terminée (pour update history)
}
```
`AITrainScene` construit ce dict et le passe à `StatsHUD.draw()` — pas de couplage direct avec `PopulationSim`.

### Rendu pygame pour les tests headless

Ne pas appeler `StatsHUD.draw()` dans les tests headless (nécessite un display). Tester uniquement la logique (`update`, propriétés, `history`).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5]
- [Source: ui/ai_train_scene.py] intégration (Story 5.4)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (Copilot Agent — Amelia)

### Debug Log References
Aucun — implémentation directe, 0 échec.

### Completion Notes List
- `StatsHUD` class created with `history`, `debug_agents`, lazy `_font` init
- `update(stats)` appends `best_fitness` to `history` only when `gen_complete` is True
- `draw(surface, stats)` renders: gen counter, best/avg/worst fitness, alive count, "V: toggle agents" hint, mini line chart (120×80px) when ≥2 history points
- pygame imported lazily in `draw`/`_draw_chart` methods (headless-compatible at module level)
- 5 headless tests: instantiation, update with gen_complete, update without gen_complete, accumulation over 5 gens, import guard (no ai.simulation)
- 260/260 tests pass (suite complète hors modules pygame non-installés)

### File List

- `ui/hud.py` (nouveau)
- `tests/test_hud.py` (nouveau)

## Change Log

- 2026-03-07: Story 5.5 implemented — StatsHUD widget with headless tests (5/5 pass)
