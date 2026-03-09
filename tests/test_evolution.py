"""tests/test_evolution.py — Tests for PopulationSim (Story 5.1), Evolution (Story 5.3), and AITrainScene (Story 5.4)."""

import copy
import importlib
import json
import os
import sys
import time

import numpy as np
import pytest

from ai.brain import Brain
from ai.evolution import generate_random_brain, mutate, select_top_n
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
        # Place spike at row 1 (walking surface) — agent walks on SOLID floor at y=1.0
        world.set_tile(8, 1, TileType.SPIKE)
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
        np.testing.assert_array_equal(fit, sim.max_x)
        # Must be a copy, not a reference
        fit[0] = -999.0
        assert sim.max_x[0] != -999.0


# ---------------------------------------------------------------------------
# Story 5.2 — Fitness Evaluation
# ---------------------------------------------------------------------------

class TestFitnessAfterZeroSteps:
    """Task 2.1 — fitness() after 0 steps returns initial positions."""

    def test_fitness_equals_initial_x(self):
        brains = _empty_brains(6)
        sim = PopulationSim(brains, _flat_world(), _config(6))
        fit = sim.fitness()
        np.testing.assert_array_almost_equal(fit, 5.0)


class TestFitnessTracksMaxPosition:
    """Task 2.2 — agent that advances then dies keeps max position."""

    def test_max_x_after_death(self):
        world = _flat_world()
        # Place a spike on the walking surface (row 1, above SOLID floor)
        world.set_tile(10, 1, TileType.SPIKE)
        brains = _empty_brains(1)
        sim = PopulationSim(brains, world, _config(pop=2))

        # Run until agent dies
        for _ in range(50000):
            if not sim.alive[0]:
                break
            sim.step(DT)

        assert not sim.alive[0], "Agent should have died on spike"
        # max_x must be exactly equal to x at death (since x never decreases)
        assert sim.fitness()[0] == pytest.approx(sim.x[0])
        # max_x must be > initial position
        assert sim.fitness()[0] > 5.0


class TestFitnessIsPure:
    """Task 2.3 — fitness() is pure: two successive calls return same result."""

    def test_two_calls_identical(self):
        brains = _empty_brains(5)
        sim = PopulationSim(brains, _flat_world(), _config(5))
        sim.step(DT)
        sim.step(DT)
        fit1 = sim.fitness()
        fit2 = sim.fitness()
        np.testing.assert_array_equal(fit1, fit2)

    def test_does_not_modify_state(self):
        brains = _empty_brains(3)
        sim = PopulationSim(brains, _flat_world(), _config(3))
        sim.step(DT)
        max_x_before = sim.max_x.copy()
        _ = sim.fitness()
        np.testing.assert_array_equal(sim.max_x, max_x_before)


class TestFitnessDeadAtStart:
    """Task 2.4 — agent killed at start has fitness ≈ initial position (5.0)."""

    def test_dead_at_start_fitness(self):
        brains = _empty_brains(3)
        sim = PopulationSim(brains, _flat_world(), _config(3))
        sim.alive[1] = False
        # Run a few steps — dead agent shouldn't move
        for _ in range(10):
            sim.step(DT)
        assert sim.fitness()[1] == pytest.approx(5.0)


class TestFitnessCappedAtWidth:
    """AC2 — agents reaching the end of the level receive exactly world width."""

    def test_fitness_capped_at_world_width(self):
        # Small world to easily reach the end
        world = _flat_world(width=10)
        brains = _empty_brains(2)
        sim = PopulationSim(brains, world, _config(2))
        
        # Run enough steps so agent reaches the end
        for _ in range(5000):
            sim.step(DT)
            
        assert sim.finished[0], "Agent should have reached the finish"
        assert sim.fitness()[0] <= 10.0, "Fitness must not exceed world width"


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


# ===========================================================================
# Story 5.3 — Evolution: Top-10 Selection & Gaussian Mutation
# ===========================================================================

def _make_brain(n_networks: int = 1, neurons_per_net: int = 1) -> Brain:
    """Utility: create a simple deterministic brain."""
    return Brain([
        Network([Neuron(dx=1.0, dy=1.0, type=TileType.SOLID, polarity="green")
                 for _ in range(neurons_per_net)])
        for _ in range(n_networks)
    ])


def _default_config() -> TrainingConfig:
    return TrainingConfig(population_size=20, top_n=5)


# ---------------------------------------------------------------------------
# Task 2.1 — select_top_n returns exactly n brains
# ---------------------------------------------------------------------------

class TestSelectTopNCount:
    def test_returns_n_brains(self):
        brains = [_make_brain() for _ in range(10)]
        fitness = np.arange(10, dtype=float)
        result = select_top_n(brains, fitness, 3)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Task 2.2 — select_top_n returns best fitness brains
