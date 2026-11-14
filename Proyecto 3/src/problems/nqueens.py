from src.engine.chromosome import ChromosomeSpec, ChromosomeType, Direction
from src.problems.base_problem import BaseProblem


class NQueens(BaseProblem):
  """Place n queens on an n x n board so that none attacks another.

  Chromosome: a permutation of 0..n-1 where index i is the column and
  chromosome[i] is the row. A permutation never repeats a row or a column,
  so the fitness only counts pairs of queens that share a diagonal. The goal
  is 0 conflicts.
  """

  def __init__(self, size):
    if size < 4:
      raise ValueError("Board size must be at least 4 (2 and 3 have no solution)")
    self.size = size
    self.length = size

  def chromosome_spec(self):
    return ChromosomeSpec(ChromosomeType.PERMUTATION, length=self.size)

  def direction(self):
    return Direction.MINIMIZE

  def conflicts(self, chromosome):
    count = 0
    for i in range(self.size):
      for j in range(i + 1, self.size):
        if abs(chromosome[i] - chromosome[j]) == j - i:
          count += 1
    return count

  def fitness(self, chromosome):
    return float(self.conflicts(chromosome))

  def decode(self, chromosome):
    return f" rows by column : {list(chromosome)}  fitness : {self.fitness(chromosome)}"

  # Both solvers return 0.0 when a conflict-free placement exists, which is
  # always true for n >= 4. They explore the whole search tree and count every
  # solution, so their running time grows with n and can be compared.

  def count_solutions_exhaustive(self):
    rows = [-1] * self.size

    def valid(column, row):
      for previous in range(column):
        if rows[previous] == row or abs(rows[previous] - row) == column - previous:
          return False
      return True

    def place(column):
      if column == self.size:
        return 1
      total = 0
      for row in range(self.size):
        if valid(column, row):
          rows[column] = row
          total += place(column + 1)
          rows[column] = -1
      return total

    return place(0)

  def count_solutions_dp(self):
    # Same search, but the used rows and the two diagonal directions are bit
    # masks. The diagonal masks are shifted one position per column, so the
    # state (rows, diag1, diag2) already identifies the current column.
    full = (1 << self.size) - 1
    memo = {}

    def place(rows, diag1, diag2):
      if rows == full:
        return 1
      state = (rows, diag1, diag2)
      if state in memo:
        return memo[state]
      total = 0
      free = full & ~(rows | diag1 | diag2)
      while free:
        bit = free & -free
        free ^= bit
        total += place(rows | bit, ((diag1 | bit) << 1) & full, (diag2 | bit) >> 1)
      memo[state] = total
      return total

    return place(0, 0, 0)

  def solve_exhaustive(self):
    return 0.0 if self.count_solutions_exhaustive() > 0 else float("inf")

  def solve_dp(self):
    return 0.0 if self.count_solutions_dp() > 0 else float("inf")


if __name__ == "__main__":
  from itertools import permutations

  print("== Fitness counts only diagonal conflicts ==")
  problem = NQueens(4)
  assert problem.fitness([1, 3, 0, 2]) == 0.0, "[1, 3, 0, 2] is a valid solution"
  assert problem.fitness([0, 1, 2, 3]) == 6.0, "all queens on one diagonal: 6 pairs"
  assert problem.fitness([0, 2, 1, 3]) == 2.0, "expected 2 diagonal pairs"
  assert problem.direction() is Direction.MINIMIZE
  assert problem.chromosome_spec().chromosome_type is ChromosomeType.PERMUTATION
  print("OK    fitness")

  print("== Invalid sizes raise ValueError ==")
  for size in (-1, 0, 1, 2, 3):
    try:
      NQueens(size)
      print(f"FAIL  size {size}: no error was raised")
    except ValueError as error:
      print(f"OK    size {size}: {error}")

  print("== Solution counts match the known values ==")
  known = {4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352}
  for size, expected in known.items():
    board = NQueens(size)
    assert board.count_solutions_exhaustive() == expected, f"exhaustive wrong for n={size}"
    assert board.count_solutions_dp() == expected, f"dp wrong for n={size}"
    assert board.solve_exhaustive() == board.solve_dp() == 0.0
  print("OK    n = 4..9")

  print("== Solution count matches brute force over permutations ==")
  for size in (4, 5, 6, 7):
    board = NQueens(size)
    brute = sum(1 for p in permutations(range(size)) if board.conflicts(p) == 0)
    assert brute == board.count_solutions_dp(), f"brute force disagrees for n={size}"
  print("OK    n = 4..7")

  print("== decode ==")
  print(problem.decode([1, 3, 0, 2]))

  print("\nAll checks finished.")
