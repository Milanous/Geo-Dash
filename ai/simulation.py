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
from engine.physics import GRAVITY, JUMP_VELOCITY, PLAYER_SPEED, PHYSICS_RATE
from engine.world import World, is_spike


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
        self.x: np.ndarray = np.full(n, 5.0)
        self.y: np.ndarray = np.full(n, 2.0)
        self.vy: np.ndarray = np.zeros(n)
        self.alive: np.ndarray = np.ones(n, dtype=bool)
        self.max_x: np.ndarray = self.x.copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self, dt: float) -> None:
        """Advance one physics step for all alive agents."""
        mask = self.alive

        # Gravity (GRAVITY is negative → vy decreases)
        self.vy[mask] += GRAVITY * dt

        # Position update
        self.y[mask] += self.vy[mask] * dt
        self.x[mask] += PLAYER_SPEED * dt

        # Floor clamp
        self.y = np.maximum(self.y, 0.0)
        np.putmask(self.vy, self.y == 0.0, 0.0)

        # Track maximum X reached
        np.maximum(self.max_x, self.x, out=self.max_x)

        # Cap at level width
        np.minimum(self.max_x, float(self.level.width), out=self.max_x)

        # Spike collision
        self._resolve_spikes()

        # Brain evaluation (jump decisions)
        self._evaluate_brains()

    def fitness(self) -> np.ndarray:
        """Return fitness array — max distance reached per agent."""
        return self.max_x.copy()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_spikes(self) -> None:
        """Kill alive agents standing on a SPIKE tile."""
        alive_indices = np.where(self.alive)[0]
        for i in alive_indices:
            if is_spike(self.level.tile_at(self.x[i], self.y[i])):
                self.alive[i] = False

    def _evaluate_brains(self) -> None:
        """Ask each alive agent's brain whether to jump."""
        alive_indices = np.where(self.alive)[0]
        for i in alive_indices:
            if self.brains[i].should_jump(self.x[i], self.y[i], self.level):
                self.vy[i] = JUMP_VELOCITY
