"""
ai/simulation.py — NumPy vectorised population simulation.

Runs N agents in parallel using NumPy arrays for physics.
Brain evaluation remains a Python loop (unavoidable without compilation).

Import rules: only stdlib + engine + ai + numpy.  Never import pygame or renderer.
[Source: architecture.md#Catégorie 5]
"""

from __future__ import annotations

import numpy as np

from ai.brain import Brain
from ai.training_config import TrainingConfig
from engine.physics import GRAVITY, JUMP_VELOCITY, PLAYER_SPEED, PHYSICS_RATE, SPIKE_HITBOX_SHRINK, SPAWN_X, SPAWN_Y
from engine.world import TileType, World, is_spike


class PopulationSim:
    """Vectorised headless simulation for a population of AI agents."""

    def __init__(
        self,
        brains: list[Brain],
        level: World,
        config: TrainingConfig,
    ) -> None:
        n = len(brains)
        self.n = n
        self.brains = brains
        self.level = level
        self.config = config
        self.max_steps = int(config.max_seconds_per_gen * PHYSICS_RATE)

        # NumPy state arrays — shape (n,)
        self.x: np.ndarray = np.full(n, SPAWN_X)
        self.y: np.ndarray = np.full(n, SPAWN_Y)
        self.vy: np.ndarray = np.zeros(n)
        self.on_ground: np.ndarray = np.zeros(n, dtype=bool)
        self.alive: np.ndarray = np.ones(n, dtype=bool)
        self.finished: np.ndarray = np.zeros(n, dtype=bool)
        self.max_x: np.ndarray = self.x.copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self, dt: float) -> None:
        """Advance one physics step for all alive agents."""
        mask = self.alive & ~self.finished

        # Gravity (GRAVITY is negative → vy decreases)
        self.vy[mask] += GRAVITY * dt

        # Position update
        self.y[mask] += self.vy[mask] * dt
        self.x[mask] += PLAYER_SPEED * dt
        self.on_ground[mask] = False

        # Floor clamp (world bottom boundary)
        at_floor = self.y <= 0.0
        self.y = np.maximum(self.y, 0.0)
        np.putmask(self.vy, at_floor, 0.0)
        self.on_ground |= at_floor

        # Track maximum X reached
        np.maximum(self.max_x, self.x, out=self.max_x)

        # Cap at level width
        np.minimum(self.max_x, float(self.level.width), out=self.max_x)

        # Collision resolution (order matches engine/player.py)
        self._resolve_floors()
        self._resolve_walls()
        self._resolve_hazards()

        # Finish detection — world edge
        edge = self.alive & ~self.finished & (self.x >= self.level.width - 1)
        self.finished |= edge

        # Brain evaluation (jump decisions)
        self._evaluate_brains()

    def fitness(self) -> np.ndarray:
        """Return fitness array — max distance reached per agent."""
        return self.max_x.copy()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_floors(self) -> None:
        """Land alive agents on top of SOLID tiles (mirrors engine/player.py)."""
        alive_indices = np.where(self.alive & ~self.finished)[0]
        for i in alive_indices:
            if self.vy[i] > 0.0:
                continue
            left_col = int(self.x[i])
            right_col = int(self.x[i] + 0.9)
            bot_row = int(self.y[i])
            for col in (left_col, right_col):
                if self.level.tile_at(col, bot_row) == TileType.SOLID:
                    self.y[i] = float(bot_row + 1)
                    self.vy[i] = 0.0
                    self.on_ground[i] = True
                    break

    def _resolve_walls(self) -> None:
        """Kill alive agents hitting the front face of a SOLID block.

        Mirrors the wall-collision logic from engine/player.py:
        check the column at the player's right edge; if SOLID and the
        agent cannot land on it (not falling or not near the top), it dies.
        """
        LANDING_TOLERANCE = 0.35
        alive_indices = np.where(self.alive & ~self.finished)[0]
        for i in alive_indices:
            wall_col = int(self.x[i] + 0.9)
            for wall_row in (int(self.y[i]), int(self.y[i] + 0.9)):
                if self.level.tile_at(wall_col, wall_row) == TileType.SOLID:
                    tile_top = float(wall_row + 1)
                    can_land = (self.vy[i] <= 0.0 and
                                self.y[i] >= tile_top - LANDING_TOLERANCE)
                    if can_land:
                        self.y[i] = tile_top
                        self.vy[i] = 0.0
                        self.on_ground[i] = True
                    elif self.y[i] < tile_top:
                        self.alive[i] = False
                        break

    def _resolve_hazards(self) -> None:
        """Check spikes (4-corner + shrunken hitbox) and FINISH tiles.

        Mirrors engine/player.py bounding-box overlap for hazards/finish.
        """
        s = SPIKE_HITBOX_SHRINK
        alive_indices = np.where(self.alive & ~self.finished)[0]
        for i in alive_indices:
            left = int(self.x[i])
            right = int(self.x[i] + 0.9)
            bot = int(self.y[i])
            top = int(self.y[i] + 0.9)
            for c in (left, right):
                for r in (bot, top):
                    t = self.level.tile_at(c, r)
                    if t == TileType.FINISH:
                        self.finished[i] = True
                    elif is_spike(t):
                        # Shrunken spike hitbox
                        sp_left = c + s
                        sp_right = c + 1.0 - s
                        sp_bot = r + s
                        sp_top = r + 1.0 - s
                        px_right = self.x[i] + 0.9
                        py_top = self.y[i] + 0.9
                        if (px_right > sp_left and self.x[i] < sp_right and
                                py_top > sp_bot and self.y[i] < sp_top):
                            self.alive[i] = False

    def _evaluate_brains(self) -> None:
        """Ask each alive agent's brain whether to jump (on_ground only)."""
        alive_indices = np.where(self.alive & ~self.finished)[0]
        for i in alive_indices:
            if not self.on_ground[i]:
                continue
            if self.brains[i].should_jump(self.x[i], self.y[i], self.level):
                self.vy[i] = JUMP_VELOCITY
                self.on_ground[i] = False
