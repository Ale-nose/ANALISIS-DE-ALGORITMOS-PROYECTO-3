
def gaussian_mutation(chromosome, mutation_rate, spec, rng, sigma):
  if sigma <= 0:
    raise ValueError("Sigma value must be above zero")
  for i in range(len(chromosome)):
    if rng.random() < mutation_rate:
      value = chromosome[i] + rng.gauss(0, sigma)
      chromosome[i] = max(spec.low, min(spec.high, value))
  return chromosome
