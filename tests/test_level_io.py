"""
tests/test_level_io.py — Tests for editor/level_io.py (Story 3.3).

All tests are headless (no pygame, no display). Files are written to
pytest's tmp_path fixture so nothing pollutes the repo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.world import TileType, World
from editor.level_io import load_level, load_level_name, sanitise_name, save_level


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def worlds_equal(w1: World, w2: World) -> bool:
    """Return True if w1 and w2 have identical dimensions and tile layout."""
    if w1.width != w2.width or w1.height != w2.height:
        return False
    for y in range(w1.height):
        for x in range(w1.width):
            if w1.tile_at(x, y) != w2.tile_at(x, y):
                return False
    return True


# ---------------------------------------------------------------------------
# Task 2.1 — save_level creates a file
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    save_level(path, world)
    assert path.exists()


# ---------------------------------------------------------------------------
# Task 2.2 — JSON contains required top-level fields
# ---------------------------------------------------------------------------

def test_save_json_contains_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    save_level(path, world, name="test_level")
    data = json.loads(path.read_text())
    assert data["version"] == 1
    assert data["name"] == "test_level"
    assert data["width"] == 10
    assert data["height"] == 5
    assert "tiles" in data


# ---------------------------------------------------------------------------
# Task 2.3 — only non-AIR tiles are written
# ---------------------------------------------------------------------------

def test_save_only_non_air_tiles_written(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    world.set_tile(3, 0, TileType.SOLID)
    world.set_tile(7, 2, TileType.SPIKE)
    save_level(path, world)
    data = json.loads(path.read_text())
    assert len(data["tiles"]) == 2
    tile_coords = {(t["x"], t["y"]) for t in data["tiles"]}
    assert (3, 0) in tile_coords
    assert (7, 2) in tile_coords


# ---------------------------------------------------------------------------
# Task 2.4 — load_level returns World with correct tiles
# ---------------------------------------------------------------------------

def test_load_returns_world_with_correct_tiles(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    world.set_tile(3, 0, TileType.SOLID)
    world.set_tile(7, 2, TileType.SPIKE)
    save_level(path, world)

    loaded = load_level(path)
    assert loaded.tile_at(3, 0) == TileType.SOLID
    assert loaded.tile_at(7, 2) == TileType.SPIKE
    assert loaded.tile_at(0, 0) == TileType.AIR


# ---------------------------------------------------------------------------
# Task 2.5 — round-trip produces identical World
# ---------------------------------------------------------------------------

def test_round_trip_produces_identical_world(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(30, 15)
    world.set_tile(0, 0, TileType.SOLID)
    world.set_tile(15, 7, TileType.SPIKE)
    world.set_tile(29, 14, TileType.SOLID)
    save_level(path, world)

    loaded = load_level(path)
    assert worlds_equal(world, loaded)


# ---------------------------------------------------------------------------
# Task 2.6 — empty world (all AIR) → tiles: []
# ---------------------------------------------------------------------------

def test_save_empty_world_tiles_array_empty(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    save_level(path, world)
    data = json.loads(path.read_text())
    assert data["tiles"] == []


# ---------------------------------------------------------------------------
# Task 2.7 — load_level with version != 1 raises ValueError
# ---------------------------------------------------------------------------

def test_load_raises_valueerror_on_wrong_version(tmp_path: Path) -> None:
    path = tmp_path / "future.json"
    path.write_text(json.dumps({"version": 2, "name": "x", "width": 10, "height": 5, "tiles": []}))
    with pytest.raises(ValueError, match="version"):
        load_level(path)


# ---------------------------------------------------------------------------
# Task 2.8 — load_level on missing file raises FileNotFoundError
# ---------------------------------------------------------------------------

def test_load_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_level(tmp_path / "does_not_exist.json")


# ---------------------------------------------------------------------------
# Task 2.9 — import guard: level_io.py does not import pygame
# ---------------------------------------------------------------------------

def test_level_io_does_not_import_pygame() -> None:
    src_path = Path(__file__).parent.parent / "editor" / "level_io.py"
    src = src_path.read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import pygame|from pygame)", src, re.MULTILINE), (
        "editor/level_io.py must not import pygame"
    )


# ---------------------------------------------------------------------------
# Task 2.10 — save_level creates parent directories
# ---------------------------------------------------------------------------

def test_save_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deep" / "level.json"
    world = World(10, 5)
    save_level(path, world)
    assert path.exists()


# ---------------------------------------------------------------------------
# Extra — tile type strings in JSON are lowercase ("solid" / "spike")
# ---------------------------------------------------------------------------

def test_save_tile_type_strings_are_lowercase(tmp_path: Path) -> None:
    path = tmp_path / "level.json"
    world = World(10, 5)
    world.set_tile(1, 1, TileType.SOLID)
    world.set_tile(2, 2, TileType.SPIKE)
    save_level(path, world)
    data = json.loads(path.read_text())
    types = {t["type"] for t in data["tiles"]}
    assert types == {"solid", "spike"}


# ===========================================================================
# Story 6.1 — sanitise_name tests (Task 4)
# ===========================================================================


# ---------------------------------------------------------------------------
# Task 4.1 — normal alphanumeric name → unchanged
# ---------------------------------------------------------------------------

def test_sanitise_name_normal_unchanged() -> None:
    assert sanitise_name("my_level") == "my_level"


# ---------------------------------------------------------------------------
# Task 4.2 — spaces → replaced by underscore
# ---------------------------------------------------------------------------

def test_sanitise_name_spaces_to_underscore() -> None:
    assert sanitise_name("Mon Niveau") == "Mon_Niveau"


# ---------------------------------------------------------------------------
# Task 4.3 — special characters removed
# ---------------------------------------------------------------------------

def test_sanitise_name_special_chars_removed() -> None:
    assert sanitise_name("Level!01?") == "Level01"


def test_sanitise_name_complex_example() -> None:
    assert sanitise_name("Mon Niveau! 01") == "Mon_Niveau_01"


# ---------------------------------------------------------------------------
# Task 4.4 — empty string → "untitled"
# ---------------------------------------------------------------------------

def test_sanitise_name_empty_string() -> None:
    assert sanitise_name("") == "untitled"


# ---------------------------------------------------------------------------
# Task 4.5 — name > 64 chars → truncated
# ---------------------------------------------------------------------------

def test_sanitise_name_truncated_at_64() -> None:
    long_name = "a" * 100
    result = sanitise_name(long_name)
    assert len(result) == 64
    assert result == "a" * 64


# ---------------------------------------------------------------------------
# Task 4.6 — only dashes/underscores (no alphanumeric) → "untitled"
# ---------------------------------------------------------------------------

def test_sanitise_name_only_dashes_untitled() -> None:
    assert sanitise_name("---") == "untitled"


def test_sanitise_name_only_underscores_untitled() -> None:
    assert sanitise_name("___") == "untitled"


# ---------------------------------------------------------------------------
# Task 4.7 — load_level_name returns JSON "name" field
# ---------------------------------------------------------------------------

def test_load_level_name_returns_name(tmp_path: Path) -> None:
    path = tmp_path / "named.json"
    world = World(10, 5)
    save_level(path, world, name="My Cool Level")
    assert load_level_name(path) == "My Cool Level"
