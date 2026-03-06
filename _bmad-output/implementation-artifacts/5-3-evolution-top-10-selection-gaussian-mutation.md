# Story 5.3: Evolution — Top-10 Selection & Gaussian Mutation

Status: ready-for-dev

## Story

As an AI trainer,
I want the top-10 brains selected and mutated to produce the next generation,
So that each generation improves on the previous one.

## Acceptance Criteria

1. **Given** `ai/evolution.py` exists with `select_top_n(brains, fitness, n=10)` and `mutate(brain)` **When** `select_top_n` is called **Then** it returns the 10 brains with the highest fitness values
2. **When** `mutate(brain)` is called **Then** it returns a **new** `Brain` (original unchanged) with one of the following applied:
   - (~70%) 1–3 neuron positions displaced by `Δ ~ N(0, 1.0²)` per axis
   - (~25%) a neuron added to or removed from a randomly chosen network
   - (~5%) an entire network added or removed
3. **And** neuron positions after mutation remain as `float` (not snapped to grid)
4. **And** mutation never produces a `Brain` with zero networks
5. **And** `tests/test_evolution.py` verifies `select_top_n` returns n items and `mutate` returns different object with valid structure

## Tasks / Subtasks

- [ ] Task 1 — `ai/evolution.py` : fonctions `select_top_n` et `mutate`
  - [ ] 1.1 `select_top_n(brains: list[Brain], fitness: np.ndarray, n: int = 10) -> list[Brain]`
    - Utiliser `np.argsort(fitness)[::-1][:n]` pour les indices top-n
    - Retourner la liste des cerveaux correspondants
  - [ ] 1.2 `mutate(brain: Brain) -> Brain`
    - Copie profonde du brain (ne PAS muter l'original — `copy.deepcopy`)
    - Tirage `r = random.random()` pour choisir le type de mutation :
      - `r < 0.70` → déplacer 1–3 neurones aléatoires : `neuron.dx += np.random.normal(0, 1.0)`, même pour `dy`
      - `r < 0.95` → ajouter ou supprimer un neurone d'un réseau aléatoire (supprimer seulement si le réseau a > 1 neurone)
      - sinon → ajouter ou supprimer un réseau entier (supprimer seulement si len(networks) > 1)
    - Garantir que le résultat a au moins 1 réseau avec au moins 1 neurone
  - [ ] 1.3 `generate_random_brain(n_networks: int = 2, neurons_per_network: int = 3) -> Brain` — helper pour créer des cerveaux aléatoires initiaux
  - [ ] 1.4 ZERO import `pygame`
- [ ] Task 2 — Ajouter tests dans `tests/test_evolution.py`
  - [ ] 2.1 Test : `select_top_n` retourne exactement `n` cerveaux
  - [ ] 2.2 Test : les cerveaux retournés sont ceux avec le meilleur fitness
  - [ ] 2.3 Test : `mutate` retourne un objet différent (pas la même référence)
  - [ ] 2.4 Test : le brain original est inchangé après `mutate`
  - [ ] 2.5 Test : `mutate` retourne un Brain avec au moins 1 réseau
  - [ ] 2.6 Test : `mutate` retourne un Brain avec au moins 1 neurone dans chaque réseau
  - [ ] 2.7 Test : `generate_random_brain` retourne un Brain valide

## Dev Notes

### Architecture obligatoire

```
ai/evolution.py  →  peut importer ai/ (neuron, network, brain), numpy, random, copy, stdlib
ai/evolution.py  →  ne peut PAS importer renderer/, pygame
```

### Import guard `numpy` pour `argsort`

`numpy` est une dépendance du projet [Source: architecture.md#Catégorie 5]. L'utiliser pour `select_top_n`. Pour la mutation gaussienne, utiliser `np.random.normal`.

### Mutation — immuabilité des cerveaux

`copy.deepcopy(brain)` garantit que les réseaux et neurones de l'original ne sont pas modifiés. Les `Neuron` sont des dataclasses — modifier `neuron.dx` sur la copie ne touche pas l'original.

### Taille des neurones aléatoires initiaux

`generate_random_brain` : `dx` et `dy` tirés dans `[-3.0, 3.0]` (uniform). Polarity random parmi `["green", "red"]`. Type random parmi `[TileType.SOLID, TileType.SPIKE]`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3]
- [Source: ai/brain.py, ai/network.py, ai/neuron.py] Story 4.x

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/evolution.py` (nouveau)
- `tests/test_evolution.py` (modifié)
