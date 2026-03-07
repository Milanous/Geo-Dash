"""
ui/hud.py — StatsHUD widget for AI training stats overlay.

Displays generation progress, fitness stats, alive count,
and a running line chart of best fitness history.

Import rules: ui/ may import pygame, engine/, but NOT ai/simulation.
[Source: Story 5.5]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class StatsHUD:
    """Live stats overlay for AI training scene."""

    def __init__(self) -> None:
        self.history: list[float] = []
        self.debug_agents: bool = False
        self._font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def update(self, stats: dict) -> None:
        """Append best_fitness to history when a generation is complete."""
        if stats.get("gen_complete"):
            self.history.append(stats["best_fitness"])

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, stats: dict) -> None:
        """Draw the stats overlay on the given surface."""
        import pygame as pg

        if self._font is None:
            self._font = pg.font.Font(None, 24)

        sw, _sh = surface.get_size()

        # --- Line chart (top-right, drawn first so text doesn't overlap) ---
        if len(self.history) >= 2:
            self._draw_chart(surface, sw)

        # --- Hint (bottom of HUD area) ---
        hint_font = pg.font.Font(None, 20)
        hint = hint_font.render("V: toggle agents", True, (100, 100, 120))
        surface.blit(hint, (sw - 140, _sh - 60))

    def _draw_chart(self, surface: pygame.Surface, sw: int) -> None:
        """Draw a mini line chart of best fitness history."""
        import pygame as pg

        chart_w, chart_h = 160, 100
        margin = 20
        cx = sw - chart_w - margin
        cy = margin

        # Background panel with better styling
        panel = pg.Rect(cx - 6, cy - 6, chart_w + 12, chart_h + 30)
        pg.draw.rect(surface, (18, 18, 32), panel, border_radius=8)
        pg.draw.rect(surface, (50, 50, 80), panel, 1, border_radius=8)

        # Chart title
        title_font = pg.font.Font(None, 20)
        title = title_font.render("Fitness History", True, (160, 170, 200))
        surface.blit(title, (cx, cy - 2))

        chart_top = cy + 18

        # Scale data
        mn = min(self.history)
        mx = max(self.history)
        rng = mx - mn if mx != mn else 1.0

        points: list[tuple[int, int]] = []
        n = len(self.history)
        for i, val in enumerate(self.history):
            px = cx + int(i / (n - 1) * (chart_w - 1))
            py = chart_top + chart_h - 1 - int((val - mn) / rng * (chart_h - 1))
            points.append((px, py))

        # Grid lines (subtle)
        for frac in (0.25, 0.5, 0.75):
            gy = chart_top + int(chart_h * (1.0 - frac))
            pg.draw.line(surface, (35, 35, 50), (cx, gy), (cx + chart_w, gy), 1)

        pg.draw.lines(surface, (0, 201, 255), False, points, 2)
