from src.engine.chromosome import Direction, is_better

EPSILON = 1e-9

def tournament_selection(population, fitnesses, direction, rng, k):
  if not 1 <= k <= len(population):
    raise ValueError("k must be in [1, population size]")
  indexes = rng.sample(range(len(population)), k)
  best = indexes[0]
  for i in indexes:
    if is_better(fitnesses[i],fitnesses[best],direction):
      best = i
  return population[best]

def ranking_selection(population, fitnesses, direction, rng, k):
    if not 1 <= k <= len(population):
      raise ValueError("k must be in [1, population size]")
    sorted_indexes = sorted(range(len(population)), key = lambda i: fitnesses[i], reverse= direction is Direction.MAXIMIZE)
    top_k = sorted_indexes[:k]
    return population [rng.choice(top_k)]
def roulette_selection(population, fitnesses, direction, rng):
  lowest = min(fitnesses)
  highest = max(fitnesses)
  weights = []
  for f in fitnesses:
    if direction is Direction.MAXIMIZE and lowest > 0:
      weights.append(f)
    elif direction is Direction.MAXIMIZE and lowest <= 0:
      weight = f - lowest + EPSILON
      weights.append(weight)
    else:
      weight = highest - f + EPSILON
      weights.append(weight)
  total = sum(weights)
  spin = rng.uniform(0,total)
  cumulative = 0.0
  for i,weight in enumerate(weights):
    cumulative += weight
    if spin <= cumulative:
      return population[i]
  return population [-1]
