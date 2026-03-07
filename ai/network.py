"""
ai/network.py — Network grouping and firing logic.

Import rules: only stdlib + engine + ai.neuron. Never import pygame or renderer.
[Source: architecture.md#Catégorie 4]
"""

from __future__ import annotations

from ai.neuron import Neuron
from engine.world import World


class Network:
    def __init__(self, neurons: list[Neuron]) -> None:
        self.neurons = neurons

    def should_fire(self, player_x: float, player_y: float, world: World) -> bool:
        if not self.neurons:
            return False
        return all(n.is_active(player_x, player_y, world) for n in self.neurons)
