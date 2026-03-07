"""
ui/ai_train_scene.py — AI training scene: generation loop with save & early stop.

Runs up to max_generations generations of neuroevolution.
Each generation: simulate → evaluate fitness → select → mutate → next.
Best brain saved after each generation. Early stop on level completion.

Import rules: ui/ may import ai/, engine/, renderer/, pygame.
[Source: Story 5.4]
"""

from __future__ import annotations

import json
import os
import random

from typing import TYPE_CHECKING

import numpy as np
import pygame

from ai.brain import Brain
from ai.evolution import generate_random_brain, mutate, select_top_n
from ai.simulation import PopulationSim
from ai.training_config import TrainingConfig
from engine.physics import PHYSICS_RATE
from engine.world import TileType, World
from ui.scene import Scene
from ui.hud import StatsHUD
from ui import theme as T

if TYPE_CHECKING:
    pass

# Steps per update() call — accelerates training without blocking render
_STEPS_PER_FRAME: int = 4

# Save directory (can be overridden for testing)
_DEFAULT_BRAINS_DIR: str = "data/brains"

# Scene-specific color overrides
_SUCCESS_COLOR = (80, 255, 80)
_PROGRESS_BG = (25, 25, 40)
_PROGRESS_FILL = (0, 170, 105)


def _build_fallback_world(width: int = 200, height: int = 20) -> World:
    """Create a flat-floor level as fallback."""
    world = World(width, height)
    for col in range(width):
        world.set_tile(col, 0, TileType.SOLID)
    return world


