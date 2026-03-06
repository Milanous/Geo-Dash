"""
engine/physics.py — Single source of truth for all physics constants and PlayerState.

Import rules: only stdlib (dataclasses). Never import pygame, renderer, or ai.
[Source: architecture.md#Catégorie 1 and #Catégorie 6]
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Physics constants
# ---------------------------------------------------------------------------

PHYSICS_RATE: int = 240
"""Fixed physics update rate in Hz."""

DT: float = 1.0 / PHYSICS_RATE
"""Physics timestep in seconds per frame (≈ 0.004167 s)."""

GRAVITY: float = -0.958
"""Vertical acceleration in blocks/frame (negative = downward)."""

JUMP_VELOCITY: float = 12.36
"""Initial vertical velocity on jump, in blocks/frame."""

PLAYER_SPEED: float = 10.3761348998
"""Horizontal auto-scroll speed in blocks/second."""

BLOCK_SIZE_PX: int = 30
"""Pixel width/height of one block. Used only at engine/renderer boundary."""

ROTATION_SPEED_DEG_PER_STEP: float = 1.875
"""Clockwise rotation per physics step (deg/step) when the cube is in-air.

  450 °/s ÷ 240 Hz = 1.875 °/step  (matches official GD cube spin rate).
"""


# ---------------------------------------------------------------------------
# Player state
# ---------------------------------------------------------------------------

@dataclass
class PlayerState:
    """
    Pure data container for the player's physical state.
    No Pygame dependency — safe to use in headless simulation.

    Coordinate convention:
      x, y   — position in blocks (float)
      vy     — vertical velocity in blocks/frame (positive = upward)
      angle  — rotation in degrees (0 = upright, positive = clockwise)
    """

    x: float = 0.0
    y: float = 0.0
    vy: float = 0.0
    on_ground: bool = True
    angle: float = 0.0
    finished: bool = False
