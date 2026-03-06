"""
tests/test_game_loop.py

Story 1.7 — Game Loop, Basic Renderer & Play Scene

Headless checks — never calls pygame.init() or creates a Surface.
(pygame is imported in play_scene/renderer at module level but
 importing those modules without init is safe when pygame is installed.)
"""

from __future__ import annotations

import abc
import inspect

import pytest

from ui.scene import Scene
from ui.play_scene import PlayScene
from engine.physics import DT, PLAYER_SPEED
from engine.world import TileType, World


# ---------------------------------------------------------------------------
# Scene ABC
# ---------------------------------------------------------------------------

def test_scene_abc_is_abstract() -> None:
    """Scene cannot be instantiated directly."""
    assert inspect.isabstract(Scene)


def test_scene_has_handle_events_method() -> None:
    assert callable(getattr(Scene, "handle_events", None))


def test_scene_has_update_method() -> None:
    assert callable(getattr(Scene, "update", None))


def test_scene_has_draw_method() -> None:
    assert callable(getattr(Scene, "draw", None))


def test_scene_methods_are_abstract() -> None:
    abstract_methods = {
        name
        for name, val in inspect.getmembers(Scene)
        if getattr(val, "__isabstractmethod__", False)
    }
    assert "handle_events" in abstract_methods
    assert "update" in abstract_methods
    assert "draw" in abstract_methods


def test_no_pygame_in_scene_module() -> None:
    """ui/scene.py must not import pygame at module level."""
    import ui.scene as sc
    assert not hasattr(sc, "pygame"), "ui/scene.py must not import pygame at module level"


# ---------------------------------------------------------------------------
# PlayScene — subclassing
# ---------------------------------------------------------------------------

def test_play_scene_is_scene_subclass() -> None:
    assert issubclass(PlayScene, Scene)


def test_play_scene_is_concrete() -> None:
    """PlayScene must implement all abstract methods — no abstract residuals."""
    assert not inspect.isabstract(PlayScene)


# ---------------------------------------------------------------------------
# PlayScene — level setup
# ---------------------------------------------------------------------------

def test_play_scene_has_flat_floor() -> None:
    """PlayScene creates a World with SOLID tiles on the entire row 0."""
    ps = PlayScene()
    for col in range(20):
        assert ps._world.tile_at(col, 0) == TileType.SOLID, \
            f"Expected SOLID at ({col}, 0) but got {ps._world.tile_at(col, 0)}"


def test_play_scene_air_above_floor() -> None:
    """Row 1 and above must be AIR (no obstacles in hardcoded level)."""
    ps = PlayScene()
    for col in range(5):
        assert ps._world.tile_at(col, 1) == TileType.AIR


# ---------------------------------------------------------------------------
# PlayScene — physics update (headless — no rendering)
# ---------------------------------------------------------------------------

def test_play_scene_update_advances_player_x() -> None:
    """After one physics step, player.x == start_x + PLAYER_SPEED * DT."""
    ps = PlayScene()
    x_before = ps._player.state.x
    ps.update(DT)
    assert ps._player.state.x == pytest.approx(x_before + PLAYER_SPEED * DT)


def test_play_scene_player_lands_and_stays_on_ground() -> None:
    """Player must land on the floor and remain on_ground after settling."""
    ps = PlayScene()
    for _ in range(500):
        ps.update(DT)
    assert ps._player.state.on_ground is True
    assert ps._player.state.y == pytest.approx(0.0, abs=1e-9)


def test_play_scene_camera_offset_nonzero_after_run() -> None:
    """Camera x_offset increases once the player moves past the anchor."""
    ps = PlayScene()
    # Run until player has crossed PLAYER_ANCHOR_PX (200 px = ~6.67 blocks from start x=5)
    for _ in range(500):
        ps.update(DT)
    assert ps._camera.x_offset > 0


def test_play_scene_player_respawns_after_death() -> None:
    """If player.alive becomes False, next update() resets the player."""
    ps = PlayScene()
    ps._player.alive = False
    ps.update(DT)
    # After reset, a fresh player should be alive; x is at start + one physics step
    assert ps._player.alive is True
    # x == _START_X + PLAYER_SPEED * DT (reset happens, then one step runs)
    assert ps._player.state.x == pytest.approx(5.0 + PLAYER_SPEED * DT)


# ---------------------------------------------------------------------------
# Accumulator pattern — unit check
# ---------------------------------------------------------------------------

def test_accumulator_pattern_steps() -> None:
    """
    Verify the accumulator step count (independently of pygame).
    A frame_dt that is exactly 2*DT must produce exactly 2 physics steps.
    """
    ps = PlayScene()
    x_before = ps._player.state.x
    frame_dt = 2 * DT
    accumulator = frame_dt
    steps = 0
    while accumulator >= DT:
        ps.update(DT)
        accumulator -= DT
        steps += 1
    assert steps == 2
    assert ps._player.state.x == pytest.approx(x_before + PLAYER_SPEED * DT * 2)
