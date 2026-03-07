"""
ai/brain.py — Brain genome with JSON serialization.

Import rules: only stdlib + engine + ai.neuron/network. Never import pygame or renderer.
[Source: architecture.md#Catégorie 4]
"""

from __future__ import annotations

from ai.network import Network
from ai.neuron import Neuron
from engine.world import TileType, World

_TYPE_TO_STR = {TileType.AIR: "air", TileType.SOLID: "solid", TileType.SPIKE: "spike"}
_STR_TO_TYPE = {v: k for k, v in _TYPE_TO_STR.items()}


class Brain:
    def __init__(self, networks: list[Network]) -> None:
        self.networks = networks

    def should_jump(self, player_x: float, player_y: float, world: World) -> bool:
        return any(net.should_fire(player_x, player_y, world) for net in self.networks)

    def to_json(self) -> dict:
        return {
            "version": 1,
            "networks": [
                {
                    "neurons": [
                        {
                            "dx": n.dx,
                            "dy": n.dy,
                            "type": _TYPE_TO_STR[n.type],
                            "polarity": n.polarity,
                        }
                        for n in net.neurons
                    ]
                }
                for net in self.networks
            ],
        }

    @classmethod
    def from_json(cls, data: dict) -> Brain:
        if data.get("version") != 1:
            raise ValueError(f"Unsupported brain version: {data.get('version')}")
        networks = []
        for net_data in data["networks"]:
            neurons = [
                Neuron(
                    dx=nd["dx"],
                    dy=nd["dy"],
                    type=_STR_TO_TYPE[nd["type"]],
                    polarity=nd["polarity"],
                )
                for nd in net_data["neurons"]
            ]
            networks.append(Network(neurons))
        return cls(networks)
