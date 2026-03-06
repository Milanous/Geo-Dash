"""
editor/editor.py — Level editor logic layer.

Owns the mutable World instance and the tile-type selection state.
Event wiring (mouse clicks, keyboard) lives in ui/editor_scene.py (Story 3.4).

Import rule: only engine/ and stdlib. NEVER import pygame, renderer, or ai.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

from engine.world import TileType, World


class Editor:
    """
    Pure-logic editor that wraps a World and tracks the selected tile type.

    Responsibilities:
    - Hold the editable World instance.
    - Track which TileType is currently selected for placement.
    - Expose place_tile() and erase_tile() for event handlers (Story 3.4).

    Not responsible for:
    - Rendering (editor_renderer.py — Story 3.4)
    - Camera pan / screen→bloc conversion (Story 3.2)
    - Save/Load (level_io.py — Story 3.3)
    """

    def __init__(self, width: int = 100, height: int = 20) -> None:
        """
        Create a new editor with an empty World.

        Args:
            width:  Number of grid columns (default 100 blocks).
            height: Number of grid rows (default 20 blocks).
        """
        self._world: World = World(width, height)
        self._selected: TileType = TileType.SOLID

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def world(self) -> World:
        """The editable World instance (read-only reference)."""
        return self._world

    @property
    def selected_tile_type(self) -> TileType:
        """Currently selected tile type for placement."""
        return self._selected

    # ------------------------------------------------------------------
    # Tile selection
    # ------------------------------------------------------------------

    def set_selected_tile_type(self, tile_type: TileType) -> None:
        """
        Change the active tile type for placement.

        Args:
            tile_type: The new tile type. Must not be TileType.AIR — erasing
                       is done exclusively via erase_tile().

        Raises:
            ValueError: If tile_type is TileType.AIR.
        """
        if tile_type is TileType.AIR:
            raise ValueError(
                "TileType.AIR cannot be selected for placement. "
                "Use erase_tile() to remove tiles."
            )
        self._selected = tile_type

    # ------------------------------------------------------------------
    # Tile placement / erasure
    # ------------------------------------------------------------------

    def place_tile(self, bx: float, by: float) -> None:
        """
        Place the currently selected tile type at block position (bx, by).

        Out-of-bounds coordinates are silently ignored (delegated to World).

        Args:
            bx: Horizontal block coordinate (float, floored to int grid index).
            by: Vertical block coordinate (float, floored to int grid index).
        """
        self._world.set_tile(bx, by, self._selected)

    def erase_tile(self, bx: float, by: float) -> None:
        """
        Erase the tile at block position (bx, by) by setting it to AIR.

        Out-of-bounds coordinates are silently ignored (delegated to World).

        Args:
            bx: Horizontal block coordinate.
            by: Vertical block coordinate.
        """
        self._world.set_tile(bx, by, TileType.AIR)
