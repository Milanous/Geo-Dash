"""
editor/editor.py — Level editor logic layer.

Owns the mutable World instance and the tile-type selection state.
Event wiring (mouse clicks, keyboard) lives in ui/editor_scene.py (Story 3.4).

Import rule: only engine/ and stdlib. NEVER import pygame, renderer, or ai.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

from engine.world import TileType, World, is_spike

# Cycle order for spike orientation (triggered by R key)
_SPIKE_CYCLE: list[TileType] = [
    TileType.SPIKE, TileType.SPIKE_RIGHT,
    TileType.SPIKE_DOWN, TileType.SPIKE_LEFT,
]


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

    def __init__(self, width: int = 10_000, height: int = 20) -> None:
        """
        Create a new editor with an empty World.

        The world auto-expands horizontally beyond *width* if needed,
        so there is no hard limit on level length.

        Args:
            width:  Initial number of grid columns (default 10 000 blocks).
            height: Number of grid rows (default 20 blocks).
        """
        self._world: World = World(width, height)
        self._selected: TileType = TileType.SOLID
        self._erase_mode: bool = False

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

    @property
    def erase_mode(self) -> bool:
        """True if the editor is in erase (delete) mode."""
        return self._erase_mode

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
        self._erase_mode = False

    def rotate_spike(self) -> None:
        """Cycle the spike orientation (UP → RIGHT → DOWN → LEFT → UP).

        If the current selection is a spike variant, cycle to the next.
        Otherwise, select SPIKE (UP) as starting point.
        """
        if is_spike(self._selected):
            idx = _SPIKE_CYCLE.index(self._selected)
            self._selected = _SPIKE_CYCLE[(idx + 1) % len(_SPIKE_CYCLE)]
        else:
            self._selected = TileType.SPIKE
        self._erase_mode = False

    def set_erase_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable erase mode.

        When erase mode is enabled, place_tile() will erase tiles instead.

        Args:
            enabled: True to enable erase mode, False to disable.
        """
        self._erase_mode = enabled

    # ------------------------------------------------------------------
    # Tile placement / erasure
    # ------------------------------------------------------------------

    def place_tile(self, bx: float, by: float) -> None:
        """
        Place the currently selected tile type at block position (bx, by).

        If erase_mode is enabled, erases the tile instead.
        Out-of-bounds coordinates are silently ignored (delegated to World).

        Args:
            bx: Horizontal block coordinate (float, floored to int grid index).
            by: Vertical block coordinate (float, floored to int grid index).
        """
        if self._erase_mode:
            self._world.set_tile(bx, by, TileType.AIR)
        else:
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
