"""
ui/save_dialog.py — Text-input overlay for naming a level before save.

Import rules: may import pygame. Never import ai/.
[Source: architecture.md#Règles d'import]
"""

from __future__ import annotations

import re

import pygame


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
            self._font = pygame.font.Font(None, 28)

        # Semi-transparent backdrop
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # Dialog box
        box_w, box_h = 400, 120
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2
        pygame.draw.rect(surface, (40, 40, 40), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, (100, 100, 100), (box_x, box_y, box_w, box_h), 2)

        # Title
        title = self._font.render("Level name:", True, (220, 220, 220))
        surface.blit(title, (box_x + 16, box_y + 12))

        # Text input field
        field_x = box_x + 16
        field_y = box_y + 50
        field_w = box_w - 32
        field_h = 32
        pygame.draw.rect(surface, (25, 25, 25), (field_x, field_y, field_w, field_h))
        pygame.draw.rect(surface, (80, 80, 80), (field_x, field_y, field_w, field_h), 1)

        # Typed text
        txt_surf = self._font.render(self._text, True, (230, 230, 230))
        surface.blit(txt_surf, (field_x + 6, field_y + 4))

        # Blinking cursor
        if self._cursor_visible:
            cx = field_x + 6 + txt_surf.get_width() + 2
            pygame.draw.line(surface, (230, 230, 230), (cx, field_y + 4), (cx, field_y + field_h - 4))

        # Hint
        hint = self._font.render("Enter = save   ESC = cancel", True, (120, 120, 120))
        surface.blit(hint, (box_x + 16, box_y + box_h - 28))
