from __future__ import annotations

import random
from collections.abc import Callable

from mesa import Agent

from core.abm.domain.contracts import Action, AgentAccountSnapshot, ExecutionReport, Observation

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
        # Sprint 1 keeps accounting immutable and no-op for the skeleton.
        _ = report
