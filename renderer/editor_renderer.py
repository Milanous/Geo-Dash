"""
renderer/editor_renderer.py — Visual rendering for the level editor.

Draws: flat background, grid lines, tiles, cursor highlight, toolbar.
Uses the same colour palette as game_renderer.py for consistency.

Import rules: may import engine/, pygame. Never ai/.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

import pygame

from engine.physics import BLOCK_SIZE_PX
from engine.world import TileType, World, is_spike

# ---------------------------------------------------------------------------
# Palette — matches game_renderer.py
# ---------------------------------------------------------------------------

_SOLID_COLOR: tuple[int, int, int] = (0, 0, 0)
_SOLID_OUTLINE: tuple[int, int, int] = (0, 160, 210)
_SPIKE_COLOR: tuple[int, int, int] = (0, 0, 0)
_SPIKE_OUTLINE: tuple[int, int, int] = (220, 220, 220)
_FINISH_COLOR: tuple[int, int, int] = (255, 210, 0)

_BG_COLOR:       tuple[int, int, int] = (12, 12, 20)
_GRID_COLOR:     tuple[int, int, int] = (28, 28, 40)
_CURSOR_COLOR:   tuple[int, int, int, int] = (0, 201, 255, 30)   # RGBA
_CURSOR_BORDER:  tuple[int, int, int] = (0, 201, 255)

_TOOLBAR_BG:     tuple[int, int, int] = (10, 10, 18)
_BTN_INACTIVE:   tuple[int, int, int] = (24, 24, 38)
_BTN_ACTIVE:     tuple[int, int, int] = (0, 120, 80)
_BTN_PLAY:       tuple[int, int, int] = (20, 50, 100)
_BTN_PLAY_HOT:   tuple[int, int, int] = (30, 80, 150)
_BTN_SAVE:       tuple[int, int, int] = (90, 60, 20)
_BTN_SAVE_HOT:   tuple[int, int, int] = (140, 95, 30)
_TEXT_COLOR:     tuple[int, int, int] = (200, 204, 215)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

_TOOLBAR_HEIGHT: int = 40   # pixels
_BTN_W: int = 80
_BTN_H: int = 28
_BTN_PAD: int = 10          # gap between buttons
_BTN_MARGIN_X: int = 10     # left margin


def _btn_rect(idx: int, screen_h: int) -> pygame.Rect:
    """Return the pygame.Rect for toolbar button at index *idx*."""
    x = _BTN_MARGIN_X + idx * (_BTN_W + _BTN_PAD)
    y = screen_h - _TOOLBAR_HEIGHT + (_TOOLBAR_HEIGHT - _BTN_H) // 2
    return pygame.Rect(x, y, _BTN_W, _BTN_H)


# Button index mapping
_BTN_SOLID_IDX: int = 0
_BTN_SPIKE_IDX: int = 1
_BTN_FINISH_IDX: int = 2
_BTN_DELETE_IDX: int = 3
_BTN_PLAY_IDX: int = 4
_BTN_SAVE_IDX: int = 5

_BTN_DELETE:     tuple[int, int, int] = (100, 30, 30)
_BTN_DELETE_HOT: tuple[int, int, int] = (150, 45, 45)


def _spike_points_editor(
    tile: TileType, sx: int, sy: int, bs: int,
) -> list[tuple[int, int]]:
    """Return the three triangle vertices for an oriented spike in the editor."""
    if tile is TileType.SPIKE:          # apex UP
        return [(sx, sy + bs), (sx + bs, sy + bs), (sx + bs // 2, sy)]
    if tile is TileType.SPIKE_DOWN:     # apex DOWN
        return [(sx, sy), (sx + bs, sy), (sx + bs // 2, sy + bs)]
    if tile is TileType.SPIKE_LEFT:     # apex LEFT
        return [(sx + bs, sy), (sx + bs, sy + bs), (sx, sy + bs // 2)]
    # SPIKE_RIGHT — apex RIGHT
    return [(sx, sy), (sx, sy + bs), (sx + bs, sy + bs // 2)]


class EditorRenderer:
    """
    Stateless renderer for the level editor.

    Call ``draw()`` once per display frame from ``EditorScene.draw()``.
    """

    def __init__(self) -> None:
        self._font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
        world: World,
        editor_camera,          # EditorCamera — avoid circular import
        cursor_bx: int,
        cursor_by: int,
        selected_tile_type: TileType,
        erase_mode: bool = False,
    ) -> None:
        """
        Render the full editor frame.

        Args:
            surface:            Destination display surface.
            world:              Current editable level grid.
            editor_camera:      EditorCamera providing viewport offsets.
            cursor_bx:          Block X the mouse is hovering over.
            cursor_by:          Block Y the mouse is hovering over.
            selected_tile_type: Currently selected tile type (for toolbar highlight).
        """
        screen_w, screen_h = surface.get_size()
        bs = BLOCK_SIZE_PX

        # 1 — Background
        surface.fill(_BG_COLOR)

        # 2 — Draw tiles
        self._draw_tiles(surface, world, editor_camera, screen_h)

        # 3 — Grid lines
        self._draw_grid(surface, editor_camera, screen_w, screen_h)

        # 4 — Cursor highlight
        self._draw_cursor(surface, editor_camera, cursor_bx, cursor_by, screen_h)

        # 5 — Toolbar
        self._draw_toolbar(surface, screen_w, screen_h, selected_tile_type, erase_mode)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _world_to_screen(
        self,
        bx: float,
        by: float,
        editor_camera,
        screen_h: int,
    ) -> tuple[int, int]:
        """Return screen top-left pixel of block (bx, by)."""
        bs = BLOCK_SIZE_PX
        sx = int((bx - editor_camera.x_offset) * bs)
        # block row `by` has its bottom at screen_y = screen_h - int((by - y_offset) * bs)
        # and its top at screen_y - bs
        sy = screen_h - int((by - editor_camera.y_offset + 1) * bs)
        return sx, sy

    def _draw_tiles(
        self,
        surface: pygame.Surface,
        world: World,
        editor_camera,
        screen_h: int,
    ) -> None:
        bs = BLOCK_SIZE_PX
        screen_w = surface.get_width()

        for row in range(world.height):
            for col in range(world.width):
                tile = world.tile_at(col, row)
                if tile is TileType.AIR:
                    continue

                sx, sy = self._world_to_screen(col, row, editor_camera, screen_h)

                # Frustum cull
                if sx + bs <= 0 or sx >= screen_w:
                    continue
                if sy + bs <= 0 or sy >= screen_h - _TOOLBAR_HEIGHT:
                    continue

                rect = pygame.Rect(sx, sy, bs, bs)

                if tile is TileType.SOLID:
                    pygame.draw.rect(surface, _SOLID_COLOR, rect)
                    pygame.draw.rect(surface, _SOLID_OUTLINE, rect, 2)
                elif is_spike(tile):
                    pts = _spike_points_editor(tile, sx, sy, bs)
                    pygame.draw.polygon(surface, _SPIKE_COLOR, pts)
                    pygame.draw.polygon(surface, _SPIKE_OUTLINE, pts, 2)
                elif tile is TileType.FINISH:
                    bar_w = 4
                    bar_rect = pygame.Rect(sx + (bs - bar_w) // 2, sy, bar_w, bs)
                    pygame.draw.rect(surface, _FINISH_COLOR, bar_rect)

    def _draw_grid(
        self,
        surface: pygame.Surface,
        editor_camera,
        screen_w: int,
        screen_h: int,
    ) -> None:
        bs = BLOCK_SIZE_PX
        usable_h = screen_h - _TOOLBAR_HEIGHT

        # First visible column / row
        start_col = int(editor_camera.x_offset)
        start_row = int(editor_camera.y_offset)

        # Number of visible cells
        cols_visible = screen_w // bs + 2
        rows_visible = usable_h // bs + 2

        # Vertical lines
        for dc in range(cols_visible):
            col = start_col + dc
            sx, _ = self._world_to_screen(col, 0, editor_camera, screen_h)
            if 0 <= sx <= screen_w:
                pygame.draw.line(surface, _GRID_COLOR, (sx, 0), (sx, usable_h))

        # Horizontal lines
        for dr in range(rows_visible):
            row = start_row + dr
            _, sy = self._world_to_screen(0, row, editor_camera, screen_h)
            # sy is top of block `row`; draw at sy + bs = bottom of block row–1
            line_y = sy + bs
            if 0 <= line_y <= usable_h:
                pygame.draw.line(surface, _GRID_COLOR, (0, line_y), (screen_w, line_y))

    def _draw_cursor(
        self,
        surface: pygame.Surface,
        editor_camera,
        cursor_bx: int,
        cursor_by: int,
        screen_h: int,
    ) -> None:
        bs = BLOCK_SIZE_PX
        sx, sy = self._world_to_screen(cursor_bx, cursor_by, editor_camera, screen_h)
        rect = pygame.Rect(sx, sy, bs, bs)

        overlay = pygame.Surface((bs, bs), pygame.SRCALPHA)
        overlay.fill(_CURSOR_COLOR)
        surface.blit(overlay, (sx, sy))
        pygame.draw.rect(surface, _CURSOR_BORDER, rect, 1)

    def _draw_toolbar(
        self,
        surface: pygame.Surface,
        screen_w: int,
        screen_h: int,
        selected_tile_type: TileType,
        erase_mode: bool = False,
    ) -> None:
        # Toolbar background + top accent line
        tb_rect = pygame.Rect(0, screen_h - _TOOLBAR_HEIGHT, screen_w, _TOOLBAR_HEIGHT)
        pygame.draw.rect(surface, _TOOLBAR_BG, tb_rect)
        pygame.draw.line(surface, (0, 201, 255), (0, screen_h - _TOOLBAR_HEIGHT), (screen_w, screen_h - _TOOLBAR_HEIGHT), 1)

        font = self._get_font()

        # Mouse position for hover states
        mx, my = pygame.mouse.get_pos()

        # SOLID button
        solid_rect = _btn_rect(_BTN_SOLID_IDX, screen_h)
        solid_color = _BTN_ACTIVE if selected_tile_type is TileType.SOLID and not erase_mode else _BTN_INACTIVE
        pygame.draw.rect(surface, solid_color, solid_rect, border_radius=3)
        lbl = font.render("SOLID", True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=solid_rect.center))

        # SPIKE button (shows current orientation arrow)
        spike_rect = _btn_rect(_BTN_SPIKE_IDX, screen_h)
        spike_color = _BTN_ACTIVE if is_spike(selected_tile_type) and not erase_mode else _BTN_INACTIVE
        pygame.draw.rect(surface, spike_color, spike_rect, border_radius=3)
        _arrow = {TileType.SPIKE: "↑", TileType.SPIKE_DOWN: "↓",
                  TileType.SPIKE_LEFT: "←", TileType.SPIKE_RIGHT: "→"}
        spike_label = "SPIKE " + _arrow.get(selected_tile_type, "↑")
        lbl = font.render(spike_label, True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=spike_rect.center))

        # FINISH button
        finish_rect = _btn_rect(_BTN_FINISH_IDX, screen_h)
        finish_color = _BTN_ACTIVE if selected_tile_type is TileType.FINISH and not erase_mode else _BTN_INACTIVE
        pygame.draw.rect(surface, finish_color, finish_rect, border_radius=3)
        lbl = font.render("FINISH", True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=finish_rect.center))

        # DELETE button
        delete_rect = _btn_rect(_BTN_DELETE_IDX, screen_h)
        if erase_mode:
            delete_color = _BTN_ACTIVE
        elif delete_rect.collidepoint(mx, my):
            delete_color = _BTN_DELETE_HOT
        else:
            delete_color = _BTN_DELETE
        pygame.draw.rect(surface, delete_color, delete_rect, border_radius=3)
        lbl = font.render("DELETE", True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=delete_rect.center))

        # PLAY-TEST button
        play_rect = _btn_rect(_BTN_PLAY_IDX, screen_h)
        play_color = _BTN_PLAY_HOT if play_rect.collidepoint(mx, my) else _BTN_PLAY
        pygame.draw.rect(surface, play_color, play_rect, border_radius=3)
        lbl = font.render("PLAY [P]", True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=play_rect.center))

        # SAVE button
        save_rect = _btn_rect(_BTN_SAVE_IDX, screen_h)
        save_color = _BTN_SAVE_HOT if save_rect.collidepoint(mx, my) else _BTN_SAVE
        pygame.draw.rect(surface, save_color, save_rect, border_radius=3)
        lbl = font.render("SAVE [S]", True, _TEXT_COLOR)
        surface.blit(lbl, lbl.get_rect(center=save_rect.center))

    def _get_font(self) -> pygame.font.Font:
        """Lazy-load a small system font."""
        if self._font is None:
            self._font = pygame.font.Font(None, 18)
        return self._font

    # ------------------------------------------------------------------
    # Helper exposed for EditorScene (hit-testing toolbar buttons)
    # ------------------------------------------------------------------

    @staticmethod
    def toolbar_btn_rect(idx: int, screen_h: int) -> pygame.Rect:
        """Return the pygame.Rect for toolbar button *idx* (0=SOLID, 1=SPIKE, 2=FINISH, 3=DELETE, 4=PLAY, 5=SAVE)."""
        return _btn_rect(idx, screen_h)

    TOOLBAR_HEIGHT: int = _TOOLBAR_HEIGHT
    BTN_SOLID_IDX:  int = _BTN_SOLID_IDX
    BTN_SPIKE_IDX:  int = _BTN_SPIKE_IDX
    BTN_FINISH_IDX: int = _BTN_FINISH_IDX
    BTN_DELETE_IDX: int = _BTN_DELETE_IDX
    BTN_PLAY_IDX:   int = _BTN_PLAY_IDX
    BTN_SAVE_IDX:   int = _BTN_SAVE_IDX
