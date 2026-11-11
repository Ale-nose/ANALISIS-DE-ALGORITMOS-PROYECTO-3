from src.engine.chromosome import ChromosomeSpec, ChromosomeType, Direction
from src.problems.base_problem import BaseProblem

class Knapsack01(BaseProblem):

  def __init__(self, weights, values, capacity):
    if len(weights) == 0 or len(weights) != len(values):
      raise ValueError("Weights and values must be non-empty and have the same length")
    if capacity < 0:
      raise ValueError("Capacity cant be negative")
    if any(w <= 0 for w in weights) or any(v < 0 for v in values):
      raise ValueError("Weights must be positive and values cant be negative")
    self.weights = list(weights)
    self.values = list(values)
    self.capacity = capacity
    self.length = len(self.weights)

  def chromosome_spec(self):
    return ChromosomeSpec(ChromosomeType.BINARY, length=self.length)

  def direction(self):
    return Direction.MAXIMIZE

  def selected_items(self, chromosome):
    return [i for i, gene in enumerate(chromosome) if gene == 1]

  def fitness(self, chromosome):
    total_weight = sum(self.weights[i] for i, g in enumerate(chromosome) if g == 1)
    total_value = sum(self.values[i] for i, g in enumerate(chromosome) if g == 1)
    if total_weight > self.capacity:
      return -float(total_weight - self.capacity)
    return float(total_value)

  def decode(self, chromosome):
    items = self.selected_items(chromosome)
    fitness = self.fitness(chromosome)
    return f" items : {items}  fitness : {fitness}"

  def solve_exhaustive(self):
    def best(index, remaining):
      if index == self.length or remaining == 0:
        return 0
      res = best(index + 1, remaining)
      if self.weights[index] <= remaining:
        res = max(res, self.values[index] + best(index + 1, remaining - self.weights[index]))
      return res

    return float(best(0, self.capacity))

  def solve_dp(self):
    memo = {}

    def best(index, remaining):
      if index == self.length or remaining == 0:
        return 0
      state = (index, remaining)
      if state in memo:
        return memo[state]
      res = best(index + 1, remaining)
      if self.weights[index] <= remaining:
        res = max(res, self.values[index] + best(index + 1, remaining - self.weights[index]))
      memo[state] = res
      return res

    return float(best(0, self.capacity))


def generate_knapsack(length, rng):
  weights = [rng.randint(1, 20) for _ in range(length)]
  values = [round(w * rng.uniform(1.0, 3.0)) for w in weights]
  capacity = max(1, sum(weights) // 2)
  return weights, values, capacity
