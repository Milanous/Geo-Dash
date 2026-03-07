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
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pygame

from ai.brain import Brain
from ai.evolution import generate_random_brain, mutate, select_top_n
from ai.simulation import PopulationSim
from ai.training_config import TrainingConfig
from engine.physics import DT, PHYSICS_RATE
from engine.world import TileType, World
from ui.scene import Scene

if TYPE_CHECKING:
    pass

# Steps per update() call — accelerates training without blocking render
_STEPS_PER_FRAME: int = 4

# Save directory (can be overridden for testing)
_DEFAULT_BRAINS_DIR: str = "data/brains"

# Visual constants
_BG_COLOR = (15, 15, 25)
_TEXT_COLOR = (220, 220, 220)
_TITLE_COLOR = (255, 255, 255)
_HINT_COLOR = (140, 140, 160)
_SUCCESS_COLOR = (80, 255, 80)


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

        # Max steps per generation
        self._max_steps_per_gen: int = int(config.max_seconds_per_gen * PHYSICS_RATE)
        self._step_count: int = 0

        # Generate initial population
        self.brains: list[Brain] = [
            generate_random_brain() for _ in range(config.population_size)
        ]

        # Start first generation simulation
        self._sim: PopulationSim = PopulationSim(
            self.brains, self.level, self.config,
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
        surface.fill(_BG_COLOR)
        sw, sh = surface.get_size()

        if self._font is None:
            self._font = pygame.font.Font(None, 28)
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, 40)

        # Title
        title = self._title_font.render("AI Training", True, _TITLE_COLOR)
        surface.blit(title, (sw // 2 - title.get_width() // 2, 30))

        # Stats
        best_fit = float(np.max(self._sim.fitness())) if self.brains else 0.0
        alive_count = int(np.sum(self._sim.alive)) if self.brains else 0
        stats: dict[str, str] = {
            "Generation": f"{self.gen_num + 1} / {self.config.max_generations}",
            "Population": str(self.config.population_size),
            "Alive": str(alive_count),
            "Best Fitness": f"{best_fit:.1f}",
            "Level Width": str(self.level.width),
            "Step": f"{self._step_count} / {self._max_steps_per_gen}",
        }

        y = 90
        for label, value in stats.items():
            txt = self._font.render(f"{label}: {value}", True, _TEXT_COLOR)
            surface.blit(txt, (60, y))
            y += 32

        # Status message (early stop / finished)
        if self.status_msg:
            color = _SUCCESS_COLOR if self.early_stopped else _TEXT_COLOR
            msg = self._font.render(self.status_msg, True, color)
            surface.blit(msg, (sw // 2 - msg.get_width() // 2, sh - 100))

        # Hint
        hint = self._font.render("[ESC] Quitter", True, _HINT_COLOR)
        surface.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 40))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generation_done(self) -> bool:
        """Check if the current generation simulation is complete."""
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

        # Early stop check
        if np.any(fitness >= float(self.level.width)):
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
