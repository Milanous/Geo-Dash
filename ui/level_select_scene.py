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
from ui import theme as T

_LIST_TOP = 110

_HINT_TEXT = (
    "[↑↓] Sélectionner  [Enter] Jouer  [E] Éditer  "
    "[T] Entraîner IA  [R] Replay  [N] Nouveau  [G] Aléatoire  [DEL] Supprimer"
)

# Sentinel index for the special "random level" entry shown at the top
_RANDOM_ENTRY_IDX = -1


class LevelSelectScene(Scene):
    """Level selection screen — main entry point of the game."""

    def __init__(self, folder: str = "data/levels") -> None:
        super().__init__()
        self._folder = folder
        self._entries: list[LevelEntry] = LevelLibrary.scan(folder)
        # Index 0 is reserved for the special random entry; real levels start at 1.
        # _selected_idx == 0  → random entry selected
        # _selected_idx >= 1  → self._entries[_selected_idx - 1] selected
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
                    # total_items = 1 (random) + len(entries)
                    if self._selected_idx < len(self._entries):
                        self._selected_idx += 1

                elif event.key == pygame.K_RETURN:
                    if self._selected_idx == 0:
                        self._open_random_generator()
                    elif self._entries:
                        self._load_and_play(self._entries[self._selected_idx - 1])

                elif event.key == pygame.K_e:
                    if self._selected_idx > 0 and self._entries:
                        self._load_and_edit(self._entries[self._selected_idx - 1])

                elif event.key == pygame.K_t:
                    if self._selected_idx == 0:
                        self._open_random_generator()
                    elif self._entries:
                        self._load_and_train(self._entries[self._selected_idx - 1])

                elif event.key == pygame.K_r:
                    if self._selected_idx > 0 and self._entries:
                        self._load_and_replay(self._entries[self._selected_idx - 1])

                elif event.key == pygame.K_g:
                    self._open_random_generator()

                elif event.key == pygame.K_n:
                    self._new_level()

                elif event.key == pygame.K_DELETE:
                    if self._selected_idx > 0 and self._entries:
                        entry = self._entries[self._selected_idx - 1]
                        LevelLibrary.delete(entry)
                        self._entries = LevelLibrary.scan(self._folder)
                        # Keep selection on the same position, clamped
                        max_idx = len(self._entries)  # 0 = random always exists
                        if self._selected_idx > max_idx:
                            self._selected_idx = max_idx

        return True

    def update(self, dt: float) -> None:
        """Rescan levels when returning from an editor sub-scene."""
        if self._came_from_edit:
            self._entries = LevelLibrary.scan(self._folder)
            self._came_from_edit = False
            # Clamp index: 0 = random level (always valid); up to len(entries)
            if self._selected_idx > len(self._entries):
                self._selected_idx = len(self._entries)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the level list centred on screen."""
        T.fill_bg(surface)

        sw = surface.get_width()
        sh = surface.get_height()

        # Lazy font init
        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, T.FONT_TITLE)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, T.FONT_HINT)

        # ── Header ───────────────────────────────────────────────────
        T.draw_header(surface, "GEO-DASH", "Sélection de niveau")

        # ── List panel ───────────────────────────────────────────────
        panel_x = sw // 2 - 220
        panel_w = 440
        list_area_top = _LIST_TOP
        list_area_bottom = sh - T.HINT_BAR_H - 10
        panel_h = list_area_bottom - list_area_top

        panel_rect = pygame.Rect(panel_x, list_area_top, panel_w, panel_h)
        T.draw_panel(surface, panel_rect)

        # ── Special random-level entry (always first) ────────────────
        inner_top = list_area_top + 10
        rand_card_rect = pygame.Rect(panel_x + 10, inner_top, panel_w - 20, T.LINE_H - 6)

        # Draw with gold accent when selected
        rand_selected = (self._selected_idx == 0)
        T.draw_card(surface, rand_card_rect, selected=rand_selected, accent=T.GOLD)

        dice_surf = self._font.render("🎲  Niveau Aléatoire", True,
                                      T.GOLD if rand_selected else T.TEXT)
        surface.blit(
            dice_surf,
            (rand_card_rect.x + 16,
             rand_card_rect.y + (rand_card_rect.height - dice_surf.get_height()) // 2),
        )
        gen_hint = self._hint_font.render("[G]", True, T.GOLD)
        surface.blit(
            gen_hint,
            (rand_card_rect.right - gen_hint.get_width() - 12,
             rand_card_rect.y + (rand_card_rect.height - gen_hint.get_height()) // 2),
        )

        # Thin separator below the random entry
        sep_y = inner_top + T.LINE_H + 2
        sep_surf = pygame.Surface((panel_w - 20, 1), pygame.SRCALPHA)
        sep_surf.fill((*T.GOLD, 40))
        surface.blit(sep_surf, (panel_x + 10, sep_y))

        real_list_top = sep_y + 6

        # ── Saved levels list ─────────────────────────────────────────
        if not self._entries:
            empty_surf = self._font.render(
                "Aucun niveau — appuyez sur [N]",
                True, T.TEXT_DIM,
            )
            surface.blit(
                empty_surf,
                (sw // 2 - empty_surf.get_width() // 2, real_list_top + 10),
            )
        else:
            avail_h = list_area_bottom - real_list_top - 4
            max_visible = max(1, avail_h // T.LINE_H)
            # Scroll offset computed relative to real entry index (1-based)
            real_idx = max(0, self._selected_idx - 1)
            scroll = max(0, real_idx - max_visible + 1)

            for vi, i in enumerate(range(scroll, min(scroll + max_visible, len(self._entries)))):
                entry = self._entries[i]
                y = real_list_top + vi * T.LINE_H

                card_rect = pygame.Rect(panel_x + 10, y, panel_w - 20, T.LINE_H - 6)
                T.draw_card(surface, card_rect, selected=(i + 1 == self._selected_idx))

                txt_surf = self._font.render(entry.name, True, T.TEXT)
                surface.blit(
                    txt_surf,
                    (card_rect.x + 16,
                     card_rect.y + (card_rect.height - txt_surf.get_height()) // 2),
                )

                idx_surf = self._hint_font.render(f"{i + 1}", True, T.TEXT_DIM)
                surface.blit(
                    idx_surf,
                    (card_rect.right - idx_surf.get_width() - 12,
                     card_rect.y + (card_rect.height - idx_surf.get_height()) // 2),
                )

            if scroll > 0:
                up_surf = self._hint_font.render("▲", True, T.CYAN)
                surface.blit(up_surf, (sw // 2 - up_surf.get_width() // 2, real_list_top + 2))
            if scroll + max_visible < len(self._entries):
                dn_surf = self._hint_font.render("▼", True, T.CYAN)
                surface.blit(dn_surf, (sw // 2 - dn_surf.get_width() // 2, list_area_bottom - 14))

        # ── Footer ───────────────────────────────────────────────────
        T.draw_footer(surface, _HINT_TEXT)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _open_random_generator(self) -> None:
        """Open the parametric level generator configuration screen."""
        from ui.gen_config_scene import GenConfigScene  # local import

        self.next_scene = GenConfigScene(return_scene=self)

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
