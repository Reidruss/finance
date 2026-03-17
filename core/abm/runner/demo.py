from __future__ import annotations

from core.abm.policies import noop_policy
from core.abm.runner.model import ABMModel


def run_demo(seed: int = 7, steps: int = 5) -> list[dict[str, object]]:
    model = ABMModel(seed=seed, episode_length=steps)
    model.register_agent("noop-1", noop_policy)
    return model.run_episode()


if __name__ == "__main__":
    for event in run_demo():
        print(event)
