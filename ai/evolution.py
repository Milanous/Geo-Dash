"""
ai/evolution.py — Top-10 selection & Gaussian mutation for neuroevolution.

Import rules: only stdlib + numpy + ai.*. Never import pygame or renderer.
[Source: architecture.md#Catégorie 5]
"""

from __future__ import annotations

import copy
import random

import numpy as np

from ai.brain import Brain
from ai.network import Network
from ai.neuron import Neuron, clamp_neuron, DX_MIN, DX_MAX, DY_MIN, DY_MAX
from ai.training_config import TrainingConfig
from engine.world import TileType


def select_top_n(brains: list[Brain], fitness: np.ndarray, n: int) -> list[Brain]:
    indices = np.argsort(fitness)[::-1][:n]
    return [brains[i] for i in indices]


def mutate(brain: Brain, config: TrainingConfig) -> Brain:
    new_brain = copy.deepcopy(brain)
    r = random.random()

    if r < config.p_move:
        _mutate_move(new_brain, config)
    elif r < config.p_move + config.p_neuron:
        _mutate_neuron(new_brain)
    elif r < config.p_move + config.p_neuron + config.p_network:
        _mutate_network(new_brain)

    # Ensure at least 1 network with 1 neuron
    if not new_brain.networks:
        new_brain.networks.append(Network([_random_neuron()]))
    for net in new_brain.networks:
        if not net.neurons:
            net.neurons.append(_random_neuron())

    return new_brain


def _mutate_move(brain: Brain, config: TrainingConfig) -> None:
    all_neurons = [n for net in brain.networks for n in net.neurons]
    if not all_neurons:
        return
    k = min(random.randint(1, 3), len(all_neurons))
    chosen = random.sample(all_neurons, k)
    for neuron in chosen:
        neuron.dx += np.random.normal(0, config.mutation_sigma)
        neuron.dy += np.random.normal(0, config.mutation_sigma)
        neuron.dx, neuron.dy = clamp_neuron(neuron.dx, neuron.dy)


def _mutate_neuron(brain: Brain) -> None:
    if not brain.networks:
        brain.networks.append(Network([_random_neuron()]))
        return

    net = random.choice(brain.networks)
    if random.random() < 0.5 and len(net.neurons) > 1:
        net.neurons.pop(random.randrange(len(net.neurons)))
    else:
        net.neurons.append(_random_neuron())


def _mutate_network(brain: Brain) -> None:
    if random.random() < 0.5 and len(brain.networks) > 1:
        brain.networks.pop(random.randrange(len(brain.networks)))
    else:
        brain.networks.append(Network([_random_neuron()]))


def _random_neuron() -> Neuron:
    return Neuron(
        dx=random.uniform(DX_MIN, DX_MAX),
        dy=random.uniform(DY_MIN, DY_MAX),
        type=random.choice([TileType.SOLID, TileType.SPIKE]),
        polarity=random.choice(["green", "red"]),
    )


def generate_random_brain(n_networks: int = 2, neurons_per_network: int = 3) -> Brain:
    networks = [
        Network([_random_neuron() for _ in range(neurons_per_network)])
        for _ in range(n_networks)
    ]
    return Brain(networks)
