"""tests/test_hud.py — Headless tests for StatsHUD (Story 5.5)."""

import importlib

from ui.hud import StatsHUD

# ---------------------------------------------------------------------------
# Task 2.1 — Instantiation
# ---------------------------------------------------------------------------


class TestStatsHUDInit:
    def test_instantiates_without_error(self):
        hud = StatsHUD()
        assert hud.history == []
        assert hud.debug_agents is False


# ---------------------------------------------------------------------------
# Task 2.2 — update() appends to history
# ---------------------------------------------------------------------------


class TestStatsHUDUpdate:
    def test_update_adds_to_history_when_gen_complete(self):
        hud = StatsHUD()
        stats = {
            "gen": 1,
            "best_fitness": 42.5,
            "avg_fitness": 20.0,
            "worst_fitness": 5.0,
            "alive": 0,
            "gen_complete": True,
        }
        hud.update(stats)
        assert hud.history == [42.5]

    def test_update_does_not_add_when_gen_not_complete(self):
        hud = StatsHUD()
        stats = {
            "gen": 1,
            "best_fitness": 42.5,
            "avg_fitness": 20.0,
            "worst_fitness": 5.0,
            "alive": 50,
            "gen_complete": False,
        }
        hud.update(stats)
        assert hud.history == []

    def test_update_accumulates_over_generations(self):
        hud = StatsHUD()
        for i in range(5):
            hud.update(
                {
                    "gen": i + 1,
                    "best_fitness": float(i * 10),
                    "avg_fitness": 0.0,
                    "worst_fitness": 0.0,
                    "alive": 0,
                    "gen_complete": True,
                }
            )
        assert hud.history == [0.0, 10.0, 20.0, 30.0, 40.0]


# ---------------------------------------------------------------------------
# Task 2.3 — Import guard
# ---------------------------------------------------------------------------


class TestStatsHUDImportGuard:
    def test_no_ai_simulation_import(self):
        source = importlib.util.find_spec("ui.hud")
        assert source is not None
        # Check that ai.simulation is not imported by the module
        with open(source.origin, "r") as f:
            content = f.read()
        assert "ai.simulation" not in content
        assert "from ai.simulation" not in content
