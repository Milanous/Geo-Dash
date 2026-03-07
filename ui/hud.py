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
            self._font = pg.font.Font(None, 26)

        sw, _sh = surface.get_size()

        # --- Text stats (top-left) ---
        x0, y = 20, 20
        lines = [
            f"Gen {stats.get('gen', 0)} / {stats.get('max_gen', '?')}",
            f"Best: {stats.get('best_fitness', 0):.1f}",
            f"Avg: {stats.get('avg_fitness', 0):.1f}",
            f"Worst: {stats.get('worst_fitness', 0):.1f}",
            f"ALIVE: {stats.get('alive', 0)}",
        ]
        for line in lines:
            txt = self._font.render(line, True, (220, 220, 220))
            surface.blit(txt, (x0, y))
            y += 24

        # --- Hint ---
        hint = self._font.render("V: toggle agents", True, (140, 140, 160))
        surface.blit(hint, (x0, y + 8))

        # --- Line chart (top-right) ---
        if len(self.history) >= 2:
            self._draw_chart(surface, sw)

    def _draw_chart(self, surface: pygame.Surface, sw: int) -> None:
        """Draw a mini line chart of best fitness history."""
        import pygame as pg

        chart_w, chart_h = 120, 80
        margin = 20
        cx = sw - chart_w - margin
        cy = margin

        # Background panel
        panel = pg.Rect(cx, cy, chart_w, chart_h)
        pg.draw.rect(surface, (30, 30, 40), panel)
        pg.draw.rect(surface, (80, 80, 100), panel, 1)

        # Scale data
        mn = min(self.history)
        mx = max(self.history)
        rng = mx - mn if mx != mn else 1.0

        points: list[tuple[int, int]] = []
        n = len(self.history)
        for i, val in enumerate(self.history):
            px = cx + int(i / (n - 1) * (chart_w - 1))
            py = cy + chart_h - 1 - int((val - mn) / rng * (chart_h - 1))
            points.append((px, py))

        pg.draw.lines(surface, (80, 255, 80), False, points, 2)
