"""
tests/test_physics.py

Story 1.2 — Physics Constants & PlayerState

Headless — never imports pygame.
"""

import math
import pytest
from engine.physics import (
    PHYSICS_RATE,
    DT,
    GRAVITY,
    JUMP_VELOCITY,
    PLAYER_SPEED,
    BLOCK_SIZE_PX,
    ROTATION_SPEED_DEG_PER_STEP,
    PlayerState,
)


# ---------------------------------------------------------------------------
# AC-1..6: Constant exact values
# ---------------------------------------------------------------------------

def test_physics_rate() -> None:
    assert PHYSICS_RATE == 240


def test_dt_value() -> None:
    assert DT == 1.0 / 240


def test_dt_derived_from_physics_rate() -> None:
    """AC-9: DT must equal 1.0 / PHYSICS_RATE exactly."""
    assert DT == 1.0 / PHYSICS_RATE


def test_gravity() -> None:
    assert GRAVITY == pytest.approx(-114.96)


def test_jump_velocity() -> None:
    assert JUMP_VELOCITY == pytest.approx(24.72)


def test_player_speed() -> None:
    assert PLAYER_SPEED == 10.3761348998


def test_block_size_px() -> None:
    assert BLOCK_SIZE_PX == 30


# ---------------------------------------------------------------------------
# AC-7: PlayerState dataclass
# ---------------------------------------------------------------------------

def test_playerstate_default_instantiation() -> None:
    ps = PlayerState()
    assert ps.x == 0.0
    assert ps.y == 0.0
    assert ps.vy == 0.0
    assert ps.on_ground is True
    assert ps.angle == 0.0


def test_playerstate_custom_values() -> None:
    ps = PlayerState(x=5.5, y=2.0, vy=-1.5, on_ground=False, angle=45.0)
    assert ps.x == 5.5
    assert ps.y == 2.0
    assert ps.vy == -1.5
    assert ps.on_ground is False
    assert ps.angle == 45.0


def test_playerstate_field_types() -> None:
    ps = PlayerState(x=1.0, y=2.0, vy=3.0, on_ground=True, angle=0.0)
    assert isinstance(ps.x, float)
    assert isinstance(ps.y, float)
    assert isinstance(ps.vy, float)
    assert isinstance(ps.on_ground, bool)
    assert isinstance(ps.angle, float)


def test_playerstate_is_mutable() -> None:
    """PlayerState fields must be assignable (not frozen dataclass)."""
    ps = PlayerState()
    ps.x = 10.0
    assert ps.x == 10.0


# ---------------------------------------------------------------------------
# AC-8: No pygame or project module imports (static — verified in test_scaffolding)
# But we also verify at runtime that engine.physics has no pygame attribute
# ---------------------------------------------------------------------------

def test_no_pygame_in_physics_module() -> None:
    import engine.physics as phys
    assert not hasattr(phys, "pygame"), "engine.physics must not import pygame"


# ---------------------------------------------------------------------------
# Story 1.5 — Player horizontal movement (AC-6)
# ---------------------------------------------------------------------------

from engine.physics import DT, GRAVITY, PLAYER_SPEED
from engine.player import Player


def test_player_x_advances_by_player_speed_dt() -> None:
    """AC-6 Story 1.5: x must increase by exactly PLAYER_SPEED * DT per step."""
    p = Player(start_x=0.0, start_y=100.0)  # high y avoids floor boundary
    p.update(DT)
    assert p.state.x == pytest.approx(PLAYER_SPEED * DT)


def test_player_x_cumulative_after_n_steps() -> None:
    """x accumulates correctly over multiple steps."""
    p = Player(start_x=0.0, start_y=100.0)
    n = 10
    for _ in range(n):
        p.update(DT)
    assert p.state.x == pytest.approx(PLAYER_SPEED * DT * n)


def test_player_vy_decreases_by_gravity_per_step() -> None:
    """AC: vy += GRAVITY * DT each step (dt-scaled gravity)."""
    p = Player(start_x=0.0, start_y=100.0)
    p.update(DT)
    # vy = 0 + GRAVITY * DT (initial vy=0 from PlayerState, start on_ground False so no jump)
    # Note: PlayerState default on_ground=True, but here start_y=100 and no floor so
    # on_ground becomes False after first update (no collision => on_ground=False)
    assert p.state.vy == pytest.approx(GRAVITY * DT)


def test_player_vy_accumulates_over_steps() -> None:
    """vy keeps accumulating GRAVITY * DT each step with no floor."""
    p = Player(start_x=0.0, start_y=100.0)
    for _ in range(5):
        p.update(DT)
    assert p.state.vy == pytest.approx(GRAVITY * DT * 5)


def test_player_y_falls_without_floor() -> None:
    """Player falls indefinitely — y decreases with no tile/floor."""
    p = Player(start_x=0.0, start_y=100.0)
    steps = 120
    for _ in range(steps):
        p.update(DT)
    assert p.state.y < 100.0


def test_no_pygame_in_player_module() -> None:
    import engine.player as ply
    assert not hasattr(ply, "pygame"), "engine.player must not import pygame"


# ---------------------------------------------------------------------------
# Story 2.4 — Player Rotation (headless)
# ---------------------------------------------------------------------------

def test_rotation_constant_value() -> None:
    """ROTATION_SPEED_DEG_PER_STEP must equal 450 °/s ÷ 240 Hz."""
    assert ROTATION_SPEED_DEG_PER_STEP == pytest.approx(1.875)


def test_angle_increases_when_airborne() -> None:
    """Angle must grow by ROTATION_SPEED_DEG_PER_STEP each in-air physics step."""
    from engine.player import Player
    p = Player(start_x=5.0, start_y=10.0)   # starts in-air (no floor below)
    p.update(DT)   # still falling, on_ground=False after step
    assert p.state.angle == pytest.approx(ROTATION_SPEED_DEG_PER_STEP)


def test_angle_snaps_to_zero_on_landing() -> None:
    """Angle must snap to 0.0 the moment the player lands (on_ground=True)."""
    from engine.player import Player
    from engine.world import World, TileType

    world = World(20, 10)
    for col in range(20):
        world.set_tile(col, 0, TileType.SOLID)

    p = Player(start_x=5.0, start_y=3.0)
    # Let player fall and accumulate rotation until grounded
    for _ in range(300):
        p.update(DT, world)
        if p.state.on_ground:
            break

    assert p.state.on_ground is True
    assert p.state.angle == pytest.approx(0.0)


def test_angle_stays_zero_while_grounded() -> None:
    """Angle must remain 0.0 across multiple steps when the player is on the floor."""
    from engine.player import Player
    from engine.world import World, TileType

    world = World(20, 10)
    for col in range(20):
        world.set_tile(col, 0, TileType.SOLID)

    # Drop player onto the floor first
    p = Player(start_x=5.0, start_y=3.0)
    for _ in range(300):
        p.update(DT, world)
        if p.state.on_ground:
            break

    # Several more steps on the ground: angle must stay 0
    for _ in range(10):
        p.update(DT, world)

    assert p.state.angle == pytest.approx(0.0)
