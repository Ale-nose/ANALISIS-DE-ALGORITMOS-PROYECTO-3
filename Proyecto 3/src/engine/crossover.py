def arithmetic_crossover(parent1, parent2, rng):
  if  len(parent1) != len(parent2):
    raise ValueError("Both parents must have the same length")
  t = rng.random()
  child = []
  for i in range(len(parent1)):
    child.append(t * parent1[i] + (1 - t) * parent2[i])
  return child