# ---------------------------------------------------------------------------

class TestSelectTopNBest:
    def test_returns_highest_fitness(self):
        brains = [_make_brain() for _ in range(5)]
        fitness = np.array([1.0, 5.0, 3.0, 4.0, 2.0])
        result = select_top_n(brains, fitness, 2)
        assert result[0] is brains[1]  # fitness 5.0
        assert result[1] is brains[3]  # fitness 4.0


# ---------------------------------------------------------------------------
# Task 2.3 — mutate returns a different object
# ---------------------------------------------------------------------------

class TestMutateDifferentObject:
    def test_mutate_returns_new_brain(self):
        brain = _make_brain(n_networks=2, neurons_per_net=2)
        cfg = _default_config()
        mutated = mutate(brain, cfg)
        assert mutated is not brain


# ---------------------------------------------------------------------------
# Task 2.4 — original brain unchanged after mutate
# ---------------------------------------------------------------------------

class TestMutateOriginalUnchanged:
    def test_original_unchanged(self):
        brain = _make_brain(n_networks=2, neurons_per_net=3)
        original_json = brain.to_json()
        cfg = _default_config()
        _ = mutate(brain, cfg)
        assert brain.to_json() == original_json


# ---------------------------------------------------------------------------
# Task 2.5 — mutate result has at least 1 network
# ---------------------------------------------------------------------------

class TestMutateAtLeastOneNetwork:
    def test_at_least_one_network(self):
        brain = _make_brain(n_networks=1, neurons_per_net=2)
        cfg = _default_config()
        for _ in range(200):
            result = mutate(brain, cfg)
            assert len(result.networks) >= 1

    def test_mutate_empty_brain_adds_network(self):
        brain = Brain([])
        cfg = _default_config()
        for _ in range(50):
            result = mutate(brain, cfg)
            assert len(result.networks) >= 1
            for net in result.networks:
                assert len(net.neurons) >= 1


# ---------------------------------------------------------------------------
# Task 2.6 — mutate result has ≥ 1 neuron per network
# ---------------------------------------------------------------------------

class TestMutateAtLeastOneNeuron:
    def test_at_least_one_neuron_per_network(self):
        brain = _make_brain(n_networks=2, neurons_per_net=1)
        cfg = _default_config()
        for _ in range(200):
            result = mutate(brain, cfg)
            for net in result.networks:
                assert len(net.neurons) >= 1


# ---------------------------------------------------------------------------
# Task 2.7 — generate_random_brain returns valid Brain
# ---------------------------------------------------------------------------

class TestGenerateRandomBrain:
    def test_returns_brain(self):
        brain = generate_random_brain()
        assert isinstance(brain, Brain)

    def test_default_dimensions(self):
        brain = generate_random_brain()
        assert len(brain.networks) == 2
        for net in brain.networks:
            assert len(net.neurons) == 3

    def test_custom_dimensions(self):
        brain = generate_random_brain(n_networks=4, neurons_per_network=5)
        assert len(brain.networks) == 4
        for net in brain.networks:
            assert len(net.neurons) == 5

    def test_neuron_positions_are_float(self):
        brain = generate_random_brain()
        for net in brain.networks:
            for n in net.neurons:
                assert isinstance(n.dx, float)
                assert isinstance(n.dy, float)

    def test_neuron_polarities_valid(self):
        brain = generate_random_brain()
        for net in brain.networks:
            for n in net.neurons:
                assert n.polarity in ("green", "red")

    def test_neuron_types_valid(self):
        brain = generate_random_brain()
        for net in brain.networks:
            for n in net.neurons:
                assert n.type in (TileType.AIR, TileType.SOLID, TileType.SPIKE)


# ---------------------------------------------------------------------------
# Task 1.4 — evolution.py import guard: no pygame
# ---------------------------------------------------------------------------

class TestEvolutionImportGuard:
    def test_no_pygame_import(self):
        mod = importlib.import_module("ai.evolution")
        assert "pygame" not in dir(mod)
        import ast, inspect
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "pygame", "evolution.py imports pygame"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "pygame", "evolution.py imports from pygame"


# ===========================================================================
# Story 5.4 — Generation Loop: 100 Generations, Save & Early Stop
# ===========================================================================


def _train_config(pop: int = 20, top_n: int = 5, max_gen: int = 3) -> TrainingConfig:
    return TrainingConfig(
        population_size=pop,
        top_n=top_n,
        max_generations=max_gen,
        max_seconds_per_gen=0.5,
    )


