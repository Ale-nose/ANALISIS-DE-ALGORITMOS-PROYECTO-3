import math

from src.engine.chromosome import ChromosomeSpec, ChromosomeType, Direction
from src.problems.base_problem import BaseProblem


class TSP(BaseProblem):
  """Travelling salesman: shortest closed tour that visits every city once."""

  def __init__(self, distances):
    n = len(distances)
    if n < 2:
      raise ValueError("TSP needs at least 2 cities")
    if any(len(row) != n for row in distances):
      raise ValueError("Distance matrix must be square")
    if any(distances[i][j] < 0 for i in range(n) for j in range(n)):
      raise ValueError("Distances cant be negative")
    self.distances = [list(row) for row in distances]
    self.length = n

  def chromosome_spec(self):
    return ChromosomeSpec(ChromosomeType.PERMUTATION, length=self.length)

  def direction(self):
    return Direction.MINIMIZE

  def tour_length(self, tour):
    total = 0
    for i in range(self.length - 1):
      total += self.distances[tour[i]][tour[i + 1]]
    total += self.distances[tour[-1]][tour[0]]
    return total

  def fitness(self, chromosome):
    return float(self.tour_length(chromosome))

  def decode(self, chromosome):
    return f" tour : {list(chromosome)}  fitness : {self.fitness(chromosome)}"

  def solve_exhaustive(self):
    # City 0 is fixed as the start, so rotations of the same tour are not repeated.
    visited = [False] * self.length
    visited[0] = True

    def best(current, count):
      if count == self.length:
        return self.distances[current][0]
      res = math.inf
      for city in range(1, self.length):
        if not visited[city]:
          visited[city] = True
          res = min(res, self.distances[current][city] + best(city, count + 1))
          visited[city] = False
      return res

    return float(best(0, 1))

  def solve_dp(self):
    # Held-Karp: same recursion, but the visited cities are a bit mask and
    # every state (current city, mask) is solved only once.
    full_mask = (1 << self.length) - 1
    memo = {}

    def best(current, mask):
      if mask == full_mask:
        return self.distances[current][0]
      state = (current, mask)
      if state in memo:
        return memo[state]
      res = math.inf
      for city in range(1, self.length):
        if not mask & (1 << city):
          res = min(res, self.distances[current][city] + best(city, mask | (1 << city)))
      memo[state] = res
      return res

    return float(best(0, 1))


def generate_distances(length, rng):
  """Random cities in a 100 x 100 square; symmetric integer distances."""
  points = [(rng.randint(0, 100), rng.randint(0, 100)) for _ in range(length)]
  matrix = [[0] * length for _ in range(length)]
  for i in range(length):
    for j in range(i + 1, length):
      d = max(1, round(math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1])))
      matrix[i][j] = d
      matrix[j][i] = d
  return matrix


if __name__ == "__main__":
  import random
  from itertools import permutations

  print("== Fitness of a known tour ==")
  square = TSP([
    [0, 1, 2, 1],
    [1, 0, 1, 2],
    [2, 1, 0, 1],
    [1, 2, 1, 0],
  ])
  assert square.fitness([0, 1, 2, 3]) == 4.0, "square perimeter should be 4"
  assert square.fitness([0, 2, 1, 3]) == 2 + 1 + 2 + 1, "crossing tour should be 6"
  assert square.direction() is Direction.MINIMIZE
  assert square.chromosome_spec().chromosome_type is ChromosomeType.PERMUTATION
  print("OK    closed tour distance includes the return to the first city")

  print("== Invalid instances raise ValueError ==")
  for name, build in [
    ("one city", lambda: TSP([[0]])),
    ("not square", lambda: TSP([[0, 1], [1, 0, 2]])),
    ("negative distance", lambda: TSP([[0, -1], [-1, 0]])),
  ]:
    try:
      build()
      print(f"FAIL  {name}: no error was raised")
    except ValueError as error:
      print(f"OK    {name}: {error}")

  print("== Generator is reproducible and symmetric ==")
  first = generate_distances(8, random.Random(1))
  assert first == generate_distances(8, random.Random(1)), "same seed, different matrix"
  assert first != generate_distances(8, random.Random(2)), "different seed, same matrix"
  assert all(first[i][j] == first[j][i] for i in range(8) for j in range(8)), "not symmetric"
  assert all(first[i][i] == 0 for i in range(8)), "diagonal must be 0"
  print("OK    generate_distances")

  print("== Exhaustive and DP match brute force ==")
  for n in range(2, 9):
    for seed in range(3):
      problem = TSP(generate_distances(n, random.Random(seed)))
      brute = min(problem.fitness(list(p)) for p in permutations(range(n)))
      assert problem.solve_exhaustive() == brute, f"exhaustive wrong for n={n}, seed={seed}"
      assert problem.solve_dp() == brute, f"dp wrong for n={n}, seed={seed}"
  print("OK    n = 2..8, 3 seeds each")

  print("== DP agrees with exhaustive on a bigger instance ==")
  problem = TSP(generate_distances(10, random.Random(5)))
  assert problem.solve_exhaustive() == problem.solve_dp()
  print("OK    n = 10")

  print("== decode ==")
  print(square.decode([0, 1, 2, 3]))

  print("\nAll checks finished.")
