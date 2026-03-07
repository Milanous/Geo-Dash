"""
ui/theme.py — Centralized visual theme for Geo-Dash UI.

Tech-minimal aesthetic: pure black backgrounds, bright cyan accents,
visible scan-lines, glowing borders, high-contrast panels.

Import rules: no pygame at module level (lazy imports inside helpers).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

# ═════════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═════════════════════════════════════════════════════════════════════════

# ── Backgrounds ──────────────────────────────────────────────────────────
BG           = (2, 2, 6)           # Near-pure black
BG_PANEL     = (8, 10, 20)         # Dark navy panel
BG_INPUT     = (6, 8, 18)          # Dark input field
BG_INPUT_ACT = (10, 15, 35)        # Active input — subtle blue glow
BG_ENTRY     = (10, 12, 24)        # List entry card
BG_SELECTED  = (5, 30, 70)         # Selected — deep electric blue

# ── Borders ──────────────────────────────────────────────────────────────
BORDER       = (20, 30, 55)        # Panel border — visible blue tint
BORDER_HI    = (35, 55, 100)       # Bright panel border
BORDER_ACC   = (0, 201, 255)       # Accent border (cyan)

# ── Text ─────────────────────────────────────────────────────────────────
TEXT         = (210, 220, 240)      # Primary text (cool white)
TEXT_SEC     = (90, 110, 150)       # Secondary / labels
TEXT_DIM     = (45, 55, 80)         # Hints, disabled — very dim
TEXT_TITLE   = (255, 255, 255)      # Titles (pure white)

# ── Accents ──────────────────────────────────────────────────────────────
CYAN         = (0, 201, 255)        # Primary accent
CYAN_DIM     = (0, 80, 120)         # Muted cyan for subtle accents
GREEN        = (0, 220, 100)        # Success / confirm
GREEN_HOT    = (0, 255, 140)        # Success hover
RED          = (255, 50, 50)        # Error / danger
GOLD         = (255, 210, 0)        # Star / special reward
PURPLE       = (140, 70, 255)       # Replay theme — brighter purple

# ── Interactive ──────────────────────────────────────────────────────────
BTN_PRI      = (0, 140, 80)         # Button primary
BTN_PRI_HOT  = (0, 190, 110)       # Button primary hover

# ═════════════════════════════════════════════════════════════════════════
# FONT SIZES
# ═════════════════════════════════════════════════════════════════════════
FONT_TITLE   = 44
FONT_BODY    = 26
FONT_SMALL   = 21
FONT_HINT    = 19

# ═════════════════════════════════════════════════════════════════════════
# LAYOUT
# ═════════════════════════════════════════════════════════════════════════
TITLE_Y      = 26
LINE_H       = 42
HINT_BAR_H   = 42
RADIUS_LG    = 10
RADIUS_SM    = 6

# ═════════════════════════════════════════════════════════════════════════
# DRAWING HELPERS
# ═════════════════════════════════════════════════════════════════════════

# Cache for background scanline overlay (built once per resolution)
_scanline_cache: dict[tuple[int, int], pygame.Surface] = {}


def fill_bg(surface: pygame.Surface) -> None:
    """Fill surface with pure black background + visible scan-lines + vignette."""
    import pygame as pg

    surface.fill(BG)
    sw, sh = surface.get_size()
    key = (sw, sh)

    # Build scanline overlay once — cached per resolution
    if key not in _scanline_cache:
        overlay = pg.Surface((sw, sh), pg.SRCALPHA)
        # Horizontal scan-lines: every 3px, alpha 22 (visible but not harsh)
        for y in range(0, sh, 3):
            pg.draw.line(overlay, (0, 0, 0, 22), (0, y), (sw, y))
        # Corner vignette (radial darkening in corners)
        vig = pg.Surface((sw, sh), pg.SRCALPHA)
        # Top gradient (fade from dark to transparent)
        for y in range(60):
            a = int(40 * (1.0 - y / 60))
            pg.draw.line(vig, (0, 0, 0, a), (0, y), (sw, y))
        # Bottom gradient
        for y in range(60):
            a = int(40 * (1.0 - y / 60))
            pg.draw.line(vig, (0, 0, 0, a), (0, sh - 1 - y), (sw, sh - 1 - y))
        overlay.blit(vig, (0, 0))
        _scanline_cache[key] = overlay

    surface.blit(_scanline_cache[key], (0, 0))


def draw_header(
    surface: pygame.Surface,
    title: str,
    subtitle: str = "",
    accent: tuple[int, int, int] = CYAN,
) -> int:
    """Draw centred title with glow accent line + optional subtitle.

    Returns the Y coordinate just below the header for content layout.
    """
    import pygame as pg

    sw = surface.get_width()

    # Title
    tfont = pg.font.Font(None, FONT_TITLE)
    ts = tfont.render(title, True, TEXT_TITLE)
    tx = sw // 2 - ts.get_width() // 2

    # Title glow (blurred duplicate behind)
    glow_surf = pg.Surface((ts.get_width() + 40, ts.get_height() + 20), pg.SRCALPHA)
    glow_text = tfont.render(title, True, (*accent, 50) if len(accent) == 3 else accent)
    glow_surf.blit(glow_text, (20, 10))
    surface.blit(glow_surf, (tx - 20, TITLE_Y - 10))

    # Actual title
    surface.blit(ts, (tx, TITLE_Y))

    # Accent line — doubled for glow effect
    lw = max(100, ts.get_width() * 2 // 3)
    ly = TITLE_Y + ts.get_height() + 8
    # Glow line (wider, lower alpha)
    glow_line = pg.Surface((lw + 20, 6), pg.SRCALPHA)
    pg.draw.line(glow_line, (*accent[:3], 60), (10, 3), (lw + 10, 3), 4)
    surface.blit(glow_line, (sw // 2 - lw // 2 - 10, ly - 2))
    # Sharp line on top
    pg.draw.line(
        surface, accent,
        (sw // 2 - lw // 2, ly), (sw // 2 + lw // 2, ly), 2,
    )

    y_below = ly + 12
    if subtitle:
        sf = pg.font.Font(None, FONT_SMALL)
        ss = sf.render(subtitle, True, TEXT_SEC)
        surface.blit(ss, (sw // 2 - ss.get_width() // 2, y_below))
        y_below += ss.get_height() + 10

    return y_below + 8


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    border_color: tuple[int, int, int] = BORDER,
) -> None:
    """Draw a rounded-rect panel with subtle inner glow on top edge."""
    import pygame as pg

    pg.draw.rect(surface, BG_PANEL, rect, border_radius=RADIUS_LG)
    pg.draw.rect(surface, border_color, rect, width=1, border_radius=RADIUS_LG)

    # Top-edge highlight (1px bright line inside the panel)
    highlight_rect = pg.Rect(rect.x + 8, rect.y + 1, rect.width - 16, 1)
    hl_surf = pg.Surface((highlight_rect.width, 1), pg.SRCALPHA)
    hl_surf.fill((*BORDER_HI, 80))
    surface.blit(hl_surf, highlight_rect.topleft)


def draw_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    selected: bool = False,
    accent: tuple[int, int, int] = CYAN,
) -> None:
    """Draw a list-entry card, optionally highlighted with glow."""
    import pygame as pg

    if selected:
        # Glow behind the card
        glow_rect = pg.Rect(rect.x - 2, rect.y - 1, rect.width + 4, rect.height + 2)
        glow_surf = pg.Surface((glow_rect.width, glow_rect.height), pg.SRCALPHA)
        pg.draw.rect(glow_surf, (*accent[:3], 25), glow_surf.get_rect(), border_radius=RADIUS_SM + 2)
        surface.blit(glow_surf, glow_rect.topleft)

        pg.draw.rect(surface, BG_SELECTED, rect, border_radius=RADIUS_SM)
        # Left accent bar (brighter, thicker)
        pg.draw.rect(
            surface, accent,
            pg.Rect(rect.x, rect.y + 2, 3, rect.height - 4),
            border_radius=2,
        )
        # Right-side subtle accent
        pg.draw.rect(
            surface, (*accent[:3],),
            pg.Rect(rect.right - 1, rect.y + 6, 1, rect.height - 12),
        )
    else:
        pg.draw.rect(surface, BG_ENTRY, rect, border_radius=RADIUS_SM)


def draw_footer(
    surface: pygame.Surface,
    hint_text: str,
) -> None:
    """Draw a fixed footer hint bar with top accent line."""
    import pygame as pg

    sw, sh = surface.get_size()
    fy = sh - HINT_BAR_H
    pg.draw.rect(surface, BG_PANEL, (0, fy, sw, HINT_BAR_H))
    # Cyan accent line at top of footer
    pg.draw.line(surface, CYAN_DIM, (0, fy), (sw, fy), 1)

    hf = pg.font.Font(None, FONT_HINT)
    hs = hf.render(hint_text, True, TEXT_DIM)
    surface.blit(
        hs,
        (sw // 2 - hs.get_width() // 2,
         fy + (HINT_BAR_H - hs.get_height()) // 2),
    )


def draw_btn(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    hover: bool = False,
    color: tuple[int, int, int] = BTN_PRI,
    hot_color: tuple[int, int, int] = BTN_PRI_HOT,
) -> None:
    """Draw a rounded button with text and border glow on hover."""
    import pygame as pg

    c = hot_color if hover else color
    pg.draw.rect(surface, c, rect, border_radius=8)

    # Border — cyan when hovered for extra pop
    if hover:
        pg.draw.rect(surface, CYAN, rect, width=2, border_radius=8)
    else:
        pg.draw.rect(surface, BORDER_HI, rect, width=1, border_radius=8)

    font = pg.font.Font(None, FONT_BODY)
    ts = font.render(label, True, TEXT_TITLE)
    surface.blit(ts, (rect.centerx - ts.get_width() // 2,
                       rect.centery - ts.get_height() // 2))
