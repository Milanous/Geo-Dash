"""
renderer/game_renderer.py — Tile, player and HUD rendering.

Import rules: may import engine/, ai/brain.py, pygame. Never ai/simulation.py.
All coordinates received/computed here are in pixels.
"""

from __future__ import annotations

import pygame

from engine.camera import Camera
from engine.player import Player
from engine.world import TileType, World, is_spike

# ---------------------------------------------------------------------------
# Palette (Geometry Dash Stereo Madness original colors)
# ---------------------------------------------------------------------------

# Blocks: Black interior with neon outline (default: cyan/blue)
_SOLID_FILL = (0, 0, 0)            # Black block interior
_SOLID_OUTLINE = (0, 201, 255)     # Cyan neon outline (#00C9FF)
_SOLID_COLOR = _SOLID_FILL         # For tint compatibility

# Spikes: Black body with white edges for visibility
_SPIKE_FILL = (0, 0, 0)            # Black spike body
_SPIKE_OUTLINE = (255, 255, 255)   # White outline (#FFFFFF)
_SPIKE_COLOR = _SPIKE_FILL         # For tint compatibility

_FINISH_COLOR = (255, 215, 0)      # Golden finish line

# Player: Lime green primary (#AFE32E), Cyan secondary (#00C9FF)
_PLAYER_PRIMARY = (175, 227, 46)   # GD lime green
_PLAYER_SECONDARY = (0, 201, 255)  # GD cyan details
_PLAYER_BORDER_COLOR = (0, 0, 0)   # Black border (2px)

# Background: #0066FF at ~25% brightness (deep blue)
_SKY_TOP    = (0, 20, 51)          # Dark blue at top (~20% of #0066FF)
_SKY_BOTTOM = (0, 30, 77)          # Slightly brighter at bottom (~30%)

# Ground line: bright neon line at collision boundary
_GROUND_LINE_COLOR = (255, 255, 255)  # White/neon ground line

# Player sprite dimensions (fraction of block size)
_INNER_RATIO: float = 0.55   # inner square is 55% of block size
_BORDER_OUTER: int = 2       # outer square border thickness (px)
_BORDER_INNER: int = 2       # inner square border thickness (px)


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


def _spike_points(
    tile: TileType, sx: int, sy: int, bs: int,
) -> list[tuple[int, int]]:
    """Return the three triangle vertices for an oriented spike."""
    if tile is TileType.SPIKE:          # apex UP
        return [(sx, sy + bs), (sx + bs, sy + bs), (sx + bs // 2, sy)]
    if tile is TileType.SPIKE_DOWN:     # apex DOWN
        return [(sx, sy), (sx + bs, sy), (sx + bs // 2, sy + bs)]
    if tile is TileType.SPIKE_LEFT:     # apex LEFT
        return [(sx + bs, sy), (sx + bs, sy + bs), (sx, sy + bs // 2)]
    # SPIKE_RIGHT — apex RIGHT
    return [(sx, sy), (sx, sy + bs), (sx + bs, sy + bs // 2)]


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
        player: Player | None,
        camera: Camera,
    ) -> None:
        """
        Render a full frame.

        Args:
            surface: Destination pygame surface (typically the display).
            world:   Current level grid (block coordinates).
            player:  Current player with PlayerState, or None to hide.
            camera:  Camera holding x_offset (pixels).
        """
        self._draw_sky(surface)
        self._draw_tiles(surface, world, camera)
        if player is not None:
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
                    # GD style: black fill + neon cyan outline
                    pygame.draw.rect(surface, _SOLID_FILL, rect)
                    pygame.draw.rect(surface, _SOLID_OUTLINE, rect, 2)  # 2px outline
                elif is_spike(tile):
                    # GD style: black body + white edges
                    pts = _spike_points(tile, sx, sy, bs)
                    pygame.draw.polygon(surface, _SPIKE_FILL, pts)
                    pygame.draw.polygon(surface, _SPIKE_OUTLINE, pts, 2)  # white outline
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

        # Outer square: lime green fill + black border (GD style)
        outer_rect = pygame.Rect(0, 0, bs, bs)
        pygame.draw.rect(sprite, _PLAYER_PRIMARY, outer_rect)
        pygame.draw.rect(sprite, _PLAYER_BORDER_COLOR, outer_rect, _BORDER_OUTER)

        # Inner square: cyan secondary color with black border
        inner_size = int(bs * _INNER_RATIO)
        inner_offset = (bs - inner_size) // 2
        inner_rect = pygame.Rect(inner_offset, inner_offset, inner_size, inner_size)
        pygame.draw.rect(sprite, _PLAYER_SECONDARY, inner_rect)
        pygame.draw.rect(sprite, _PLAYER_BORDER_COLOR, inner_rect, _BORDER_INNER)

        # --- Apply clockwise rotation ---
        # pygame.transform.rotate is counter-clockwise, so negate the angle
        rotated = pygame.transform.rotate(sprite, -player.state.angle)

        # Blit centred on the player's block centre
        blit_rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, blit_rect)
