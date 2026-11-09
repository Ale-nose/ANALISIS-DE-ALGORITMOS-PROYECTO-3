from src.engine.chromosome import ChromosomeSpec,ChromosomeType,Direction
from src.problems.base_problem import BaseProblem

CUT_THRESHOLD = 0.5

class RodCutting(BaseProblem):

  def __init__(self, prices):
    if len(prices) < 2:
      raise ValueError("Length muist be greater than 2")
    if any(price < 0 for price in prices):
      raise ValueError("prices cant be negative")
    self.prices = list(prices)
    self.length = len(prices)

  def price(self, piece_length):
    return self.prices[piece_length - 1]

  def chromosome_spec(self):
    spec = ChromosomeSpec(ChromosomeType.REAL,length= self.length - 1,low = 0.0, high=1.0)
    return spec
  def direction(self):
    return Direction.MAXIMIZE
  def pieces(self, chromosome):
    result = []
    start = 0
    for pos in range(1, self.length):
      if chromosome[pos -1] >= CUT_THRESHOLD:
        result.append(pos - start)
        start = pos
    result.append(self.length - start)
    return result
  def fitness(self, chromosome):
    pieces = self.pieces(chromosome)
    total = sum(self.price(p) for p in pieces)
    return float(total)
  def decode(self, chromosome):
    pieces = self.pieces(chromosome)
    fitness = self.fitness(chromosome)
    text = f" pieces : {pieces}  fitness : {fitness}"
    return text
  def solve_exhaustive(self):
    def best(remaining):
      if remaining == 0:
        return 0
      res = 0
      for piece in range(1, remaining + 1):
        res = max(res, self.price(piece) + best(remaining - piece))
      return res

    return float(best(self.length))

  def solve_dp(self):
    memo = [-1] * (self.length + 1)
    def best(remaining):
      if remaining == 0:
        return 0
      if memo[remaining] != -1:
        return memo[remaining]
      res = 0
      for piece in range(1, remaining + 1):
        res = max(res, self.price(piece) + best(remaining - piece))
      memo[remaining] = res
      return res
    
    return float(best(self.length))

def generate_prices(length, rng):
  prices = []
  for piece in range(1, length + 1):
    price = round(piece *  rng.uniform(1.0, 3.0))
    prices.append(price)
  return prices

