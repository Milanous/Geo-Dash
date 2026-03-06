"""Tests for editor.level_library — headless, no pygame."""

from __future__ import annotations

import json
from pathlib import Path

from editor.level_library import LevelEntry, LevelLibrary


# ── 2.1 scan() on empty folder → empty list ─────────────────────────

def test_scan_empty_folder(tmp_path: Path) -> None:
    assert LevelLibrary.scan(tmp_path) == []


# ── 2.2 scan() on absent folder → empty list, no exception ──────────

def test_scan_absent_folder(tmp_path: Path) -> None:
    absent = tmp_path / "does_not_exist"
    assert LevelLibrary.scan(absent) == []


# ── 2.3 scan() returns one entry per .json file ─────────────────────

def test_scan_returns_all_json_files(tmp_path: Path) -> None:
    for name in ("a.json", "b.json", "c.json"):
        (tmp_path / name).write_text(json.dumps({"tiles": []}))
    # Also add a non-json file that should be ignored
    (tmp_path / "readme.txt").write_text("ignore me")

    entries = LevelLibrary.scan(tmp_path)
    assert len(entries) == 3
    names = {e.name for e in entries}
    assert names == {"a", "b", "c"}


# ── 2.4 entries sorted newest first ─────────────────────────────────

def test_scan_sorted_newest_first(tmp_path: Path) -> None:
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"tiles": []}))
    # Ensure a measurable mtime difference
    import os
    os.utime(old, (1000, 1000))

    new = tmp_path / "new.json"
    new.write_text(json.dumps({"tiles": []}))
    os.utime(new, (2000, 2000))

    entries = LevelLibrary.scan(tmp_path)
    assert entries[0].name == "new"
    assert entries[1].name == "old"


# ── 2.5 delete() removes the file ───────────────────────────────────

def test_delete_removes_file(tmp_path: Path) -> None:
    f = tmp_path / "to_delete.json"
    f.write_text(json.dumps({"tiles": []}))
    entry = LevelEntry(name="to_delete", path=f, modified_at=f.stat().st_mtime)

    LevelLibrary.delete(entry)
    assert not f.exists()


# ── 2.6 delete() on already-absent file → no exception ──────────────

def test_delete_absent_file_no_error(tmp_path: Path) -> None:
    absent = tmp_path / "ghost.json"
    entry = LevelEntry(name="ghost", path=absent, modified_at=0.0)
    LevelLibrary.delete(entry)  # should not raise


# ── 2.7 import guard — level_library.py must NOT import pygame ──────

def test_no_pygame_import() -> None:
    import editor.level_library as mod

    source = Path(mod.__file__).read_text()
    assert "import pygame" not in source
