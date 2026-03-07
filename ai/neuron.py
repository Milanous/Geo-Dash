"""
ai/neuron.py — Neuron dataclass for environmental sensing.

Import rules: only stdlib + engine. Never import pygame or renderer.
[Source: architecture.md#Catégorie 4]
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.world import TileType, World


@dataclass
class Neuron:
    dx: float
    dy: float
    type: TileType
    polarity: str  # "green" | "red"

    def is_active(self, player_x: float, player_y: float, world: World) -> bool:
        tile = world.tile_at(player_x + self.dx, player_y + self.dy)
        match = tile == self.type
        return match if self.polarity == "green" else not match
