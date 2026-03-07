"""
ui/play_scene.py — Play scene: human player on a level.

Loads a flat-floor fallback world (used by headless tests and manual play
until the level editor is available — Epic 3).

Import rules: ui/ may import engine/, renderer/, pygame.
"""

from __future__ import annotations

import pygame

from engine.camera import Camera
from engine.physics import SPAWN_X, SPAWN_Y
from engine.player import Player
from engine.world import TileType, World
from renderer.game_renderer import GameRenderer
from renderer.vfx import VFXSystem
from ui.scene import Scene
from ui import theme as T

# Starting position (in block coordinates)
_START_X: float = SPAWN_X
_START_Y: float = SPAWN_Y

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
      P      → toggle pause
      ESC    → quit (or return to editor when return_scene is set)
    """

    # Pause button layout (top-right corner)
    _PAUSE_BTN_W: int = 90
    _PAUSE_BTN_H: int = 32
    _PAUSE_BTN_MARGIN: int = 10

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
        self._paused: bool = False

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
                    if self._paused:
                        self._paused = False
                        continue
                    if self._return_scene is not None:
                        self.next_scene = self._return_scene
                        return True
                    return False
                if event.key == pygame.K_p:
                    self._paused = not self._paused
                    continue
                if event.key == pygame.K_SPACE and not self._paused:
                    self._player.jump()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._pause_btn_rect_hit(event.pos):
                    self._paused = not self._paused
        return True

    def _pause_btn_rect(self, surface: pygame.Surface) -> pygame.Rect:
        """Return the pause button rectangle for the given surface."""
        sw = surface.get_width()
        return pygame.Rect(
            sw - self._PAUSE_BTN_W - self._PAUSE_BTN_MARGIN,
            self._PAUSE_BTN_MARGIN,
            self._PAUSE_BTN_W,
            self._PAUSE_BTN_H,
        )

    def _pause_btn_rect_hit(self, pos: tuple[int, int]) -> bool:
        """Check if *pos* is inside the pause button (uses last known screen size)."""
        try:
            surface = pygame.display.get_surface()
            if surface is None:
                return False
            return self._pause_btn_rect(surface).collidepoint(pos)
        except pygame.error:
            return False

    def update(self, dt: float) -> None:
        """
        Advance physics by one timestep.

        Death takes priority over victory.
        On death: confetti effect, 2-second pause, then restart.
        On finish: switch to VictoryScene.
        """
        if self._paused:
            return

        # Auto-jump (bunny-hop): jump if SPACE is held and player just landed
        # Guard with try/except for headless tests where video isn't initialized
        try:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and self._player.alive:
                self._player.jump()
        except pygame.error:
            pass  # Video system not initialized (headless tests)

        # Update VFX particles even during death (for confetti animation)
        if self._death_timer is not None:
            # Keep updating particles for confetti effect
            self._vfx.advance_particles(dt)
            self._death_timer -= dt
            if self._death_timer <= 0:
                # Respawn player AND reset camera to starting position
                self._player = Player(start_x=_START_X, start_y=_START_Y)
                self._camera = Camera()  # Reset camera to start
                self._vfx.reset()
                self._death_timer = None
            return

        # Death check — priority over victory
        if not self._player.alive:
            # Spawn confetti at player's death position
            self._vfx.spawn_death_confetti(self._player.state.x, self._player.state.y)
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
        self._draw_pause_button(surface)
        if self._paused:
            self._draw_pause_overlay(surface)

    # ------------------------------------------------------------------
    # Pause UI
    # ------------------------------------------------------------------

    def _draw_pause_button(self, surface: pygame.Surface) -> None:
        """Draw a small pause/resume button in the top-right corner."""
        rect = self._pause_btn_rect(surface)
        label = "▶ Play" if self._paused else "❚❚ Pause"
        bg = T.BTN_PRI if not self._paused else T.GREEN

        pygame.draw.rect(surface, bg, rect, border_radius=T.RADIUS_SM)
        pygame.draw.rect(surface, T.BORDER_HI, rect, width=1, border_radius=T.RADIUS_SM)

        font = pygame.font.Font(None, T.FONT_HINT)
        txt = font.render(label, True, T.TEXT_TITLE)
        surface.blit(txt, (
            rect.x + (rect.width - txt.get_width()) // 2,
            rect.y + (rect.height - txt.get_height()) // 2,
        ))

    def _draw_pause_overlay(self, surface: pygame.Surface) -> None:
        """Draw a semi-transparent overlay with PAUSED text."""
        sw, sh = surface.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        big_font = pygame.font.Font(None, 64)
        txt = big_font.render("PAUSE", True, T.CYAN)
        surface.blit(txt, (sw // 2 - txt.get_width() // 2, sh // 2 - txt.get_height() // 2 - 20))

        hint_font = pygame.font.Font(None, T.FONT_SMALL)
        hint = hint_font.render("[P] Reprendre  |  [ESC] Quitter", True, T.TEXT_SEC)
        surface.blit(hint, (sw // 2 - hint.get_width() // 2, sh // 2 + 30))
