from src.engine.chromosome import ChromosomeSpec, ChromosomeType, Direction
from src.problems.base_problem import BaseProblem

class Partition(BaseProblem):

  def __init__(self, numbers):
    if len(numbers) < 2:
      raise ValueError("Length must be at least 2")
    if any(x <= 0 for x in numbers):
      raise ValueError("Numbers must be positive")
    self.numbers = list(numbers)
    self.length = len(self.numbers)
    self.total_sum = sum(self.numbers)

  def chromosome_spec(self):
    return ChromosomeSpec(ChromosomeType.BINARY, length=self.length)

  def direction(self):
    return Direction.MINIMIZE

  def subsets(self, chromosome):
    subset_a = [self.numbers[i] for i, g in enumerate(chromosome) if g == 0]
    subset_b = [self.numbers[i] for i, g in enumerate(chromosome) if g == 1]
    return subset_a, subset_b

  def fitness(self, chromosome):
    sum_a = sum(self.numbers[i] for i, g in enumerate(chromosome) if g == 0)
    sum_b = self.total_sum - sum_a
    return float(abs(sum_a - sum_b))

  def decode(self, chromosome):
    subset_a, subset_b = self.subsets(chromosome)
    fitness = self.fitness(chromosome)
    return f" subset_a : {subset_a}  subset_b : {subset_b}  fitness : {fitness}"

  def solve_exhaustive(self):
    def best(index, current_sum):
      if index == self.length:
        return abs(self.total_sum - 2 * current_sum)
      if index == 0:
        return best(1, self.numbers[0])
      return min(
        best(index + 1, current_sum + self.numbers[index]),
        best(index + 1, current_sum),
      )

    return float(best(0, 0))

  def solve_dp(self):
    memo = {}

    def best(index, current_sum):
      if index == self.length:
        return abs(self.total_sum - 2 * current_sum)
      state = (index, current_sum)
      if state in memo:
        return memo[state]
      if index == 0:
        res = best(1, self.numbers[0])
      else:
        res = min(
          best(index + 1, current_sum + self.numbers[index]),
          best(index + 1, current_sum),
        )
      memo[state] = res
      return res

    return float(best(0, 0))


def generate_numbers(length, rng):
  return [rng.randint(1, 50) for _ in range(length)]