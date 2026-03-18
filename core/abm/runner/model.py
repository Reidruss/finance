from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
import importlib

from mesa import Model

from core.abm.adapters import LobMarketAdapter
from core.abm.domain import (
	Action,
	ActionRejectReason,
	ActionType,
	BaseABMAgent,
	ExecutionReport,
	ExecutionStatus,
	MarketSnapshot,
	Observation,
	PolicyFn,
	Side,
)
from core.abm.runner.seeding import derive_seed, make_rng, normalize_seed
from core.abm.scheduler import DeterministicScheduler
from core.abm.policies import ArchetypeConfig, create_archetype_policy


@dataclass(frozen=True)
class MarketTick:
	timestamp_ns: int
	symbol: str
	bid_price: float
	ask_price: float
	bid_size: float = 1.0
	ask_size: float = 1.0


@dataclass(frozen=True)
class ActionLimits:
	min_price: float = 0.01
	max_price: float = 10_000_000.0
	max_quantity: float = 1_000_000.0


class ABMModel(Model):
	"""Deterministic ABM model with market adapter and state hydration."""

	def __init__(
		self,
		seed: int | None = 0,
		episode_length: int = 10,
		market_ticks: Iterable[MarketTick] | None = None,
		market_adapter: LobMarketAdapter | None = None,
		action_limits: ActionLimits | None = None,
	) -> None:
		super().__init__()
		self.global_seed = normalize_seed(seed)
		self.episode_length = episode_length
		self.scheduler = DeterministicScheduler()
		self.action_limits = action_limits or ActionLimits()
		self.telemetry: list[dict[str, object]] = []
		self._step_index = 0
		self._archetype_metadata: list[dict[str, object]] = []
		self._market_ticks = list(market_ticks) if market_ticks is not None else self._default_ticks()
		if not self._market_ticks:
			raise ValueError("market_ticks must contain at least one tick")

		self.market_adapter = market_adapter
		if self.market_adapter is None:
			try:
				self.market_adapter = LobMarketAdapter(symbol=self._market_ticks[0].symbol)
			except Exception:
				self.market_adapter = None

		self._fee_model = None
		self._slippage_model = None
		try:
			friction_engine = importlib.import_module("friction_engine")

			self._fee_model = friction_engine.SimpleFeeModel(5.0, 10.0)
			self._slippage_model = friction_engine.StochasticSlippageModel(1.0, 0.2)
		except Exception:
			self._fee_model = None
			self._slippage_model = None

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

	def register_archetype_agent(
		self,
		agent_id: str,
		archetype_key: str,
		config: ArchetypeConfig,
		deterministic_mode: bool | None = None,
	) -> BaseABMAgent:
		active_config = config
		if deterministic_mode is not None:
			active_config = replace(config, deterministic_mode=deterministic_mode)

		policy = create_archetype_policy(archetype_key=archetype_key, config=active_config)
		policy_rng = make_rng(derive_seed(self.global_seed, f"archetype:{archetype_key}:{agent_id}"))
		policy.set_random_stream(policy_rng)
		agent = self.register_agent(agent_id, policy)

		self._archetype_metadata.append(
			{
				"agent_id": agent_id,
				"config": active_config.to_metadata(),
				"stream_seed_namespace": f"archetype:{archetype_key}:{agent_id}",
			}
		)
		return agent

	def experiment_metadata(self) -> dict[str, object]:
		return {
			"global_seed": self.global_seed,
			"episode_length": self.episode_length,
			"market_symbol": self._market_ticks[0].symbol,
			"archetypes": list(self._archetype_metadata),
		}

	def current_tick(self) -> MarketTick:
		idx = min(self._step_index, len(self._market_ticks) - 1)
		return self._market_ticks[idx]

	def make_observation(self) -> Observation:
		if self.market_adapter is not None:
			s = self.market_adapter.snapshot()
			return Observation(
				timestamp_ns=self._step_index,
				market=MarketSnapshot(
					symbol=self._market_ticks[0].symbol,
					bid_price=s.bid_price,
					ask_price=s.ask_price,
					bid_size=s.bid_size,
					ask_size=s.ask_size,
					last_trade_price=s.last_trade_price,
				),
				features={
					"spread": s.ask_price - s.bid_price,
					"midpoint": s.midpoint,
					"imbalance": s.imbalance,
					"short_return": s.short_return,
					"recent_trade_qty": s.recent_trade_qty,
				},
			)

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
		for agent in self.scheduler.agents:
			agent.mark_to_market(observation.features["midpoint"])

		self.telemetry.append(
			{
				"step": self._step_index,
				"timestamp_ns": observation.timestamp_ns,
				"num_agents": len(action_bundle),
				"actions": [action.action_type.value for _, action in action_bundle],
				"reports": [report.status.value for report in reports],
				"reasons": [report.reason for report in reports],
				"reject_reasons": [report.reject_reason.value for report in reports],
				"latency_us": [report.latency_us for report in reports],
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
			report = self._execute_action(agent, action)
			agent.on_execution(report)
			reports.append(report)
		return reports

	def _execute_action(self, agent: BaseABMAgent, action: Action) -> ExecutionReport:
		if action.action_type is ActionType.HOLD:
			return ExecutionReport(
				agent_id=str(agent.agent_id),
				order_id=None,
				status=ExecutionStatus.NONE,
				reason="hold",
			)

		valid, reject_reason, reason = self._validate_action(action)
		if not valid:
			return ExecutionReport(
				agent_id=str(agent.agent_id),
				order_id=action.order_id,
				status=ExecutionStatus.REJECTED,
				side=action.side,
				requested_qty=action.quantity or 0.0,
				reason=reason,
				reject_reason=reject_reason,
			)

		if self.market_adapter is None:
			return ExecutionReport(
				agent_id=str(agent.agent_id),
				order_id=action.order_id,
				status=ExecutionStatus.REJECTED,
				side=action.side,
				requested_qty=action.quantity or 0.0,
				reason="market adapter unavailable",
				reject_reason=ActionRejectReason.ADAPTER_ERROR,
			)

		if action.action_type is ActionType.PLACE:
			exec_result = self.market_adapter.place_order(
				order_id=action.order_id or "",
				side=action.side or Side.BUY,
				price=action.price or 0.0,
				quantity=action.quantity or 0.0,
			)
			fee_cost, slippage_cost = self._estimate_friction(
				fill_price=exec_result.fill_price,
				filled_qty=exec_result.filled_qty,
			)
			return ExecutionReport(
				agent_id=str(agent.agent_id),
				order_id=action.order_id,
				status=exec_result.status,
				side=action.side,
				requested_qty=action.quantity or 0.0,
				filled_qty=exec_result.filled_qty,
				fill_price=exec_result.fill_price,
				reason=exec_result.reason,
				reject_reason=exec_result.reject_reason,
				fee_cost=fee_cost,
				slippage_cost=slippage_cost,
				latency_us=exec_result.latency_us,
			)

		exec_result = self.market_adapter.cancel_order(order_id=action.order_id or "")
		return ExecutionReport(
			agent_id=str(agent.agent_id),
			order_id=action.order_id,
			status=exec_result.status,
			side=action.side,
			requested_qty=action.quantity or 0.0,
			reason=exec_result.reason,
			reject_reason=exec_result.reject_reason,
			latency_us=exec_result.latency_us,
		)

	def _validate_action(self, action: Action) -> tuple[bool, ActionRejectReason, str]:
		if action.action_type is ActionType.PLACE:
			if action.price is None or action.price < self.action_limits.min_price or action.price > self.action_limits.max_price:
				return False, ActionRejectReason.LIMIT_VIOLATION, "price violates action limits"
			if action.quantity is None or action.quantity <= 0 or action.quantity > self.action_limits.max_quantity:
				return False, ActionRejectReason.LIMIT_VIOLATION, "quantity violates action limits"
			if action.side is None:
				return False, ActionRejectReason.INVALID_ACTION, "place action requires side"
			return True, ActionRejectReason.NONE, "ok"

		if action.action_type is ActionType.CANCEL and not action.order_id:
			return False, ActionRejectReason.INVALID_ACTION, "cancel action requires order_id"

		return True, ActionRejectReason.NONE, "ok"

	def _estimate_friction(self, fill_price: float | None, filled_qty: float) -> tuple[float, float]:
		if fill_price is None or filled_qty <= 0:
			return 0.0, 0.0

		fee_cost = 0.0
		slippage_cost = 0.0
		if self._fee_model is not None:
			fr = self._fee_model.calculate_friction(fill_price, filled_qty, False)
			fee_cost = float(getattr(fr, "fee_cost", 0.0))
		if self._slippage_model is not None:
			slippage_cost = max(0.0, float(self._slippage_model.calculate_slippage(fill_price, filled_qty)))
		return fee_cost, slippage_cost

	def _default_ticks(self) -> list[MarketTick]:
		return [
			MarketTick(timestamp_ns=i, symbol="BTC-USD", bid_price=100.0 + i, ask_price=101.0 + i)
			for i in range(self.episode_length)
		]

