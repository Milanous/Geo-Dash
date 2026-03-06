"""
renderer/vfx.py — Visual effects: glow, ground particles, movement trail.

Import rules: may import engine/, pygame. Never engine/player.py directly —
receives PlayerState only as a data container.

pygame is imported LAZILY (inside draw methods only) so this module remains
importable in headless test contexts without a display.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from engine.physics import BLOCK_SIZE_PX, PlayerState

if TYPE_CHECKING:
    import pygame


# ---------------------------------------------------------------------------
# Internal data types
# ---------------------------------------------------------------------------

@dataclass
class _Particle:
    """A single short-lived particle stored in world-block coordinates."""
    wx: float          # world x (blocks)
    wy: float          # world y (blocks)
    vx: float          # velocity in blocks/s (horizontal)
    vy: float          # velocity in blocks/s (upward = positive in screen)
    lifetime: float    # seconds remaining
    max_lifetime: float


# ---------------------------------------------------------------------------
# VFX constants
# ---------------------------------------------------------------------------

_TRAIL_MAXLEN: int = 30         # ~0.5 s at 60 FPS
_PARTICLE_COUNT: int = 8        # burst size on landing
_PARTICLE_LIFETIME: float = 0.3 # seconds
_PARTICLE_SPEED_MIN: float = 0.5  # blocks/s
_PARTICLE_SPEED_MAX: float = 2.0  # blocks/s
_GLOW_RADIUS_PX: int = 22       # radius of bloom halo (pixels)


# ---------------------------------------------------------------------------
# VFXSystem
# ---------------------------------------------------------------------------

class VFXSystem:
    """
    Manages and renders all visual effects for the player cube:
      - Gradient motion trail (world-space, last 30 positions)
      - Ground-landing particle burst
      - Soft glow/bloom halo

    Usage:
        vfx = VFXSystem()
        # each physics step:
        vfx.update(player.state, dt)
        # each render frame:
        vfx.draw(surface, camera.x_offset)
    """

    def __init__(self) -> None:
        # Trail: deque of (world_x_blocks, world_y_blocks) — newest at index 0
        self._trail: deque[tuple[float, float]] = deque(maxlen=_TRAIL_MAXLEN)
        self._particles: list[_Particle] = []
        self._was_on_ground: bool = True

    # ------------------------------------------------------------------
    # State update (no pygame — safe for headless tests)
    # ------------------------------------------------------------------

    def update(self, player_state: PlayerState, dt: float) -> None:
        """
        Advance VFX state by one physics timestep.

        Detects landing transitions (on_ground False→True) and spawns
        particles automatically.

        Args:
            player_state: Current player physics state (read-only).
            dt:           Physics timestep in seconds.
        """
        # 1. Record trail position (world-space blocks)
        self._trail.appendleft((player_state.x, player_state.y))

        # 2. Landing detection — False → True transition
        if player_state.on_ground and not self._was_on_ground:
            self.on_land(player_state.x, player_state.y)

        self._was_on_ground = player_state.on_ground

        # 3. Advance and expire particles
        alive: list[_Particle] = []
        for p in self._particles:
            p.wx += p.vx * dt
            p.wy += p.vy * dt
            p.lifetime -= dt
            if p.lifetime > 0.0:
                alive.append(p)
        self._particles = alive

    def on_land(self, bx: float, by: float) -> None:
        """
        Spawn a burst of particles at world-block position (bx, by).

        Called automatically by update() on landing transition.
        Can also be called manually for testing.

        Args:
            bx: Player world x in blocks.
            by: Player world y in blocks.
        """
        for _ in range(_PARTICLE_COUNT):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(_PARTICLE_SPEED_MIN, _PARTICLE_SPEED_MAX)
            self._particles.append(_Particle(
                wx=bx,
                wy=by,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                lifetime=_PARTICLE_LIFETIME,
                max_lifetime=_PARTICLE_LIFETIME,
            ))

    def reset(self) -> None:
        """Clear all trail and particle state (e.g. after player respawn)."""
        self._trail.clear()
        self._particles.clear()
        self._was_on_ground = True

    # ------------------------------------------------------------------
    # Accessors for tests (no pygame)
    # ------------------------------------------------------------------

    @property
    def trail_length(self) -> int:
        """Number of positions currently in the trail deque."""
        return len(self._trail)

    @property
    def particle_count(self) -> int:
        """Number of active (unexpired) particles."""
        return len(self._particles)

    # ------------------------------------------------------------------
    # Drawing (pygame used here — never called in headless tests)
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", camera_offset_px: int) -> None:
        """
        Render glow, trail and particles onto *surface*.

        Args:
            surface:          Destination pygame surface.
            camera_offset_px: Horizontal camera offset in pixels.
        """
        import pygame  # lazy import — keeps module headless-safe

        bs = BLOCK_SIZE_PX
        screen_h = surface.get_height()

        trail_list = list(self._trail)

        # 1. Glow — behind everything, drawn first
        if trail_list:
            bx, by = trail_list[0]
            cx = int(bx * bs) - camera_offset_px + bs // 2
            cy = screen_h - int((by + 1) * bs) + bs // 2
            self._draw_glow(surface, cx, cy)

        # 2. Trail — gradient white (head) → grey (tail)
        for i in range(len(trail_list) - 1):
            bx1, by1 = trail_list[i]
            bx2, by2 = trail_list[i + 1]
            x1 = int(bx1 * bs) - camera_offset_px + bs // 2
            y1 = screen_h - int((by1 + 1) * bs) + bs // 2
            x2 = int(bx2 * bs) - camera_offset_px + bs // 2
            y2 = screen_h - int((by2 + 1) * bs) + bs // 2
            t = i / max(len(trail_list) - 1, 1)
            val = int(255 - t * 175)   # 255 (white) → 80 (grey)
            pygame.draw.line(surface, (val, val, val), (x1, y1), (x2, y2), 2)

        # 3. Particles — small filled circles, fade as lifetime shrinks
        for p in self._particles:
            alpha_ratio = p.lifetime / p.max_lifetime
            radius = max(1, int(4 * alpha_ratio))
            brightness = int(255 * alpha_ratio)
            color = (brightness, int(brightness * 0.85), 60)
            px_screen = int(p.wx * bs) - camera_offset_px + bs // 2
            py_screen = screen_h - int((p.wy + 1) * bs) + bs // 2
            pygame.draw.circle(surface, color, (px_screen, py_screen), radius)

    def _draw_glow(self, surface: "pygame.Surface", cx: int, cy: int) -> None:
        """Draw a soft radial bloom halo centred at (cx, cy)."""
        import pygame  # lazy import

        r = _GLOW_RADIUS_PX
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            alpha = int(35 * (i / r) ** 2)
            pygame.draw.circle(glow, (220, 80, 80, alpha), (r, r), i)
        surface.blit(glow, (cx - r, cy - r))
