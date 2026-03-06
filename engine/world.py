"""
engine/world.py — Tile grid and coordinate system.

Owns all bloc ↔ pixel conversions. Engine and AI modules work exclusively
in float blocks; conversion to pixels happens only at the renderer boundary.

Import rules: only stdlib + engine.physics. Never import pygame, renderer, or ai.
[Source: architecture.md#Catégorie 2]
"""

from __future__ import annotations

from enum import Enum, auto

from engine.physics import BLOCK_SIZE_PX


# ---------------------------------------------------------------------------
# Tile types
# ---------------------------------------------------------------------------

class TileType(Enum):
    """All tile physics types used in the grid."""
    AIR    = auto()
    SOLID  = auto()
    SPIKE  = auto()
    FINISH = auto()


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class World:
    """
    Tile-grid level container and single owner of bloc ↔ pixel conversion.

    Coordinate convention:
      - All public methods accept block coordinates (float).
      - Grid storage uses integer indices (floor of float input).
      - Out-of-bounds access always returns TileType.AIR — never raises.
    """

    BLOCK_SIZE_PX: int = BLOCK_SIZE_PX  # mirrors engine.physics constant

    def __init__(self, width: int, height: int) -> None:
        """
        Create an empty world of *width* × *height* blocks, filled with AIR.

        Args:
            width:  Number of columns (horizontal blocks).
            height: Number of rows (vertical blocks).
        """
        self.width  = width
        self.height = height
        # _grid[row][col] — indexed as _grid[y][x]
        self._grid: list[list[TileType]] = [
            [TileType.AIR] * width for _ in range(height)
        ]

    # ------------------------------------------------------------------
    # Coordinate conversions (static — no instance state needed)
    # ------------------------------------------------------------------

    @staticmethod
    def to_px(bloc: float) -> int:
        """Convert a block coordinate / distance to pixels (truncates)."""
        return int(bloc * World.BLOCK_SIZE_PX)

    @staticmethod
    def to_bloc(px: int | float) -> float:
        """Convert a pixel coordinate / distance to blocks (float)."""
        return px / World.BLOCK_SIZE_PX

    # ------------------------------------------------------------------
    # Grid access
    # ------------------------------------------------------------------

    def tile_at(self, bx: float, by: float) -> TileType:
        """
        Return the tile type at block position (bx, by).

        Float inputs are floored to integer grid indices.
        Out-of-bounds positions return TileType.AIR (no exception).
        """
        col = int(bx)
        row = int(by)
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return TileType.AIR
        return self._grid[row][col]

    def set_tile(self, bx: float, by: float, tile_type: TileType) -> None:
        """
        Set the tile type at block position (bx, by).

        Float inputs are floored to integer grid indices.
        Silently ignores out-of-bounds positions.
        """
        col = int(bx)
        row = int(by)
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return
        self._grid[row][col] = tile_type
