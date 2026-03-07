"""
main.py — Geo-Dash entry point.

Story 1.7: fixed-timestep game loop (240 Hz physics / 60 FPS rendering).
Accumulator pattern: while accumulator >= DT: physics_step(); accumulator -= DT

Story 6.3: starts with LevelSelectScene; scenes can request a transition by
setting their `next_scene` attribute to another Scene instance.
"""

import sys
import pygame

from engine.physics import DT
from ui.level_select_scene import LevelSelectScene


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Geo-Dash")
    clock = pygame.time.Clock()

    scene = LevelSelectScene()
    accumulator = 0.0

    running = True
    while running:
        # Cap frame_dt to avoid spiral-of-death on slow frames
        frame_dt = min(clock.tick(60) / 1000.0, 0.1)
        accumulator += frame_dt

        # Handle events (ESC / QUIT returns False → stop loop)
        running = scene.handle_events()

        # Scene transition requested?
        if scene.next_scene is not None:
            scene = scene.next_scene
            scene.next_scene = None  # clear stale next_scene on reused scenes

        # Fixed-timestep physics steps
        while accumulator >= DT:
            scene.update(DT)
            accumulator -= DT

        # Render once per display frame
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
