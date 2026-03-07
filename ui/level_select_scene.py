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
_TITLE_COLOR = (255, 255, 255)
_HINT_COLOR = (140, 140, 160)
_LINE_HEIGHT = 36
_TITLE_Y = 40
_LIST_TOP = 100
_HINT_MARGIN_BOTTOM = 30

_HINT_TEXT = (
    "[↑↓] Sélectionner  [Enter] Jouer  [E] Éditer  "
    "[T] Entraîner IA  [N] Nouveau  [DEL] Supprimer"
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
            self._title_font = pygame.font.Font(None, 40)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, 22)

        # Title
        title_surf = self._title_font.render("Level Select", True, _TITLE_COLOR)
        surface.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, _TITLE_Y))

        # Level list
        if not self._entries:
            empty_surf = self._font.render(
                "Aucun niveau — appuyez sur [N] pour en créer un",
                True, _HINT_COLOR,
            )
            surface.blit(
                empty_surf,
                (sw // 2 - empty_surf.get_width() // 2, _LIST_TOP),
            )
        else:
            for i, entry in enumerate(self._entries):
                y = _LIST_TOP + i * _LINE_HEIGHT
                label = entry.name
                if i == self._selected_idx:
                    # Highlight bar
                    bar_rect = pygame.Rect(
                        sw // 2 - 200, y - 2, 400, _LINE_HEIGHT,
                    )
                    pygame.draw.rect(surface, _SELECTED_COLOR, bar_rect, border_radius=4)
                txt_surf = self._font.render(label, True, _TEXT_COLOR)
                surface.blit(
                    txt_surf,
                    (sw // 2 - txt_surf.get_width() // 2, y + 4),
                )

        # Keyboard hints at bottom
        hint_surf = self._hint_font.render(_HINT_TEXT, True, _HINT_COLOR)
        surface.blit(
            hint_surf,
            (sw // 2 - hint_surf.get_width() // 2, sh - _HINT_MARGIN_BOTTOM),
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

    def _new_level(self) -> None:
        """Open a blank editor; flag for rescan on return."""
        from ui.editor_scene import EditorScene  # local import

        self._came_from_edit = True
        self.next_scene = EditorScene(return_scene=self)
