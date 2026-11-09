"""genetic algorithm engine.

    selection(population, fitnesses, direction, rng) -> Chromosome
        Returns ONE parent taken from ``population``. It may return the same
        list object stored in the population; the engine copies it if needed.

    crossover(parent1, parent2, rng) -> Chromosome
        Returns ONE new child. It must not modify the parents.

    mutation(chromosome, mutation_rate, spec, rng) -> Chromosome
        Returns the mutated chromosome. It may modify ``chromosome`` in place,
        because the engine always passes a child it owns.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import pairwise

from src.engine.chromosome import (
    ChromosomeSpec,
    ChromosomeType,
    Direction,
    is_better,
    random_chromosome,
)

Chromosome = list
FitnessFunction = Callable[[Chromosome], float]
SelectionOperator = Callable[[list[Chromosome], list[float], Direction, random.Random], Chromosome]
CrossoverOperator = Callable[[Chromosome, Chromosome, random.Random], Chromosome]
MutationOperator = Callable[[Chromosome, float, ChromosomeSpec, random.Random], Chromosome]

STOP_MAX_EVALUATIONS = "max_evaluations"
STOP_NO_IMPROVEMENT = "no_improvement"


class FitnessEvaluator:
    """Single entry point for every fitness call.

    Counts evaluations, enforces the evaluation budget exactly and keeps the
    best value seen after each evaluation (the convergence curve).
    """

    def __init__(
        self,
        fitness_function: FitnessFunction,
        direction: Direction,
        max_evaluations: int,
    ) -> None:
        if max_evaluations <= 0:
            raise ValueError("max_evaluations must be positive")
        self.fitness_function = fitness_function
        self.direction = direction
        self.max_evaluations = max_evaluations
        self.count = 0
        self.best_value: float | None = None
        self.best_chromosome: Chromosome | None = None
        self.history: list[tuple[int, float]] = []

    def budget_exhausted(self) -> bool:
        """Return True when no more evaluations are allowed."""
        return self.count >= self.max_evaluations

    def evaluate(self, chromosome: Chromosome) -> float:
        """Evaluate one chromosome, update the best so far and record history."""
        if self.budget_exhausted():
            raise RuntimeError("evaluation budget exhausted")
        value = self.fitness_function(chromosome)
        self.count += 1
        if self.best_value is None or is_better(value, self.best_value, self.direction):
            self.best_value = value
            self.best_chromosome = list(chromosome)
        self.history.append((self.count, self.best_value))
        return value


@dataclass
class GAConfig:
    """Every tunable parameter of one genetic algorithm run.

    Set ``max_generations_without_improvement`` to None to disable that
    stopping rule, so every run spends exactly ``max_evaluations`` (required
    when comparing configurations in Experiment 1).
    """

    population_size: int
    selection: SelectionOperator
    crossover: CrossoverOperator
    crossover_rate: float
    mutation: MutationOperator
    mutation_rate: float
    elitism: int
    max_evaluations: int
    max_generations_without_improvement: int | None = None
    seed: int = 0

    def __post_init__(self) -> None:
        if self.population_size < 2:
            raise ValueError("population_size must be at least 2")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be in [0, 1]")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be in [0, 1]")
        if not 0 <= self.elitism < self.population_size:
            raise ValueError("elitism must be in [0, population_size)")
        if self.max_evaluations < self.population_size:
            raise ValueError("max_evaluations must cover at least the initial population")
        if (
            self.max_generations_without_improvement is not None
            and self.max_generations_without_improvement <= 0
        ):
            raise ValueError("max_generations_without_improvement must be positive or None")


@dataclass
class GAResult:
    """What one genetic algorithm run returns."""

    best_chromosome: Chromosome
    best_fitness: float
    evaluations_used: int
    generations: int
    stop_reason: str
    seed: int
    history: list[tuple[int, float]] = field(repr=False)


def _elite_indices(fitnesses: list[float], direction: Direction, count: int) -> list[int]:
    """Return the indices of the ``count`` best chromosomes, best first."""
    if count == 0:
        return []
    order = sorted(
        range(len(fitnesses)),
        key=lambda index: fitnesses[index],
        reverse=direction is Direction.MAXIMIZE,
    )
    return order[:count]


def run_genetic_algorithm(
    spec: ChromosomeSpec,
    fitness_function: FitnessFunction,
    direction: Direction,
    config: GAConfig,
) -> GAResult:
    """Run the genetic algorithm and return the best chromosome found.

    Cycle (as in the assignment):
      1. Random initial population.
      2. Evaluate fitness (the initial population counts toward the budget).
      3. Copy the elite to the new population (elites are NOT re-evaluated).
      4. Until the new population is full: select two parents, cross them with
         probability ``crossover_rate`` (otherwise the child copies parent 1),
         mutate the child, evaluate it and add it.
      5. Replace the population.
      6. Stop on the evaluation budget or on K generations without improvement.
      7. Return the best chromosome found.
    """
    rng = random.Random(config.seed)
    evaluator = FitnessEvaluator(fitness_function, direction, config.max_evaluations)

    population = [random_chromosome(spec, rng) for _ in range(config.population_size)]
    fitnesses = [evaluator.evaluate(chromosome) for chromosome in population]

    generations = 0
    generations_without_improvement = 0
    stop_reason = STOP_MAX_EVALUATIONS

    while not evaluator.budget_exhausted():
        if (
            config.max_generations_without_improvement is not None
            and generations_without_improvement >= config.max_generations_without_improvement
        ):
            stop_reason = STOP_NO_IMPROVEMENT
            break

        best_before = evaluator.best_value

        new_population: list[Chromosome] = []
        new_fitnesses: list[float] = []
        for index in _elite_indices(fitnesses, direction, config.elitism):
            new_population.append(list(population[index]))
            new_fitnesses.append(fitnesses[index])

        while len(new_population) < config.population_size and not evaluator.budget_exhausted():
            parent1 = config.selection(population, fitnesses, direction, rng)
            parent2 = config.selection(population, fitnesses, direction, rng)
            if rng.random() < config.crossover_rate:
                child = config.crossover(parent1, parent2, rng)
            else:
                child = list(parent1)
            child = config.mutation(child, config.mutation_rate, spec, rng)
            new_population.append(child)
            new_fitnesses.append(evaluator.evaluate(child))

        if len(new_population) < config.population_size:
            break

        population = new_population
        fitnesses = new_fitnesses
        generations += 1

        if is_better(evaluator.best_value, best_before, direction):
            generations_without_improvement = 0
        else:
            generations_without_improvement += 1

    return GAResult(
        best_chromosome=list(evaluator.best_chromosome),
        best_fitness=evaluator.best_value,
        evaluations_used=evaluator.count,
        generations=generations,
        stop_reason=stop_reason,
        seed=config.seed,
        history=evaluator.history,
    )


if __name__ == "__main__":
    # Placeholder operators used ONLY by these checks. They are deliberately
    # different from the assignment operators (Tasks 2, 3, 6 and 10).
    def placeholder_selection(population, fitnesses, direction, rng):
        return rng.choice(population)

    def placeholder_crossover(parent1, parent2, rng):
        middle = len(parent1) // 2
        return list(parent1[:middle]) + list(parent2[middle:])

    def placeholder_mutation(chromosome, mutation_rate, spec, rng):
        for index in range(len(chromosome)):
            if rng.random() < mutation_rate:
                chromosome[index] = rng.uniform(spec.low, spec.high)
        return chromosome

    def make_config(**overrides):
        values = {
            "population_size": 20,
            "selection": placeholder_selection,
            "crossover": placeholder_crossover,
            "crossover_rate": 0.9,
            "mutation": placeholder_mutation,
            "mutation_rate": 0.1,
            "elitism": 2,
            "max_evaluations": 1000,
            "max_generations_without_improvement": None,
            "seed": 42,
        }
        values.update(overrides)
        return GAConfig(**values)

    spec = ChromosomeSpec(ChromosomeType.REAL, 10, low=0.0, high=1.0)

    print("== is_better ==")
    assert is_better(5, 3, Direction.MAXIMIZE) and not is_better(3, 5, Direction.MAXIMIZE)
    assert is_better(3, 5, Direction.MINIMIZE) and not is_better(5, 3, Direction.MINIMIZE)
    assert not is_better(4, 4, Direction.MAXIMIZE) and not is_better(4, 4, Direction.MINIMIZE)
    print("OK    both directions, ties are not improvements")

    print("== FitnessEvaluator ==")
    evaluator = FitnessEvaluator(sum, Direction.MAXIMIZE, 3)
    candidate = [5, 5]
    evaluator.evaluate([1, 1])
    evaluator.evaluate(candidate)
    candidate[0] = -100
    evaluator.evaluate([0, 1])
    assert evaluator.history == [(1, 2), (2, 10), (3, 10)], evaluator.history
    assert evaluator.best_chromosome == [5, 5], "best_chromosome must be a copy"
    try:
        evaluator.evaluate([1, 1])
        print("FAIL  evaluation allowed past the budget")
    except RuntimeError as error:
        print(f"OK    counts, keeps a copy of the best and rejects extra calls: {error}")

    print("== Invalid configurations raise ValueError ==")
    invalid_cases = [
        ("population_size=1", {"population_size": 1}),
        ("crossover_rate=1.5", {"crossover_rate": 1.5}),
        ("mutation_rate=-0.1", {"mutation_rate": -0.1}),
        ("elitism=population_size", {"elitism": 20}),
        ("max_evaluations<population_size", {"max_evaluations": 10}),
        ("K=0", {"max_generations_without_improvement": 0}),
    ]
    for name, overrides in invalid_cases:
        try:
            make_config(**overrides)
            print(f"FAIL  {name}: no error was raised")
        except ValueError as error:
            print(f"OK    {name}: {error}")

    print("== Budget is spent exactly ==")
    for budget in (1000, 1001, 1013):
        result = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(max_evaluations=budget))
        assert result.evaluations_used == budget, f"used {result.evaluations_used} of {budget}"
        assert len(result.history) == budget, "one history entry per evaluation"
        assert result.stop_reason == STOP_MAX_EVALUATIONS
        print(f"OK    budget {budget}: used {result.evaluations_used}, {result.generations} full generations")

    print("== Elites are not re-evaluated ==")
    # 20 initial + 18 per generation (20 - 2 elites) * 5 generations = 110
    result = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(max_evaluations=110))
    assert result.generations == 5, f"expected 5 generations, got {result.generations}"
    print("OK    110 evaluations = 20 initial + 5 generations of 18 children")

    print("== MAXIMIZE improves and never gets worse ==")
    result = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(max_evaluations=5000))
    values = [best for _, best in result.history]
    assert all(later >= earlier for earlier, later in pairwise(values)), "curve went down"
    assert result.best_fitness > values[0], "no improvement over the first evaluation"
    assert sum(result.best_chromosome) == result.best_fitness, "best_chromosome does not match best_fitness"
    print(f"OK    first = {values[0]:.3f}, final = {result.best_fitness:.3f} (optimum 10)")

    print("== MINIMIZE improves and never gets worse ==")
    result = run_genetic_algorithm(spec, sum, Direction.MINIMIZE, make_config(max_evaluations=5000))
    values = [best for _, best in result.history]
    assert all(later <= earlier for earlier, later in pairwise(values)), "curve went up"
    assert result.best_fitness < values[0], "no improvement over the first evaluation"
    print(f"OK    first = {values[0]:.3f}, final = {result.best_fitness:.3f} (optimum 0)")

    print("== Same seed gives the same run, different seed a different one ==")
    first = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(seed=7))
    second = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(seed=7))
    other = run_genetic_algorithm(spec, sum, Direction.MAXIMIZE, make_config(seed=8))
    assert first.history == second.history and first.best_chromosome == second.best_chromosome
    assert first.history != other.history
    print("OK    reproducible")

    print("== Stops after K generations without improvement ==")
    result = run_genetic_algorithm(
        spec,
        lambda chromosome: 0.0,
        Direction.MAXIMIZE,
        make_config(max_generations_without_improvement=4),
    )
    assert result.stop_reason == STOP_NO_IMPROVEMENT, result.stop_reason
    assert result.generations == 4, f"expected 4 generations, got {result.generations}"
    print(f"OK    stopped by '{result.stop_reason}' after {result.generations} generations")

    print("== No crossover: child is a copy, parents stay intact ==")
    result = run_genetic_algorithm(
        spec, sum, Direction.MAXIMIZE, make_config(crossover_rate=0.0, mutation_rate=0.5)
    )
    assert sum(result.best_chromosome) == result.best_fitness, "mutation leaked into a stored chromosome"
    print("OK    in-place mutation never corrupts parents or the best chromosome")

    print("\nAll checks finished.")