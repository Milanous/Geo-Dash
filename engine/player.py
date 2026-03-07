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
    SPIKE_HITBOX_SHRINK,
    WALL_CORNER_FORGIVENESS,
    PlayerState,
)
from engine.world import TileType, World, is_spike


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
          2. Floor landing — player falling onto SOLID tiles.
          3. Wall collision — player running into SOLID tile side (kills).
          4. Hazard/finish detection.
        
        Landing vs Wall logic:
          - If player is FALLING (vy <= 0) AND player's bottom is near the
            top of the block (within LANDING_TOLERANCE), it's a landing.
          - Otherwise, hitting a SOLID block from the side is death.
        """
        # World bottom boundary — catches player even with no tiles (AC Story 1.6)
        if self.state.y <= 0.0:
            self.state.y = 0.0
            self.state.vy = 0.0
            self.state.on_ground = True

        if world is None:
            return

        # Tolerance for "coming from above" — player.y must be >= tile_top - this
        LANDING_TOLERANCE = 0.35  # ~10 pixels of grace for landing on corners

        # 1. Floor collision — check BOTH bottom corners for landing
        if self.state.vy <= 0.0:
            left_col = int(self.state.x)
            right_col = int(self.state.x + 0.9)
            bot_row = int(self.state.y)
            
            for col in (left_col, right_col):
                if world.tile_at(col, bot_row) == TileType.SOLID:
                    self.state.y = float(bot_row + 1)
                    self.state.vy = 0.0
                    self.state.on_ground = True
                    break

        # 2. Wall collision (front-face / right-side check)
        # Check blocks that the player's right edge overlaps
        wall_col = int(self.state.x + 0.9)
        for wall_row in (int(self.state.y), int(self.state.y + 0.9)):
            if world.tile_at(wall_col, wall_row) == TileType.SOLID:
                tile_top = float(wall_row + 1)
                
                # Can this be a landing instead of a wall hit?
                # Landing = player is falling AND player's bottom is close to tile's top
                can_land = (self.state.vy <= 0.0 and 
                           self.state.y >= tile_top - LANDING_TOLERANCE)
                
                if can_land:
                    # Land on top of the block
                    self.state.y = tile_top
                    self.state.vy = 0.0
                    self.state.on_ground = True
                else:
                    # True wall collision — player is beside the block, not above
                    # Only kill if player overlaps the block vertically
                    if self.state.y < tile_top:
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
                elif is_spike(t):
                    # Corner forgiveness: check if player is truly inside
                    # the shrunken spike hitbox, not just grazing the corner
                    if self._is_inside_spike_hitbox(c, r):
                        self.alive = False
                        self.state.finished = False

    # ------------------------------------------------------------------
    # Jump
    # ------------------------------------------------------------------

    def _is_wall_hit_valid(self, wall_row: int) -> bool:
        """
        Check if the player truly overlaps the wall's vertical hitbox.

        Corner forgiveness: the player must overlap the wall tile's vertical
        extent by at least WALL_CORNER_FORGIVENESS to count as a lethal hit.
        Grazing just the top or bottom corner is forgiven.

        Args:
            wall_row: Grid row of the wall tile.

        Returns:
            True if wall collision should kill the player.
        """
        # Player vertical bounds (same 0.9 size used elsewhere)
        py_bot = self.state.y
        py_top = self.state.y + 0.9

        # Shrunken wall vertical hitbox
        f = WALL_CORNER_FORGIVENESS
        wall_bot = wall_row + f
        wall_top = wall_row + 1.0 - f

        # Check if player overlaps the shrunken vertical zone
        return py_top > wall_bot and py_bot < wall_top

    def _is_inside_spike_hitbox(self, spike_col: int, spike_row: int) -> bool:
        """
        Check if the player's bounding box overlaps the shrunken spike hitbox.

        The spike hitbox is reduced by SPIKE_HITBOX_SHRINK on all sides,
        providing corner forgiveness — grazing the extreme edges of a spike
        won't kill the player.

        Args:
            spike_col: Grid column of the spike tile.
            spike_row: Grid row of the spike tile.

        Returns:
            True if player overlaps the shrunken spike zone.
        """
        # Player bounding box (same 0.9 size used elsewhere)
        px_left = self.state.x
        px_right = self.state.x + 0.9
        py_bot = self.state.y
        py_top = self.state.y + 0.9

        # Shrunken spike hitbox
        s = SPIKE_HITBOX_SHRINK
        sp_left = spike_col + s
        sp_right = spike_col + 1.0 - s
        sp_bot = spike_row + s
        sp_top = spike_row + 1.0 - s

        # AABB overlap test
        overlap_x = px_right > sp_left and px_left < sp_right
        overlap_y = py_top > sp_bot and py_bot < sp_top
        return overlap_x and overlap_y

    def jump(self) -> None:
        """
        Initiate a jump if the player is on the ground.

        No double-jump: if on_ground is False, this is a no-op.
        Sets vy = JUMP_VELOCITY and on_ground = False.
        """
        if self.state.on_ground:
            self.state.vy = JUMP_VELOCITY
            self.state.on_ground = False
