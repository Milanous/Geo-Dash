"""
engine/level_generator.py — Parametric procedural level generator.

Produces a World filled according to configurable parameters.
No randomness beyond the seeded RNG — fully reproducible given the same seed.

Import rules: stdlib + engine only. Never import pygame, renderer, or ai.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from engine.world import TileType, World, is_spike


# ---------------------------------------------------------------------------
# Passability constraint helper
# ---------------------------------------------------------------------------

def _max_passable_steps(step_width: int, step_height: int) -> int:
    """
    Return the maximum passable step count for given step dimensions.

    Derived empirically from GD physics (jump height ≈ 2.66 blocs,
    horizontal range ≈ 4.46 blocs):

    step_width=1, step_height=1 → max 3 steps  (each step is a single-column wall)
    step_width=1, step_height=2 → max 2 steps  (wall too tall to climb reliably)
    step_width=2, step_height=1 → max 4 steps
    step_width=2, step_height=2 → max 3 steps
    step_width=3, step_height=1 → max 5 steps
    step_width=3, step_height=2 → max 4 steps
    step_width>=4, any height    → max 5 steps
    """
    if step_width >= 4:
        return 5
    table = {
        (1, 1): 3, (1, 2): 2,
        (2, 1): 4, (2, 2): 3,
        (3, 1): 5, (3, 2): 4,
    }
    return table.get((step_width, step_height), 5)


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
        max_gap_width:        Maximum width of a floor gap (1–3; >3 is unplayable).
        platform_probability: Probability [0–1] that a floating platform starts
                              at each column.
        platform_min_width:   Minimum width of a floating platform in blocks.
        platform_max_width:   Maximum width of a floating platform in blocks.
        platform_min_height:  Minimum height of floating platforms above floor
                              (in blocks, must be >= 3 for corridor clearance).
        platform_max_height:  Maximum height of floating platforms above floor
                              (in blocks).
        spike_under_platform: Whether to place SPIKE_DOWN tiles directly under
                              each platform tile (dangerous underside). Spikes
                              are skipped on columns that already have a floor
                              spike, to avoid impossible corridors.
        stair_probability:    Probability [0–1] that a staircase pattern starts
                              at each column.
        stair_max_steps:      Maximum number of steps in a staircase. Capped
                              automatically by passability constraints.
        stair_step_height:    Height gained per step (1 or 2 blocks).
        stair_step_width:     Horizontal width of each step in blocks.
                              step_width=1 + max_steps>3 is rejected as unplayable.
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
    stair_max_steps: int = 4
    stair_step_height: int = 1
    stair_step_width: int = 3   # columns per step (wider = easier to climb)

    seed: int | None = None

    def __post_init__(self) -> None:  # noqa: PLR0912
        if self.length < 20:
            raise ValueError("length must be >= 20")
        if self.height < 5:
            raise ValueError("height must be >= 5")
        if not 0.0 <= self.spike_density <= 1.0:
            raise ValueError("spike_density must be in [0, 1]")
        if not 0.0 <= self.gap_probability <= 1.0:
            raise ValueError("gap_probability must be in [0, 1]")
        if not 1 <= self.max_gap_width <= 3:
            raise ValueError("max_gap_width must be between 1 and 3")
        if not 0.0 <= self.platform_probability <= 1.0:
            raise ValueError("platform_probability must be in [0, 1]")
        if self.platform_min_width < 1:
            raise ValueError("platform_min_width must be >= 1")
        if self.platform_max_width < self.platform_min_width:
            raise ValueError("platform_max_width must be >= platform_min_width")
        if self.platform_min_height < 3:
            raise ValueError("platform_min_height must be >= 3 (corridor clearance)")
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
        if self.stair_step_width < 1:
            raise ValueError("stair_step_width must be >= 1")
        max_passable = _max_passable_steps(self.stair_step_width, self.stair_step_height)
        if self.stair_max_steps > max_passable:
            raise ValueError(
                f"With stair_step_width={self.stair_step_width} and "
                f"stair_step_height={self.stair_step_height}, "
                f"stair_max_steps must be <= {max_passable} "
                f"(passability constraint)"
            )


# ---------------------------------------------------------------------------
# Safe-zone constants
# ---------------------------------------------------------------------------

_SAFE_START = 15   # flat landing zone — 15 blocks, no hazards
_SAFE_END = 4      # clear approach before the finish tile

# Minimum gap between the end of one gap and the start of the next
# (prevents chaining gaps into an impassable super-gap)
_GAP_COOLDOWN_EXTRA = 4   # additional columns beyond max_gap_width

# Safe landing tiles forced SOLID after every gap
_POST_GAP_SAFE_TILES = 2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_level(config: GeneratorConfig | None = None) -> World:
    """
    Build and return a World according to *config*.

    The generated level always guarantees:
      - 15-block flat safe start (no spikes, no gaps).
      - Each gap ≤ 3 blocks wide with 2 SOLID landing blocks after it and a
        cooldown that prevents two gaps from chaining.
      - After a gap, no spike on either of the 2 landing tiles.
      - No SPIKE_DOWN directly above a floor spike (impossible corridor).
      - Staircase step count capped by passability constraints.
      - Staircase height limited to leave adequate clearance below any
        platform ceiling.

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
    forbidden_cols = _place_platforms(world, config, rng)
    _fix_floor_under_platforms(world, config, forbidden_cols)
    _place_stairs(world, config, rng, forbidden_cols)
    _place_finish(world, config)

    return world


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------

