"""
tests/test_editor_camera.py

Story 3.2 — Editor Camera Pan

Headless — never imports pygame.
"""

import inspect
import re

import pytest

from editor.editor_camera import EditorCamera, PAN_SPEED_DEFAULT
from engine.physics import BLOCK_SIZE_PX


# ---------------------------------------------------------------------------
# 2.1 Initial offset is (0.0, 0.0)
# ---------------------------------------------------------------------------

def test_initial_offsets_are_zero() -> None:
    cam = EditorCamera()
    assert cam.x_offset == 0.0
    assert cam.y_offset == 0.0


# ---------------------------------------------------------------------------
# 2.2 pan_pixels(30, 0) shifts x_offset by 1 block
# ---------------------------------------------------------------------------

def test_pan_pixels_x_one_block() -> None:
    cam = EditorCamera()
    cam.pan_pixels(BLOCK_SIZE_PX, 0)
    assert cam.x_offset == pytest.approx(1.0)
    assert cam.y_offset == pytest.approx(0.0)


def test_pan_pixels_y_one_block_down_decreases_y_offset() -> None:
    """Dragging down (dy_px > 0) reduces y_offset (world moves up)."""
    cam = EditorCamera()
    cam.pan_blocks(0.0, 5.0)  # set y_offset=5 first
    cam.pan_pixels(0, BLOCK_SIZE_PX)  # drag down by 1 block worth of pixels
    assert cam.y_offset == pytest.approx(4.0)


def test_pan_pixels_y_up_increases_y_offset() -> None:
    """Dragging up (dy_px < 0) increases y_offset."""
    cam = EditorCamera()
    cam.pan_pixels(0, -BLOCK_SIZE_PX)
    assert cam.y_offset == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 2.3 pan_pixels negative X clamped to 0
# ---------------------------------------------------------------------------

def test_pan_pixels_negative_x_clamped() -> None:
    cam = EditorCamera()
    cam.pan_pixels(-999 * BLOCK_SIZE_PX, 0)
    assert cam.x_offset == 0.0


# ---------------------------------------------------------------------------
# 2.4 pan_pixels negative Y clamped to 0
# ---------------------------------------------------------------------------

def test_pan_pixels_negative_y_clamped() -> None:
    cam = EditorCamera()
    # Dragging down by huge amount when y_offset=0 → stays at 0
    cam.pan_pixels(0, 999 * BLOCK_SIZE_PX)
    assert cam.y_offset == 0.0


# ---------------------------------------------------------------------------
# 2.5 pan_blocks(5.0, 2.0) sets offsets correctly
# ---------------------------------------------------------------------------

def test_pan_blocks_sets_offsets() -> None:
    cam = EditorCamera()
    cam.pan_blocks(5.0, 2.0)
    assert cam.x_offset == pytest.approx(5.0)
    assert cam.y_offset == pytest.approx(2.0)


def test_pan_blocks_clamps_negative_to_zero() -> None:
    cam = EditorCamera()
    cam.pan_blocks(-100.0, -100.0)
    assert cam.x_offset == 0.0
    assert cam.y_offset == 0.0


# ---------------------------------------------------------------------------
# 2.6 screen_to_world at origin with zero offset
# ---------------------------------------------------------------------------

def test_screen_to_world_origin_zero_offset() -> None:
    """
    Screen (0, 0) with zero offset and screen_h=600:
      bx = 0 / 30 + 0 = 0.0
      by = (600 - 0) / 30 + 0 = 20.0  (top of a 20-row world)
    """
    cam = EditorCamera()
    bx, by = cam.screen_to_world(0, 0, screen_h=600)
    assert bx == pytest.approx(0.0)
    assert by == pytest.approx(600 / BLOCK_SIZE_PX)


def test_screen_to_world_bottom_left_zero_offset() -> None:
    """
    Screen (0, screen_h) → by = 0 (world bottom row).
    """
    cam = EditorCamera()
    screen_h = 600
    bx, by = cam.screen_to_world(0, screen_h, screen_h=screen_h)
    assert bx == pytest.approx(0.0)
    assert by == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 2.7 screen_to_world accounts for x_offset and y_offset
# ---------------------------------------------------------------------------

def test_screen_to_world_with_x_offset() -> None:
    cam = EditorCamera()
    cam.pan_blocks(10.0, 0.0)
    bx, by = cam.screen_to_world(0, 300, screen_h=600)
    assert bx == pytest.approx(10.0)  # 0/30 + 10


def test_screen_to_world_with_y_offset() -> None:
    cam = EditorCamera()
    cam.pan_blocks(0.0, 5.0)
    bx, by = cam.screen_to_world(0, 600, screen_h=600)
    # (600 - 600) / 30 + 5 = 5.0
    assert by == pytest.approx(5.0)


def test_screen_to_world_with_both_offsets() -> None:
    cam = EditorCamera()
    cam.pan_blocks(3.0, 2.0)
    bx, by = cam.screen_to_world(BLOCK_SIZE_PX, 0, screen_h=600)
    assert bx == pytest.approx(4.0)                        # 1 + 3
    assert by == pytest.approx(600 / BLOCK_SIZE_PX + 2.0)  # 20 + 2


# ---------------------------------------------------------------------------
# 2.8 step with "right" moves x_offset by pan_speed * dt
# ---------------------------------------------------------------------------

def test_step_right_moves_x_offset() -> None:
    speed = 5.0
    cam = EditorCamera(pan_speed=speed)
    cam.step(dt=1.0, keys={"right": True})
    assert cam.x_offset == pytest.approx(speed * 1.0)


def test_step_left_moves_x_offset_back() -> None:
    speed = 5.0
    cam = EditorCamera(pan_speed=speed)
    cam.pan_blocks(10.0, 0.0)
    cam.step(dt=1.0, keys={"left": True})
    assert cam.x_offset == pytest.approx(10.0 - speed)


def test_step_up_moves_y_offset() -> None:
    speed = 5.0
    cam = EditorCamera(pan_speed=speed)
    cam.step(dt=2.0, keys={"up": True})
    assert cam.y_offset == pytest.approx(speed * 2.0)


def test_step_down_moves_y_offset_back() -> None:
    speed = 5.0
    cam = EditorCamera(pan_speed=speed)
    cam.pan_blocks(0.0, 10.0)
    cam.step(dt=1.0, keys={"down": True})
    assert cam.y_offset == pytest.approx(10.0 - speed)


# ---------------------------------------------------------------------------
# 2.9 step with no active keys → offset unchanged
# ---------------------------------------------------------------------------

def test_step_no_keys_does_not_move() -> None:
    cam = EditorCamera()
    cam.pan_blocks(3.0, 7.0)
    cam.step(dt=1.0, keys={})
    assert cam.x_offset == pytest.approx(3.0)
    assert cam.y_offset == pytest.approx(7.0)


def test_step_all_false_does_not_move() -> None:
    cam = EditorCamera()
    cam.pan_blocks(2.0, 4.0)
    cam.step(dt=1.0, keys={"left": False, "right": False, "up": False, "down": False})
    assert cam.x_offset == pytest.approx(2.0)
    assert cam.y_offset == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# 2.10 Import guard — editor_camera.py must not import pygame
# ---------------------------------------------------------------------------

def test_editor_camera_does_not_import_pygame() -> None:
    import editor.editor_camera as mod
    src = inspect.getsource(mod)
    has_import = bool(re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE))
    assert not has_import, "editor/editor_camera.py must not contain 'import pygame'"
