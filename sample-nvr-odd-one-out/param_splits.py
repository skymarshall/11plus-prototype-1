"""
Allowed parameter value splits for odd-one-out NVR questions (picture-based-questions-guide.md §5).

For random parameters that do not determine the answer, value counts across options must follow
allowed splits so no single option is uniquely different. This module defines allowed splits per
number of options and provides sampling/assignment helpers.
"""

import random
from typing import Optional

# Allowed splits: tuple of counts (e.g. (2, 3) = two values, one appears 2× one 3×).
# Never 4–1 for 5 options; never 3–1 for 4 options; never 5–1 for 6 options.
ALLOWED_SPLITS: dict[int, list[tuple[int, ...]]] = {
    4: [(2, 2), (2, 1, 1)],
    5: [(2, 3), (3, 1, 1), (2, 2, 1), (2, 1, 1, 1), (1, 1, 1, 1, 1)],
    6: [
        (3, 3), (2, 2, 2), (4, 2), (4, 1, 1), (3, 2, 1),
        (3, 1, 1, 1), (2, 2, 1, 1), (2, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1),
    ],
}


def sample_split(
    n_options: int,
    rng: Optional[random.Random] = None,
    max_values: Optional[int] = None,
) -> tuple[int, ...]:
    """Return a random allowed split for n_options (e.g. (2, 3) or (3, 1, 1) for 5). If max_values is set, only return splits that need at most that many distinct values (len(split) <= max_values)."""
    rng = rng or random.Random()
    splits = ALLOWED_SPLITS.get(n_options)
    if not splits:
        raise ValueError(f"No allowed splits for n_options={n_options}")
    if max_values is not None:
        splits = [s for s in splits if len(s) <= max_values]
        if not splits:
            raise ValueError(f"No allowed split for n_options={n_options} with max_values={max_values}")
    return rng.choice(splits)


def assign_split_to_indices(
    split: tuple[int, ...],
    n_options: int,
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Assign value indices to n_options so counts match split.
    split e.g. (2, 3) => 2 options get value index 0, 3 get value index 1.
    Returns list of length n_options, e.g. [0, 1, 0, 1, 1].
    """
    rng = rng or random.Random()
    if sum(split) != n_options:
        raise ValueError(f"Split {split} does not sum to n_options={n_options}")
    # Build list of value indices: split[0] copies of 0, split[1] copies of 1, ...
    indices: list[int] = []
    for val_idx, count in enumerate(split):
        indices.extend([val_idx] * count)
    rng.shuffle(indices)
    return indices
