"""
tests/test_level_generator.py

Tests for engine/level_generator.py — procedural level generation.
Covers config validation, basic guarantees, and the four advanced patterns:
  - Stepping stones (mandatory floating blocks)
  - Floor-level spikes (y=1)
  - Gapped stairs (gaps 1-3 between steps)
  - Spiked stairs (1-block steps with lone transition spikes)

Headless — never imports pygame.
"""

import pytest

from engine.level_generator import GeneratorConfig, generate_level
from engine.world import TileType, World, is_spike


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_START = 15
_SAFE_END = 4


def _floor_tiles(world: World) -> list[TileType]:
    """Return tiles at y=0 for every column."""
    return [world.tile_at(x, 0) for x in range(world.width)]


# ---------------------------------------------------------------------------
# GeneratorConfig validation
# ---------------------------------------------------------------------------

class TestConfigValidation:

    def test_default_config_valid(self) -> None:
        cfg = GeneratorConfig()
        assert cfg.length == 1000

    def test_stepping_stone_prob_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="stepping_stone_prob"):
            GeneratorConfig(stepping_stone_prob=1.5)

    def test_stepping_stone_min_count_too_low(self) -> None:
        with pytest.raises(ValueError, match="stepping_stone_min_count"):
            GeneratorConfig(stepping_stone_min_count=1)

    def test_stepping_stone_max_lt_min(self) -> None:
        with pytest.raises(ValueError, match="stepping_stone_max_count"):
            GeneratorConfig(stepping_stone_min_count=4,
                            stepping_stone_max_count=2)

    def test_floor_spike_density_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="floor_spike_density"):
            GeneratorConfig(floor_spike_density=-0.1)

    def test_gapped_stair_prob_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="gapped_stair_prob"):
            GeneratorConfig(gapped_stair_prob=2.0)

    def test_gapped_stair_max_steps_too_low(self) -> None:
        with pytest.raises(ValueError, match="gapped_stair_max_steps"):
            GeneratorConfig(gapped_stair_max_steps=1)

    def test_gapped_stair_step_width_too_low(self) -> None:
        with pytest.raises(ValueError, match="gapped_stair_step_width"):
            GeneratorConfig(gapped_stair_step_width=0)

    def test_spiked_stair_prob_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="spiked_stair_prob"):
            GeneratorConfig(spiked_stair_prob=-0.5)

    def test_spiked_stair_max_steps_too_low(self) -> None:
        with pytest.raises(ValueError, match="spiked_stair_max_steps"):
            GeneratorConfig(spiked_stair_max_steps=0)

    def test_spiked_stair_step_width_too_low(self) -> None:
        with pytest.raises(ValueError, match="spiked_stair_step_width"):
            GeneratorConfig(spiked_stair_step_width=0)


# ---------------------------------------------------------------------------
# Basic generation guarantees
# ---------------------------------------------------------------------------

class TestGenerateLevel:

    def test_default_generates_world(self) -> None:
        w = generate_level()
        assert w.width == 1002
        assert w.height == 20

    def test_seeded_reproducibility(self) -> None:
        cfg = GeneratorConfig(seed=123, length=100)
        w1 = generate_level(cfg)
        w2 = generate_level(GeneratorConfig(seed=123, length=100))
        for x in range(w1.width):
            for y in range(w1.height):
                assert w1.tile_at(x, y) == w2.tile_at(x, y)

    def test_safe_start_zone(self) -> None:
        cfg = GeneratorConfig(seed=1, length=100)
        w = generate_level(cfg)
        for x in range(_SAFE_START):
            assert w.tile_at(x, 0) == TileType.SOLID

    def test_finish_tile_present(self) -> None:
        cfg = GeneratorConfig(seed=1, length=50)
        w = generate_level(cfg)
        assert w.tile_at(49, 0) == TileType.FINISH


# ---------------------------------------------------------------------------
# Stepping stones
# ---------------------------------------------------------------------------

class TestSteppingStones:

    def _cfg(self, seed: int = 42) -> GeneratorConfig:
        return GeneratorConfig(
            length=300, seed=seed,
            stepping_stone_prob=0.5,
            stepping_stone_min_count=3,
            stepping_stone_max_count=5,
            # Disable other patterns to isolate
            spike_density=0.0,
            gap_probability=0.0,
            platform_probability=0.0,
            stair_probability=0.0,
            floor_spike_density=0.0,
            gapped_stair_prob=0.0,
            spiked_stair_prob=0.0,
        )

    def test_stepping_stones_created(self) -> None:
        """At least one floating SOLID above AIR floor must exist."""
        w = generate_level(self._cfg())
        found = False
        for x in range(_SAFE_START, 296):
            if (w.tile_at(x, 0) == TileType.AIR
                    and any(w.tile_at(x, h) == TileType.SOLID
                            for h in range(1, 4))):
                found = True
                break
        assert found, "No stepping stones found"

    def test_safe_start_untouched(self) -> None:
        w = generate_level(self._cfg())
        for x in range(_SAFE_START):
            assert w.tile_at(x, 0) == TileType.SOLID

    def test_stones_height_range(self) -> None:
        """All floating stones should be at height 1-3."""
        w = generate_level(self._cfg())
        for x in range(_SAFE_START, 296):
            if w.tile_at(x, 0) == TileType.AIR:
                for h in range(4, w.height):
                    # No stone above height 3 (from stepping stones)
                    # (platforms are disabled)
                    assert w.tile_at(x, h) == TileType.AIR


# ---------------------------------------------------------------------------
# Floor-level spikes (y=1)
# ---------------------------------------------------------------------------

