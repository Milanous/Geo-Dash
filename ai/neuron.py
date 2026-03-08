"""
ai/neuron.py — Neuron dataclass for environmental sensing.

Import rules: only stdlib + engine. Never import pygame or renderer.
[Source: architecture.md#Catégorie 4]
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.world import TileType, World, is_spike

# ── Neuron placement bounds (in blocks, relative to player) ───────
DX_MIN: float = -1.0   # max 1 block behind
DX_MAX: float = 9.0    # up to 9 blocks ahead
DY_MIN: float = -3.0   # 3 blocks below
DY_MAX: float = 5.0    # 5 blocks above


def _reflect(value: float, lo: float, hi: float) -> float:
    """Reflect *value* back inside [lo, hi] to avoid boundary pile-up."""
    span = hi - lo
    while value < lo or value > hi:
        if value < lo:
            value = lo + (lo - value)
        if value > hi:
            value = hi - (value - hi)
        # Guard against degenerate span (shouldn't happen with our constants)
        if span <= 0:
            return (lo + hi) / 2
    return value


def clamp_neuron(dx: float, dy: float) -> tuple[float, float]:
    """Reflect dx/dy back into the allowed neuron zone (avoids edge pile-up)."""
    return _reflect(dx, DX_MIN, DX_MAX), _reflect(dy, DY_MIN, DY_MAX)


@dataclass
class Neuron:
    dx: float
    dy: float
    type: TileType
    polarity: str  # "green" | "red"

    def is_active(self, player_x: float, player_y: float, world: World) -> bool:
        tile = world.tile_at(player_x + self.dx, player_y + self.dy)
        if self.type == TileType.SPIKE:
            match = is_spike(tile)
        else:
            match = tile == self.type
        return match if self.polarity == "green" else not match
