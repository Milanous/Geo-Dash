"""
tests/test_world.py

Story 1.3 — Tile Grid World & Coordinate System

Headless — never imports pygame.
"""

import pytest
from engine.world import TileType, World


# ---------------------------------------------------------------------------
# AC-1: TileType enum members
# ---------------------------------------------------------------------------

def test_tiletype_has_air() -> None:
    assert TileType.AIR is not None


def test_tiletype_has_solid() -> None:
    assert TileType.SOLID is not None


def test_tiletype_has_spike() -> None:
    assert TileType.SPIKE is not None


def test_tiletype_members_are_distinct() -> None:
    assert TileType.AIR != TileType.SOLID
    assert TileType.AIR != TileType.SPIKE
    assert TileType.SOLID != TileType.SPIKE


# ---------------------------------------------------------------------------
# AC-2: Default world is all AIR
# ---------------------------------------------------------------------------

def test_world_default_all_air() -> None:
    w = World(10, 5)
    for y in range(5):
        for x in range(10):
            assert w.tile_at(x, y) == TileType.AIR, f"Expected AIR at ({x},{y})"


def test_world_stores_dimensions() -> None:
    w = World(20, 15)
    assert w.width == 20
    assert w.height == 15


# ---------------------------------------------------------------------------
# AC-3: set_tile / tile_at round-trip
# ---------------------------------------------------------------------------

def test_set_tile_solid() -> None:
    w = World(10, 10)
    w.set_tile(3, 4, TileType.SOLID)
    assert w.tile_at(3, 4) == TileType.SOLID


def test_set_tile_spike() -> None:
    w = World(10, 10)
    w.set_tile(0, 0, TileType.SPIKE)
    assert w.tile_at(0, 0) == TileType.SPIKE


def test_set_tile_does_not_affect_neighbours() -> None:
    w = World(10, 10)
    w.set_tile(5, 5, TileType.SOLID)
    assert w.tile_at(4, 5) == TileType.AIR
    assert w.tile_at(6, 5) == TileType.AIR
    assert w.tile_at(5, 4) == TileType.AIR
    assert w.tile_at(5, 6) == TileType.AIR


def test_set_tile_overwrite() -> None:
    w = World(10, 10)
    w.set_tile(2, 2, TileType.SOLID)
    w.set_tile(2, 2, TileType.SPIKE)
    assert w.tile_at(2, 2) == TileType.SPIKE


def test_set_tile_float_coords_floor() -> None:
    """Float block coords are floored to integer grid indices."""
    w = World(10, 10)
    w.set_tile(3.9, 4.7, TileType.SOLID)
    assert w.tile_at(3, 4) == TileType.SOLID


def test_tile_at_float_coords_floor() -> None:
    w = World(10, 10)
    w.set_tile(3, 4, TileType.SPIKE)
    assert w.tile_at(3.0, 4.0) == TileType.SPIKE
    assert w.tile_at(3.99, 4.99) == TileType.SPIKE


# ---------------------------------------------------------------------------
# AC-4/5/6: to_px and to_bloc conversions
# ---------------------------------------------------------------------------

def test_to_px_one_block() -> None:
    assert World.to_px(1.0) == 30


def test_to_px_half_block() -> None:
    assert World.to_px(0.5) == 15


def test_to_px_zero() -> None:
    assert World.to_px(0.0) == 0


def test_to_px_fractional_truncates() -> None:
    # int(2.9 * 30) = int(87.0) = 87
    assert World.to_px(2.9) == 87


def test_to_bloc_thirty_pixels() -> None:
    assert World.to_bloc(30) == 1.0


def test_to_bloc_zero() -> None:
    assert World.to_bloc(0) == 0.0


def test_to_bloc_returns_float() -> None:
    assert isinstance(World.to_bloc(15), float)


def test_to_bloc_to_px_roundtrip() -> None:
    """to_bloc(to_px(n)) == n for integer blocks."""
    for n in range(0, 20):
        assert World.to_bloc(World.to_px(float(n))) == float(n)


# ---------------------------------------------------------------------------
# OOB: tile_at and set_tile are safe beyond grid bounds
# ---------------------------------------------------------------------------

def test_tile_at_oob_returns_air() -> None:
    w = World(5, 5)
    assert w.tile_at(-1, 0)  == TileType.AIR
    assert w.tile_at(0, -1)  == TileType.AIR
    assert w.tile_at(5, 0)   == TileType.AIR
    assert w.tile_at(0, 5)   == TileType.AIR
    assert w.tile_at(100, 100) == TileType.AIR


def test_set_tile_oob_silent() -> None:
    """set_tile on OOB position must not raise."""
    w = World(5, 5)
    w.set_tile(-1, 0, TileType.SOLID)   # must not raise
    w.set_tile(0, -1, TileType.SOLID)
    w.set_tile(5, 0, TileType.SOLID)
    w.set_tile(0, 5, TileType.SOLID)


# ---------------------------------------------------------------------------
# AC-7: No pygame import (runtime check)
# ---------------------------------------------------------------------------

def test_no_pygame_in_world_module() -> None:
    import engine.world as wm
    assert not hasattr(wm, "pygame"), "engine.world must not import pygame"


