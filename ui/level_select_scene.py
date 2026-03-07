"""
ui/level_select_scene.py — Level selection scene (main entry point).

Displays all saved levels and allows the player to Play, Edit or Train AI.
Keyboard navigation: ↑/↓ select, Enter→Play, E→Edit, T→Train AI,
N→New Level, DEL→delete with rescan, ESC→quit.

Import rules: ui/ may import editor/, engine/, renderer/, pygame.
"""

from __future__ import annotations

import pygame

from editor.level_io import load_level
from editor.level_library import LevelEntry, LevelLibrary
from ui.scene import Scene

# ── Visual constants ──────────────────────────────────────────────────
_BG_COLOR = (15, 15, 25)
_TEXT_COLOR = (220, 220, 220)
_SELECTED_COLOR = (60, 120, 200)
_SELECTED_GLOW = (40, 90, 180)
_TITLE_COLOR = (255, 255, 255)
_SUBTITLE_COLOR = (160, 170, 200)
_HINT_COLOR = (140, 140, 160)
_ACCENT_COLOR = (0, 201, 255)        # Cyan accent (matches game palette)
_PANEL_BG = (20, 20, 35)
_PANEL_BORDER = (40, 50, 80)
_ENTRY_BG = (25, 25, 40)
_LINE_HEIGHT = 44
_TITLE_Y = 30
_LIST_TOP = 120
_HINT_BAR_H = 50

_HINT_TEXT = (
    "[↑↓] Sélectionner  [Enter] Jouer  [E] Éditer  "
    "[T] Entraîner IA  [R] Replay  [N] Nouveau  [DEL] Supprimer"
)