class TestFloorSpikes:

    def _cfg(self, seed: int = 42) -> GeneratorConfig:
        return GeneratorConfig(
            length=300, seed=seed,
            floor_spike_density=0.5,
            # Disable everything else
            spike_density=0.0,
            gap_probability=0.0,
            platform_probability=0.0,
            stair_probability=0.0,
            stepping_stone_prob=0.0,
            gapped_stair_prob=0.0,
            spiked_stair_prob=0.0,
        )

    def test_floor_spikes_placed(self) -> None:
        w = generate_level(self._cfg())
        count = sum(1 for x in range(w.width)
                    if w.tile_at(x, 1) == TileType.SPIKE)
        assert count > 0, "No floor spikes at y=1"

    def test_floor_spikes_above_solid(self) -> None:
        """Every floor spike at y=1 must have SOLID at y=0 below."""
        w = generate_level(self._cfg())
        for x in range(w.width):
            if w.tile_at(x, 1) == TileType.SPIKE:
                assert w.tile_at(x, 0) == TileType.SOLID, (
                    f"Floor spike at x={x} y=1 without SOLID below"
                )

    def test_floor_spikes_never_consecutive(self) -> None:
        """No two floor spikes at y=1 should be adjacent."""
        w = generate_level(self._cfg())
        prev_spike = False
        for x in range(w.width):
            cur_spike = w.tile_at(x, 1) == TileType.SPIKE
            if cur_spike and prev_spike:
                pytest.fail(
                    f"Consecutive floor spikes at y=1: x={x-1} and x={x}"
                )
            prev_spike = cur_spike

    def test_no_floor_spikes_in_safe_start(self) -> None:
        w = generate_level(self._cfg())
        for x in range(_SAFE_START):
            assert w.tile_at(x, 1) != TileType.SPIKE


# ---------------------------------------------------------------------------
# Gapped stairs
# ---------------------------------------------------------------------------

class TestGappedStairs:

    def _cfg(self, seed: int = 42) -> GeneratorConfig:
        return GeneratorConfig(
            length=300, seed=seed,
            gapped_stair_prob=0.5,
            gapped_stair_max_steps=4,
            gapped_stair_step_width=2,
            # Disable others
            spike_density=0.0,
            gap_probability=0.0,
            platform_probability=0.0,
            stair_probability=0.0,
            stepping_stone_prob=0.0,
            floor_spike_density=0.0,
            spiked_stair_prob=0.0,
        )

    def test_gapped_stairs_have_rising_solids(self) -> None:
        """At least one column should have SOLID above y=0."""
        w = generate_level(self._cfg())
        found = False
        for x in range(_SAFE_START, 296):
            for y in range(1, 5):
                if w.tile_at(x, y) == TileType.SOLID:
                    found = True
                    break
            if found:
                break
        assert found, "No rising SOLID blocks found (gapped stairs)"

    def test_gapped_stairs_have_floor_gaps(self) -> None:
        """At least one gap (AIR at y=0) should exist within the stair zone."""
        w = generate_level(self._cfg())
        found_gap = False
        for x in range(_SAFE_START, 296):
            if w.tile_at(x, 0) == TileType.AIR:
                # Check there's a rising SOLID nearby (stair context)
                for nx in range(max(0, x - 5), min(w.width, x + 5)):
                    if w.tile_at(nx, 2) == TileType.SOLID:
                        found_gap = True
                        break
            if found_gap:
                break
        assert found_gap, "No gaps found in gapped stairs"


# ---------------------------------------------------------------------------
# Spiked stairs
# ---------------------------------------------------------------------------

class TestSpikedStairs:

    def _cfg(self, seed: int = 42) -> GeneratorConfig:
        return GeneratorConfig(
            length=300, seed=seed,
            spiked_stair_prob=0.5,
            spiked_stair_max_steps=4,
            spiked_stair_step_width=2,
            # Disable others
            spike_density=0.0,
            gap_probability=0.0,
            platform_probability=0.0,
            stair_probability=0.0,
            stepping_stone_prob=0.0,
            floor_spike_density=0.0,
            gapped_stair_prob=0.0,
        )

    def test_spiked_stairs_have_transition_spikes(self) -> None:
        """At least one SPIKE above y=1 should exist (transition spike)."""
        w = generate_level(self._cfg())
        found = False
        for x in range(_SAFE_START, 296):
            for y in range(2, 6):
                if w.tile_at(x, y) == TileType.SPIKE:
                    found = True
                    break
            if found:
                break
        assert found, "No transition spikes found in spiked stairs"

    def test_spiked_stair_spikes_are_isolated(self) -> None:
        """Transition spikes (y>=2) must never be horizontally adjacent."""
        w = generate_level(self._cfg())
        for y in range(2, 10):
            prev_spike = False
            for x in range(w.width):
                cur = w.tile_at(x, y) == TileType.SPIKE
                if cur and prev_spike:
                    pytest.fail(
                        f"Adjacent spiked-stair spikes at y={y}: "
                        f"x={x-1} and x={x}"
                    )
                prev_spike = cur

    def test_spiked_stair_spike_has_solid_below(self) -> None:
        """Each transition spike should have SOLID directly below."""
        w = generate_level(self._cfg())
        for x in range(_SAFE_START, 296):
            for y in range(2, 10):
                if w.tile_at(x, y) == TileType.SPIKE:
                    assert w.tile_at(x, y - 1) == TileType.SOLID, (
                        f"Spike at ({x},{y}) has no SOLID at ({x},{y-1})"
                    )


# ---------------------------------------------------------------------------
# No pygame import
# ---------------------------------------------------------------------------

def test_level_generator_no_pygame() -> None:
    import engine.level_generator as lg
    assert not hasattr(lg, "pygame"), "engine.level_generator must not import pygame"