def _place_floor(world: World, cfg: GeneratorConfig, rng: random.Random) -> None:
    """
    Place the ground floor (y=0) across the full level length.

    Gap rules enforced here:
      - Gaps are capped at max_gap_width (≤ 3) blocks.
      - After any gap, the next 2 columns are forced SOLID (safe landing).
      - A cooldown of (max_gap_width + GAP_COOLDOWN_EXTRA) columns prevents
        two gaps from appearing back-to-back (chained impassable super-gap).
      - Spikes never appear on the 2 safe-landing columns after a gap.
    """
    col = 0
    gap_end = 0              # first column that is no longer in the gap
    post_gap_safe_until = 0  # columns before this must be SOLID (landing zone)
    gap_allowed_from = _SAFE_START  # earliest column where a new gap may start

    while col < cfg.length:
        in_safe_start = col < _SAFE_START
        in_safe_end = col >= cfg.length - _SAFE_END - 1

        # ── Inside a gap: leave tile as AIR ──────────────────────────
        if col < gap_end:
            col += 1
            continue

        # ── Forced SOLID landing zone after gap ───────────────────────
        if col < post_gap_safe_until:
            world.set_tile(col, 0, TileType.SOLID)
            col += 1
            continue

        # ── Try to start a new gap ────────────────────────────────────
        if not in_safe_start and not in_safe_end and col >= gap_allowed_from:
            if rng.random() < cfg.gap_probability:
                gap_width = rng.randint(1, cfg.max_gap_width)
                gap_end = col + gap_width          # cols [col, gap_end) are AIR
                post_gap_safe_until = gap_end + _POST_GAP_SAFE_TILES
                gap_allowed_from = post_gap_safe_until + cfg.max_gap_width + _GAP_COOLDOWN_EXTRA
                col += 1
                continue

        # ── Regular floor tile ────────────────────────────────────────
        if in_safe_start or in_safe_end:
            world.set_tile(col, 0, TileType.SOLID)
        else:
            if rng.random() < cfg.spike_density:
                world.set_tile(col, 0, TileType.SPIKE)
            else:
                world.set_tile(col, 0, TileType.SOLID)

        col += 1


def _place_platforms(world: World, cfg: GeneratorConfig, rng: random.Random) -> set[int]:
    """
    Place floating platforms above the floor.

    Each platform is a horizontal row of SOLID tiles at a random height.
    If ``cfg.spike_under_platform`` is True, SPIKE_DOWN tiles are placed
    on the row directly below the platform surface, making the underside
    hazardous. However:
      - SPIKE_DOWN is skipped on any column whose floor tile (y=0) is already
        a spike — this prevents the impossible "spike floor + spike ceiling"
        scenario where the player cannot jump safely.

    Returns:
        A set of column indices that form the "forbidden zone": the platform
        body plus a 1-block safety margin on each side.  Floor hazards in
        this zone are corrected by ``_fix_floor_under_platforms`` and
        staircases that overlap this zone are skipped.
    """
    forbidden_cols: set[int] = set()
    col = _SAFE_START
    skip_until = 0

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
                # Skip if floor below already has a spike → impossible corridor
                if cfg.spike_under_platform and height - 1 >= 1:
                    floor_tile = world.tile_at(pc, 0)
                    if not is_spike(floor_tile):
                        world.set_tile(pc, height - 1, TileType.SPIKE_DOWN)

            # Register forbidden floor zone: platform body + 1-block margin each side
            for fc in range(max(0, col - 1), min(cfg.length, end_col + 2)):
                forbidden_cols.add(fc)

            skip_until = end_col + 2

        col += 1

    return forbidden_cols


