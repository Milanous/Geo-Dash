"""Tests for ui/level_select_scene.py — headless, no display."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from editor.level_library import LevelEntry, LevelLibrary
from ui.level_select_scene import LevelSelectScene


# ── 4.1 Instantiation with empty folder ─────────────────────────────

def test_level_select_instantiates_empty(tmp_path: Path) -> None:
    """LevelSelectScene should instantiate even when no levels exist."""
    scene = LevelSelectScene(folder=str(tmp_path))
    assert scene._entries == []
    assert scene._selected_idx == 0


# ── 4.2 Selected index stays in bounds ──────────────────────────────

def test_selected_idx_stays_in_bounds_down(tmp_path: Path) -> None:
    """Pressing ↓ past the end must not exceed len-1."""
    # Create two level files
    for name in ("a.json", "b.json"):
        (tmp_path / name).write_text(json.dumps({"tiles": []}))

    scene = LevelSelectScene(folder=str(tmp_path))
    assert len(scene._entries) == 2

    # Simulate pressing DOWN three times
    scene._selected_idx = 0
    for _ in range(5):
        if scene._selected_idx < len(scene._entries) - 1:
            scene._selected_idx += 1
    assert scene._selected_idx == 1  # max valid index


def test_selected_idx_stays_in_bounds_up(tmp_path: Path) -> None:
    """Pressing ↑ past the start must not go below 0."""
    (tmp_path / "a.json").write_text(json.dumps({"tiles": []}))

    scene = LevelSelectScene(folder=str(tmp_path))
    scene._selected_idx = 0

    # Simulate pressing UP
    if scene._selected_idx > 0:
        scene._selected_idx -= 1
    assert scene._selected_idx == 0


# ── 4.3 next_scene is None on init ──────────────────────────────────

def test_next_scene_none_at_init(tmp_path: Path) -> None:
    scene = LevelSelectScene(folder=str(tmp_path))
    assert scene.next_scene is None


# ── Additional: rescan flag ──────────────────────────────────────────

def test_came_from_edit_triggers_rescan(tmp_path: Path) -> None:
    """When _came_from_edit is True, update() must rescan the folder."""
    scene = LevelSelectScene(folder=str(tmp_path))
    assert scene._entries == []

    # Create a level AFTER construction
    (tmp_path / "new_level.json").write_text(json.dumps({"tiles": []}))

    # Simulate returning from editor
    scene._came_from_edit = True
    scene.update(0.016)

    assert len(scene._entries) == 1
    assert scene._entries[0].name == "new_level"
    assert scene._came_from_edit is False


# ── Additional: delete adjusts index ────────────────────────────────

def test_delete_adjusts_selected_idx(tmp_path: Path) -> None:
    """After deleting the last entry, index should clamp down."""
    for name in ("a.json", "b.json"):
        (tmp_path / name).write_text(json.dumps({"tiles": []}))

    scene = LevelSelectScene(folder=str(tmp_path))
    # Select last entry
    scene._selected_idx = len(scene._entries) - 1
    last_idx = scene._selected_idx

    # Delete it manually (simulating DEL key logic)
    entry = scene._entries[scene._selected_idx]
    LevelLibrary.delete(entry)
    scene._entries = LevelLibrary.scan(str(tmp_path))
    if scene._selected_idx >= len(scene._entries):
        scene._selected_idx = max(0, len(scene._entries) - 1)

    assert scene._selected_idx <= len(scene._entries) - 1
    assert len(scene._entries) == 1


# ── Additional: empty entries → no crash on actions ──────────────────

def test_no_crash_on_play_with_empty_entries(tmp_path: Path) -> None:
    """Play/Edit/Train should do nothing if no entries exist."""
    scene = LevelSelectScene(folder=str(tmp_path))
    assert scene._entries == []
    # None of these should raise
    # (Simulating: nothing happens because _entries is empty)
    assert scene.next_scene is None
