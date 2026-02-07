"""
Weighted choice by frequency modifiers (question-gen/QUESTION-GENERATION-DESIGN.md §4, Frequency modifiers).

Templates use **common**, **uncommon**, and **rare** to set probabilities.
This module provides reusable weighted sampling for all question templates.
"""

import random
from typing import Any, Optional, Sequence

# Weights per guide §4 Frequency modifiers
WEIGHT_COMMON = 1.0
WEIGHT_UNCOMMON = 1.0 / 3.0
WEIGHT_RARE = 1.0 / 10.0

FREQUENCY_WEIGHTS: dict[str, float] = {
    "common": WEIGHT_COMMON,
    "uncommon": WEIGHT_UNCOMMON,
    "rare": WEIGHT_RARE,
}


def weight_for(frequency: str) -> float:
    """Return weight for a frequency label. Unknown labels default to common (1.0)."""
    return FREQUENCY_WEIGHTS.get(frequency.strip().lower(), WEIGHT_COMMON)


def weighted_choice(
    rng: random.Random,
    choices: Sequence[tuple[Any, str]],
) -> Any:
    """
    Choose one item from (item, frequency) pairs using template frequency weights.

    frequency is "common", "uncommon", or "rare" (case-insensitive).
    Unrecognised labels are treated as "common".

    Returns the chosen item (first element of the chosen pair).
    """
    if not choices:
        raise ValueError("weighted_choice requires at least one choice")
    weights = [weight_for(freq) for _, freq in choices]
    total = sum(weights)
    if total <= 0:
        raise ValueError("total weight must be positive")
    r = rng.uniform(0.0, total)
    acc = 0.0
    for (item, _), w in zip(choices, weights):
        acc += w
        if r <= acc:
            return item
    return choices[-1][0]


def weighted_choice_from_pool(
    rng: random.Random,
    pool: Sequence[Any],
    frequency_by_item: Optional[dict[Any, str]] = None,
) -> Any:
    """
    Choose one item from a pool. If frequency_by_item is given, use those
    frequencies (common/uncommon/rare); otherwise all items are common.
    """
    if not pool:
        raise ValueError("pool must be non-empty")
    freq_map = frequency_by_item or {}
    choices = [(item, freq_map.get(item, "common")) for item in pool]
    return weighted_choice(rng, choices)