class AITrainScene(Scene):
    """Training scene: run generations of neuroevolution with visual feedback."""

    def __init__(
        self,
        config: TrainingConfig,
        world: World | None = None,
        level_name: str = "",
        return_scene: Scene | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.level: World = world if world is not None else _build_fallback_world()
        self.level_name = level_name
        self._return_scene = return_scene
        self.brains_dir = _DEFAULT_BRAINS_DIR

        # Generation state
        self.gen_num: int = 0
        self.finished: bool = False
        self.early_stopped: bool = False
        self.status_msg: str = ""

        # HUD from story 5.5
        self.hud = StatsHUD()

        # All-time best distance (across all generations)
        self._best_dist_all: float = 0.0

        # Distance to FINISH (for percentage display)
        self._finish_x: float = self.level.find_finish_x()

        # Max steps per generation
        self._max_steps_per_gen: int = int(config.max_seconds_per_gen * PHYSICS_RATE)
        self._step_count: int = 0

        # Generate initial population
        self.brains: list[Brain] = [
            generate_random_brain() for _ in range(config.population_size)
        ]

        # Start first generation simulation
        self._sim: PopulationSim = PopulationSim(
            self.brains,
            self.level,
            self.config,
        )
        self._step_count = 0

        # Lazy font init
        self._font: pygame.font.Font | None = None
        self._title_font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False
                if event.key == pygame.K_RETURN and self.finished:
                    from ui.replay_scene import ReplayScene
                    self.next_scene = ReplayScene(
                        world=self.level,
                        return_scene=self._return_scene,
                        brains_dir=self.brains_dir,
                        auto_gen=self.gen_num,
                    )
                    return True
        return True

    def update(self, dt: float) -> None:
        if self.finished:
            return

        for _ in range(_STEPS_PER_FRAME):
            if self._generation_done():
                self._end_generation()
                return
            self._sim.step(dt)
            self._step_count += 1

    def draw(self, surface: pygame.Surface) -> None:
        T.fill_bg(surface)
        sw, sh = surface.get_size()

        if self._font is None:
            self._font = pygame.font.Font(None, T.FONT_BODY)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, T.FONT_TITLE)

        # Draw HUD (chart in top-right)
        stats_dict = {
            "gen": self.gen_num + 1,
            "best_fitness": float(np.max(self._sim.fitness())) if self.brains else 0.0,
            "avg_fitness": float(np.mean(self._sim.fitness())) if self.brains else 0.0,
            "worst_fitness": float(np.min(self._sim.fitness())) if self.brains else 0.0,
            "gen_complete": False,
        }
        self.hud.draw(surface, stats_dict)

        # ── Header ─────────────────────────────────────────────────
        T.draw_header(surface, "AI Training")

        # ── Stats panel (left side) ─────────────────────────────
        best_fit = float(np.max(self._sim.fitness())) if self.brains else 0.0
        finish = max(1.0, self._finish_x)
        gen_dist_pct = best_fit / finish * 100
        self._best_dist_all = max(self._best_dist_all, best_fit)
        all_dist_pct = self._best_dist_all / finish * 100
        stats_items: list[tuple[str, str]] = [
            ("Génération", f"{self.gen_num + 1} / {self.config.max_generations}"),
            ("Population", str(self.config.population_size)),
            ("Dist max (gén)", f"{best_fit:.1f}  ({gen_dist_pct:.1f}%)"),
            ("Dist max (all)", f"{all_dist_pct:.1f}%"),
            ("Largeur niveau", str(int(self._finish_x))),
        ]

        panel_x, panel_y = 30, 86
        panel_w = 280
        panel_h = len(stats_items) * 28 + 66
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        T.draw_panel(surface, panel_rect)

        small_font = pygame.font.Font(None, 22)
        y = panel_y + 12
        for label, value in stats_items:
            lbl = small_font.render(label, True, T.TEXT_SEC)
            val = small_font.render(value, True, T.TEXT)
            surface.blit(lbl, (panel_x + 14, y))
            surface.blit(val, (panel_x + panel_w - val.get_width() - 14, y))
            y += 28

        # ── Step progress bar ───────────────────────────────────
        progress_label = small_font.render("Progression", True, T.TEXT_SEC)
        surface.blit(progress_label, (panel_x + 14, y + 4))

        bar_x = panel_x + 14
        bar_y = y + 24
        bar_w = panel_w - 28
        bar_h = 10
        pygame.draw.rect(surface, _PROGRESS_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        progress = min(1.0, self._step_count / max(1, self._max_steps_per_gen))
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            pygame.draw.rect(surface, _PROGRESS_FILL, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        pct_text = small_font.render(f"{int(progress * 100)}%", True, T.TEXT)
        surface.blit(pct_text, (bar_x + bar_w + 6, bar_y - 2))

        # ── Status message (center) ──────────────────────────────
        if self.status_msg:
            color = _SUCCESS_COLOR if self.early_stopped else T.TEXT
            msg = self._font.render(self.status_msg, True, color)
            surface.blit(msg, (sw // 2 - msg.get_width() // 2, sh - 120))

        # Watch-best hint shown when training is done
        if self.finished:
            watch_hint = self._font.render(
                "[Entrée] Voir le meilleur  [ESC] Quitter", True, _SUCCESS_COLOR
            )
            surface.blit(watch_hint, (sw // 2 - watch_hint.get_width() // 2, sh - 86))

        # ── Footer ────────────────────────────────────────────────
        T.draw_footer(surface, "[ESC] Quitter")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generation_done(self) -> bool:
        """Check if the current generation simulation is complete."""
        if np.any(self._sim.finished):
            return True
        if np.all(~self._sim.alive):
            return True
        if self._step_count >= self._max_steps_per_gen:
            return True
        return False

    def _end_generation(self) -> None:
        """Finish current generation: evaluate, save, evolve or stop."""
        self.gen_num += 1
        fitness = self._sim.fitness()

        # Save best brain
        best_idx = int(np.argmax(fitness))
        best_brain = self.brains[best_idx]
        best_fitness = float(fitness[best_idx])
        self._save_best_brain(best_brain, best_fitness)

        # Early stop check — an agent reached the finish
        if np.any(self._sim.finished):
            self.finished = True
            self.early_stopped = True
            self.status_msg = "Level Completed!"
            return

        # Max generations check
        if self.gen_num >= self.config.max_generations:
            self.finished = True
            self.status_msg = (
                f"Training complete — {self.config.max_generations} generations. "
                f"Best fitness: {best_fitness:.1f}"
            )
            return

        # Evolve next generation
        elites = select_top_n(self.brains, fitness, n=self.config.top_n)
        next_gen: list[Brain] = list(elites)
        while len(next_gen) < self.config.population_size:
            parent = random.choice(elites)
            next_gen.append(mutate(parent, self.config))

        self.brains = next_gen
        self._sim = PopulationSim(self.brains, self.level, self.config)
        self._step_count = 0

    def _save_best_brain(self, brain: Brain, fitness: float) -> None:
        """Save the best brain of this generation to disk."""
        os.makedirs(self.brains_dir, exist_ok=True)
        data = {
            "version": 1,
            "generation": self.gen_num,
            "fitness": fitness,
            "networks": brain.to_json()["networks"],
        }
        path = os.path.join(self.brains_dir, f"gen_{self.gen_num:03d}_best.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
