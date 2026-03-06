"""
engine/camera.py — Scrolling camera for horizontal world tracking.

Converts world block coordinates to screen pixel coordinates via an x_offset.
The camera follows the player keeping them at a fixed anchor position.

Import rules: only engine.world (for World.to_px). Never import pygame, renderer, ai.
[Source: architecture.md#Catégorie 2]
"""

from __future__ import annotations

from engine.world import World


# Fixed screen X position where the player appears (pixels from left edge)
PLAYER_ANCHOR_PX: int = 200


class Camera:
    """
    Horizontal scrolling camera.

    Attributes:
        x_offset: Pixel column of the world visible at screen x=0.
                  Always >= 0 (world never scrolls left of its start).
    """

    def __init__(self, x_offset: int = 0) -> None:
        self.x_offset: int = max(0, x_offset)

    def world_to_screen_x(self, bloc_x: float) -> int:
        """
        Convert a world X position (blocks) to a screen X position (pixels).

        Args:
            bloc_x: World X coordinate in blocks.

        Returns:
            Screen X position in pixels.
        """
        return World.to_px(bloc_x) - self.x_offset

    def follow(self, player_x: float) -> None:
        """
        Update x_offset so the player appears at PLAYER_ANCHOR_PX on screen.

        The offset is clamped to >= 0 to prevent scrolling before world start.

        Args:
            player_x: Player X position in blocks.
        """
        desired = World.to_px(player_x) - PLAYER_ANCHOR_PX
        self.x_offset = max(0, desired)
