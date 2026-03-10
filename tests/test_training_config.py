import ast
import pytest
from ai.training_config import TrainingConfig


class TestTrainingConfigDefaults:
    def test_default_instantiation(self):
        cfg = TrainingConfig()
        assert cfg.population_size == 1000
        assert cfg.max_generations == 500
        assert cfg.top_n == 200
        assert cfg.mutation_sigma == 1.0
        assert cfg.max_seconds_per_gen == 120.0
        assert cfg.p_move == 0.99
        assert cfg.p_neuron == 0.008
        assert cfg.p_network == 0.002
        assert cfg.mutations_per_individual == 3


class TestTrainingConfigValidation:
    def test_p_move_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(p_move=-0.1)

    def test_p_neuron_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(p_neuron=-0.1)

    def test_p_move_plus_p_neuron_exceeds_one(self):
        with pytest.raises(ValueError):
            TrainingConfig(p_move=0.80, p_neuron=0.30, p_network=0.0)

    def test_top_n_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(top_n=0)

    def test_top_n_gte_population_size(self):
        with pytest.raises(ValueError):
            TrainingConfig(top_n=50, population_size=10)

    def test_population_size_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(population_size=0)

    def test_population_size_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(population_size=-5)

    def test_max_generations_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(max_generations=0)

    def test_mutation_sigma_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(mutation_sigma=0)

    def test_mutation_sigma_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(mutation_sigma=-1.0)

    def test_max_seconds_per_gen_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(max_seconds_per_gen=0)

    def test_max_seconds_per_gen_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(max_seconds_per_gen=-10.0)

    def test_mutations_per_individual_zero(self):
        with pytest.raises(ValueError):
            TrainingConfig(mutations_per_individual=0)

    def test_mutations_per_individual_negative(self):
        with pytest.raises(ValueError):
            TrainingConfig(mutations_per_individual=-1)


class TestTrainingConfigImportGuard:
    def test_no_pygame_import(self):
        import pathlib
        src = pathlib.Path(__file__).resolve().parent.parent / "ai" / "training_config.py"
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pygame"), \
                        f"training_config.py must not import pygame (found: {alias.name})"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith("pygame"), \
                        f"training_config.py must not import pygame (found: {node.module})"
                    assert not node.module.startswith("renderer"), \
                        f"training_config.py must not import renderer (found: {node.module})"
