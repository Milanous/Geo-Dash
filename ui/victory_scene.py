"""
ui/victory_scene.py — Victory screen shown when the player reaches the finish.

Displays "LEVEL COMPLETE!", the level name, and options to replay or
return to level select.

Import rules: ui/ may import engine/, renderer/, pygame.
"""

from __future__ import annotations

import pygame

from engine.world import World
from ui.scene import Scene

# ── Visual constants ──────────────────────────────────────────────────
_BG_COLOR = (10, 10, 20)
_TITLE_COLOR = (80, 255, 100)
_STAR_COLOR = (255, 215, 0)
_TEXT_COLOR = (220, 220, 220)
_HINT_COLOR = (140, 140, 160)
_PANEL_BG = (18, 18, 32)
_PANEL_BORDER = (50, 60, 90)
_ACCENT_COLOR = (0, 201, 255)


class VictoryScene(Scene):
    """
    Victory screen — shown when the player finishes a level.

    Controls:
      R     → replay the same level
      Enter → return to level select
      ESC   → return to level select
    """

    def __init__(
        self,
        level_name: str = "",
        world: World | None = None,
        return_scene: Scene | None = None,
    ) -> None:
        super().__init__()
        self._level_name: str = level_name
        self._world: World | None = world
        self._return_scene: Scene | None = return_scene
        self._title_font: pygame.font.Font | None = None
        self._name_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._replay()
                    return True
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._go_level_select()
                    return True
        return True

    def update(self, dt: float) -> None:  # noqa: ARG002
        """Nothing to update — static screen."""

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(_BG_COLOR)

        sw = surface.get_width()
        sh = surface.get_height()

        # Lazy font init
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, 56)
        if self._name_font is None:
            self._name_font = pygame.font.Font(None, 32)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, 26)

        # ── Centred victory panel ───────────────────────────────
        panel_w, panel_h = 420, 260
        px = (sw - panel_w) // 2
        py = (sh - panel_h) // 2 - 20
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        pygame.draw.rect(surface, _PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(surface, _PANEL_BORDER, panel_rect, width=1, border_radius=12)

        # Star decorations "  ★  ★  ★  "
        star_font = pygame.font.Font(None, 42)
        stars = star_font.render("★   ★   ★", True, _STAR_COLOR)
        surface.blit(stars, (sw // 2 - stars.get_width() // 2, py + 24))

        # "LEVEL COMPLETE!"
        title = self._title_font.render("LEVEL COMPLETE!", True, _TITLE_COLOR)
        surface.blit(title, (sw // 2 - title.get_width() // 2, py + 70))

        # Accent line
        line_w = 160
        line_y = py + 70 + title.get_height() + 12
        pygame.draw.line(
            surface, _ACCENT_COLOR,
            (sw // 2 - line_w // 2, line_y),
            (sw // 2 + line_w // 2, line_y), 2,
        )

        # Level name
        if self._level_name:
            name_surf = self._name_font.render(self._level_name, True, _TEXT_COLOR)
            surface.blit(name_surf, (sw // 2 - name_surf.get_width() // 2, line_y + 16))

        # Options (inside panel, near bottom)
        hint = self._hint_font.render(
            "[R] Rejouer    [Enter/ESC] Sélection niveaux",
            True,
            _HINT_COLOR,
        )
        surface.blit(
            hint,
            (sw // 2 - hint.get_width() // 2, py + panel_h - 42),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _replay(self) -> None:
        """Restart the same level via a fresh PlayScene."""
        from ui.play_scene import PlayScene  # local import to avoid cycle

        self.next_scene = PlayScene(
            world=self._world,
            return_scene=self._return_scene,
            level_name=self._level_name,
        )

    def _go_level_select(self) -> None:
        """Return to level select (or quit if no return_scene)."""
        if self._return_scene is not None:
            self.next_scene = self._return_scene
        else:
            from ui.level_select_scene import LevelSelectScene  # local import

            self.next_scene = LevelSelectScene()
