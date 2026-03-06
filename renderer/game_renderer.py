"""
renderer/game_renderer.py — Tile, player and HUD rendering.

Import rules: may import engine/, ai/brain.py, pygame. Never ai/simulation.py.
All coordinates received/computed here are in pixels.
"""

from __future__ import annotations

import pygame

from engine.camera import Camera
from engine.player import Player
from engine.world import TileType, World

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

_SOLID_COLOR = (160, 160, 160)
_SPIKE_COLOR = (255, 110, 40)
_FINISH_COLOR = (50, 220, 80)
_PLAYER_COLOR = (220, 50, 50)
_PLAYER_BORDER_COLOR = (0, 0, 0)

# Gradient sky colours (top → bottom)
_SKY_TOP    = (8,  8, 38)
_SKY_BOTTOM = (42, 42, 88)

# Player sprite dimensions (fraction of block size)
_INNER_RATIO: float = 0.55   # inner square is 55% of block size
_BORDER_OUTER: int = 2       # outer square border thickness (px)
_BORDER_INNER: int = 1       # inner square border thickness (px)


# ---------------------------------------------------------------------------
# Tint helper — pure function, no pygame, safe for headless tests
# ---------------------------------------------------------------------------

def _compute_tint(
    base_color: tuple[int, int, int],
    col: int,
    row: int,
) -> tuple[int, int, int]:
    """
    Return a deterministically tinted variant of *base_color*.

    The lightness offset is in the range ±10% of each channel's base value,
    seeded uniquely by (col, row) using a cheap integer hash.

    Args:
        base_color: RGB triple of the canonical tile colour.
        col:        Tile column index (world grid).
        row:        Tile row index (world grid).

    Returns:
        A new RGB triple with channels clamped to [0, 255].
    """
    # Knuth multiplicative hash — deterministic, no stdlib random needed
    seed = (col * 2_654_435_761 ^ row * 22_695_477) & 0xFFFF_FFFF
    # Map [0, 2³²) → [-0.10, +0.10]
    offset = (seed / 0xFFFF_FFFF - 0.5) * 0.20
    r = min(255, max(0, int(base_color[0] * (1.0 + offset))))
    g = min(255, max(0, int(base_color[1] * (1.0 + offset))))
    b = min(255, max(0, int(base_color[2] * (1.0 + offset))))
    return (r, g, b)


class GameRenderer:
    """
    Renderer: draws gradient sky, world tiles (with tint variation),
    the player and the background onto the given pygame.Surface.

    The tint cache (`_tint_cache`) stores per-tile tinted colours computed
    once on first encounter — never recalculated every frame.

    Call once per rendered frame after all physics steps have been processed.
    """

    def __init__(self) -> None:
        # Lazy tint cache: (col, row) → tinted RGB tuple
        self._tint_cache: dict[tuple[int, int], tuple[int, int, int]] = {}

    def draw(
        self,
        surface: pygame.Surface,
        world: World,
        player: Player,
        camera: Camera,
    ) -> None:
        """
        Render a full frame.

        Args:
            surface: Destination pygame surface (typically the display).
            world:   Current level grid (block coordinates).
            player:  Current player with PlayerState.
            camera:  Camera holding x_offset (pixels).
        """
        self._draw_sky(surface)
        self._draw_tiles(surface, world, camera)
        self._draw_player(surface, player, camera)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_sky(self, surface: pygame.Surface) -> None:
        """Fill the background with a vertical gradient (top to bottom)."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        for y in range(screen_h):
            t = y / max(screen_h - 1, 1)
            r = int(_SKY_TOP[0] + (_SKY_BOTTOM[0] - _SKY_TOP[0]) * t)
            g = int(_SKY_TOP[1] + (_SKY_BOTTOM[1] - _SKY_TOP[1]) * t)
            b = int(_SKY_TOP[2] + (_SKY_BOTTOM[2] - _SKY_TOP[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (screen_w, y))

    def _draw_tiles(
        self,
        surface: pygame.Surface,
        world: World,
        camera: Camera,
    ) -> None:
        bs = World.to_px(1.0)          # block size in pixels (BLOCK_SIZE_PX)
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        for row in range(world.height):
            for col in range(world.width):
                tile = world.tile_at(col, row)
                if tile == TileType.AIR:
                    continue

                sx = camera.world_to_screen_x(col)
                # Y-axis flip: row=0 is at the bottom of the screen
                # row n → screen_y = screen_h - (n+1)*bs
                sy = screen_h - (row + 1) * bs

                # Frustum cull — skip tiles fully off screen
                if sx + bs <= 0 or sx >= screen_w:
                    continue
                if sy + bs <= 0 or sy >= screen_h:
                    continue

                rect = pygame.Rect(sx, sy, bs, bs)

                if tile == TileType.SOLID:
                    key = (col, row)
                    if key not in self._tint_cache:
                        self._tint_cache[key] = _compute_tint(_SOLID_COLOR, col, row)
                    pygame.draw.rect(surface, self._tint_cache[key], rect)
                elif tile == TileType.SPIKE:
                    key = (col, row)
                    if key not in self._tint_cache:
                        self._tint_cache[key] = _compute_tint(_SPIKE_COLOR, col, row)
                    # Filled equilateral triangle occupying the full 1×1 tile area
                    pts = [
                        (sx,           sy + bs),   # bottom-left
                        (sx + bs,      sy + bs),   # bottom-right
                        (sx + bs // 2, sy),         # apex
                    ]
                    pygame.draw.polygon(surface, self._tint_cache[key], pts)
                elif tile == TileType.FINISH:
                    # Bright green vertical bar centred in the block
                    bar_w = 4
                    bar_rect = pygame.Rect(sx + (bs - bar_w) // 2, sy, bar_w, bs)
                    pygame.draw.rect(surface, _FINISH_COLOR, bar_rect)

    def _draw_player(
        self,
        surface: pygame.Surface,
        player: Player,
        camera: Camera,
    ) -> None:
        bs = World.to_px(1.0)
        screen_h = surface.get_height()

        # Player screen position — centre of the 1×1 block
        cx = camera.world_to_screen_x(player.state.x) + bs // 2
        cy = screen_h - int((player.state.y + 1) * bs) + bs // 2

        # --- Build the sprite on an offscreen surface (with alpha) ---
        sprite = pygame.Surface((bs, bs), pygame.SRCALPHA)

        # Outer square: red fill + black border
        outer_rect = pygame.Rect(0, 0, bs, bs)
        pygame.draw.rect(sprite, _PLAYER_COLOR, outer_rect)
        pygame.draw.rect(sprite, _PLAYER_BORDER_COLOR, outer_rect, _BORDER_OUTER)

        # Inner square: centered at ~55% of block size
        inner_size = int(bs * _INNER_RATIO)
        inner_offset = (bs - inner_size) // 2
        inner_rect = pygame.Rect(inner_offset, inner_offset, inner_size, inner_size)
        pygame.draw.rect(sprite, _PLAYER_COLOR, inner_rect)
        pygame.draw.rect(sprite, _PLAYER_BORDER_COLOR, inner_rect, _BORDER_INNER)

        # --- Apply clockwise rotation ---
        # pygame.transform.rotate is counter-clockwise, so negate the angle
        rotated = pygame.transform.rotate(sprite, -player.state.angle)

        # Blit centred on the player's block centre
        blit_rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, blit_rect)
