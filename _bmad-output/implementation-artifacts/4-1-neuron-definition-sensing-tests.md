# Story 4.1: Neuron — Definition, Sensing & Tests

Status: ready-for-dev

## Story

As an AI designer,
I want neurons that can sense the environment around the player and report active/inactive state,
So that brains can perceive the level.

## Acceptance Criteria

1. **Given** `ai/neuron.py` exists with a `Neuron` dataclass **When** `Neuron(dx=2.0, dy=-1.0, type=TileType.SPIKE, polarity="green")` is created **Then** `neuron.dx` and `neuron.dy` are `float` values (not grid-snapped integers)
2. **When** `neuron.is_active(player_x, player_y, world)` is called **And** the tile at `(player_x + dx, player_y + dy)` is `TileType.SPIKE` **Then** a green neuron returns `True`
3. **And** a red neuron (`polarity="red"`) returns `False`
4. **When** the tile does NOT match the neuron's type **Then** a green neuron returns `False`, a red neuron returns `True`
5. **And** `ai/neuron.py` does not import `pygame`
6. **And** `tests/test_brain.py` covers all four polarity × match combinations

## Tasks / Subtasks

- [ ] Task 1 — `ai/neuron.py` : dataclass `Neuron`
  - [ ] 1.1 `@dataclass class Neuron` avec champs : `dx: float`, `dy: float`, `type: TileType`, `polarity: str` (valeurs: `"green"` | `"red"`)
  - [ ] 1.2 `is_active(self, player_x: float, player_y: float, world: World) -> bool`
    - Vérifie le tile à `(player_x + self.dx, player_y + self.dy)` via `world.tile_at()`
    - `"green"` → retourne `True` si le tile correspond à `self.type`
    - `"red"` → retourne `True` si le tile ne correspond PAS à `self.type`
  - [ ] 1.3 ZERO import `pygame`
- [ ] Task 2 — `tests/test_brain.py` : tests `Neuron` headless
  - [ ] 2.1 Test : `Neuron.dx` et `dy` sont bien des floats
  - [ ] 2.2 Test : green neuron, tile correspond → `True`
  - [ ] 2.3 Test : green neuron, tile ne correspond pas → `False`
  - [ ] 2.4 Test : red neuron, tile correspond → `False`
  - [ ] 2.5 Test : red neuron, tile ne correspond pas → `True`
  - [ ] 2.6 Test : `is_active` sur position hors-limites → AIR retourné silencieusement (pas de crash)
  - [ ] 2.7 Test : import guard — `neuron.py` n'importe pas `pygame`

## Dev Notes

### Architecture obligatoire

**Import rule** [Source: architecture.md#Règles d'import] :
```
ai/  →  peut importer engine/, numpy, stdlib
ai/  →  ne peut PAS importer renderer/, pygame
```

### Interface attendue

```python
# ai/neuron.py
from __future__ import annotations
from dataclasses import dataclass
from engine.world import TileType, World

@dataclass
class Neuron:
    dx: float
    dy: float
    type: TileType
    polarity: str  # "green" | "red"

    def is_active(self, player_x: float, player_y: float, world: World) -> bool:
        tile = world.tile_at(player_x + self.dx, player_y + self.dy)
        match = (tile == self.type)
        return match if self.polarity == "green" else not match
```

### Schéma JSON du neurone [Source: architecture.md#Catégorie 4]

```json
{"dx": 2.5, "dy": -1.0, "type": "spike", "polarity": "green"}
```
La sérialisation JSON sera implémentée en Story 4.3 (`Brain.to_json()` / `from_json()`). Cette story livre uniquement la logique de détection.

### Polarity — sémantique

| polarity | tile correspond | résultat |
|---|---|---|
| `"green"` | ✅ | `True` |
| `"green"` | ❌ | `False` |
| `"red"` | ✅ | `False` |
| `"red"` | ❌ | `True` |

`"red"` = neurone inhibiteur — actif quand le danger N'est PAS là. Utile pour "saute si la voie est libre".

### Utilisation de `world.tile_at()`

`World.tile_at(bx, by)` retourne `TileType.AIR` pour les positions hors-limites — comportement silencieux garanti [Source: engine/world.py]. Pas de guard nécessaire dans `Neuron.is_active()`.

### Fichier de tests `test_brain.py`

Ce fichier accueillera **toutes** les stories AI (4.1, 4.2, 4.3) selon l'AC : "tests/test_brain.py covers...". Créer le fichier dans cette story et l'enrichir dans les stories suivantes.

### Structure physique

```
ai/
    __init__.py     ← existe déjà
    neuron.py       ← À CRÉER
tests/
    test_brain.py   ← À CRÉER (accueillera aussi les tests 4.2 et 4.3)
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Catégorie 4 — Schémas JSON]
- [Source: engine/world.py] `TileType`, `World.tile_at()`

## Dev Agent Record

### Agent Model Used
_À remplir_

### Debug Log References

### Completion Notes List

### File List

- `ai/neuron.py` (nouveau)
- `tests/test_brain.py` (nouveau)
