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
from ui import theme as T

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
    ("P(network)", "p_network", float, 0.05),
    ("Mutations/individual", "mutations_per_individual", int, 1),
]

# ── Layout constants ─────────────────────────────────────────────────
_FIELD_START_Y = 120
_FIELD_SPACING = 44
_LABEL_X = 140
_INPUT_X = 420
_INPUT_W = 200
_INPUT_H = 32
_BUTTON_W = 240
_BUTTON_H = 46
_BUTTON_MARGIN_BOTTOM = 58

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
        T.fill_bg(surface)
        sw = surface.get_width()

        # Lazy font init
        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, T.FONT_TITLE)
        if self._small_font is None:
            self._small_font = pygame.font.Font(None, T.FONT_SMALL)

        # ── Header ─────────────────────────────────────────────────
        sub_text = f"Niveau : {self._level_name}" if self._level_name else "Configuration des hyperparamètres"
        T.draw_header(surface, "AI Training Configuration", sub_text)

        # ── Form panel ─────────────────────────────────────────────
        panel_x = 80
        panel_w = sw - 160
        panel_top = _FIELD_START_Y - 16
        panel_h = len(FIELDS) * _FIELD_SPACING + 30
        panel_rect = pygame.Rect(panel_x, panel_top, panel_w, panel_h)
        T.draw_panel(surface, panel_rect)

        # Fields
        self._field_rects.clear()
        for i, (label, attr, _, _) in enumerate(FIELDS):
            y = _FIELD_START_Y + i * _FIELD_SPACING

            lbl_surf = self._font.render(label, True, T.TEXT_SEC)
            surface.blit(lbl_surf, (_LABEL_X, y + 5))

            rect = pygame.Rect(_INPUT_X, y, _INPUT_W, _INPUT_H)
            self._field_rects[attr] = rect

            is_active = attr == self.active_field
            bg = T.BG_INPUT_ACT if is_active else T.BG_INPUT
            border = T.BORDER_ACC if is_active else T.BORDER_HI

            pygame.draw.rect(surface, bg, rect, border_radius=T.RADIUS_SM)
            pygame.draw.rect(surface, border, rect, width=1 if not is_active else 2, border_radius=T.RADIUS_SM)

            val_surf = self._font.render(self.values[attr], True, T.TEXT)
            surface.blit(val_surf, (rect.x + 10, rect.y + 5))

        # Error message
        if self.error_msg:
            err_surf = self._small_font.render(self.error_msg, True, T.RED)
            err_y = panel_top + panel_h + 12
            surface.blit(err_surf, (sw // 2 - err_surf.get_width() // 2, err_y))

        # ── Launch button ──────────────────────────────────────────
        sh = surface.get_height()
        btn_x = sw // 2 - _BUTTON_W // 2
        btn_y = sh - _BUTTON_MARGIN_BOTTOM - _BUTTON_H
        btn_rect = pygame.Rect(btn_x, btn_y, _BUTTON_W, _BUTTON_H)
        self._button_rect = btn_rect

        mouse_pos = pygame.mouse.get_pos()
        hover = btn_rect.collidepoint(mouse_pos)
        T.draw_btn(surface, btn_rect, "▶  Lancer l'entraînement", hover=hover)

        # Footer hint
        T.draw_footer(surface, "[ESC] Retour   [Entrée] Lancer")

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
