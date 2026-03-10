"""
engine/level_generator.py — Parametric procedural level generator.

Produces a World filled according to configurable parameters.
No randomness beyond the seeded RNG — fully reproducible given the same seed.

Import rules: stdlib + engine only. Never import pygame, renderer, or ai.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from engine.world import TileType, World

# ---------------------------------------------------------------------------
# GeneratorConfig
# ---------------------------------------------------------------------------

@dataclass
class GeneratorConfig:
    """
    All parameters controlling procedural level generation.

    Attributes:
        length:               Total level length in blocks.
        height:               World height in blocks (vertical span).
        spike_density:        Probability [0–1] that a floor block becomes a spike.
        gap_probability:      Probability [0–1] that a new gap starts at each column.
        max_gap_width:        Maximum width of a floor gap in blocks.
        platform_probability: Probability [0–1] that a floating platform starts
                              at each column.
        platform_min_width:   Minimum width of a floating platform in blocks.
        platform_max_width:   Maximum width of a floating platform in blocks.
        platform_min_height:  Minimum height of floating platforms above floor
                              (in blocks).
        platform_max_height:  Maximum height of floating platforms above floor
                              (in blocks).
        spike_under_platform: Whether to place spikes directly under each
                              platform tile (dangerous underside).
        stair_probability:    Probability [0–1] that a staircase pattern starts
                              at each column.
        stair_max_steps:      Maximum number of steps in a staircase.
        stair_step_height:    Height gained per step (in blocks, 1 or 2).
        seed:                 RNG seed for reproducibility. None = random.
    """

    length: int = 1000
    height: int = 20

    # Floor hazards
    spike_density: float = 0.15
    gap_probability: float = 0.10
    max_gap_width: int = 3

    # Floating platforms
    platform_probability: float = 0.08
    platform_min_width: int = 2
    platform_max_width: int = 5
    platform_min_height: int = 3
    platform_max_height: int = 6
    spike_under_platform: bool = True

    # Staircase blocks
    stair_probability: float = 0.06
    stair_max_steps: int = 5
    stair_step_height: int = 1

    seed: int | None = None

    def __post_init__(self) -> None:
        if self.length < 20:
            raise ValueError("length must be >= 20")
        if self.height < 5:
            raise ValueError("height must be >= 5")
        if not 0.0 <= self.spike_density <= 1.0:
            raise ValueError("spike_density must be in [0, 1]")
        if not 0.0 <= self.gap_probability <= 1.0:
            raise ValueError("gap_probability must be in [0, 1]")
        if self.max_gap_width < 1:
            raise ValueError("max_gap_width must be >= 1")
        if not 0.0 <= self.platform_probability <= 1.0:
            raise ValueError("platform_probability must be in [0, 1]")
        if self.platform_min_width < 1:
            raise ValueError("platform_min_width must be >= 1")
        if self.platform_max_width < self.platform_min_width:
            raise ValueError("platform_max_width must be >= platform_min_width")
        if self.platform_min_height < 2:
            raise ValueError("platform_min_height must be >= 2")
        if self.platform_max_height < self.platform_min_height:
            raise ValueError("platform_max_height must be >= platform_min_height")
        if self.platform_max_height >= self.height - 1:
            raise ValueError("platform_max_height must be < height - 1")
        if not 0.0 <= self.stair_probability <= 1.0:
            raise ValueError("stair_probability must be in [0, 1]")
        if self.stair_max_steps < 1:
            raise ValueError("stair_max_steps must be >= 1")
        if self.stair_step_height not in (1, 2):
            raise ValueError("stair_step_height must be 1 or 2")


# ---------------------------------------------------------------------------
# Safe-zone constants
# ---------------------------------------------------------------------------

_SAFE_START = 6    # columns free of hazards at the beginning
_SAFE_END = 4      # columns free of hazards before the finish tile


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_level(config: GeneratorConfig | None = None) -> World:
    """
    Build and return a World according to *config*.

    The generated level always has:
      - A solid floor across the full length (with gaps where configured).
      - A safe start zone (first ``_SAFE_START`` columns: floor only, no spikes).
      - A safe end zone (last ``_SAFE_END`` columns: floor only, then FINISH).
      - Optional floating platforms (with optional spikes underneath).
      - Optional staircase patterns rising from the floor.
      - Optional spikes on floor tiles (outside safe zones).

    Args:
        config: Parameters for generation. Defaults to GeneratorConfig().

    Returns:
        A fully populated World ready for play or AI training.
    """
    if config is None:
        config = GeneratorConfig()

    rng = random.Random(config.seed)
    world = World(config.length + 2, config.height)

    _place_floor(world, config, rng)
    _place_platforms(world, config, rng)
    _place_stairs(world, config, rng)
    _place_finish(world, config)

    return world


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------

def _place_floor(world: World, cfg: GeneratorConfig, rng: random.Random) -> None:
    """
    Place the ground floor (row y=0) across the full level length.

    Rules:
      - Always SOLID in the safe-start and safe-end zones.
      - Outside safe zones: random gaps and random spike tiles.
      - Spikes are placed only on columns that have a SOLID floor tile.
    """
    col = 0
    gap_remaining = 0  # columns left in the current gap

    while col < cfg.length:
        in_safe_start = col < _SAFE_START
        in_safe_end = col >= cfg.length - _SAFE_END - 1

        if gap_remaining > 0:
            # This column is inside a gap — leave it AIR
            gap_remaining -= 1
            col += 1
            continue

        # Decide whether to start a new gap
        if not in_safe_start and not in_safe_end:
            if rng.random() < cfg.gap_probability:
                gap_width = rng.randint(1, cfg.max_gap_width)
                gap_remaining = gap_width - 1
                col += 1
                continue

        # Place the floor tile
        if not in_safe_start and not in_safe_end:
            if rng.random() < cfg.spike_density:
                world.set_tile(col, 0, TileType.SPIKE)
            else:
                world.set_tile(col, 0, TileType.SOLID)
        else:
            world.set_tile(col, 0, TileType.SOLID)

        col += 1


def _place_platforms(world: World, cfg: GeneratorConfig, rng: random.Random) -> None:
    """
    Place floating platforms above the floor.

    Each platform is a horizontal row of SOLID tiles at a random height.
    If ``cfg.spike_under_platform`` is True, SPIKE tiles are placed
    on the row directly below the platform surface, making the underside
    hazardous (the player cannot safely fly underneath).
    """
    col = _SAFE_START
    skip_until = 0  # column index at which we may start the next platform

    while col < cfg.length - _SAFE_END - 1:
        if col < skip_until:
            col += 1
            continue

        if rng.random() < cfg.platform_probability:
            width = rng.randint(cfg.platform_min_width, cfg.platform_max_width)
            height = rng.randint(cfg.platform_min_height, cfg.platform_max_height)

            end_col = min(col + width, cfg.length - _SAFE_END - 1)

            for pc in range(col, end_col):
                # Platform surface
                world.set_tile(pc, height, TileType.SOLID)

                # Spikes on the underside (height - 1)
                if cfg.spike_under_platform and height - 1 >= 1:
                    world.set_tile(pc, height - 1, TileType.SPIKE_DOWN)

            # Leave a gap after the platform before placing the next one
            skip_until = end_col + 2

        col += 1


def _place_stairs(world: World, cfg: GeneratorConfig, rng: random.Random) -> None:
    """
    Place staircase patterns rising from the floor.

    Each staircase is a sequence of ascending SOLID columns starting from the
    floor. Column k of the staircase has SOLID tiles from y=0 up to
    y = k * cfg.stair_step_height (inclusive). The visual effect is a rising
    staircase the player must jump over.

    Spikes are NOT placed on or around stairs regardless of spike_density,
    to keep the hazard readable.
    """
    col = _SAFE_START
    skip_until = 0

    while col < cfg.length - _SAFE_END - 1:
        if col < skip_until:
            col += 1
            continue

        if rng.random() < cfg.stair_probability:
            steps = rng.randint(2, cfg.stair_max_steps)
            max_stair_height = min(
                steps * cfg.stair_step_height,
                cfg.height - 2,
            )

            for step in range(steps):
                sc = col + step
                if sc >= cfg.length - _SAFE_END - 1:
                    break
                top = min((step + 1) * cfg.stair_step_height, cfg.height - 2)
                for ry in range(0, top + 1):
                    # Only set if currently AIR (don't overwrite spike/platform)
                    if world.tile_at(sc, ry) == TileType.AIR:
                        world.set_tile(sc, ry, TileType.SOLID)

            # Clear area before the staircase so the player has room to approach
            skip_until = col + steps + 3

        col += 1


def _place_finish(world: World, cfg: GeneratorConfig) -> None:
    """Place the FINISH tile at the end of the level."""
    finish_col = cfg.length - 1
    world.set_tile(finish_col, 0, TileType.FINISH)
