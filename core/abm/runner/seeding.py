from __future__ import annotations

import hashlib
import random


def normalize_seed(seed: int | None) -> int:
    if seed is None:
        return 0
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return seed


def derive_seed(global_seed: int, namespace: str) -> int:
    data = f"{global_seed}:{namespace}".encode("utf-8")
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def make_rng(seed: int) -> random.Random:
    return random.Random(seed)
