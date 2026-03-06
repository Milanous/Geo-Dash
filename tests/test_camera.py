"""
tests/test_camera.py

Story 1.4 — Scrolling Camera

Headless — never imports pygame.
"""

import pytest
from engine.camera import Camera, PLAYER_ANCHOR_PX
from engine.world import World


# ---------------------------------------------------------------------------
# AC-1: world_to_screen_x with zero offset
# ---------------------------------------------------------------------------

def test_world_to_screen_x_zero_offset() -> None:
    cam = Camera(x_offset=0)
    # bloc_x=1.0 → to_px=30, screen = 30 - 0 = 30
    assert cam.world_to_screen_x(1.0) == 30


def test_world_to_screen_x_zero_bloc_zero_offset() -> None:
    cam = Camera(x_offset=0)
    assert cam.world_to_screen_x(0.0) == 0


def test_world_to_screen_x_matches_formula() -> None:
    """AC-1: result == World.to_px(bloc_x) - x_offset for any value."""
    cam = Camera(x_offset=0)
    for bloc_x in [0.0, 1.0, 5.5, 10.0, 33.3]:
        expected = World.to_px(bloc_x) - cam.x_offset
        assert cam.world_to_screen_x(bloc_x) == expected


# ---------------------------------------------------------------------------
# AC-1 (continued): world_to_screen_x with non-zero offset
# ---------------------------------------------------------------------------

def test_world_to_screen_x_with_offset() -> None:
    cam = Camera(x_offset=60)
    # bloc_x=5.0 → to_px=150, screen = 150 - 60 = 90
    assert cam.world_to_screen_x(5.0) == 90


def test_world_to_screen_x_formula_with_offset() -> None:
    cam = Camera(x_offset=300)
    for bloc_x in [0.0, 2.0, 10.0, 20.5]:
        expected = World.to_px(bloc_x) - 300
        assert cam.world_to_screen_x(bloc_x) == expected


def test_world_to_screen_x_can_return_negative() -> None:
    """Objects behind camera can have negative screen X — that's valid."""
    cam = Camera(x_offset=300)
    # bloc_x=1.0 → to_px=30, screen = 30 - 300 = -270
    assert cam.world_to_screen_x(1.0) == -270


# ---------------------------------------------------------------------------
# AC-2: follow() positions player at PLAYER_ANCHOR_PX
# ---------------------------------------------------------------------------

def test_follow_sets_offset_to_anchor_player() -> None:
    cam = Camera()
    # player at bloc 10 → px 300, desired offset = 300 - PLAYER_ANCHOR_PX
    cam.follow(10.0)
    expected_offset = World.to_px(10.0) - PLAYER_ANCHOR_PX
    assert cam.x_offset == max(0, expected_offset)


def test_follow_player_appears_at_anchor() -> None:
    cam = Camera()
    player_x = 15.0
    cam.follow(player_x)
    screen_x = cam.world_to_screen_x(player_x)
    assert screen_x == PLAYER_ANCHOR_PX


def test_follow_player_appears_at_anchor_various_positions() -> None:
    cam = Camera()
    for player_x in [7.0, 10.0, 20.0, 50.0]:
        cam.follow(player_x)
        assert cam.world_to_screen_x(player_x) == PLAYER_ANCHOR_PX, (
            f"Player at bloc {player_x} should appear at screen x={PLAYER_ANCHOR_PX}"
        )


def test_follow_updates_offset_on_each_call() -> None:
    cam = Camera()
    cam.follow(10.0)
    offset_at_10 = cam.x_offset
    cam.follow(20.0)
    offset_at_20 = cam.x_offset
    assert offset_at_20 > offset_at_10


# ---------------------------------------------------------------------------
# AC-3: x_offset never goes below 0
# ---------------------------------------------------------------------------

def test_follow_near_start_clamps_to_zero() -> None:
    """Player near x=0 → desired offset negative → clamped to 0."""
    cam = Camera()
    cam.follow(0.0)
    assert cam.x_offset == 0


def test_follow_clamps_when_player_before_anchor() -> None:
    cam = Camera()
    # player at bloc 1 → px 30, desired = 30 - 200 = -170 → clamped to 0
    cam.follow(1.0)
    assert cam.x_offset == 0


def test_camera_init_clamps_negative_offset() -> None:
    cam = Camera(x_offset=-100)
    assert cam.x_offset == 0


def test_x_offset_never_negative_after_follow_sequence() -> None:
    cam = Camera()
    for player_x in [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]:
        cam.follow(player_x)
        assert cam.x_offset >= 0, f"x_offset went negative at player_x={player_x}"


# ---------------------------------------------------------------------------
# AC-4: No pygame import (runtime check)
# ---------------------------------------------------------------------------

def test_no_pygame_in_camera_module() -> None:
    import engine.camera as cam_mod
    assert not hasattr(cam_mod, "pygame"), "engine.camera must not import pygame"
