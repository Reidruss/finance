from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from core.abm.domain import ActionRejectReason, ExecutionStatus, Side


@dataclass(frozen=True)
class AdapterExecution:
	status: ExecutionStatus
	reason: str
	reject_reason: ActionRejectReason = ActionRejectReason.NONE
	filled_qty: float = 0.0
	fill_price: float | None = None
	latency_us: int = 0


@dataclass(frozen=True)
class AdapterSnapshot:
	bid_price: float
	ask_price: float
	bid_size: float
	ask_size: float
	midpoint: float
	imbalance: float
	short_return: float
	last_trade_price: float
	recent_trade_qty: float


class LobMarketAdapter:
	"""ABM adapter for the Rust-backed lob_engine Python bindings."""

	def __init__(
		self,
		symbol: str,
		tick_size: float = 1.0,
		max_quantity: float = 1_000_000.0,
		book=None,
	) -> None:
		import lob_engine

		self.symbol = symbol
		self.tick_size = tick_size
		self.max_quantity = max_quantity
		self._next_engine_id = 1
		self._order_id_to_engine_id: dict[str, int] = {}
		self._mid_history: deque[float] = deque(maxlen=8)
		self._last_trade_price = 100.0
		self._recent_trade_qty = 0.0

		self._lob = lob_engine
		if book is not None:
			self._book = book
		else:
			self._book = lob_engine.PyOrderBook(symbol)

	def active_order_count(self) -> int:
		return int(self._book.active_order_count())

	def place_order(self, order_id: str, side: Side, price: float, quantity: float) -> AdapterExecution:
		started = time.perf_counter_ns()
		if quantity <= 0 or quantity > self.max_quantity:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason="quantity violates limits",
				reject_reason=ActionRejectReason.LIMIT_VIOLATION,
				latency_us=self._latency_us(started),
			)
		if price <= 0:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason="price must be positive",
				reject_reason=ActionRejectReason.INVALID_ACTION,
				latency_us=self._latency_us(started),
			)

		engine_id = self._order_id_to_engine_id.get(order_id)
		if engine_id is None:
			engine_id = self._next_engine_id
			self._next_engine_id += 1
			self._order_id_to_engine_id[order_id] = engine_id

		price_tick = self._to_price_tick(price)
		qty_int = self._to_qty_int(quantity)
		best_bid_tick = self._book.best_bid()
		best_ask_tick = self._book.best_ask()
		pre_cross_volume = 0
		fill_price_tick: int | None = None

		try:
			if side is Side.BUY and best_ask_tick is not None and price_tick >= int(best_ask_tick):
				pre_cross_volume = int(self._book.get_volume_at_price(self._lob.PySide.Ask, int(best_ask_tick)))
				fill_price_tick = int(best_ask_tick)
			elif side is Side.SELL and best_bid_tick is not None and price_tick <= int(best_bid_tick):
				pre_cross_volume = int(self._book.get_volume_at_price(self._lob.PySide.Bid, int(best_bid_tick)))
				fill_price_tick = int(best_bid_tick)

			self._book.add_limit_order(engine_id, qty_int, self._to_engine_side(side), price_tick)
		except Exception as exc:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason=f"adapter add_limit_order error: {exc}",
				reject_reason=ActionRejectReason.ADAPTER_ERROR,
				latency_us=self._latency_us(started),
			)

		filled_qty = float(min(qty_int, pre_cross_volume))
		fill_price = self._from_price_tick(fill_price_tick) if fill_price_tick is not None else None
		latency_us = self._latency_us(started)

		if filled_qty <= 0:
			return AdapterExecution(
				status=ExecutionStatus.NONE,
				reason="order accepted and resting",
				latency_us=latency_us,
			)

		self._record_trade(fill_price if fill_price is not None else price, filled_qty)
		if filled_qty >= quantity:
			return AdapterExecution(
				status=ExecutionStatus.FILLED,
				reason="order fully crossed",
				filled_qty=filled_qty,
				fill_price=fill_price,
				latency_us=latency_us,
			)

		return AdapterExecution(
			status=ExecutionStatus.PARTIAL,
			reason="order partially crossed",
			filled_qty=filled_qty,
			fill_price=fill_price,
			latency_us=latency_us,
		)

	def cancel_order(self, order_id: str) -> AdapterExecution:
		started = time.perf_counter_ns()
		engine_id = self._order_id_to_engine_id.get(order_id)
		if engine_id is None:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason="order_id not found",
				reject_reason=ActionRejectReason.ORDER_NOT_FOUND,
				latency_us=self._latency_us(started),
			)

		try:
			canceled = bool(self._book.cancel_order(engine_id))
		except Exception as exc:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason=f"adapter cancel_order error: {exc}",
				reject_reason=ActionRejectReason.ADAPTER_ERROR,
				latency_us=self._latency_us(started),
			)

		if not canceled:
			return AdapterExecution(
				status=ExecutionStatus.REJECTED,
				reason="order already filled or missing",
				reject_reason=ActionRejectReason.ORDER_NOT_FOUND,
				latency_us=self._latency_us(started),
			)

		self._order_id_to_engine_id.pop(order_id, None)
		return AdapterExecution(
			status=ExecutionStatus.NONE,
			reason="order canceled",
			latency_us=self._latency_us(started),
		)

	def snapshot(self) -> AdapterSnapshot:
		best_bid_tick = self._book.best_bid()
		best_ask_tick = self._book.best_ask()

		bid_price = self._from_price_tick(best_bid_tick) if best_bid_tick is not None else max(1.0, self._last_trade_price - self.tick_size)
		ask_price = self._from_price_tick(best_ask_tick) if best_ask_tick is not None else bid_price + self.tick_size
		midpoint = (bid_price + ask_price) / 2.0
		self._mid_history.append(midpoint)

		bid_size = float(self._book.get_volume_at_price(self._lob.PySide.Bid, int(best_bid_tick))) if best_bid_tick is not None else 0.0
		ask_size = float(self._book.get_volume_at_price(self._lob.PySide.Ask, int(best_ask_tick))) if best_ask_tick is not None else 0.0
		total = bid_size + ask_size
		imbalance = ((bid_size - ask_size) / total) if total > 0 else 0.0

		short_return = 0.0
		if len(self._mid_history) >= 2 and self._mid_history[0] > 0:
			short_return = (self._mid_history[-1] - self._mid_history[0]) / self._mid_history[0]

		return AdapterSnapshot(
			bid_price=bid_price,
			ask_price=ask_price,
			bid_size=bid_size,
			ask_size=ask_size,
			midpoint=midpoint,
			imbalance=imbalance,
			short_return=short_return,
			last_trade_price=self._last_trade_price,
			recent_trade_qty=self._recent_trade_qty,
		)

	def _record_trade(self, trade_price: float, qty: float) -> None:
		self._last_trade_price = trade_price
		self._recent_trade_qty = qty

	def _to_engine_side(self, side: Side):
		if side is Side.BUY:
			return self._lob.PySide.Bid
		return self._lob.PySide.Ask

	def _to_price_tick(self, price: float) -> int:
		return max(1, int(round(price / self.tick_size)))

	def _from_price_tick(self, price_tick: int | None) -> float:
		if price_tick is None:
			return self._last_trade_price
		return float(price_tick) * self.tick_size

	def _to_qty_int(self, quantity: float) -> int:
		return max(1, int(round(quantity)))

	def _latency_us(self, started_ns: int) -> int:
		return int((time.perf_counter_ns() - started_ns) / 1000)