def _fix_floor_under_platforms(
    world: World, cfg: GeneratorConfig, forbidden_cols: set[int]
) -> None:
    """
    Ensure the floor (y=0) inside the forbidden zone is safe to land on.

    Gaps (AIR) and spikes under or adjacent to a platform force the player
    to jump in a direction where SPIKE_DOWN tiles may be waiting.  This pass
    retroactively converts any such hazardous floor tile to SOLID, giving the
    player a clean run-up and landing zone around every platform.
    """
    for col in sorted(forbidden_cols):
        if col < 0 or col >= cfg.length:
            continue
        tile = world.tile_at(col, 0)
        if tile == TileType.AIR or is_spike(tile):
            world.set_tile(col, 0, TileType.SOLID)


def _place_stairs(
    world: World,
    cfg: GeneratorConfig,
    rng: random.Random,
    forbidden_cols: set[int],
) -> None:
    """
    Place staircase patterns rising from the floor.

    Each staircase has ``stair_max_steps`` steps. Every step occupies
    ``stair_step_width`` columns, all filled from y=0 up to the same height.
    Height increases by ``stair_step_height`` per step.

    Passability is guaranteed by:
      - Step count capped at ``_max_passable_steps(step_width, step_height)``
        (enforced in GeneratorConfig.__post_init__ and again here as a safety net).
      - Stair height limited so that at least 2 blocks of clearance remain
        below any platform or SPIKE_DOWN ceiling above.
      - Staircases whose approach (col-1), body, or 1-block exit margin
        overlaps a platform forbidden zone are skipped entirely — placing a
        stair under a platform forces the player to reach dangerous heights.
    """
    col = _SAFE_START
    skip_until = 0
    max_steps = _max_passable_steps(cfg.stair_step_width, cfg.stair_step_height)

    while col < cfg.length - _SAFE_END - 1:
        if col < skip_until:
            col += 1
            continue

        if rng.random() < cfg.stair_probability:
            steps = rng.randint(2, min(cfg.stair_max_steps, max_steps))

            # Skip if approach (col-1), stair body, or 1-block exit overlaps a
            # platform protected zone — stairs under platforms are unpassable.
            stair_end = col + steps * cfg.stair_step_width
            if any(
                c in forbidden_cols
                for c in range(max(0, col - 1), min(cfg.length, stair_end + 2))
            ):
                col += 1
                continue

            for step in range(steps):
                step_top = min(
                    (step + 1) * cfg.stair_step_height,
                    cfg.height - 2,
                )
                # Each step spans stair_step_width columns
                for w_idx in range(cfg.stair_step_width):
                    sc = col + step * cfg.stair_step_width + w_idx
                    if sc >= cfg.length - _SAFE_END - 1:
                        break

                    # Find the lowest ceiling (SOLID or SPIKE_DOWN) above
                    # this column so we can limit the stair height safely.
                    # Need 2 blocks of clearance: player (1 block) + 1 buffer.
                    ceiling_y = cfg.height
                    for ry in range(1, cfg.height):
                        t = world.tile_at(sc, ry)
                        if t in (TileType.SOLID, TileType.SPIKE_DOWN):
                            ceiling_y = ry
                            break

                    # Stair top must leave ≥ 2 clear blocks below ceiling
                    # (player stands at safe_top+1, needs safe_top+2 < ceiling_y)
                    safe_top = min(step_top, ceiling_y - 3)
                    safe_top = max(0, safe_top)

                    for ry in range(0, safe_top + 1):
                        if world.tile_at(sc, ry) == TileType.AIR:
                            world.set_tile(sc, ry, TileType.SOLID)

            total_width = steps * cfg.stair_step_width
            skip_until = col + total_width + 3

        col += 1


def _place_finish(world: World, cfg: GeneratorConfig) -> None:
    """Place the FINISH tile at the end of the level."""
    finish_col = cfg.length - 1
    world.set_tile(finish_col, 0, TileType.FINISH)
