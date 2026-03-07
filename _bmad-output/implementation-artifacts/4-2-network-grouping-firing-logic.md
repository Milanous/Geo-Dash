# Story 4.2: Network — Grouping & Firing Logic

Status: done

## Story

As an AI designer,
I want a network that groups neurons and fires when all are active,
So that complex conditions can trigger a jump.

## Acceptance Criteria

1. **Given** `ai/network.py` exists with a `Network` class **When** `Network(neurons=[n1, n2])` is created **And** `network.should_fire(player_x, player_y, world)` is called **Then** it returns `True` only if ALL neurons return `True` from `is_active()`
2. **When** any one neuron returns `False` **Then** `should_fire()` returns `False`
3. **And** a `Network` with a single neuron fires if that neuron is active
4. **And** `Network` with empty neuron list never fires
5. **And** `ai/network.py` does not import `pygame`
6. **And** `tests/test_brain.py` covers all-active, one-inactive, and empty-network cases

## Tasks / Subtasks

- [x] Task 1 — `ai/network.py` : class `Network`
  - [x] 1.1 `class Network` avec champ `neurons: list[Neuron]`
  - [x] 1.2 `should_fire(self, player_x: float, player_y: float, world: World) -> bool`
    - Retourne `False` si `self.neurons` est vide
    - Retourne `True` uniquement si **tous** les neurones sont actifs (`all(...)`)
  - [x] 1.3 ZERO import `pygame`
- [x] Task 2 — Ajouter tests dans `tests/test_brain.py`
  - [x] 2.1 Test : tous les neurones actifs → `True`
  - [x] 2.2 Test : un neurone inactif → `False`
  - [x] 2.3 Test : réseau vide → `False`
  - [x] 2.4 Test : réseau à un seul neurone actif → `True`
  - [x] 2.5 Test : réseau à un seul neurone inactif → `False`

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
ai/  →  peut importer engine/, numpy, stdlib
ai/  →  ne peut PAS importer renderer/, pygame
```

### Interface attendue

```python
# ai/network.py
from __future__ import annotations
from ai.neuron import Neuron
from engine.world import World

class Network:
    def __init__(self, neurons: list[Neuron]) -> None:
        self.neurons = neurons

    def should_fire(self, player_x: float, player_y: float, world: World) -> bool:
        if not self.neurons:
            return False
        return all(n.is_active(player_x, player_y, world) for n in self.neurons)
```

### Logique AND — justification

Un réseau = une condition complexe. Tous les neurones doivent être actifs simultanément. Exemple : "il y a un spike à droite ET le sol est là en dessous" → saut si les deux sont vrais.

Le `Brain` (Story 4.3) utilisera la logique OR entre réseaux : sauter si N'IMPORTE QUEL réseau se déclenche.

### Réseau vide

Un réseau sans neurones ne fournit aucune information → `should_fire()` retourne `False`. Cela prévient des mutations créant des réseaux "toujours vrais".

### Enrichir `tests/test_brain.py`

Ce fichier a été créé en Story 4.1. Ajouter une section clairement délimitée `# --- Network ---` avec les nouveaux tests.

### Structure physique

```
ai/
    neuron.py   ← Story 4.1 ✅
    network.py  ← À CRÉER
tests/
    test_brain.py ← Story 4.1 ✅ (enrichir)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]
- [Source: ai/neuron.py] interface Neuron (Story 4.1)
- [Source: engine/world.py] World

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/network.py` (nouveau)
- `tests/test_brain.py` (modifié — tests Network ajoutés)
