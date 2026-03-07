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

GRAVITY: float = -114.96
"""Vertical acceleration in blocks/s² (negative = downward).

Derived from GD pixel physics: 0.958 px/frame² × 60² fps² ÷ 30 px/block.
"""

JUMP_VELOCITY: float = 24.72
"""Initial vertical velocity on jump, in blocks/s.

Derived from GD pixel physics: 12.36 px/frame × 60 fps ÷ 30 px/block.
"""

PLAYER_SPEED: float = 10.3761348998
"""Horizontal auto-scroll speed in blocks/second."""

BLOCK_SIZE_PX: int = 30
"""Pixel width/height of one block. Used only at engine/renderer boundary."""

ROTATION_SPEED_DEG_PER_STEP: float = 1.875
"""Clockwise rotation per physics step (deg/step) when the cube is in-air.

  450 °/s ÷ 240 Hz = 1.875 °/step  (matches official GD cube spin rate).
"""

SPIKE_HITBOX_SHRINK: float = 0.18
"""Inward margin (in blocks) to shrink spike hitboxes for corner forgiveness.

This makes spike collisions more forgiving when grazing corners — a common
"feel good" tweak in precision platformers like Geometry Dash.
~0.18 blocks ≈ 5.4 pixels de tolérance sur les angles.
"""

WALL_CORNER_FORGIVENESS: float = 0.22
"""Vertical tolerance (in blocks) for wall collision corner forgiveness.

When the player grazes just the top or bottom corner of a SOLID block,
this margin prevents an unfair death. The player must overlap the wall's
vertical hitbox by at least this amount to trigger a kill.
~0.22 blocks ≈ 6.6 pixels de tolérance sur les angles des murs.
"""

SPAWN_X: float = 5.0
"""Default horizontal spawn position in blocks."""

SPAWN_Y: float = 5.0
"""Default vertical spawn position in blocks (must be above floor)."""


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
