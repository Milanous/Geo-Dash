"""
editor/editor_camera.py — Editor camera with 2D pan support.

Manages the viewport offset (in blocks) for the level editor.
Screen ↔ world coordinate conversion lives here; event wiring lives in
ui/editor_scene.py (Story 3.4).

Import rule: only engine/ and stdlib. NEVER import pygame, renderer, or ai.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

from engine.physics import BLOCK_SIZE_PX

# Default pan speed in blocks per second (arrow key navigation)
PAN_SPEED_DEFAULT: float = 5.0


class EditorCamera:
    """
    2D scrolling camera for the level editor.

    Tracks a viewport offset (x_offset, y_offset) in **block** units.
    Both offsets are always >= 0 to prevent scrolling outside world bounds.

    Coordinate conventions (project-wide):
      - World Y = 0 at the bottom, positive upward.
      - Screen Y = 0 at the top, positive downward (pygame).
      - Conversion: by = (screen_h - sy) / BLOCK_SIZE_PX + y_offset

    Not responsible for:
      - Rendering (editor_renderer.py — Story 3.4)
      - Receiving pygame events directly (ui/editor_scene.py — Story 3.4)
      - Tile placement logic (editor/editor.py — Story 3.1)
    """

    def __init__(self, pan_speed: float = PAN_SPEED_DEFAULT) -> None:
        """
        Initialise the editor camera at the world origin.

        Args:
            pan_speed: Arrow-key pan speed in blocks/second (default 5.0).
        """
        self.x_offset: float = 0.0  # blocks, always >= 0
        self.y_offset: float = 0.0  # blocks, always >= 0
        self._pan_speed: float = pan_speed

    # ------------------------------------------------------------------
    # Pan — pixels
    # ------------------------------------------------------------------

    def pan_pixels(self, dx_px: int, dy_px: int) -> None:
        """
        Pan the camera by a pixel delta (e.g. from a mouse drag).

        The delta is converted to blocks using BLOCK_SIZE_PX before being
        applied. Offsets are clamped to >= 0.

        Args:
            dx_px: Horizontal pixel delta (positive = pan right).
            dy_px: Vertical pixel delta (positive = pan down in screen space,
                   which means the world moves upward → y_offset decreases).
        """
        self.x_offset = max(0.0, self.x_offset + dx_px / BLOCK_SIZE_PX)
        # Screen Y is inverted relative to world Y: dragging down (dy_px > 0)
        # means we want to see content below, so world y_offset decreases.
        self.y_offset = max(0.0, self.y_offset - dy_px / BLOCK_SIZE_PX)

    # ------------------------------------------------------------------
    # Pan — blocks
    # ------------------------------------------------------------------

    def pan_blocks(self, dx_blk: float, dy_blk: float) -> None:
        """
        Pan the camera by a block delta.

        Offsets are clamped to >= 0.

        Args:
            dx_blk: Horizontal block delta (positive = pan right).
            dy_blk: Vertical block delta (positive = pan up in world space).
        """
        self.x_offset = max(0.0, self.x_offset + dx_blk)
        self.y_offset = max(0.0, self.y_offset + dy_blk)

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def screen_to_world(self, sx: int, sy: int, screen_h: int) -> tuple[float, float]:
        """
        Convert screen pixel coordinates to world block coordinates.

        Takes camera offset and Y-axis flip into account.

        Args:
            sx:       Screen X in pixels (0 = left edge).
            sy:       Screen Y in pixels (0 = top edge, pygame convention).
            screen_h: Total screen height in pixels (needed for Y flip).

        Returns:
            (bx, by) world block coordinates (floats).
        """
        bx = sx / BLOCK_SIZE_PX + self.x_offset
        by = (screen_h - sy) / BLOCK_SIZE_PX + self.y_offset
        return bx, by

    # ------------------------------------------------------------------
    # Keyboard step
    # ------------------------------------------------------------------

    def step(self, dt: float, keys: dict[str, bool]) -> None:
        """
        Advance the camera by keyboard input for one time step.

        The caller (ui/editor_scene.py) is responsible for building the
        *keys* dict from ``pygame.key.get_pressed()``.

        Expected keys: ``"left"``, ``"right"``, ``"up"``, ``"down"``.
        Missing keys default to False (no movement).

        Args:
            dt:   Time delta in seconds.
            keys: Mapping of direction name → pressed state.
        """
        speed = self._pan_speed * dt
        if keys.get("right"):
            self.pan_blocks(speed, 0.0)
        if keys.get("left"):
            self.pan_blocks(-speed, 0.0)
        if keys.get("up"):
            self.pan_blocks(0.0, speed)
        if keys.get("down"):
            self.pan_blocks(0.0, -speed)
