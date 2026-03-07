"""
tests/test_replay_scene.py — Story 5.6 acceptance tests.

AC-1: ReplayScene scans data/brains/ for gen_NNN_best.json files.
       Empty directory → empty list, no crash.
AC-2: Loading a generation creates a Brain + Player ready for simulation.

Headless — uses temporary directories, no pygame display.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile

import pytest

from ai.brain import Brain
from ai.network import Network
from ai.neuron import Neuron
from engine.world import TileType, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_world() -> World:
    """Flat floor level for replay tests."""
    w = World(50, 10)
    for col in range(50):
        w.set_tile(col, 0, TileType.SOLID)
    return w


def _dummy_brain_json() -> dict:
    """Minimal valid brain JSON (version 1)."""
    brain = Brain([
        Network([
            Neuron(dx=1.0, dy=0.0, type=TileType.SOLID, polarity="green"),
        ])
    ])
    return brain.to_json()


# ---------------------------------------------------------------------------
# AC-1: scan empty directory → empty list, no crash
# ---------------------------------------------------------------------------

class TestReplayScan:
    def test_empty_dir_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        from ui.replay_scene import ReplayScene

        scene = ReplayScene(
            world=_simple_world(),
            brains_dir=str(tmp_path),
        )
        assert scene._generations == []

    def test_nonexistent_dir_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        from ui.replay_scene import ReplayScene

        scene = ReplayScene(
            world=_simple_world(),
            brains_dir=str(tmp_path / "nope"),
        )
        assert scene._generations == []

    def test_scan_finds_generations(self, tmp_path: pathlib.Path) -> None:
        from ui.replay_scene import ReplayScene

        for gen in (1, 5, 10):
            path = tmp_path / f"gen_{gen:03d}_best.json"
            path.write_text(json.dumps(_dummy_brain_json()), encoding="utf-8")
        # Also place a non-matching file
        (tmp_path / "random.json").write_text("{}", encoding="utf-8")

        scene = ReplayScene(
            world=_simple_world(),
            brains_dir=str(tmp_path),
        )
        assert scene._generations == [1, 5, 10]


# ---------------------------------------------------------------------------
# AC-2: loading a generation creates Brain + Player
# ---------------------------------------------------------------------------

class TestReplayLoad:
    def test_load_gen_creates_brain_and_player(self, tmp_path: pathlib.Path) -> None:
        from ui.replay_scene import ReplayScene

        data = _dummy_brain_json()
        data["generation"] = 3
        data["fitness"] = 42.0
        path = tmp_path / "gen_003_best.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        scene = ReplayScene(
            world=_simple_world(),
            brains_dir=str(tmp_path),
        )
        scene._load_gen(3)

        assert scene._brain is not None
        assert scene._player is not None
        assert scene._player.alive is True
        assert scene._camera is not None
        assert scene._current_gen == 3

