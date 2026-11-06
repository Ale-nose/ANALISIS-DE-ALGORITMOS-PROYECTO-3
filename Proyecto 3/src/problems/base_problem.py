from abc import ABC, abstractmethod
from src.engine.chromosome import ChromosomeSpec,Direction

class BaseProblem(ABC):

  @abstractmethod
  def chromosome_spec(self) -> ChromosomeSpec:
    ...
  @abstractmethod
  def direction(self) -> Direction:
    ...
  @abstractmethod
  def fitness(self, chromosome) -> float:
    ...

  @abstractmethod
  def solve_exhaustive(self) -> float:
    ...

  @abstractmethod
  def solve_dp(self) -> float:
    ...
  
  def decode(self, chromosome) -> str:
    return str(chromosome) 

if __name__ == "__main__":
    from src.engine.chromosome import ChromosomeType

    class DummyProblem(BaseProblem):
        """Maximize the sum of 3 real genes in [0, 1]. Optimum = 3.0."""

        def chromosome_spec(self) -> ChromosomeSpec:
            return ChromosomeSpec(ChromosomeType.REAL, 3, low=0.0, high=1.0)

        def direction(self) -> Direction:
            return Direction.MAXIMIZE

        def fitness(self, chromosome: list) -> float:
            return sum(chromosome)

        def solve_exhaustive(self) -> float:
            return 3.0

        def solve_dp(self) -> float:
            return 3.0

    class IncompleteProblem(BaseProblem):
        """Forgets fitness, solve_exhaustive and solve_dp on purpose."""

        def chromosome_spec(self) -> ChromosomeSpec:
            return ChromosomeSpec(ChromosomeType.BINARY, 4)

        def direction(self) -> Direction:
            return Direction.MINIMIZE

    print("== BaseProblem cannot be instantiated ==")
    try:
        BaseProblem()
        print("FAIL  BaseProblem() was created; are the methods marked @abstractmethod?")
    except TypeError as error:
        print(f"OK    {error}")

    print("== A subclass missing methods cannot be instantiated ==")
    try:
        IncompleteProblem()
        print("FAIL  IncompleteProblem() was created")
    except TypeError as error:
        print(f"OK    {error}")

    print("== A complete subclass works ==")
    problem = DummyProblem()
    spec = problem.chromosome_spec()
    assert isinstance(spec, ChromosomeSpec), "chromosome_spec must return a ChromosomeSpec"
    assert problem.direction() is Direction.MAXIMIZE, "direction is wrong"
    assert problem.fitness([0.5, 0.25, 0.25]) == 1.0, "fitness is wrong"
    assert problem.solve_exhaustive() == problem.solve_dp() == 3.0, "exact solvers disagree"
    print(f"OK    spec = {spec}")
    print(f"OK    direction = {problem.direction().value}")

    print("== decode has a default implementation ==")
    decoded = problem.decode([0.1, 0.2, 0.3])
    assert decoded == "[0.1, 0.2, 0.3]", f"unexpected decode output: {decoded}"
    print(f"OK    decode -> {decoded}")

    print("\nAll checks finished.")