def _validate_parents(parent1, parent2):
  if len(parent1) != len(parent2):
    raise ValueError("Both parents must have the same length")


def arithmetic_crossover(parent1, parent2, rng):
  if len(parent1) != len(parent2):
    raise ValueError("Both parents must have the same length")
  t = rng.random()
  child = []
  for i in range(len(parent1)):
    child.append(t * parent1[i] + (1 - t) * parent2[i])
  return child


def one_point_crossover(parent1, parent2, rng):
  _validate_parents(parent1, parent2)
  n = len(parent1)
  if n < 2:
    return list(parent1)
  cut = rng.randint(1, n - 1)
  return list(parent1[:cut]) + list(parent2[cut:])


def two_point_crossover(parent1, parent2, rng):
  _validate_parents(parent1, parent2)
  n = len(parent1)
  if n < 2:
    return list(parent1)
  if n == 2:
    cut1, cut2 = 1, 2
  else:
    cut1, cut2 = sorted(rng.sample(range(1, n), 2))
  return list(parent1[:cut1]) + list(parent2[cut1:cut2]) + list(parent1[cut2:])


def uniform_crossover(parent1, parent2, rng):
  _validate_parents(parent1, parent2)
  return [
    parent1[i] if rng.random() < 0.5 else parent2[i]
    for i in range(len(parent1))
  ]


def ox_crossover(parent1, parent2, rng):
  _validate_parents(parent1, parent2)
  n = len(parent1)
  if n < 2:
    return list(parent1)
  start, end = sorted(rng.sample(range(n), 2))
  child = [None] * n
  child[start : end + 1] = parent1[start : end + 1]
  segment_values = set(parent1[start : end + 1])
  remaining = [gene for gene in parent2 if gene not in segment_values]

  rem_idx = 0
  for i in range(n):
    if child[i] is None:
      child[i] = remaining[rem_idx]
      rem_idx += 1
  return child


def pmx_crossover(parent1, parent2, rng):
  _validate_parents(parent1, parent2)
  n = len(parent1)
  if n < 2:
    return list(parent1)
  start, end = sorted(rng.sample(range(n), 2))
  child = [None] * n
  child[start : end + 1] = parent1[start : end + 1]
  mapping = {parent1[i]: parent2[i] for i in range(start, end + 1)}

  for i in range(n):
    if start <= i <= end:
      continue
    candidate = parent2[i]
    while candidate in mapping:
      candidate = mapping[candidate]
    child[i] = candidate
  return child
