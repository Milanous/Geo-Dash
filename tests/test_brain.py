"""tests/test_brain.py — Tests for Neuron (4.1), Network (4.2), Brain (4.3)."""

import importlib
import sys

from engine.world import TileType, World

from ai.neuron import Neuron
from ai.network import Network
from ai.brain import Brain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world_with_spike(col: int = 3, row: int = 1) -> World:
    """Return a 10×5 world with a single SPIKE tile at (col, row)."""
    w = World(10, 5)
    w.set_tile(col, row, TileType.SPIKE)
    return w


# ---------------------------------------------------------------------------
# Neuron (Story 4.1)
# ---------------------------------------------------------------------------

class TestNeuron:
    def test_dx_dy_are_floats(self):
        n = Neuron(dx=2.0, dy=-1.0, type=TileType.SPIKE, polarity="green")
        assert isinstance(n.dx, float)
        assert isinstance(n.dy, float)

    def test_green_matching_tile(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="green")
        assert n.is_active(0.0, 0.0, world) is True

    def test_green_non_matching_tile(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=0.0, dy=0.0, type=TileType.SPIKE, polarity="green")
        assert n.is_active(0.0, 0.0, world) is False

    def test_red_matching_tile(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="red")
        assert n.is_active(0.0, 0.0, world) is False

    def test_red_non_matching_tile(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=0.0, dy=0.0, type=TileType.SPIKE, polarity="red")
        assert n.is_active(0.0, 0.0, world) is True

    def test_out_of_bounds_returns_air(self):
        world = World(5, 5)
        n = Neuron(dx=100.0, dy=100.0, type=TileType.AIR, polarity="green")
        assert n.is_active(0.0, 0.0, world) is True

    def test_no_pygame_import(self):
        spec = importlib.util.find_spec("ai.neuron")
        assert spec is not None
        mod = importlib.import_module("ai.neuron")
        assert "pygame" not in sys.modules or "pygame" not in dir(mod)


# ---------------------------------------------------------------------------
# Network (Story 4.2)
# ---------------------------------------------------------------------------

class TestNetwork:
    def test_all_active_fires(self):
        world = _make_world_with_spike(3, 1)
        n1 = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="green")
        n2 = Neuron(dx=0.0, dy=0.0, type=TileType.SPIKE, polarity="red")
        net = Network([n1, n2])
        assert net.should_fire(0.0, 0.0, world) is True

    def test_one_inactive_does_not_fire(self):
        world = _make_world_with_spike(3, 1)
        n1 = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="green")
        n2 = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="red")  # red + match = False
        net = Network([n1, n2])
        assert net.should_fire(0.0, 0.0, world) is False

    def test_empty_network_does_not_fire(self):
        world = World(5, 5)
        net = Network([])
        assert net.should_fire(0.0, 0.0, world) is False

    def test_single_active_neuron_fires(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="green")
        net = Network([n])
        assert net.should_fire(0.0, 0.0, world) is True

    def test_single_inactive_neuron_does_not_fire(self):
        world = _make_world_with_spike(3, 1)
        n = Neuron(dx=0.0, dy=0.0, type=TileType.SPIKE, polarity="green")  # AIR ≠ SPIKE
        net = Network([n])
        assert net.should_fire(0.0, 0.0, world) is False

    def test_no_pygame_import(self):
        mod = importlib.import_module("ai.network")
        assert "pygame" not in dir(mod)


# ---------------------------------------------------------------------------
# Brain (Story 4.3)
# ---------------------------------------------------------------------------

class TestBrain:
    def test_should_jump_any_fires(self):
        world = _make_world_with_spike(3, 1)
        n_active = Neuron(dx=3.0, dy=1.0, type=TileType.SPIKE, polarity="green")
        net1 = Network([])  # never fires
        net2 = Network([n_active])
        brain = Brain([net1, net2])
        assert brain.should_jump(0.0, 0.0, world) is True

    def test_should_jump_none_fires(self):
        world = _make_world_with_spike(3, 1)
        n_inactive = Neuron(dx=0.0, dy=0.0, type=TileType.SPIKE, polarity="green")
        net = Network([n_inactive])
        brain = Brain([net])
        assert brain.should_jump(0.0, 0.0, world) is False

    def test_should_jump_empty_brain(self):
        world = World(5, 5)
        brain = Brain([])
        assert brain.should_jump(0.0, 0.0, world) is False

    def test_to_json_structure(self):
        n = Neuron(dx=2.5, dy=-1.0, type=TileType.SPIKE, polarity="green")
        brain = Brain([Network([n])])
        data = brain.to_json()
        assert data["version"] == 1
        assert len(data["networks"]) == 1
        neuron_data = data["networks"][0]["neurons"][0]
        assert neuron_data == {"dx": 2.5, "dy": -1.0, "type": "spike", "polarity": "green"}

    def test_from_json_round_trip(self):
        n1 = Neuron(dx=1.0, dy=0.0, type=TileType.SOLID, polarity="red")
        n2 = Neuron(dx=2.5, dy=-1.0, type=TileType.SPIKE, polarity="green")
        original = Brain([Network([n1, n2]), Network([n1])])
        data = original.to_json()
        restored = Brain.from_json(data)

        world = _make_world_with_spike(3, 1)
        for px in [0.0, 1.0, 5.0]:
            for py in [0.0, 1.0, 3.0]:
                assert original.should_jump(px, py, world) == restored.should_jump(px, py, world)

    def test_from_json_bad_version(self):
        import pytest
        with pytest.raises(ValueError):
            Brain.from_json({"version": 2, "networks": []})

    def test_no_pygame_import(self):
        mod = importlib.import_module("ai.brain")
        assert "pygame" not in dir(mod)