def _make_ai_train_scene(
    config: TrainingConfig | None = None,
    world: World | None = None,
):
    """Create an AITrainScene with pygame mocked to avoid SDL init errors."""
    import unittest.mock as mock

    # Completely patch pygame
    with mock.patch.dict("sys.modules", {"pygame": mock.MagicMock()}):
        import importlib
        import ui.ai_train_scene as mod
        importlib.reload(mod)
        
        # Override steps per frame to 1 for easier deterministic testing
        mod._STEPS_PER_FRAME = 1

        if config is None:
            config = _train_config()
        if world is None:
            world = _flat_world()
            
        scene = mod.AITrainScene(config=config, world=world)
        return scene


# ---------------------------------------------------------------------------
# Task 2.1 — Generation loop produces population_size brains each iteration
# ---------------------------------------------------------------------------

class TestAITrainSceneGenerationLoop:
    def test_population_size_maintained(self):
        """The generation loop in AITrainScene maintains population_size brains."""
        # Story 5.4 Task 2.1 requires testing loop produces 1000 brains at each iteration
        cfg = _train_config(pop=1000, top_n=10, max_gen=2)
        scene = _make_ai_train_scene(config=cfg)

        # Force generation to complete quickly
        scene._max_steps_per_gen = 2
        
        assert len(scene.brains) == 1000
        assert scene.gen_num == 0

        # Step 1
        scene.update(DT)
        assert scene.gen_num == 0
        
        # Step 2 -> forces _end_generation
        scene.update(DT)
        
        # NOTE: with the mock, _STEPS_PER_FRAME is 1 so one update() is 1 step
        # Since _max_steps_per_gen is 2, it requires a 3rd update to trigger _generation_done
        # because _generation_done is evaluated BEFORE sim.step in the loop.
        scene.update(DT)
        
        assert scene.gen_num == 1
        assert len(scene.brains) == 1000
        
        # Original sim should be replaced with a new one
        assert scene._step_count == 0


# ---------------------------------------------------------------------------
# Task 2.2 — gen_num increments after each generation
# ---------------------------------------------------------------------------

class TestAITrainSceneGenNumIncrements:
    def test_gen_num_increments(self):
        """gen_num increments correctly and respects max_generations."""
        cfg = _train_config(pop=10, top_n=3, max_gen=3)
        scene = _make_ai_train_scene(config=cfg)

        scene._max_steps_per_gen = 1
        
        assert not scene.finished

        # First step increments _step_count to 1
        scene.update(DT)
        assert scene.gen_num == 0
        
        # Second call to update() catches _step_count >= _max_steps_per_gen
        scene.update(DT)
        assert scene.gen_num == 1
        assert not scene.finished
        
        # Gen 2
        scene.update(DT) # step to 1
        scene.update(DT) # ends gen
        assert scene.gen_num == 2
        assert not scene.finished

        # Gen 3
        scene.update(DT) # step to 1
        scene.update(DT) # ends gen
        assert scene.gen_num == 3
        assert scene.finished  # Reached max_generations
        assert "Training complete" in scene.status_msg


# ---------------------------------------------------------------------------
# Task 2.3 — gen_001_best.json created after 1st generation (tmp_path)
# ---------------------------------------------------------------------------

class TestAITrainSceneBestBrainSaved:
    def test_best_brain_saved_to_tmp_path(self, tmp_path):
        """AITrainScene saves the best brain to the configured directory."""
        cfg = _train_config(pop=10, top_n=3, max_gen=2)
        scene = _make_ai_train_scene(config=cfg)

        # Redirect save dir to tmp_path
        brains_dir = str(tmp_path / "brains")
        scene.brains_dir = brains_dir

        scene._max_steps_per_gen = 1
        
        # Trigger generation end
        scene.update(DT) # step to 1
        scene.update(DT) # ends gen

        assert scene.gen_num == 1
        
        path = os.path.join(brains_dir, "gen_001_best.json")
        assert os.path.isfile(path)
        
        with open(path) as f:
            saved = json.load(f)
            
        assert saved["version"] == 1
        assert saved["generation"] == 1
        assert "fitness" in saved
        assert "networks" in saved


# ---------------------------------------------------------------------------
# Early Stop
# ---------------------------------------------------------------------------

class TestAITrainSceneEarlyStop:
    def test_early_stop_on_level_completion(self):
        """Scene stops early if an agent reaches the level width."""
        cfg = _train_config(pop=5, top_n=2, max_gen=10)
        # Small world
        world = _flat_world(width=10)
        scene = _make_ai_train_scene(config=cfg, world=world)

        # Force one agent to win
        scene._sim.max_x[0] = 11.0
        scene._sim.finished[0] = True

        # Trigger generation end
        scene._step_count = scene._max_steps_per_gen
        scene.update(DT)

        assert scene.early_stopped
        assert scene.finished
        assert scene.status_msg == "Level Completed!"
