from core.abm.domain import Action, ExecutionReport, ExecutionStatus, Side
from core.abm.runner.model import ABMModel


def test_friction_adjustment_math() -> None:
    model = ABMModel(seed=3, episode_length=1, market_adapter=None)
    agent = model.register_agent("acc-agent", lambda o, r: Action.hold())
    report = ExecutionReport(
        agent_id="acc-agent",
        order_id="o-1",
        status=ExecutionStatus.FILLED,
        side=Side.BUY,
        requested_qty=2.0,
        filled_qty=2.0,
        fill_price=100.0,
        fee_cost=1.0,
        slippage_cost=2.0,
        reason="unit-test",
    )

    agent.on_execution(report)

    assert agent.account.cash == -203.0
    assert agent.account.inventory == 2.0
    assert agent.account.realized_pnl == -3.0

    agent.mark_to_market(110.0)
    assert agent.account.unrealized_pnl == 220.0
