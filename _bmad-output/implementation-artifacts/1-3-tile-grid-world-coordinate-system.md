# Story 1.3: Tile Grid World & Coordinate System

Status: review

## Story

As a developer,
I want a `World` class that stores the level tile grid and converts between block and pixel coordinates,
so that all modules share a single coordinate system.

## Acceptance Criteria

1. **Given** `engine/world.py` exists with `TileType(Enum)` and `World` **When** `TileType` is imported **Then** it has members: `AIR`, `SOLID`, `SPIKE`
2. **When** `World(width, height)` is instantiated **Then** `world.tile_at(bx, by)` returns `TileType.AIR` for any in-bounds position
3. **And** `world.set_tile(bx, by, TileType.SOLID)` then `world.tile_at(bx, by)` returns `TileType.SOLID`
4. **And** `World.to_px(1.0) == 30`
5. **And** `World.to_bloc(30) == 1.0`
6. **And** `World.to_px(0.5) == 15`
7. **And** `engine/world.py` does not import `pygame`
8. **And** `tests/test_world.py` covers all above with passing tests

## Tasks / Subtasks

- [x] Task 1 — Implement engine/world.py (AC: 1-7)
  - [x] 1.1 Define `TileType(Enum)` with `AIR`, `SOLID`, `SPIKE`
  - [x] 1.2 Implement `World(width, height)` with internal grid defaulting to AIR
  - [x] 1.3 Implement `tile_at(bx, by)` — returns TileType, clamps OOB to AIR
  - [x] 1.4 Implement `set_tile(bx, by, tile_type)`
  - [x] 1.5 Implement `World.to_px(bloc)` static method
  - [x] 1.6 Implement `World.to_bloc(px)` static method
- [x] Task 2 — Write tests/test_world.py (AC: 8)
  - [x] 2.1 TileType enum members
  - [x] 2.2 Default world is all AIR
  - [x] 2.3 set_tile / tile_at round-trip
  - [x] 2.4 to_px / to_bloc conversions
  - [x] 2.5 OOB tile_at returns AIR (no crash)

## Dev Notes

### Architecture Reference
```python
# engine/world.py — from architecture.md#Catégorie 2
class World:
    BLOCK_SIZE_PX: int = 30

    @staticmethod
    def to_px(bloc: float) -> int:
        return int(bloc * World.BLOCK_SIZE_PX)

    @staticmethod
    def to_bloc(px: int) -> float:
        return px / World.BLOCK_SIZE_PX

    def tile_at(self, bx: float, by: float) -> TileType: ...
```

### Grid Storage
- Use a 2D list: `self._grid: list[list[TileType]]` — `_grid[y][x]`
- Grid indices are integer block coordinates (floor of float inputs)
- OOB access → return `TileType.AIR` (graceful, no crash)
- `width` and `height` are in blocks (integers)

### Coordinate Convention
- All args `bx`, `by` in blocks (float) — floor to int for grid lookup
- `to_px` → `int(bloc * BLOCK_SIZE_PX)` — truncates (matches architecture)
- `to_bloc` → `px / BLOCK_SIZE_PX` — returns float

### Import Rules
- `engine/world.py` imports only stdlib and `engine/physics.py` (for `BLOCK_SIZE_PX`)
- Forbidden: `pygame`, `renderer`, `ai`

### References
- [Source: architecture.md#Catégorie 2] — World class pattern
- [Source: architecture.md#Naming Patterns] — TileType enum, coordinate naming
- [Source: epics.md#Story 1.3] — acceptance criteria

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (GitHub Copilot)

### Debug Log References

### Completion Notes List
- `TileType` enum (AIR, SOLID, SPIKE) via `enum.auto()`.
- `World` stores grid as `list[list[TileType]]` indexed `_grid[y][x]`.
- `tile_at` and `set_tile` floor float inputs to int; OOB is silently handled.
- `to_px` imports `BLOCK_SIZE_PX` from `engine.physics` — single source of truth.
- 24 new tests; 59/59 total ✅

### File List
- engine/world.py
- tests/test_world.py
- _bmad-output/implementation-artifacts/1-3-tile-grid-world-coordinate-system.md

### Change Log
- 2026-03-05: Story file created, status → in-progress
- 2026-03-05: Implementation complete, 59/59 tests pass, status → review
