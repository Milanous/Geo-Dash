"""
tests/test_editor_scene.py — Headless logic tests for ui/editor_scene.py (Story 3.4).

These tests exercise only the pure logic (tile placement via world coords,
camera coordinate conversion) — NO pygame display, NO rendering calls.
"""

from __future__ import annotations

import math

from engine.world import TileType
from ui.editor_scene import EditorScene


# ---------------------------------------------------------------------------
# Task 3.1 — EditorScene instantiates without error (no display)
# ---------------------------------------------------------------------------

def test_editor_scene_instantiates() -> None:
    scene = EditorScene()
    assert scene._editor is not None
    assert scene._camera is not None
    assert scene._renderer is not None


# ---------------------------------------------------------------------------
# Task 3.2 — screen_to_world + place_tile → correct tile in world
# ---------------------------------------------------------------------------

def test_place_tile_via_screen_coords() -> None:
    """
    At camera offset 0,0 and screen_h=600:
      screen_to_world(15, 585, 600) → bx=0.5, by=0.5 → tile at (0, 0)
    """
    scene = EditorScene()
    screen_h = 600
    bx, by = scene._camera.screen_to_world(15, screen_h - 15, screen_h)
    ibx, iby = math.floor(bx), math.floor(by)
    scene._editor.place_tile(ibx, iby)
    assert scene._editor.world.tile_at(ibx, iby) == TileType.SOLID


def test_place_tile_spike_via_screen_coords() -> None:
    scene = EditorScene()
    screen_h = 600
    scene._editor.set_selected_tile_type(TileType.SPIKE)
    bx, by = scene._camera.screen_to_world(45, screen_h - 45, screen_h)
    ibx, iby = math.floor(bx), math.floor(by)
    scene._editor.place_tile(ibx, iby)
    assert scene._editor.world.tile_at(ibx, iby) == TileType.SPIKE


def test_place_tile_with_camera_offset() -> None:
    """With x_offset=10, screen coord sx=15 → bx = 15/30 + 10 = 10.5 → tile 10."""
    scene = EditorScene()
    screen_h = 600
    scene._camera.x_offset = 10.0
    scene._camera.y_offset = 0.0
    bx, by = scene._camera.screen_to_world(15, screen_h - 15, screen_h)
    ibx, iby = math.floor(bx), math.floor(by)
    assert ibx == 10
    scene._editor.place_tile(ibx, iby)
    assert scene._editor.world.tile_at(ibx, iby) == TileType.SOLID


# ---------------------------------------------------------------------------
# Task 3.3 — erase_tile via screen coords → AIR
# ---------------------------------------------------------------------------

def test_erase_tile_via_screen_coords() -> None:
    scene = EditorScene()
    screen_h = 600
    bx, by = scene._camera.screen_to_world(15, screen_h - 15, screen_h)
    ibx, iby = math.floor(bx), math.floor(by)
    # Place first
    scene._editor.place_tile(ibx, iby)
    assert scene._editor.world.tile_at(ibx, iby) == TileType.SOLID
    # Then erase
    scene._editor.erase_tile(ibx, iby)
    assert scene._editor.world.tile_at(ibx, iby) == TileType.AIR


def test_erase_nonexistent_tile_is_noop() -> None:
    scene = EditorScene()
    # Erasing an already-AIR tile should not raise
    scene._editor.erase_tile(5, 5)
    assert scene._editor.world.tile_at(5, 5) == TileType.AIR


# ---------------------------------------------------------------------------
# Additional — EditorScene with level_path loads existing world
# ---------------------------------------------------------------------------

def test_editor_scene_loads_level(tmp_path) -> None:
    from engine.world import World
    from editor.level_io import save_level

    # Save a level to tmp_path
    world = World(50, 15)
    world.set_tile(3, 1, TileType.SOLID)
    level_file = tmp_path / "test.json"
    save_level(level_file, world)

    scene = EditorScene(level_path=str(level_file))
    assert scene._editor.world.tile_at(3, 1) == TileType.SOLID
    assert scene._editor.world.width == 50
    assert scene._editor.world.height == 15


def test_editor_scene_initial_selected_tile_is_solid() -> None:
    scene = EditorScene()
    assert scene._editor.selected_tile_type == TileType.SOLID


def test_editor_scene_next_scene_starts_none() -> None:
    scene = EditorScene()
    assert scene.next_scene is None


# ---------------------------------------------------------------------------
# Story 6.5 — SAVE button in toolbar
# ---------------------------------------------------------------------------

def test_btn_save_idx_exists_and_equals_4() -> None:
    from renderer.editor_renderer import EditorRenderer
    assert hasattr(EditorRenderer, "BTN_SAVE_IDX")
    assert EditorRenderer.BTN_SAVE_IDX == 4


def test_toolbar_btn_rect_save_returns_valid_rect() -> None:
    import pygame
    from renderer.editor_renderer import EditorRenderer
    rect = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_SAVE_IDX, 600)
    assert isinstance(rect, pygame.Rect)
    assert rect.width > 0 and rect.height > 0
def test_save_button_hit_test_triggers_save_logic(monkeypatch) -> None:
    """AC8: Verify clicking the SAVE button rect triggers the save logic."""
    import pygame
    from renderer.editor_renderer import EditorRenderer
    from ui.editor_scene import EditorScene

    scene = EditorScene()
    
    # Mock _do_save to verify it gets called
    did_call_save = False
    def mock_do_save():
        nonlocal did_call_save
        did_call_save = True
    
    monkeypatch.setattr(scene, "_do_save", mock_do_save)
    
    # Needs a level name so it calls _do_save instead of opening SaveDialog
    scene._level_name = "test_level"

    # Get the SAVE button rect
    screen_h = 600
    save_rect = EditorRenderer.toolbar_btn_rect(EditorRenderer.BTN_SAVE_IDX, screen_h)
    
    # Click exactly in the middle of the save button
    mx = save_rect.centerx
    my = save_rect.centery
    
    # Setup mock event
    class MockEvent:
        def __init__(self, pos):
            self.type = pygame.MOUSEBUTTONDOWN
            self.button = 1
            self.pos = pos
            self.buttons = (1, 0, 0)
    
    mock_event = MockEvent((mx, my))
    
    # The actual handle_events logic pulls from pygame.event.get() and pygame.key.get_mods()
    monkeypatch.setattr(pygame.event, "get", lambda: [mock_event])
    monkeypatch.setattr(pygame.key, "get_mods", lambda: 0)
    
    # Trigger event handling
    scene.handle_events()
    
    assert did_call_save is True