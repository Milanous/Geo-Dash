"""
editor/level_io.py — Level persistence (save/load JSON).

Serialises a World grid to a versioned JSON file and restores it.
Only non-AIR tiles are stored; AIR is implicit.

Import rules: stdlib + engine only. Never import pygame, renderer, or ai.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from engine.world import TileType, World

# ---------------------------------------------------------------------------
# Tile type ↔ JSON string mapping (independent of enum names)
# ---------------------------------------------------------------------------

_TYPE_TO_STR: dict[TileType, str] = {
    TileType.SOLID:  "solid",
    TileType.SPIKE:  "spike",
    TileType.FINISH: "finish",
}

_STR_TO_TYPE: dict[str, TileType] = {v: k for k, v in _TYPE_TO_STR.items()}

_FORMAT_VERSION = 1

_MAX_NAME_LEN = 64


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitise_name(raw: str) -> str:
    """
    Sanitise a user-provided level name for safe filesystem usage.

    Rules:
      1. Replace spaces with underscores.
      2. Strip everything not in ``[a-zA-Z0-9_-]``.
      3. Truncate to 64 characters.
      4. If the result is empty or has no alphanumeric character → ``"untitled"``.
    """
    name = raw.replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    name = name[:_MAX_NAME_LEN]
    if not name or not re.search(r"[a-zA-Z0-9]", name):
        return "untitled"
    return name


def load_level_name(path: str | Path) -> str:
    """
    Read a level JSON file and return only the ``"name"`` field.

    This is a lightweight alternative to :func:`load_level` — it does NOT
    reconstruct a :class:`World`.

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("name", "untitled"))

def save_level(path: str | Path, world: World, name: str = "untitled") -> None:
    """
    Serialise *world* to a JSON file at *path*.

    Only non-AIR tiles are written (AIR is implicit). Parent directories are
    created automatically if they do not exist.

    Schema::

        {
          "version": 1,
          "name": "<name>",
          "width": <int>,
          "height": <int>,
          "tiles": [{"x": <int>, "y": <int>, "type": "solid"|"spike"}, ...]
        }

    Args:
        path:   Destination file path (str or pathlib.Path).
        world:  World instance to serialise.
        name:   Human-readable level name stored in the file (default "untitled").
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tiles: list[dict] = []
    for y in range(world.height):
        for x in range(world.width):
            tile = world.tile_at(x, y)
            if tile is not TileType.AIR:
                tiles.append({"x": x, "y": y, "type": _TYPE_TO_STR[tile]})

    data = {
        "version": _FORMAT_VERSION,
        "name": name,
        "width": world.width,
        "height": world.height,
        "tiles": tiles,
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_level(path: str | Path) -> World:
    """
    Load and return a World from a JSON level file at *path*.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError:        If the file's ``"version"`` field is not 1.
    """
    path = Path(path)
    # Let FileNotFoundError propagate naturally
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("version") != _FORMAT_VERSION:
        raise ValueError(
            f"Unsupported level file version: {data.get('version')!r} "
            f"(expected {_FORMAT_VERSION})"
        )

    world = World(data["width"], data["height"])

    for tile_data in data["tiles"]:
        tile_type = _STR_TO_TYPE[tile_data["type"]]
        world.set_tile(tile_data["x"], tile_data["y"], tile_type)

    return world
