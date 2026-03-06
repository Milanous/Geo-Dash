# Story 4.3: Brain — Genome & JSON Serialization

Status: ready-for-dev

## Story

As an AI designer,
I want a Brain that aggregates networks and triggers a jump when any network fires,
So that the full decision logic is encapsulated in a serializable genome.

## Acceptance Criteria

1. **Given** `ai/brain.py` exists with a `Brain` class **When** `Brain(networks=[net1, net2])` is created **And** `brain.should_jump(player_x, player_y, world)` is called **Then** it returns `True` if ANY network fires
2. **And** returns `False` only if NO network fires
3. **When** `brain.to_json()` is called **Then** it returns a dict matching the schema: `{"version": 1, "networks": [{"neurons": [{"dx": float, "dy": float, "type": "spike"|"solid"|"air", "polarity": "green"|"red"}]}]}`
4. **When** `Brain.from_json(data)` is called **Then** it returns an equivalent `Brain` that behaves identically
5. **And** a round-trip (to_json → from_json) produces a brain with identical `should_jump()` results for any input
6. **And** `ai/brain.py` does not import `pygame`
7. **And** `tests/test_brain.py` covers should_jump (any fires, none fires) and round-trip serialization

## Tasks / Subtasks

- [ ] Task 1 — `ai/brain.py` : class `Brain`
  - [ ] 1.1 `class Brain` avec champ `networks: list[Network]`
  - [ ] 1.2 `should_jump(self, player_x: float, player_y: float, world: World) -> bool`
    - Retourne `True` si **au moins un** réseau se déclenche (`any(...)`)
    - Retourne `False` si `self.networks` est vide ou si aucun ne se déclenche
  - [ ] 1.3 `to_json(self) -> dict` — sérialise le Brain selon le schéma défini
  - [ ] 1.4 `Brain.from_json(data: dict) -> Brain` — classmethod de désérialisation, lève `ValueError` si `version != 1`
  - [ ] 1.5 ZERO import `pygame`
- [ ] Task 2 — Ajouter tests dans `tests/test_brain.py`
  - [ ] 2.1 Test : `should_jump` retourne `True` si au moins un réseau se déclenche
  - [ ] 2.2 Test : `should_jump` retourne `False` si aucun réseau ne se déclenche
  - [ ] 2.3 Test : `should_jump` retourne `False` pour un Brain sans réseau
  - [ ] 2.4 Test : `to_json()` retourne `version=1` et la structure complète
  - [ ] 2.5 Test : `from_json(to_json())` round-trip → Brain fonctionnellement identique
  - [ ] 2.6 Test : `from_json` avec `version=2` lève `ValueError`

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
ai/  →  peut importer engine/, numpy, stdlib
ai/  →  ne peut PAS importer renderer/, pygame
```

### Schéma JSON Brain [Source: architecture.md#Catégorie 4]

```json
{
  "version": 1,
  "networks": [
    {
      "neurons": [
        {"dx": 2.5, "dy": -1.0, "type": "spike", "polarity": "green"},
        {"dx": 1.0, "dy":  0.0, "type": "solid",  "polarity": "red"}
      ]
    }
  ]
}
```

Note : le schéma fichier Brain inclut aussi `"generation"` et `"fitness"` (géré par `evolution.py` lors de la sauvegarde en Story 5.3). `Brain.to_json()` produit le noyau sans ces champs (ils sont wrappés par l'appelant).

### Mapping TileType ↔ chaîne JSON

```python
_TYPE_TO_STR = {TileType.AIR: "air", TileType.SOLID: "solid", TileType.SPIKE: "spike"}
_STR_TO_TYPE = {v: k for k, v in _TYPE_TO_STR.items()}
```

### Interface attendue

```python
# ai/brain.py
from __future__ import annotations
from ai.network import Network
from ai.neuron import Neuron
from engine.world import TileType, World

class Brain:
    def __init__(self, networks: list[Network]) -> None:
        self.networks = networks

    def should_jump(self, player_x: float, player_y: float, world: World) -> bool:
        return any(net.should_fire(player_x, player_y, world) for net in self.networks)

    def to_json(self) -> dict: ...

    @classmethod
    def from_json(cls, data: dict) -> Brain: ...
```

### Structure physique

```
ai/
    neuron.py   ← Story 4.1 ✅
    network.py  ← Story 4.2 ✅
    brain.py    ← À CRÉER
tests/
    test_brain.py ← Stories 4.1/4.2 ✅ (enrichir)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Catégorie 4 — Schémas JSON]
- [Source: ai/neuron.py, ai/network.py] interfaces Stories 4.1/4.2

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/brain.py` (nouveau)
- `tests/test_brain.py` (modifié — tests Brain ajoutés)
