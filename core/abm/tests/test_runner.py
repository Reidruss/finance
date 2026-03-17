import random

from core.abm.domain import Action, Observation, Side
from core.abm.policies import noop_policy
from core.abm.runner.model import ABMModel


def seeded_policy(observation: Observation, rng: random.Random) -> Action:
    _ = observation
    if rng.random() > 0.5:
        price = 100.0 + rng.random()
        return Action.place(side=Side.BUY, price=price, quantity=1.0, order_id=f"buy-{rng.randint(1, 999)}")
    return Action.hold()


def _run_action_sequence(seed: int) -> list[list[str]]:
    model = ABMModel(seed=seed, episode_length=6)
    model.register_agent("agent-a", seeded_policy)
    model.register_agent("agent-b", seeded_policy)
    telemetry = model.run_episode()
    return [event["actions"] for event in telemetry]


def test_identical_seed_produces_identical_action_sequence() -> None:
    seq_a = _run_action_sequence(seed=42)
    seq_b = _run_action_sequence(seed=42)
    seq_c = _run_action_sequence(seed=43)

    assert seq_a == seq_b
    assert seq_a != seq_c


def test_noop_episode_completes_without_errors() -> None:
    model = ABMModel(seed=11, episode_length=4)
    model.register_agent("noop-agent", noop_policy)
    telemetry = model.run_episode()

    assert len(telemetry) == 4
    assert all(event["actions"] == ["hold"] for event in telemetry)


def test_mesa_model_bootstraps_and_steps_one_tick() -> None:
    model = ABMModel(seed=17, episode_length=1)
    model.step()

    assert len(model.telemetry) == 1
    assert model.telemetry[0]["step"] == 0
