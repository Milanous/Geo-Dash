"""
ui/save_dialog.py — Text-input overlay for naming a level before save.

Import rules: may import pygame. Never import ai/.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

import re

import pygame

from ui import theme as T


# Characters accepted while typing (includes space — sanitise_name handles cleanup)
_ALLOWED_RE = re.compile(r"^[a-zA-Z0-9 _-]$")

_CURSOR_BLINK_PERIOD: float = 0.5  # seconds per toggle


class SaveDialog:
    """
    Modal text-input overlay for level name entry.

    Lifecycle:
      1. Instantiate (headless-safe — no pygame surface/font in __init__).
      2. For each event, call ``update(event)`` which returns:
         - ``str``   — user pressed Enter → the typed name
         - ``False`` — user pressed ESC → cancelled
         - ``None``  — still typing (no decision yet)
      3. Call ``draw(surface)`` each frame to render the overlay.

    The constructor does NOT touch ``pygame.font`` or ``pygame.Surface`` so
    that tests can instantiate ``SaveDialog`` without a display.
    """

    def __init__(self, initial_text: str = "") -> None:
        self._text: str = initial_text
        self._cursor_timer: float = 0.0
        self._cursor_visible: bool = True

        # Lazy-initialised pygame resources (set in draw)
        self._font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def update(self, event: pygame.event.Event) -> str | None | bool:
        """
        Process a single pygame event.

        Returns:
            str   — Enter pressed → the current text (may be empty).
            False — ESC pressed → dialog cancelled.
            None  — still typing, no decision yet.
        """
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            return self._text

        if event.key == pygame.K_ESCAPE:
            return False

        if event.key == pygame.K_BACKSPACE:
            self._text = self._text[:-1]
            return None

        # Accept only allowed characters
        ch = event.unicode
        if ch and _ALLOWED_RE.match(ch):
            self._text += ch

        return None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def tick(self, dt: float) -> None:
        """Advance cursor blink timer."""
        self._cursor_timer += dt
        if self._cursor_timer >= _CURSOR_BLINK_PERIOD:
            self._cursor_timer -= _CURSOR_BLINK_PERIOD
            self._cursor_visible = not self._cursor_visible

    def draw(self, surface: pygame.Surface) -> None:
        """Render the save dialog overlay onto *surface*."""
        sw, sh = surface.get_size()

        # Lazy font init
        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)

        # Semi-transparent backdrop
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        # Dialog box
        box_w, box_h = 440, 148
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(surface, T.BG_PANEL, box_rect, border_radius=T.RADIUS_LG)
        pygame.draw.rect(surface, T.BORDER_HI, box_rect, 1, border_radius=T.RADIUS_LG)

        # Title
        title = self._font.render("Nom du niveau :", True, T.TEXT)
        surface.blit(title, (box_x + 20, box_y + 18))

        # Accent line
        pygame.draw.line(
            surface, T.CYAN,
            (box_x + 20, box_y + 46),
            (box_x + box_w - 20, box_y + 46), 1,
        )

        # Text input field
        field_x = box_x + 20
        field_y = box_y + 60
        field_w = box_w - 40
        field_h = 34
        pygame.draw.rect(surface, T.BG_INPUT, (field_x, field_y, field_w, field_h), border_radius=T.RADIUS_SM)
        pygame.draw.rect(surface, T.BORDER_HI, (field_x, field_y, field_w, field_h), 1, border_radius=T.RADIUS_SM)

        # Typed text
        txt_surf = self._font.render(self._text, True, T.TEXT)
        surface.blit(txt_surf, (field_x + 10, field_y + 6))

        # Blinking cursor
        if self._cursor_visible:
            cx = field_x + 10 + txt_surf.get_width() + 2
            pygame.draw.line(surface, T.CYAN, (cx, field_y + 6), (cx, field_y + field_h - 6), 2)

        # Hint
        hint_font = pygame.font.Font(None, T.FONT_HINT)
        hint = hint_font.render("Enter = sauvegarder   ESC = annuler", True, T.TEXT_DIM)
        surface.blit(hint, (box_x + (box_w - hint.get_width()) // 2, box_y + box_h - 28))
