from dataclasses import dataclass


@dataclass
class TrainingConfig:
    population_size: int = 1000
    max_generations: int = 300
    top_n: int = 100
    mutation_sigma: float = 3.0
    max_seconds_per_gen: float = 120.0
    p_move: float = 0.99
    p_neuron: float = 0.0095
    p_network: float = 0.0005
    mutations_per_individual: int = 3

    def __post_init__(self):
        if self.population_size < 1:
            raise ValueError("population_size must be >= 1")
        if self.max_generations < 1:
            raise ValueError("max_generations must be >= 1")
        if self.mutation_sigma <= 0:
            raise ValueError("mutation_sigma must be > 0")
        if self.max_seconds_per_gen <= 0:
            raise ValueError("max_seconds_per_gen must be > 0")
        if self.p_move < 0.0 or self.p_move > 1.0:
            raise ValueError("p_move must be between 0.0 and 1.0")
        if self.p_neuron < 0.0 or self.p_neuron > 1.0:
            raise ValueError("p_neuron must be between 0.0 and 1.0")
        if self.p_network < 0.0 or self.p_network > 1.0:
            raise ValueError("p_network must be between 0.0 and 1.0")
        if self.p_move + self.p_neuron + self.p_network > 1.0:
            raise ValueError("p_move + p_neuron + p_network must be <= 1.0")
        if self.top_n < 1:
            raise ValueError("top_n must be >= 1")
        if self.top_n >= self.population_size:
            raise ValueError("top_n must be < population_size")
        if self.mutations_per_individual < 1:
            raise ValueError("mutations_per_individual must be >= 1")
