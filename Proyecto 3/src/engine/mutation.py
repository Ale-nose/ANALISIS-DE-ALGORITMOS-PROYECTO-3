def gaussian_mutation(chromosome, mutation_rate, spec, rng, sigma=0.1):
  if sigma <= 0:
    raise ValueError("Sigma value must be above zero")
  for i in range(len(chromosome)):
    if rng.random() < mutation_rate:
      value = chromosome[i] + rng.gauss(0, sigma)
      chromosome[i] = max(spec.low, min(spec.high, value))
  return chromosome


def bit_flip_mutation(chromosome, mutation_rate, spec, rng):
  for i in range(len(chromosome)):
    if rng.random() < mutation_rate:
      chromosome[i] = 1 - chromosome[i]
  return chromosome


def swap_mutation(chromosome, mutation_rate, spec, rng):
  if len(chromosome) >= 2 and rng.random() < mutation_rate:
    i, j = rng.sample(range(len(chromosome)), 2)
    chromosome[i], chromosome[j] = chromosome[j], chromosome[i]
  return chromosome


def inversion_mutation(chromosome, mutation_rate, spec, rng):
  if len(chromosome) >= 2 and rng.random() < mutation_rate:
    start, end = sorted(rng.sample(range(len(chromosome)), 2))
    chromosome[start : end + 1] = reversed(chromosome[start : end + 1])
  return chromosome
