from __future__ import annotations

import random

from core.abm.domain import ActionType, MarketSnapshot, Observation
from core.abm.policies import (
    DEFAULT_ARCHETYPE_REGISTRY,
    MarketMakerConfig,
    MomentumTraderConfig,
    NoiseTraderConfig,
    create_archetype_policy,
)
from core.abm.runner.model import ABMModel, MarketTick


def _observation(step: int, last_trade_price: float) -> Observation:
    return Observation(
        timestamp_ns=step,
        market=MarketSnapshot(
            symbol="BTC-USD",
            bid_price=last_trade_price - 0.5,
            ask_price=last_trade_price + 0.5,
            bid_size=10.0,
            ask_size=9.0,
            last_trade_price=last_trade_price,
        ),
        features={"spread": 1.0, "midpoint": last_trade_price, "inventory": 0.0},
    )


def _run_policy_for_valid_actions(policy, prices: list[float]) -> None:
    rng = random.Random(19)
    for i, px in enumerate(prices):
        action = policy(_observation(i, px), rng)
        assert action.action_type in (ActionType.PLACE, ActionType.CANCEL, ActionType.HOLD)
        if action.action_type is ActionType.PLACE:
            assert action.side is not None
            assert action.price is not None and action.price > 0
            assert action.quantity is not None and action.quantity > 0
            assert action.order_id is not None


def test_archetype_registry_resolves_known_keys() -> None:
    keys = DEFAULT_ARCHETYPE_REGISTRY.keys()

    assert "noise" in keys
    assert "momentum" in keys
    assert "market_maker" in keys

    assert create_archetype_policy("noise", NoiseTraderConfig()).__class__.__name__ == "NoiseTraderPolicy"
    assert create_archetype_policy("momentum", MomentumTraderConfig()).__class__.__name__ == "MomentumTraderPolicy"
    assert create_archetype_policy("market_maker", MarketMakerConfig()).__class__.__name__ == "InventoryAwareMarketMakerPolicy"


def test_each_archetype_emits_valid_actions() -> None:
    _run_policy_for_valid_actions(create_archetype_policy("noise", NoiseTraderConfig()), [100.0 + i for i in range(10)])
    _run_policy_for_valid_actions(
        create_archetype_policy("momentum", MomentumTraderConfig(lookback=3, threshold_bps=1.0)),
        [100.0, 100.2, 100.6, 101.2, 101.5, 101.8],
    )
    _run_policy_for_valid_actions(create_archetype_policy("market_maker", MarketMakerConfig()), [100.0 + i for i in range(10)])


def _run_trace(seed: int) -> tuple[list[list[str]], dict[str, object]]:
    ticks = [
        MarketTick(timestamp_ns=i, symbol="BTC-USD", bid_price=100.0 + i, ask_price=101.0 + i)
        for i in range(8)
    ]
    model = ABMModel(seed=seed, episode_length=8, market_ticks=ticks)
    model.register_archetype_agent("noise-1", "noise", NoiseTraderConfig(), deterministic_mode=True)
    model.register_archetype_agent("mom-1", "momentum", MomentumTraderConfig(), deterministic_mode=True)
    model.register_archetype_agent("mm-1", "market_maker", MarketMakerConfig(), deterministic_mode=True)
    telemetry = model.run_episode()
    trace = [event["actions"] for event in telemetry]
    return trace, model.experiment_metadata()


def test_deterministic_mode_reproduces_exact_action_trace() -> None:
    trace_a, metadata_a = _run_trace(seed=123)
    trace_b, metadata_b = _run_trace(seed=999)

    # In deterministic mode, action traces should be seed-invariant for regression replay.
    assert trace_a == trace_b
    assert metadata_a["archetypes"]
    assert metadata_b["archetypes"]


def test_three_archetypes_run_with_isolated_state_and_serialized_config() -> None:
    model = ABMModel(seed=42, episode_length=6)
    noise_agent = model.register_archetype_agent("n", "noise", NoiseTraderConfig(order_probability=1.0))
    mom_agent = model.register_archetype_agent("m", "momentum", MomentumTraderConfig(lookback=2, threshold_bps=0.0))
    mm_agent = model.register_archetype_agent("q", "market_maker", MarketMakerConfig(spread_bps=5.0))

    telemetry = model.run_episode()
    metadata = model.experiment_metadata()

    assert len(telemetry) == 6
    assert noise_agent.agent_id != mom_agent.agent_id != mm_agent.agent_id

    # Each policy owns its own mutable runtime counters.
    assert noise_agent.policy.state.order_seq >= 1
    assert mom_agent.policy.state.step >= 1
    assert mm_agent.policy.state.order_seq >= 1

    assert len(metadata["archetypes"]) == 3
    archetype_names = [entry["config"]["archetype"] for entry in metadata["archetypes"]]
    assert archetype_names == ["noise", "momentum", "market_maker"]
