from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from mesa import Model

from core.abm.domain import (
	Action,
	ActionType,
	BaseABMAgent,
	ExecutionReport,
	ExecutionStatus,
	MarketSnapshot,
	Observation,
	PolicyFn,
)
from core.abm.runner.seeding import derive_seed, make_rng, normalize_seed
from core.abm.scheduler import DeterministicScheduler


@dataclass(frozen=True)
class MarketTick:
	timestamp_ns: int
	symbol: str
	bid_price: float
	ask_price: float
	bid_size: float = 1.0
	ask_size: float = 1.0


class ABMModel(Model):
	"""Minimal deterministic ABM model shell for Sprint 1."""

	def __init__(
		self,
		seed: int | None = 0,
		episode_length: int = 10,
		market_ticks: Iterable[MarketTick] | None = None,
	) -> None:
		super().__init__()
		self.global_seed = normalize_seed(seed)
		self.episode_length = episode_length
		self.scheduler = DeterministicScheduler()
		self.telemetry: list[dict[str, object]] = []
		self._step_index = 0
		self._market_ticks = list(market_ticks) if market_ticks is not None else self._default_ticks()
		if not self._market_ticks:
			raise ValueError("market_ticks must contain at least one tick")

	def register_agent(self, agent_or_id, policy: PolicyFn | None = None):
		# Mesa 3 calls model.register_agent(agent) from Agent.__init__.
		if isinstance(agent_or_id, BaseABMAgent):
			super().register_agent(agent_or_id)
			self.scheduler.add(agent_or_id)
			return agent_or_id

		if policy is None:
			raise ValueError("policy is required when registering by agent_id")

		agent_id = str(agent_or_id)
		rng = make_rng(derive_seed(self.global_seed, f"agent:{agent_id}"))
		return BaseABMAgent(unique_id=agent_id, model=self, policy=policy, rng=rng)

	def current_tick(self) -> MarketTick:
		idx = min(self._step_index, len(self._market_ticks) - 1)
		return self._market_ticks[idx]

	def make_observation(self) -> Observation:
		tick = self.current_tick()
		spread = tick.ask_price - tick.bid_price
		midpoint = (tick.ask_price + tick.bid_price) / 2.0
		return Observation(
			timestamp_ns=tick.timestamp_ns,
			market=MarketSnapshot(
				symbol=tick.symbol,
				bid_price=tick.bid_price,
				ask_price=tick.ask_price,
				bid_size=tick.bid_size,
				ask_size=tick.ask_size,
				last_trade_price=midpoint,
			),
			features={"spread": spread, "midpoint": midpoint},
		)

	def step(self) -> None:
		if self._step_index >= self.episode_length:
			return

		observation = self.make_observation()
		action_bundle = self.scheduler.step(lambda _agent: observation)
		reports = self._execute(action_bundle)

		self.telemetry.append(
			{
				"step": self._step_index,
				"timestamp_ns": observation.timestamp_ns,
				"num_agents": len(action_bundle),
				"actions": [action.action_type.value for _, action in action_bundle],
				"reports": [report.status.value for report in reports],
			}
		)
		self._step_index += 1

	def run_episode(self) -> list[dict[str, object]]:
		while self._step_index < self.episode_length:
			self.step()
		return self.telemetry

	def _execute(
		self,
		action_bundle: list[tuple[BaseABMAgent, Action]],
	) -> list[ExecutionReport]:
		reports: list[ExecutionReport] = []
		for agent, action in action_bundle:
			if action.action_type is ActionType.HOLD:
				report = ExecutionReport(
					agent_id=str(agent.agent_id),
					order_id=None,
					status=ExecutionStatus.NONE,
					reason="hold",
				)
			else:
				report = ExecutionReport(
					agent_id=str(agent.agent_id),
					order_id=action.order_id,
					status=ExecutionStatus.REJECTED,
					reason="Sprint 1 skeleton does not route to market adapter",
				)
			agent.on_execution(report)
			reports.append(report)
		return reports

	def _default_ticks(self) -> list[MarketTick]:
		return [
			MarketTick(timestamp_ns=i, symbol="BTC-USD", bid_price=100.0 + i, ask_price=101.0 + i)
			for i in range(self.episode_length)
		]