# ---------------------------------------------------------------------------
# Story 1.6 — Player jump, collision & floor boundary (AC-5)
# ---------------------------------------------------------------------------

from engine.player import Player
from engine.physics import JUMP_VELOCITY, DT, GRAVITY


def _make_floor_world(width: int = 20, height: int = 10) -> World:
    """Helper: create a World with a row of SOLID tiles at y=0."""
    w = World(width, height)
    for col in range(width):
        w.set_tile(col, 0, TileType.SOLID)
    return w


def test_player_lands_on_solid_floor_tiles() -> None:
    """AC-1: Fall onto SOLID tiles at y=0 → y=0, vy=0, on_ground=True."""
    world = _make_floor_world()
    p = Player(start_x=5.0, start_y=3.0)
    # Simulate enough steps for the player to fall to y=0
    for _ in range(500):
        p.update(DT, world)
        if p.state.on_ground:
            break
    assert p.state.y == pytest.approx(0.0, abs=1e-9)
    assert p.state.vy == pytest.approx(0.0)
    assert p.state.on_ground is True


def test_player_world_boundary_without_tiles() -> None:
    """AC-4: World boundary at y=0 catches player even without any tile."""
    empty_world = World(20, 10)  # all AIR
    p = Player(start_x=5.0, start_y=3.0)
    for _ in range(500):
        p.update(DT, empty_world)
        if p.state.on_ground:
            break
    assert p.state.y == pytest.approx(0.0, abs=1e-9)
    assert p.state.vy == pytest.approx(0.0)
    assert p.state.on_ground is True


def test_player_world_boundary_no_world_arg() -> None:
    """World boundary (y<=0) works even without a world argument."""
    p = Player(start_x=0.0, start_y=3.0)
    for _ in range(500):
        p.update(DT, None)
        if p.state.on_ground:
            break
    assert p.state.y == pytest.approx(0.0, abs=1e-9)
    assert p.state.on_ground is True


def test_player_jump_when_on_ground() -> None:
    """AC-2: jump() from on_ground=True → vy=JUMP_VELOCITY, on_ground=False."""
    world = _make_floor_world()
    p = Player(start_x=5.0, start_y=3.0)
    # Land first
    for _ in range(500):
        p.update(DT, world)
        if p.state.on_ground:
            break
    assert p.state.on_ground is True
    p.jump()
    assert p.state.vy == pytest.approx(JUMP_VELOCITY)
    assert p.state.on_ground is False


def test_player_no_double_jump() -> None:
    """AC-3: jump() while on_ground=False must leave vy unchanged."""
    p = Player(start_x=5.0, start_y=5.0)
    # Force airborne state
    p.state.on_ground = False
    p.state.vy = -2.0
    p.jump()
    # vy must NOT have changed to JUMP_VELOCITY
    assert p.state.vy == pytest.approx(-2.0)


def test_player_jump_leaves_ground_first_step() -> None:
    """After jump, next update does not snap back to ground immediately."""
    world = _make_floor_world()
    p = Player(start_x=5.0, start_y=3.0)
    for _ in range(500):
        p.update(DT, world)
        if p.state.on_ground:
            break
    p.jump()
    p.update(DT, world)
    # After one step airborne (y should be > 0)
    assert p.state.y > 0.0


def test_player_spike_sets_alive_false() -> None:
    """Entering a SPIKE tile sets player.alive = False."""
    # Full row of SPIKEs at y=2 — player falls from y=5 and passes through y=2
    # regardless of horizontal position (PLAYER_SPEED shifts x significantly)
    world = World(100, 10)
    for col in range(100):
        world.set_tile(col, 2, TileType.SPIKE)
    p = Player(start_x=0.0, start_y=5.0)
    for _ in range(500):
        p.update(DT, world)
        if not p.alive:
            break
    assert p.alive is False


def test_player_stops_updating_when_dead() -> None:
    """Dead player (alive=False) must not move on subsequent updates."""
    p = Player(start_x=2.0, start_y=5.0)
    p.alive = False
    x_before = p.state.x
    y_before = p.state.y
    p.update(DT)
    assert p.state.x == x_before
    assert p.state.y == y_before


# ---------------------------------------------------------------------------
# Story 2.3 — Spike Tiles & Death Detection
# ---------------------------------------------------------------------------

def test_spike_at_player_grid_cell_kills_in_one_step() -> None:
    """Player falling one tile above a row of spikes must die in one update."""
    world = World(20, 10)
    # Row 0 = all spikes; player starts at y=1.0 and falls into row 0
    for col in range(20):
        world.set_tile(col, 0, TileType.SPIKE)
    p = Player(start_x=0.0, start_y=1.0)
    p.update(DT, world)
    assert p.alive is False


def test_spike_collision_does_not_snap_player_y() -> None:
    """Unlike SOLID, hitting a SPIKE must not snap the player's y to the tile surface."""
    world = World(20, 10)
    # Row 1 = all spikes; player starts at y=1.5 and falls into row 1
    for col in range(20):
        world.set_tile(col, 1, TileType.SPIKE)
    p = Player(start_x=0.0, start_y=1.5)
    p.update(DT, world)
    assert p.alive is False
    # SOLID snap would have set y=1.0 exactly; SPIKE must leave y unchanged
    assert p.state.y != 1.0
