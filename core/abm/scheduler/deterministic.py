from __future__ import annotations

from collections.abc import Callable

from core.abm.domain.agent import BaseABMAgent
from core.abm.domain.contracts import Action, Observation


class DeterministicScheduler:
    """Deterministic activation by sorted agent id."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseABMAgent] = {}

    def add(self, agent: BaseABMAgent) -> None:
        self._agents[str(agent.agent_id)] = agent

    def clear(self) -> None:
        self._agents.clear()

    @property
    def agents(self) -> list[BaseABMAgent]:
        return [self._agents[k] for k in sorted(self._agents)]

    def step(
        self,
        observation_factory: Callable[[BaseABMAgent], Observation],
    ) -> list[tuple[BaseABMAgent, Action]]:
        results: list[tuple[BaseABMAgent, Action]] = []
        for agent in self.agents:
            observation = observation_factory(agent)
            results.append((agent, agent.act(observation)))
        return results
