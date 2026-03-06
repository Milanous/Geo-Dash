"""
ui/play_scene.py — Play scene: human player on a level.

Loads a flat-floor fallback world (used by headless tests and manual play
until the level editor is available — Epic 3).

Import rules: ui/ may import engine/, renderer/, pygame.
"""

from __future__ import annotations

import pygame

from engine.camera import Camera
from engine.player import Player
from engine.world import TileType, World
from renderer.game_renderer import GameRenderer
from renderer.vfx import VFXSystem
from ui.scene import Scene

# Starting position (in block coordinates)
_START_X: float = 5.0
_START_Y: float = 5.0

# Fallback hardcoded level dimensions (used when no .gmd is supplied)
_WORLD_WIDTH: int = 200
_WORLD_HEIGHT: int = 20


def _build_fallback_world() -> World:
    """Create a flat-floor level: SOLID tiles across the entire row 0."""
    world = World(_WORLD_WIDTH, _WORLD_HEIGHT)
    for col in range(_WORLD_WIDTH):
        world.set_tile(col, 0, TileType.SOLID)
    return world


class PlayScene(Scene):
    """
    Play scene for the human-controlled cube.

    Physics runs at 240 Hz (via fixed-timestep accumulator in main.py).
    Rendering is triggered once per display frame (60 FPS) by main.py.

    Controls:
      SPACE  → jump (only from ground)
      ESC    → quit (or return to editor when return_scene is set)
    """

    def __init__(
        self,
        world: World | None = None,
        return_scene: Scene | None = None,
        level_name: str = "",
    ) -> None:
        super().__init__()
        self._world: World = world if world is not None else _build_fallback_world()
        self._player: Player = Player(start_x=_START_X, start_y=_START_Y)
        self._camera: Camera = Camera()
        self._renderer: GameRenderer = GameRenderer()
        self._vfx: VFXSystem = VFXSystem()
        self._return_scene: Scene | None = return_scene
        self._level_name: str = level_name
        self._death_timer: float | None = None

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        """
        Process pygame events.

        Returns:
            False if ESC or QUIT was received (request exit / no return_scene);
            True otherwise. When return_scene is set, ESC switches scene instead.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False
                if event.key == pygame.K_SPACE:
                    self._player.jump()
        return True

    def update(self, dt: float) -> None:
        """
        Advance physics by one timestep.

        Death takes priority over victory.
        On death (no return_scene): 2-second pause, then restart.
        On death (with return_scene): immediate return to editor.
        On finish: switch to VictoryScene.
        """
        # Death timer countdown (human play, no return_scene)
        if self._death_timer is not None:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self._player = Player(start_x=_START_X, start_y=_START_Y)
                self._vfx.reset()
                self._death_timer = None
            return

        # Death check — priority over victory
        if not self._player.alive:
            if self._return_scene is not None:
                self.next_scene = self._return_scene
                return
            self._death_timer = 2.0
            return

        if self._player.state.finished:
            from ui.victory_scene import VictoryScene  # local import to avoid cycle

            self.next_scene = VictoryScene(
                level_name=self._level_name,
                world=self._world,
                return_scene=self._return_scene,
            )
            return

        self._player.update(dt, self._world)
        self._camera.follow(self._player.state.x)
        self._vfx.update(self._player.state, dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the current frame onto *surface*."""
        player_to_draw = None if self._death_timer is not None else self._player
        self._renderer.draw(surface, self._world, player_to_draw, self._camera)
        self._vfx.draw(surface, self._camera.x_offset)
