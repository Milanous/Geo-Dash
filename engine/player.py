"""
engine/player.py — Player physics: movement, gravity, collision, jump.

Import rules: only engine.physics and engine.world. Never import pygame, renderer, ai.
[Source: architecture.md#Catégorie 1, #Catégorie 6, #Process Patterns]
"""

from __future__ import annotations

from engine.physics import (
    GRAVITY,
    JUMP_VELOCITY,
    PLAYER_SPEED,
    ROTATION_SPEED_DEG_PER_STEP,
    PlayerState,
)
from engine.world import TileType, World


class Player:
    """
    Single human-controlled player with physics and collision.

    Coordinate convention (y-axis):
      - y=0 is the world floor level (bottom boundary).
      - Positive y = upward.
      - GRAVITY is negative → vy decreases each step → player falls.
      - JUMP_VELOCITY is positive → initial upward velocity.

    The player is a 1×1 block bounding box positioned at (state.x, state.y)
    where (x, y) is the bottom-left corner in block coordinates.
    """

    def __init__(self, start_x: float = 0.0, start_y: float = 1.0) -> None:
        self.state = PlayerState(
            x=start_x,
            y=start_y,
            vy=0.0,
            on_ground=False,
            angle=0.0,
        )
        self.alive: bool = True

    # ------------------------------------------------------------------
    # Main physics step
    # ------------------------------------------------------------------

    def update(self, dt: float, world: World | None = None) -> None:
        """
        Advance physics by one timestep dt (seconds).

        Order: horizontal move → gravity → vertical move → collision resolve.

        Args:
            dt:    Physics timestep in seconds (typically DT = 1/240).
            world: Level grid for tile collision. If None, only world
                   boundary (y <= 0) is enforced.
        """
        if not self.alive or self.state.finished:
            return

        # 1. Horizontal auto-scroll (AC Story 1.5: x += PLAYER_SPEED * dt)
        self.state.x += PLAYER_SPEED * dt

        # 2. Gravity (dt-scaled, blocks/s²)
        self.state.vy += GRAVITY * dt

        # 3. Vertical position update
        self.state.y += self.state.vy * dt
        self.state.on_ground = False

        # 4. Collision resolution
        self._resolve_collision(world)

        # 5. Finish detection — world edge
        if world is not None and self.state.x >= world.width - 1:
            self.state.finished = True
            return

        if self.state.finished:
            return

        # 6. Rotation update (after collision so on_ground is final)
        if self.state.on_ground:
            self.state.angle = 0.0
        else:
            # Clockwise rotation: angle grows positively
            self.state.angle = (self.state.angle + ROTATION_SPEED_DEG_PER_STEP) % 360.0

    # ------------------------------------------------------------------
    # Collision resolution
    # ------------------------------------------------------------------

    def _resolve_collision(self, world: World | None) -> None:
        """
        Resolve player against world boundary and tile grid.

        Resolution order:
          1. World bottom boundary (y <= 0) — always enforced.
          2. Tile SOLID/SPIKE detection based on current (x, y).
        """
        # World bottom boundary — catches player even with no tiles (AC Story 1.6)
        if self.state.y <= 0.0:
            self.state.y = 0.0
            self.state.vy = 0.0
            self.state.on_ground = True

        if world is None:
            return

        # Tile collision
        col = int(self.state.x)
        row = int(self.state.y)
        tile = world.tile_at(col, row)

        # 1. Floor collision (bottom-left corner check)
        if tile == TileType.SOLID and self.state.vy <= 0.0:
            # Snap to the top surface of this tile row
            self.state.y = float(row + 1)
            self.state.vy = 0.0
            self.state.on_ground = True

        # 2. Wall collision (front-face / right-side check)
        # After floor resolution, check if the player's right edge overlaps
        # a SOLID tile at the player's body height.
        wall_col = int(self.state.x + 0.9)
        for wall_row in (int(self.state.y), int(self.state.y + 0.9)):
            if world.tile_at(wall_col, wall_row) == TileType.SOLID:
                # Not a wall hit if the player is standing on top of that tile
                if self.state.y < float(wall_row + 1):
                    self.alive = False
                    self.state.finished = False
                    return

        # 3. Bounding-box overlap for hazards and finish lines
        # Box approx: x to x+0.9, y to y+0.9 to avoid edge clipping
        left, right = int(self.state.x), int(self.state.x + 0.9)
        bot, top = int(self.state.y), int(self.state.y + 0.9)

        for c in (left, right):
            for r in (bot, top):
                t = world.tile_at(c, r)
                if t == TileType.FINISH:
                    self.state.finished = True
                elif t == TileType.SPIKE:
                    self.alive = False
                    self.state.finished = False

    # ------------------------------------------------------------------
    # Jump
    # ------------------------------------------------------------------

    def jump(self) -> None:
        """
        Initiate a jump if the player is on the ground.

        No double-jump: if on_ground is False, this is a no-op.
        Sets vy = JUMP_VELOCITY and on_ground = False.
        """
        if self.state.on_ground:
            self.state.vy = JUMP_VELOCITY
            self.state.on_ground = False
