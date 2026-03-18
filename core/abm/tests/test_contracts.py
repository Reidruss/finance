import pytest

from core.abm.domain import Action, ActionType, ExecutionReport, ExecutionStatus, MarketSnapshot, Observation, Side


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

    with pytest.raises(ValueError):
        ExecutionReport(agent_id="a", order_id="o", status=ExecutionStatus.NONE, latency_us=-1)


def test_execution_report_defaults() -> None:
    report = ExecutionReport(agent_id="a", order_id="o", status=ExecutionStatus.NONE)
    assert report.reject_reason.value == "none"
