"""
ui/train_config_scene.py — Hyperparameter configuration screen for AI training.

Displays editable fields for TrainingConfig parameters.
User can click fields to edit, then launch training or press ESC to go back.

Import rules: ui/ may import ai/, engine/, pygame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from ai.training_config import TrainingConfig
from ui.scene import Scene

if TYPE_CHECKING:
    from engine.world import World

# ── Field definitions ────────────────────────────────────────────────
# (label, attr_name, type, default_value)
FIELDS: list[tuple[str, str, type, int | float]] = [
    ("Population size", "population_size", int, 1000),
    ("Max generations", "max_generations", int, 100),
    ("Top-N selection", "top_n", int, 10),
    ("Mutation sigma", "mutation_sigma", float, 1.0),
    ("Max seconds/gen", "max_seconds_per_gen", float, 120.0),
    ("P(move)", "p_move", float, 0.70),
    ("P(neuron)", "p_neuron", float, 0.25),
]

# ── Visual constants ─────────────────────────────────────────────────
_BG_COLOR = (15, 15, 25)
_TITLE_COLOR = (255, 255, 255)
_LABEL_COLOR = (200, 200, 210)
_INPUT_BG = (30, 30, 45)
_INPUT_ACTIVE_BG = (40, 40, 60)
_INPUT_BORDER = (80, 80, 100)
_INPUT_ACTIVE_BORDER = (60, 140, 255)
_TEXT_COLOR = (220, 220, 220)
_ERROR_COLOR = (255, 80, 80)
_BUTTON_COLOR = (40, 130, 80)
_BUTTON_HOVER_COLOR = (50, 160, 100)
_BUTTON_TEXT_COLOR = (255, 255, 255)

_FIELD_START_Y = 100
_FIELD_SPACING = 50
_LABEL_X = 120
_INPUT_X = 420
_INPUT_W = 200
_INPUT_H = 34
_BUTTON_W = 220
_BUTTON_H = 44
_BUTTON_MARGIN_BOTTOM = 60

# Allowed characters for numeric input
_DIGITS = set("0123456789")


class TrainConfigScene(Scene):
    """Configuration screen for AI training hyperparameters."""

    def __init__(
        self,
        world: World | None = None,
        level_name: str = "",
        return_scene: Scene | None = None,
    ) -> None:
        super().__init__()
        self._world = world
        self._level_name = level_name
        self._return_scene_instance = return_scene
        
        self.values: dict[str, str] = {
            attr: str(default) for _, attr, _, default in FIELDS
        }
        self.active_field: str | None = None
        self.error_msg: str = ""

        # Lazy-init fonts / rects (require pygame.init)
        self._font: pygame.font.Font | None = None
        self._title_font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._field_rects: dict[str, pygame.Rect] = {}
        self._button_rect: pygame.Rect | None = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.next_scene = self._get_return_scene()
                    return True

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._try_launch()
                    return True

                if self.active_field is not None:
                    self._handle_typing(event)

        return True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(_BG_COLOR)
        sw = surface.get_width()

        # Lazy font init
        if self._font is None:
            self._font = pygame.font.Font(None, 28)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, 40)
        if self._small_font is None:
            self._small_font = pygame.font.Font(None, 22)

        # Title
        title_surf = self._title_font.render(
            "AI Training Configuration", True, _TITLE_COLOR,
        )
        surface.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, 36))

        # Fields
        self._field_rects.clear()
        for i, (label, attr, _, _) in enumerate(FIELDS):
            y = _FIELD_START_Y + i * _FIELD_SPACING

            # Label
            lbl_surf = self._font.render(label, True, _LABEL_COLOR)
            surface.blit(lbl_surf, (_LABEL_X, y + 6))

            # Input box
            rect = pygame.Rect(_INPUT_X, y, _INPUT_W, _INPUT_H)
            self._field_rects[attr] = rect

            is_active = attr == self.active_field
            bg = _INPUT_ACTIVE_BG if is_active else _INPUT_BG
            border = _INPUT_ACTIVE_BORDER if is_active else _INPUT_BORDER

            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, border, rect, width=2, border_radius=4)

            # Value text
            val_surf = self._font.render(self.values[attr], True, _TEXT_COLOR)
            surface.blit(val_surf, (rect.x + 8, rect.y + 6))

        # Error message
        if self.error_msg:
            err_surf = self._small_font.render(self.error_msg, True, _ERROR_COLOR)
            err_y = _FIELD_START_Y + len(FIELDS) * _FIELD_SPACING + 10
            surface.blit(err_surf, (sw // 2 - err_surf.get_width() // 2, err_y))

        # Launch button
        sh = surface.get_height()
        btn_x = sw // 2 - _BUTTON_W // 2
        btn_y = sh - _BUTTON_MARGIN_BOTTOM - _BUTTON_H
        btn_rect = pygame.Rect(btn_x, btn_y, _BUTTON_W, _BUTTON_H)
        self._button_rect = btn_rect

        mouse_pos = pygame.mouse.get_pos()
        hover = btn_rect.collidepoint(mouse_pos)
        color = _BUTTON_HOVER_COLOR if hover else _BUTTON_COLOR
        pygame.draw.rect(surface, color, btn_rect, border_radius=6)

        btn_txt = self._font.render("Launch Training", True, _BUTTON_TEXT_COLOR)
        surface.blit(
            btn_txt,
            (btn_rect.centerx - btn_txt.get_width() // 2,
             btn_rect.centery - btn_txt.get_height() // 2),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Determine which field or button was clicked."""
        # Check button
        if self._button_rect and self._button_rect.collidepoint(pos):
            self._try_launch()
            return

        # Check input fields
        self.active_field = None
        for attr, rect in self._field_rects.items():
            if rect.collidepoint(pos):
                self.active_field = attr
                break

    def _handle_typing(self, event: pygame.event.Event) -> None:
        """Process keyboard input on the active field."""
        attr = self.active_field
        if attr is None:
            return

        if event.key == pygame.K_BACKSPACE:
            self.values[attr] = self.values[attr][:-1]
        elif event.unicode in _DIGITS:
            self.values[attr] += event.unicode
        elif event.unicode == "." and "." not in self.values[attr]:
            self.values[attr] += "."

    def _try_launch(self) -> None:
        """Validate values, build TrainingConfig, and transition to AITrainScene."""
        self.error_msg = ""
        kwargs: dict[str, int | float] = {}

        for _, attr, typ, _ in FIELDS:
            raw = self.values[attr].strip()
            if not raw:
                self.error_msg = f"Field '{attr}' cannot be empty."
                return
            try:
                kwargs[attr] = typ(raw)
            except ValueError:
                self.error_msg = f"Invalid value for '{attr}': {raw}"
                return

        try:
            config = TrainingConfig(**kwargs)
        except ValueError as exc:
            self.error_msg = str(exc)
            return

        try:
            from ui.ai_train_scene import AITrainScene  # local import

            self.next_scene = AITrainScene(
                config=config,
                world=self._world,
                level_name=self._level_name,
                return_scene=self._get_return_scene(),
            )
        except ImportError:
            # AITrainScene not yet implemented (Story 5.4); store config for later
            self.error_msg = "AITrainScene not available yet."

    def _get_return_scene(self) -> Scene | None:
        """Return the saved return scene, or build a new LevelSelectScene."""
        if self._return_scene_instance is not None:
            return self._return_scene_instance
            
        try:
            from ui.level_select_scene import LevelSelectScene

            return LevelSelectScene()
        except ImportError:
            return None
