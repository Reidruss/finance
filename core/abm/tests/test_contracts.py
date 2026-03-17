import pytest

from core.abm.domain import Action, ActionType, MarketSnapshot, Observation, Side


def test_contracts_reject_malformed_values() -> None:
    with pytest.raises(ValueError):
        MarketSnapshot(symbol="BTC-USD", bid_price=102.0, ask_price=101.0)

    with pytest.raises(TypeError):
        Observation(
            timestamp_ns=1,
            market=MarketSnapshot(symbol="BTC-USD", bid_price=100.0, ask_price=101.0),
            features={"spread": "wide"},
        )

    with pytest.raises(ValueError):
        Action(action_type=ActionType.CANCEL, order_id=None)

    with pytest.raises(ValueError):
        Action.place(side=Side.BUY, price=-1.0, quantity=1.0, order_id="o-1")
