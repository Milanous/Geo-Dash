"""
tests/test_finish.py — Tests for TileType.FINISH, finish detection, and JSON round-trip.

Story 6.4 — AC 1-8.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

from editor.level_io import load_level, save_level
from engine.physics import PlayerState
from engine.player import Player
from engine.world import TileType, World


# ── 9.1 TileType.FINISH exists ──────────────────────────────────────


def test_tiletype_finish_exists() -> None:
    """TileType enum must include a FINISH member."""
    assert hasattr(TileType, "FINISH")
    assert TileType.FINISH is not TileType.AIR
    assert TileType.FINISH is not TileType.SOLID
    assert TileType.FINISH is not TileType.SPIKE


# ── 9.2 PlayerState.finished defaults to False ──────────────────────


def test_playerstate_finished_default() -> None:
    """PlayerState.finished must be False at init."""
    state = PlayerState()
    assert state.finished is False


# ── 9.3 Player on FINISH tile → finished == True ────────────────────


def test_player_finish_tile() -> None:
    """Player stepping on a FINISH tile becomes finished after update."""
    world = World(20, 10)
    # Solid floor except column 10 which is FINISH
    for col in range(20):
        world.set_tile(col, 0, TileType.SOLID)
    world.set_tile(10, 0, TileType.FINISH)

    player = Player(start_x=10.0, start_y=1.0)
    # Force on ground so physics won't drop the player much
    player.state.on_ground = True
    player.state.vy = 0.0

    assert player.state.finished is False
    player.update(1 / 240, world)
    assert player.state.finished is True


def test_player_finish_tile_overlap() -> None:
    """Player bounding box overlapping a FINISH tile on its right edge triggers finish."""
    world = World(20, 10)
    world.set_tile(10, 0, TileType.FINISH)

    # Placed slightly before the tile, right edge crosses x=10
    player = Player(start_x=9.5, start_y=0.0)
    player.state.on_ground = True
    player.state.vy = 0.0

    assert player.state.finished is False
    # Next physics step keeps player overlapping x=10
    player.update(1 / 240, world)
    assert player.state.finished is True


# ── 9.4 Player at world edge → finished == True ─────────────────────


def test_player_finish_world_edge() -> None:
    """Player reaching x >= world.width - 1 becomes finished."""
    world = World(20, 10)
    for col in range(20):
        world.set_tile(col, 0, TileType.SOLID)

    # Place player near the right edge
    player = Player(start_x=19.0, start_y=1.0)
    player.state.on_ground = True
    player.state.vy = 0.0

    player.update(1 / 240, world)
    assert player.state.finished is True


# ── 9.5 JSON round-trip with FINISH tile ────────────────────────────


def test_json_roundtrip_finish() -> None:
    """A world with FINISH tiles survives save → load round-trip."""
    world = World(10, 5)
    world.set_tile(3, 0, TileType.SOLID)
    world.set_tile(9, 2, TileType.FINISH)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test_finish.json"
        save_level(path, world, name="finish_test")

        # Verify JSON contains "finish"
        data = json.loads(path.read_text(encoding="utf-8"))
        types_in_json = {t["type"] for t in data["tiles"]}
        assert "finish" in types_in_json

        # Reload and compare
        loaded = load_level(path)
        assert loaded.tile_at(9, 2) is TileType.FINISH
        assert loaded.tile_at(3, 0) is TileType.SOLID


# ── 9.6 Load old JSON without FINISH → no error ─────────────────────


def test_load_old_json_no_finish() -> None:
    """An old-format JSON file (no FINISH tiles) loads without error."""
    data = {
        "version": 1,
        "name": "old_level",
        "width": 10,
        "height": 5,
        "tiles": [
            {"x": 0, "y": 0, "type": "solid"},
            {"x": 1, "y": 0, "type": "spike"},
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "old.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        world = load_level(path)
        assert world.tile_at(0, 0) is TileType.SOLID
        assert world.tile_at(1, 0) is TileType.SPIKE


# ── 9.7 Import guard — player.py doesn't import pygame ──────────────


def test_player_no_pygame_import() -> None:
    """engine/player.py must not import pygame (headless-safe)."""
    source = Path("engine/player.py").read_text(encoding="utf-8")
    in_docstring = False
    for line in source.splitlines():
        stripped = line.strip()
        # Toggle docstring state on triple-quote boundaries
        if '"""' in stripped:
            count = stripped.count('"""')
            if count == 1:
                in_docstring = not in_docstring
            # count >= 2 means open+close on same line — stays outside
            continue
        if in_docstring:
            continue
        # Skip comments
        if stripped.startswith("#"):
            continue
        assert "import pygame" not in stripped, f"Found pygame import: {stripped}"


# ── Extra: finished player does not update physics ───────────────────


def test_finished_player_no_physics() -> None:
    """Once finished, further update() calls do not change position."""
    world = World(20, 10)
    for col in range(20):
        world.set_tile(col, 0, TileType.SOLID)
    world.set_tile(10, 0, TileType.FINISH)

    player = Player(start_x=10.0, start_y=1.0)
    player.state.on_ground = True
    player.state.vy = 0.0
    player.update(1 / 240, world)
    assert player.state.finished is True

    x_after_finish = player.state.x
    player.update(1 / 240, world)
    # Position must not change once finished
    assert player.state.x == x_after_finish
