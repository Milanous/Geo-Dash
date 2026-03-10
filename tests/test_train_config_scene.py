"""
tests/test_train_config_scene.py — Headless tests for TrainConfigScene.

No pygame.init() or display surface required.
Tests validate logic via direct attribute manipulation + _try_launch().
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ui.train_config_scene import FIELDS, TrainConfigScene


def _make_scene(**overrides: str) -> TrainConfigScene:
    """Build a TrainConfigScene without calling __init__ (no pygame)."""
    scene = TrainConfigScene.__new__(TrainConfigScene)
    scene.values = {attr: str(default) for _, attr, _, default in FIELDS}
    scene.values.update(overrides)
    scene.active_field = None
    scene.error_msg = ""
    scene.next_scene = None
    # Provide placeholders for the newly added attrs to avoid AttributeErrors
    scene._world = None
    scene._level_name = ""
    scene._return_scene_instance = None
    scene._gen_config = None
    return scene


class TestDefaultValues:
    """2.1 — Default values are correct at init."""

    def test_values_match_field_defaults(self):
        scene = _make_scene()
        assert scene.values["population_size"] == "1000"
        assert scene.values["max_generations"] == "500"
        assert scene.values["top_n"] == "200"
        assert scene.values["mutation_sigma"] == "1.0"
        assert scene.values["max_seconds_per_gen"] == "120.0"
        assert scene.values["p_move"] == "0.99"
        assert scene.values["p_neuron"] == "0.008"
        assert scene.values["p_network"] == "0.002"

    def test_all_fields_present(self):
        scene = _make_scene()
        expected_attrs = {attr for _, attr, _, _ in FIELDS}
        assert set(scene.values.keys()) == expected_attrs


class TestInvalidProbabilities:
    """2.2 — p_move + p_neuron > 1.0 ➜ error, no transition."""

    def test_p_move_08_p_neuron_03(self):
        scene = _make_scene(p_move="0.8", p_neuron="0.3", p_network="0.0")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None

    def test_p_move_1_p_neuron_01(self):
        scene = _make_scene(p_move="1.0", p_neuron="0.01", p_network="0.0")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None


class TestInvalidTopN:
    """2.3 — top_n >= population_size ➜ error, no transition."""

    def test_top_n_50_pop_10(self):
        scene = _make_scene(top_n="50", population_size="10")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None

    def test_top_n_equals_pop(self):
        scene = _make_scene(top_n="100", population_size="100")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None


class TestValidLaunch:
    """2.4 — Valid values ➜ next_scene set (AITrainScene mocked)."""

    @patch("ui.train_config_scene.AITrainScene", create=True)
    def test_valid_defaults_set_next_scene(self, mock_cls: MagicMock):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        with patch.dict(
            "sys.modules",
            {"ui.ai_train_scene": MagicMock(AITrainScene=mock_cls)},
        ):
            scene = _make_scene()
            scene._try_launch()

        assert scene.error_msg == ""
        assert scene.next_scene is mock_instance

    def test_empty_field_triggers_error(self):
        scene = _make_scene(population_size="")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None

    def test_non_numeric_triggers_error(self):
        scene = _make_scene(mutation_sigma="abc")
        scene._try_launch()
        assert scene.error_msg != ""
        assert scene.next_scene is None
