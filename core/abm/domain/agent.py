from __future__ import annotations

import random
from collections.abc import Callable

from mesa import Agent

from core.abm.domain.contracts import Action, AgentAccountSnapshot, ExecutionReport, ExecutionStatus, Observation, Side
from core.abm.policies.archetypes import BaseArchetypePolicy

PolicyFn = Callable[[Observation, random.Random], Action]


class BaseABMAgent(Agent):
    """Mesa agent wrapper with deterministic RNG and typed contracts."""

    def __init__(self, unique_id: str, model, policy: PolicyFn, rng: random.Random) -> None:
        self.agent_id = unique_id
        super().__init__(model=model)
        self.policy = policy
        self.deterministic_rng = rng
        self.account = AgentAccountSnapshot(
            agent_id=self.agent_id,
            cash=0.0,
            inventory=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )

    def act(self, observation: Observation) -> Action:
        return self.policy(observation, self.deterministic_rng)

    def on_execution(self, report: ExecutionReport) -> None:
        cash = self.account.cash
        inventory = self.account.inventory
        realized = self.account.realized_pnl

        if report.status in (ExecutionStatus.FILLED, ExecutionStatus.PARTIAL) and report.fill_price and report.filled_qty:
            notional = report.fill_price * report.filled_qty
            friction_cost = report.fee_cost + report.slippage_cost

            if report.side is Side.BUY:
                cash -= notional + friction_cost
                inventory += report.filled_qty
            elif report.side is Side.SELL:
                cash += notional - friction_cost
                inventory -= report.filled_qty

            realized -= friction_cost

        self.account = AgentAccountSnapshot(
            agent_id=self.account.agent_id,
            cash=cash,
            inventory=inventory,
            realized_pnl=realized,
            unrealized_pnl=self.account.unrealized_pnl,
        )

    def mark_to_market(self, mark_price: float) -> None:
        self.account = AgentAccountSnapshot(
            agent_id=self.account.agent_id,
            cash=self.account.cash,
            inventory=self.account.inventory,
            realized_pnl=self.account.realized_pnl,
            unrealized_pnl=self.account.inventory * mark_price,
        )


class ArchetypeABMAgent(BaseABMAgent):
    """Typed Mesa agent wrapper that owns a two-stage archetype policy."""

    def __init__(self, unique_id: str, model, policy: BaseArchetypePolicy, rng: random.Random) -> None:
        super().__init__(unique_id=unique_id, model=model, policy=policy, rng=rng)
        self.archetype_policy = policy
