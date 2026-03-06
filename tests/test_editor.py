"""
tests/test_editor.py

Story 3.1 — Level Editor Core: Grid Display & Tile Placement

Headless — never imports pygame.
"""

import inspect

import pytest

from editor.editor import Editor
from engine.world import TileType, World


# ---------------------------------------------------------------------------
# 2.1 Editor initialises an empty World (all AIR)
# ---------------------------------------------------------------------------

def test_editor_world_is_all_air_on_init() -> None:
    ed = Editor(width=10, height=5)
    for y in range(5):
        for x in range(10):
            assert ed.world.tile_at(x, y) == TileType.AIR, f"Expected AIR at ({x},{y})"


# ---------------------------------------------------------------------------
# 2.2 place_tile() places selected_tile_type at the correct position
# ---------------------------------------------------------------------------

def test_place_tile_places_selected_type() -> None:
    ed = Editor(width=10, height=5)
    ed.place_tile(3, 2)
    assert ed.world.tile_at(3, 2) == TileType.SOLID


def test_place_tile_spike_after_selection_change() -> None:
    ed = Editor(width=10, height=5)
    ed.set_selected_tile_type(TileType.SPIKE)
    ed.place_tile(5, 1)
    assert ed.world.tile_at(5, 1) == TileType.SPIKE


# ---------------------------------------------------------------------------
# 2.3 erase_tile() resets position to AIR
# ---------------------------------------------------------------------------

def test_erase_tile_resets_to_air() -> None:
    ed = Editor(width=10, height=5)
    ed.place_tile(4, 3)
    assert ed.world.tile_at(4, 3) == TileType.SOLID  # sanity
    ed.erase_tile(4, 3)
    assert ed.world.tile_at(4, 3) == TileType.AIR


# ---------------------------------------------------------------------------
# 2.4 set_selected_tile_type(SPIKE) updates selection
# ---------------------------------------------------------------------------

def test_set_selected_tile_type_spike() -> None:
    ed = Editor()
    assert ed.selected_tile_type == TileType.SOLID  # default
    ed.set_selected_tile_type(TileType.SPIKE)
    assert ed.selected_tile_type == TileType.SPIKE


def test_set_selected_tile_type_back_to_solid() -> None:
    ed = Editor()
    ed.set_selected_tile_type(TileType.SPIKE)
    ed.set_selected_tile_type(TileType.SOLID)
    assert ed.selected_tile_type == TileType.SOLID


# ---------------------------------------------------------------------------
# 2.5 place_tile() out-of-bounds does not crash
# ---------------------------------------------------------------------------

def test_place_tile_out_of_bounds_does_not_crash() -> None:
    ed = Editor(width=10, height=5)
    ed.place_tile(-1, 0)    # negative x
    ed.place_tile(0, -1)    # negative y
    ed.place_tile(100, 0)   # x >= width
    ed.place_tile(0, 100)   # y >= height
    ed.place_tile(999, 999) # both out


def test_erase_tile_out_of_bounds_does_not_crash() -> None:
    ed = Editor(width=10, height=5)
    ed.erase_tile(-5, -5)
    ed.erase_tile(50, 50)


# ---------------------------------------------------------------------------
# 2.6 set_selected_tile_type(AIR) raises ValueError
# ---------------------------------------------------------------------------

def test_set_selected_air_raises_value_error() -> None:
    ed = Editor()
    with pytest.raises(ValueError):
        ed.set_selected_tile_type(TileType.AIR)


def test_set_selected_air_does_not_change_selection() -> None:
    ed = Editor()
    ed.set_selected_tile_type(TileType.SPIKE)
    with pytest.raises(ValueError):
        ed.set_selected_tile_type(TileType.AIR)
    assert ed.selected_tile_type == TileType.SPIKE  # unchanged


# ---------------------------------------------------------------------------
# 2.7 editor/editor.py does not import pygame
# ---------------------------------------------------------------------------

def test_editor_does_not_import_pygame() -> None:
    import re
    import editor.editor as mod
    src = inspect.getsource(mod)
    # Match actual import statements, not occurrences in docstrings/comments.
    has_import = bool(re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE))
    assert not has_import, "editor/editor.py must not contain 'import pygame'"


# ---------------------------------------------------------------------------
# 2.8 Default selection is SOLID
# ---------------------------------------------------------------------------

def test_default_selected_tile_type_is_solid() -> None:
    ed = Editor()
    assert ed.selected_tile_type == TileType.SOLID


def test_place_tile_solid_by_default() -> None:
    ed = Editor(width=10, height=5)
    ed.place_tile(0, 0)
    assert ed.world.tile_at(0, 0) == TileType.SOLID


# ---------------------------------------------------------------------------
# 2.9 Round-trip: place → erase → AIR
# ---------------------------------------------------------------------------

def test_round_trip_place_then_erase_returns_air() -> None:
    ed = Editor(width=10, height=5)
    ed.place_tile(7, 4)
    assert ed.world.tile_at(7, 4) == TileType.SOLID
    ed.erase_tile(7, 4)
    assert ed.world.tile_at(7, 4) == TileType.AIR


def test_round_trip_spike_place_then_erase() -> None:
    ed = Editor(width=10, height=5)
    ed.set_selected_tile_type(TileType.SPIKE)
    ed.place_tile(2, 1)
    ed.erase_tile(2, 1)
    assert ed.world.tile_at(2, 1) == TileType.AIR
