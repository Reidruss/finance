import pytest

pytest.importorskip("lob_engine")

from core.abm.adapters import LobMarketAdapter
from core.abm.domain import Action, Side
from core.abm.runner.model import ABMModel


class ScriptPolicy:
    def __init__(self, scripted_actions: list[Action]) -> None:
        self._actions = scripted_actions
        self._idx = 0

    def __call__(self, observation, rng):
        _ = observation
        _ = rng
        if self._idx >= len(self._actions):
            return Action.hold()
        action = self._actions[self._idx]
        self._idx += 1
        return action


def test_place_and_cancel_updates_book() -> None:
    adapter = LobMarketAdapter(symbol="BTC-USD")
    policy = ScriptPolicy(
        [
            Action.place(side=Side.BUY, price=99.0, quantity=3.0, order_id="o-1"),
            Action.cancel(order_id="o-1"),
            Action.hold(),
        ]
    )
    model = ABMModel(seed=5, episode_length=3, market_adapter=adapter)
    model.register_agent("agent-1", policy)
    telemetry = model.run_episode()

    assert adapter.active_order_count() == 0
    assert telemetry[0]["reject_reasons"] == ["none"]
    assert telemetry[1]["reject_reasons"] == ["none"]


def test_crossing_order_produces_fill_and_account_delta() -> None:
    adapter = LobMarketAdapter(symbol="BTC-USD")
    seed = adapter.place_order(order_id="seed-ask", side=Side.SELL, price=101.0, quantity=10.0)
    assert seed.status.value == "none"

    policy = ScriptPolicy([Action.place(side=Side.BUY, price=101.0, quantity=4.0, order_id="cross-buy")])
    model = ABMModel(seed=7, episode_length=1, market_adapter=adapter)
    agent = model.register_agent("buyer", policy)
    telemetry = model.run_episode()

    assert telemetry[0]["reports"][0] in ("filled", "partial")
    assert agent.account.inventory > 0
    assert agent.account.cash < 0
    assert agent.account.realized_pnl <= 0
