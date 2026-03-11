"""
ui/gen_config_scene.py — Parametric level generation configuration screen.

Displays editable fields for GeneratorConfig parameters.
User can navigate fields with Tab/click, then:
  [Enter] / [P] → Generate & Play
  [T]           → Generate & Train AI
  [ESC]         → Back to LevelSelectScene

Import rules: ui/ may import engine/, pygame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from engine.level_generator import GeneratorConfig, generate_level
from ui.scene import Scene
from ui import theme as T

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Field definitions — (label, attr_name, python_type, section_tag)
# section_tag groups fields visually: "base" | "hazard" | "platform" | "stair"
# ---------------------------------------------------------------------------

_DEFAULTS = GeneratorConfig()

FIELDS: list[tuple[str, str, type, str]] = [
    # ── Base ─────────────────────────────────────────────────────────────
    ("Longueur (blocs)",         "length",               int,   "base"),
    ("Hauteur monde (blocs)",    "height",               int,   "base"),
    ("Graine (vide = aléat.)",   "seed",                 str,   "base"),
    # ── Dangers de sol ───────────────────────────────────────────────────
    ("Densité piques",           "spike_density",        float, "hazard"),
    ("Proba. gap",               "gap_probability",      float, "hazard"),
    ("Largeur max gap",          "max_gap_width",        int,   "hazard"),
    # ── Plateformes ──────────────────────────────────────────────────────
    ("Proba. plateforme",        "platform_probability", float, "platform"),
    ("Largeur min plateforme",   "platform_min_width",   int,   "platform"),
    ("Largeur max plateforme",   "platform_max_width",   int,   "platform"),
    ("Hauteur min plateforme",   "platform_min_height",  int,   "platform"),
    ("Hauteur max plateforme",   "platform_max_height",  int,   "platform"),
    ("Piques sous plateforme",   "spike_under_platform", bool,  "platform"),
    # ── Escaliers ────────────────────────────────────────────────────────
    ("Proba. escalier",          "stair_probability",    float, "stair"),
    ("Nb. marchés max",          "stair_max_steps",      int,   "stair"),
    ("Hauteur par marche",       "stair_step_height",    int,   "stair"),
    ("Largeur par marche",       "stair_step_width",     int,   "stair"),    # ── Blocs suspendus ──────────────────────────────────────────────
    ("Proba. blocs suspendus",   "stepping_stone_prob",      float, "stepping"),
    ("Nb. min pierres",          "stepping_stone_min_count", int,   "stepping"),
    ("Nb. max pierres",          "stepping_stone_max_count", int,   "stepping"),
    # ── Dangers joueur ───────────────────────────────────────────────
    ("Densité piques sol (y=1)", "floor_spike_density",  float, "hazard"),
    # ── Escaliers à trous ────────────────────────────────────────────
    ("Proba. esc. à trous",      "gapped_stair_prob",       float, "gstair"),
    ("Nb. marches max (trous)",  "gapped_stair_max_steps",  int,   "gstair"),
    ("Largeur marche (trous)",   "gapped_stair_step_width", int,   "gstair"),
    # ── Escaliers à piques ───────────────────────────────────────────
    ("Proba. esc. à piques",     "spiked_stair_prob",       float, "spstair"),
    ("Nb. marches max (piques)", "spiked_stair_max_steps",  int,   "spstair"),
    ("Largeur marche (piques)",  "spiked_stair_step_width", int,   "spstair"),]

_SECTION_LABELS: dict[str, str] = {
    "base":     "GÉNÉRAL",
    "hazard":   "DANGERS SOL",
    "platform": "PLATEFORMES",
    "stair":    "ESCALIERS",
    "stepping": "BLOCS SUSPENDUS",
    "gstair":   "ESCALIERS À TROUS",
    "spstair":  "ESCALIERS À PIQUES",
}

_SECTION_ACCENT: dict[str, tuple[int, int, int]] = {
    "base":     T.CYAN,
    "hazard":   T.RED,
    "platform": T.PURPLE,
    "stair":    T.GOLD,
    "stepping": T.CYAN,
    "gstair":   T.GOLD,
    "spstair":  T.RED,
}

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

_LABEL_X = 60
_INPUT_X = 390
_INPUT_W = 170
_INPUT_H = 28
_ROW_H = 36
_SECTION_GAP = 14         # extra vertical gap before a section header
_PANEL_MARGIN_X = 44
_PANEL_TOP = 105
_BUTTON_W = 220
_BUTTON_H = 44
_BUTTON_GAP = 14
_FOOTER_H = T.HINT_BAR_H

_DIGITS = set("0123456789")

# How many rows fit in one "column" before we split to a second column
_ROWS_PER_COL = 14


class GenConfigScene(Scene):
    """Configuration screen for parametric level generation."""

    def __init__(self, return_scene: Scene | None = None) -> None:
        super().__init__()
        self._return_scene = return_scene

        # String buffer for each editable field
        self.values: dict[str, str] = {}
        for _, attr, typ, _ in FIELDS:
            if attr == "seed":
                self.values[attr] = ""
            elif typ == bool:
                default = getattr(_DEFAULTS, attr)
                self.values[attr] = "oui" if default else "non"
            else:
                self.values[attr] = str(getattr(_DEFAULTS, attr))

        self.active_field: str | None = None
        self.error_msg: str = ""

        # Populated lazily on first draw (needs pygame.init)
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._hint_font: pygame.font.Font | None = None
        self._field_rects: dict[str, pygame.Rect] = {}
        self._play_btn_rect: pygame.Rect | None = None
        self._train_btn_rect: pygame.Rect | None = None

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
                    self.next_scene = self._return_scene
                    return True

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._try_generate_and_play()
                    return True

                if event.key == pygame.K_t:
                    if self.active_field is None:
                        self._try_generate_and_train()
                        return True

                if event.key == pygame.K_TAB:
                    self._cycle_field(reverse=bool(
                        pygame.key.get_mods() & pygame.KMOD_SHIFT
                    ))

                if self.active_field is not None:
                    self._handle_typing(event)

        return True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        T.fill_bg(surface)

        # Lazy font init
        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)
        if self._small_font is None:
            self._small_font = pygame.font.Font(None, T.FONT_SMALL)
        if self._hint_font is None:
            self._hint_font = pygame.font.Font(None, T.FONT_HINT)

        sw = surface.get_width()
        sh = surface.get_height()

        T.draw_header(surface, "NIVEAU ALÉATOIRE", "Configurer la génération procédurale",
                      accent=T.GOLD)

        # ── Two-column form ───────────────────────────────────────────
        col_w = (sw - 2 * _PANEL_MARGIN_X) // 2 - 8
        self._field_rects.clear()

        # Group fields by section, preserving insertion order
        sections: dict[str, list[tuple[str, str, type]]] = {}
        for label, attr, typ, sec in FIELDS:
            sections.setdefault(sec, []).append((label, attr, typ))

        # Assign each section to column 0 (left) or 1 (right)
        col_assignment: list[tuple[int, str]] = []
        left_rows = 0
        for sec, items in sections.items():
            rows_needed = len(items) + 1  # +1 for the section header
            if left_rows < _ROWS_PER_COL:
                col_assignment.append((0, sec))
                left_rows += rows_needed
            else:
                col_assignment.append((1, sec))

        # Draw each column
        col_y: list[int] = [_PANEL_TOP, _PANEL_TOP]

        for col_idx, sec in col_assignment:
            items = sections[sec]
            x_off = _PANEL_MARGIN_X + col_idx * (col_w + 16)
            y = col_y[col_idx]
            accent = _SECTION_ACCENT[sec]

            # Section header
            sec_label = _SECTION_LABELS[sec]
            sec_surf = self._hint_font.render(sec_label, True, accent)
            surface.blit(sec_surf, (x_off, y))
            pygame.draw.line(
                surface, (*accent, 120),
                (x_off, y + sec_surf.get_height() + 2),
                (x_off + col_w - 10, y + sec_surf.get_height() + 2),
                1,
            )
            y += sec_surf.get_height() + 8

            for label, attr, typ in items:
                # Label
                lbl_surf = self._small_font.render(label, True, T.TEXT_SEC)
                surface.blit(lbl_surf, (x_off, y + 5))

                # Input box
                in_x = x_off + col_w - _INPUT_W
                rect = pygame.Rect(in_x, y, _INPUT_W, _INPUT_H)
                self._field_rects[attr] = rect

                is_active = attr == self.active_field
                bg = T.BG_INPUT_ACT if is_active else T.BG_INPUT
                border = T.BORDER_ACC if is_active else T.BORDER_HI

                pygame.draw.rect(surface, bg, rect, border_radius=T.RADIUS_SM)
                pygame.draw.rect(surface, border, rect,
                                 width=2 if is_active else 1,
                                 border_radius=T.RADIUS_SM)

                val_surf = self._small_font.render(self.values[attr], True, T.TEXT)
                surface.blit(val_surf, (rect.x + 8, rect.y + 5))

                y += _ROW_H

            col_y[col_idx] = y + _SECTION_GAP

        # ── Error message ─────────────────────────────────────────────
        if self.error_msg:
            err_surf = self._small_font.render(self.error_msg, True, T.RED)
            surface.blit(
                err_surf,
                (sw // 2 - err_surf.get_width() // 2,
                 sh - _FOOTER_H - _BUTTON_H - _BUTTON_GAP - err_surf.get_height() - 6),
            )

        # ── Action buttons ────────────────────────────────────────────
        total_btn_w = _BUTTON_W * 2 + _BUTTON_GAP
        btn_start_x = sw // 2 - total_btn_w // 2
        btn_y = sh - _FOOTER_H - _BUTTON_H - 4

        mouse_pos = pygame.mouse.get_pos()

        play_rect = pygame.Rect(btn_start_x, btn_y, _BUTTON_W, _BUTTON_H)
        self._play_btn_rect = play_rect
        T.draw_btn(surface, play_rect, "▶  Jouer",
                   hover=play_rect.collidepoint(mouse_pos))

        train_rect = pygame.Rect(btn_start_x + _BUTTON_W + _BUTTON_GAP,
                                 btn_y, _BUTTON_W, _BUTTON_H)
        self._train_btn_rect = train_rect
        T.draw_btn(surface, train_rect, "⚡  Entraîner IA",
                   hover=train_rect.collidepoint(mouse_pos),
                   color=T.PURPLE)

        T.draw_footer(
            surface,
            "[Tab] Champ suivant   [Entrée] Jouer   [T] Entraîner IA   [ESC] Retour",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self._play_btn_rect and self._play_btn_rect.collidepoint(pos):
            self._try_generate_and_play()
            return
        if self._train_btn_rect and self._train_btn_rect.collidepoint(pos):
            self._try_generate_and_train()
            return

        self.active_field = None
        for attr, rect in self._field_rects.items():
            if rect.collidepoint(pos):
                self.active_field = attr
                break

    def _cycle_field(self, reverse: bool = False) -> None:
        """Move focus to the next (or previous) field."""
        attrs = [attr for _, attr, _, _ in FIELDS]
        if self.active_field is None:
            self.active_field = attrs[-1 if reverse else 0]
            return
        try:
            idx = attrs.index(self.active_field)
        except ValueError:
            self.active_field = attrs[0]
            return
        delta = -1 if reverse else 1
        self.active_field = attrs[(idx + delta) % len(attrs)]

    def _handle_typing(self, event: pygame.event.Event) -> None:
        attr = self.active_field
        if attr is None:
            return

        # Find type for this field
        field_type = str
        for _, a, t, _ in FIELDS:
            if a == attr:
                field_type = t
                break

        if event.key == pygame.K_BACKSPACE:
            self.values[attr] = self.values[attr][:-1]
            return

        if field_type == bool:
            # Toggle with any key press
            current = self.values[attr].strip().lower()
            self.values[attr] = "non" if current == "oui" else "oui"
            return

        ch = event.unicode
        if field_type == int and ch in _DIGITS:
            self.values[attr] += ch
        elif field_type == float and (ch in _DIGITS or (ch == "." and "." not in self.values[attr])):
            self.values[attr] += ch
        elif field_type == str:    # seed field — allow digits only
            if ch in _DIGITS:
                self.values[attr] += ch

    def _build_config(self) -> GeneratorConfig | None:
        """Parse fields into a GeneratorConfig, setting self.error_msg on failure."""
        self.error_msg = ""
        kwargs: dict = {}

        for _, attr, typ, _ in FIELDS:
            raw = self.values[attr].strip()

            if attr == "seed":
                kwargs["seed"] = int(raw) if raw else None
                continue

            if typ == bool:
                kwargs[attr] = raw.lower() == "oui"
                continue

            if not raw:
                self.error_msg = f"Le champ « {attr} » ne peut pas être vide."
                return None
            try:
                kwargs[attr] = typ(raw)
            except ValueError:
                self.error_msg = f"Valeur invalide pour « {attr} » : {raw}"
                return None

        try:
            return GeneratorConfig(**kwargs)
        except ValueError as exc:
            self.error_msg = str(exc)
            return None

    def _try_generate_and_play(self) -> None:
        config = self._build_config()
        if config is None:
            return

        world = generate_level(config)

        from ui.play_scene import PlayScene  # local import to avoid cycle

        self.next_scene = PlayScene(
            world=world,
            return_scene=self,
            level_name="Niveau aléatoire",
        )

    def _try_generate_and_train(self) -> None:
        config = self._build_config()
        if config is None:
            return

        world = generate_level(config)

        from ui.train_config_scene import TrainConfigScene  # local import

        self.next_scene = TrainConfigScene(
            world=world,
            level_name="Niveau aléatoire",
            return_scene=self,
            gen_config=config,
        )