class LevelSelectScene(Scene):
    """Level selection screen — main entry point of the game."""

    def __init__(self, folder: str = "data/levels") -> None:
        super().__init__()
        self._folder = folder
        self._entries: list[LevelEntry] = LevelLibrary.scan(folder)
        self._selected_idx: int = 0
        self._font: pygame.font.Font | None = None
        self._title_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None
        # Flag to rescan after returning from EditorScene
        self._came_from_edit: bool = False

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key == pygame.K_UP:
                    if self._selected_idx > 0:
                        self._selected_idx -= 1

                elif event.key == pygame.K_DOWN:
                    if self._selected_idx < len(self._entries) - 1:
                        self._selected_idx += 1

                elif event.key == pygame.K_RETURN:
                    if self._entries:
                        self._load_and_play(self._entries[self._selected_idx])

                elif event.key == pygame.K_e:
                    if self._entries:
                        self._load_and_edit(self._entries[self._selected_idx])

                elif event.key == pygame.K_t:
                    if self._entries:
                        self._load_and_train(self._entries[self._selected_idx])

                elif event.key == pygame.K_r:
                    if self._entries:
                        self._load_and_replay(self._entries[self._selected_idx])

                elif event.key == pygame.K_n:
                    self._new_level()

                elif event.key == pygame.K_DELETE:
                    if self._entries:
                        entry = self._entries[self._selected_idx]
                        LevelLibrary.delete(entry)
                        self._entries = LevelLibrary.scan(self._folder)
                        if self._selected_idx >= len(self._entries):
                            self._selected_idx = max(0, len(self._entries) - 1)

        return True

    def update(self, dt: float) -> None:
        """Rescan levels when returning from an editor sub-scene."""
        if self._came_from_edit:
            self._entries = LevelLibrary.scan(self._folder)
            self._came_from_edit = False
            # Clamp index in case levels changed
            if self._selected_idx >= len(self._entries):
                self._selected_idx = max(0, len(self._entries) - 1)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the level list centred on screen."""
        surface.fill(_BG_COLOR)

        sw = surface.get_width()
        sh = surface.get_height()

        # Lazy font init (pygame must be initialised before Font creation)
        if self._font is None:
            self._font = pygame.font.Font(None, 28)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, 44)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, 22)

        # ── Header area ──────────────────────────────────────────────
        # Title
        title_surf = self._title_font.render("GEO-DASH", True, _TITLE_COLOR)
        surface.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, _TITLE_Y))

        # Accent line under title
        line_w = 120
        line_y = _TITLE_Y + title_surf.get_height() + 8
        pygame.draw.line(
            surface, _ACCENT_COLOR,
            (sw // 2 - line_w // 2, line_y),
            (sw // 2 + line_w // 2, line_y), 2,
        )

        # Subtitle
        sub_font = pygame.font.Font(None, 24)
        sub_surf = sub_font.render("Sélection de niveau", True, _SUBTITLE_COLOR)
        surface.blit(sub_surf, (sw // 2 - sub_surf.get_width() // 2, line_y + 10))

        # ── List panel ───────────────────────────────────────────────
        panel_x = sw // 2 - 220
        panel_w = 440
        list_area_top = _LIST_TOP
        list_area_bottom = sh - _HINT_BAR_H - 10
        panel_h = list_area_bottom - list_area_top

        # Panel background
        panel_rect = pygame.Rect(panel_x, list_area_top, panel_w, panel_h)
        pygame.draw.rect(surface, _PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(surface, _PANEL_BORDER, panel_rect, width=1, border_radius=8)

        # Level list
        if not self._entries:
            empty_surf = self._font.render(
                "Aucun niveau — appuyez sur [N]",
                True, _HINT_COLOR,
            )
            surface.blit(
                empty_surf,
                (sw // 2 - empty_surf.get_width() // 2, list_area_top + 30),
            )
        else:
            # Visible entries (clip to panel)
            inner_top = list_area_top + 10
            max_visible = (panel_h - 20) // _LINE_HEIGHT
            # Scroll offset so selected is always visible
            scroll = max(0, self._selected_idx - max_visible + 1)

            for vi, i in enumerate(range(scroll, min(scroll + max_visible, len(self._entries)))):
                entry = self._entries[i]
                y = inner_top + vi * _LINE_HEIGHT
                label = entry.name

                # Entry card background
                card_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, _LINE_HEIGHT - 6)

                if i == self._selected_idx:
                    # Selected — accent fill + left accent bar
                    pygame.draw.rect(surface, _SELECTED_COLOR, card_rect, border_radius=5)
                    # Left accent bar
                    pygame.draw.rect(
                        surface, _ACCENT_COLOR,
                        pygame.Rect(card_rect.x, card_rect.y, 3, card_rect.height),
                        border_radius=2,
                    )
                else:
                    # Normal card
                    pygame.draw.rect(surface, _ENTRY_BG, card_rect, border_radius=5)

                txt_surf = self._font.render(label, True, _TEXT_COLOR)
                surface.blit(
                    txt_surf,
                    (card_rect.x + 16, card_rect.y + (card_rect.height - txt_surf.get_height()) // 2),
                )

                # Entry index indicator
                idx_surf = self._hint_font.render(f"{i + 1}", True, _HINT_COLOR)
                surface.blit(
                    idx_surf,
                    (card_rect.right - idx_surf.get_width() - 12,
                     card_rect.y + (card_rect.height - idx_surf.get_height()) // 2),
                )

            # Scroll indicators
            if scroll > 0:
                up_surf = self._hint_font.render("▲", True, _ACCENT_COLOR)
                surface.blit(up_surf, (sw // 2 - up_surf.get_width() // 2, list_area_top + 2))
            if scroll + max_visible < len(self._entries):
                dn_surf = self._hint_font.render("▼", True, _ACCENT_COLOR)
                surface.blit(dn_surf, (sw // 2 - dn_surf.get_width() // 2, list_area_bottom - 14))

        # ── Footer hint bar ──────────────────────────────────────────
        footer_y = sh - _HINT_BAR_H
        pygame.draw.rect(surface, _PANEL_BG, (0, footer_y, sw, _HINT_BAR_H))
        pygame.draw.line(surface, _PANEL_BORDER, (0, footer_y), (sw, footer_y), 1)

        hint_surf = self._hint_font.render(_HINT_TEXT, True, _HINT_COLOR)
        surface.blit(
            hint_surf,
            (sw // 2 - hint_surf.get_width() // 2,
             footer_y + (_HINT_BAR_H - hint_surf.get_height()) // 2),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_and_play(self, entry: LevelEntry) -> None:
        """Load *entry* and switch to PlayScene with return here."""
        from ui.play_scene import PlayScene  # local import to avoid cycle

        world = load_level(str(entry.path))
        self.next_scene = PlayScene(world=world, return_scene=self, level_name=entry.name)

    def _load_and_edit(self, entry: LevelEntry) -> None:
        """Open the editor for *entry*; flag for rescan on return."""
        from ui.editor_scene import EditorScene  # local import

        editor = EditorScene(level_path=str(entry.path), return_scene=self)
        self._came_from_edit = True
        self.next_scene = editor

    def _load_and_train(self, entry: LevelEntry) -> None:
        """Launch AI training on *entry*."""
        from ui.train_config_scene import TrainConfigScene

        world = load_level(str(entry.path))
        self.next_scene = TrainConfigScene(
            world=world,
            level_name=entry.name,
            return_scene=self,
        )

    def _load_and_replay(self, entry: LevelEntry) -> None:
        """Open the replay scene for *entry*."""
        from ui.replay_scene import ReplayScene  # local import

        world = load_level(str(entry.path))
        self.next_scene = ReplayScene(world=world, return_scene=self)

    def _new_level(self) -> None:
        """Open a blank editor; flag for rescan on return."""
        from ui.editor_scene import EditorScene  # local import

        self._came_from_edit = True
        self.next_scene = EditorScene(return_scene=self)
