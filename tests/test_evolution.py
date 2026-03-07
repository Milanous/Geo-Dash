"""tests/test_evolution.py — Tests for PopulationSim (Story 5.1)."""

import importlib
import sys
import time

import numpy as np
import pytest

from ai.brain import Brain
from ai.network import Network
from ai.neuron import Neuron
from ai.simulation import PopulationSim
from ai.training_config import TrainingConfig
from engine.physics import DT, GRAVITY, PLAYER_SPEED, PHYSICS_RATE
from engine.world import TileType, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_brains(n: int) -> list[Brain]:
    """Return *n* brains with no networks (never jump)."""
    return [Brain([]) for _ in range(n)]


def _flat_world(width: int = 200, height: int = 10) -> World:
    """Return a flat world with SOLID floor at row 0."""
    w = World(width, height)
    for col in range(width):
        w.set_tile(col, 0, TileType.SOLID)
    return w


def _config(pop: int = 10) -> TrainingConfig:
    return TrainingConfig(population_size=pop, top_n=min(pop - 1, 5))


# ---------------------------------------------------------------------------
# Task 2.1 — Array shapes
# ---------------------------------------------------------------------------

class TestPopulationSimInit:
    def test_array_shapes(self):
        n = 50
        brains = _empty_brains(n)
        sim = PopulationSim(brains, _flat_world(), _config(n))
        assert sim.x.shape == (n,)
        assert sim.y.shape == (n,)
        assert sim.vy.shape == (n,)
        assert sim.alive.shape == (n,)
        assert sim.alive.dtype == bool

    def test_max_steps(self):
        cfg = TrainingConfig(population_size=10, top_n=5, max_seconds_per_gen=30.0)
        sim = PopulationSim(_empty_brains(10), _flat_world(), cfg)
        assert sim.max_steps == int(30.0 * PHYSICS_RATE)


# ---------------------------------------------------------------------------
# Task 2.2 — Dead agents don't move
# ---------------------------------------------------------------------------

class TestDeadAgents:
    def test_dead_agents_frozen(self):
        brains = _empty_brains(5)
        sim = PopulationSim(brains, _flat_world(), _config(5))
        sim.alive[2] = False
        x_before = sim.x[2]
        y_before = sim.y[2]
        sim.step(DT)
        assert sim.x[2] == x_before
        assert sim.y[2] == y_before


# ---------------------------------------------------------------------------
# Task 2.3 — Alive agents advance
# ---------------------------------------------------------------------------

class TestAliveMovement:
    def test_x_advances_by_player_speed_dt(self):
        brains = _empty_brains(3)
        sim = PopulationSim(brains, _flat_world(), _config(3))
        x0 = sim.x[0]
        sim.step(DT)
        assert sim.x[0] == pytest.approx(x0 + PLAYER_SPEED * DT, abs=1e-9)


# ---------------------------------------------------------------------------
# Task 2.4 — Spike kills agent
# ---------------------------------------------------------------------------

class TestSpikeCollision:
    def test_spike_kills_agent(self):
        world = _flat_world()
        # Place spike at floor level — agent falls to y=0 before reaching it
        world.set_tile(8, 0, TileType.SPIKE)
        brains = _empty_brains(1)
        sim = PopulationSim(brains, world, _config(pop=2))
        # Advance until agent hits the spike or we timeout
        for _ in range(10000):
            if not sim.alive[0]:
                break
            sim.step(DT)
        assert not sim.alive[0]


# ---------------------------------------------------------------------------
# Task 2.5 — Fitness returns X positions
# ---------------------------------------------------------------------------

class TestFitness:
    def test_fitness_returns_x_copy(self):
        brains = _empty_brains(4)
        sim = PopulationSim(brains, _flat_world(), _config(4))
        sim.step(DT)
        fit = sim.fitness()
        np.testing.assert_array_equal(fit, sim.x)
        # Must be a copy, not a reference
        fit[0] = -999.0
        assert sim.x[0] != -999.0


# ---------------------------------------------------------------------------
# Task 2.6 — Benchmark: 1000 agents × 7200 steps < 60 s
# ---------------------------------------------------------------------------

class TestBenchmark:
    @pytest.mark.slow
    def test_1000_agents_under_60s(self):
        n = 1000
        brains = _empty_brains(n)
        cfg = TrainingConfig(population_size=n, top_n=10, max_seconds_per_gen=30.0)
        sim = PopulationSim(brains, _flat_world(width=500), cfg)
        steps = sim.max_steps  # 30 s × 240 Hz = 7200

        t0 = time.perf_counter()
        for _ in range(steps):
            sim.step(DT)
        elapsed = time.perf_counter() - t0

        assert elapsed < 60.0, f"Benchmark too slow: {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# Task 2.7 — Import guard
# ---------------------------------------------------------------------------

class TestImportGuard:
    def test_no_pygame_import(self):
        mod = importlib.import_module("ai.simulation")
        assert "pygame" not in dir(mod)
        # Check actual import statements in source (not comments/docstrings)
        import ast, inspect
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "pygame", "simulation.py imports pygame"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "pygame", "simulation.py imports from pygame"
