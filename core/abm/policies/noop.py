from __future__ import annotations

import random

from core.abm.domain.contracts import Action, Observation


def noop_policy(observation: Observation, rng: random.Random) -> Action:
    _ = observation
    _ = rng
    return Action.hold()
