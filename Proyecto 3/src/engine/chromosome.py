
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import random

class ChromosomeType(Enum):
  BINARY = "binary"
  REAL = "real"
  PERMUTATION = "permutation"
class Direction(Enum):
  MAXIMIZE = "maximize"
  MINIMIZE = "minimize"

@dataclass
class ChromosomeSpec:
  chromosome_type : ChromosomeType
  length : int
  low: Optional[float] = None
  high: Optional[float] = None

  def __post_init__(self):
    if self.length <= 0:
      raise ValueError
    if self.chromosome_type is ChromosomeType.REAL:
      if self.high is None or self.low is None:
        raise ValueError
      if  self.low >= self.high:
        raise ValueError
def random_chromosome(spec,rng):
  if spec.chromosome_type is ChromosomeType.REAL:
    values = [None] * spec.length
    for i in range(spec.length):
      values[i] = rng.uniform(spec.low,spec.high)
    return values
  raise NotImplementedError("binary and permuted not yet implemented")

def is_better(candidate, current, direction):
    if direction is Direction.MAXIMIZE:
        return candidate > current
    return candidate < current

if __name__ == "__main__":
    print("== Valid REAL chromosome ==")
    spec = ChromosomeSpec(ChromosomeType.REAL, 5, low=0.0, high=1.0)
    chromosome = random_chromosome(spec, random.Random(42))
    print(chromosome)
    assert chromosome is not None, "random_chromosome returned None"
    assert len(chromosome) == spec.length, "wrong length"
    assert all(spec.low <= gene <= spec.high for gene in chromosome), "gene out of bounds"

    print("== Same seed gives the same chromosome ==")
    again = random_chromosome(spec, random.Random(42))
    print(again)
    assert chromosome == again, "same seed produced different chromosomes"

    print("== Different seed gives a different chromosome ==")
    other = random_chromosome(spec, random.Random(7))
    print(other)
    assert chromosome != other, "different seeds produced the same chromosome"

    print("== Invalid specs must raise ValueError ==")
    invalid_cases = [
        ("negative length", lambda: ChromosomeSpec(ChromosomeType.REAL, -3, low=0.0, high=1.0)),
        ("zero length", lambda: ChromosomeSpec(ChromosomeType.BINARY, 0)),
        ("REAL without low", lambda: ChromosomeSpec(ChromosomeType.REAL, 5, high=1.0)),
        ("REAL without high", lambda: ChromosomeSpec(ChromosomeType.REAL, 5, low=0.0)),
        ("low greater than high", lambda: ChromosomeSpec(ChromosomeType.REAL, 5, low=5.0, high=1.0)),
        ("low equal to high", lambda: ChromosomeSpec(ChromosomeType.REAL, 5, low=1.0, high=1.0)),
    ]
    for name, build in invalid_cases:
        try:
            build()
            print(f"FAIL  {name}: no error was raised")
        except ValueError as error:
            print(f"OK    {name}: {error}")

    print("== low = 0.0 must be accepted ==")
    ChromosomeSpec(ChromosomeType.REAL, 3, low=0.0, high=1.0)
    print("OK    low = 0.0 accepted")

    print("== BINARY without bounds must be accepted ==")
    ChromosomeSpec(ChromosomeType.BINARY, 4)
    print("OK    BINARY spec created")

    print("== Unimplemented types must raise NotImplementedError ==")
    for chromosome_type in (ChromosomeType.BINARY, ChromosomeType.PERMUTATION):
        try:
            random_chromosome(ChromosomeSpec(chromosome_type, 4), random.Random(1))
            print(f"FAIL  {chromosome_type.name}: no error was raised")
        except NotImplementedError as error:
            print(f"OK    {chromosome_type.name}: {error}")

    print("== Direction values ==")
    assert Direction.MAXIMIZE.value == "maximize", "MAXIMIZE has the wrong text"
    assert Direction.MINIMIZE.value == "minimize", "MINIMIZE has the wrong text"
    print("OK    Direction values are correct")

    print("\nAll checks finished.")