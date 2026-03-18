from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class ActionType(str, Enum):
    PLACE = "place"
    CANCEL = "cancel"
    HOLD = "hold"


class ExecutionStatus(str, Enum):
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    NONE = "none"


class ActionRejectReason(str, Enum):
    NONE = "none"
    INVALID_ACTION = "invalid_action"
    LIMIT_VIOLATION = "limit_violation"
    ORDER_NOT_FOUND = "order_not_found"
    ADAPTER_ERROR = "adapter_error"


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float = 0.0
    ask_size: float = 0.0
    last_trade_price: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.bid_price <= 0 or self.ask_price <= 0:
            raise ValueError("bid_price and ask_price must be positive")
        if self.bid_price > self.ask_price:
            raise ValueError("bid_price cannot exceed ask_price")


@dataclass(frozen=True)
class Observation:
    timestamp_ns: int
    market: MarketSnapshot
    features: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be non-negative")
        for name, value in self.features.items():
            if not isinstance(name, str):
                raise TypeError("feature names must be strings")
            if not isinstance(value, (int, float)):
                raise TypeError("feature values must be numeric")


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    side: Side | None = None
    price: float | None = None
    quantity: float | None = None
    order_id: str | None = None

    @classmethod
    def hold(cls) -> "Action":
        return cls(action_type=ActionType.HOLD)

    @classmethod
    def place(cls, side: Side, price: float, quantity: float, order_id: str) -> "Action":
        return cls(
            action_type=ActionType.PLACE,
            side=side,
            price=price,
            quantity=quantity,
            order_id=order_id,
        )

    @classmethod
    def cancel(cls, order_id: str) -> "Action":
        return cls(action_type=ActionType.CANCEL, order_id=order_id)

    def __post_init__(self) -> None:
        if self.action_type is ActionType.PLACE:
            if self.side is None:
                raise ValueError("place action requires side")
            if self.price is None or self.price <= 0:
                raise ValueError("place action requires positive price")
            if self.quantity is None or self.quantity <= 0:
                raise ValueError("place action requires positive quantity")
            if not self.order_id:
                raise ValueError("place action requires order_id")
        elif self.action_type is ActionType.CANCEL:
            if not self.order_id:
                raise ValueError("cancel action requires order_id")
        elif self.action_type is ActionType.HOLD:
            if any(v is not None for v in (self.side, self.price, self.quantity, self.order_id)):
                raise ValueError("hold action cannot contain order fields")


@dataclass(frozen=True)
class ExecutionReport:
    agent_id: str
    order_id: str | None
    status: ExecutionStatus
    side: Side | None = None
    requested_qty: float = 0.0
    filled_qty: float = 0.0
    fill_price: float | None = None
    reason: str = ""
    reject_reason: ActionRejectReason = ActionRejectReason.NONE
    fee_cost: float = 0.0
    slippage_cost: float = 0.0
    latency_us: int = 0

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise ValueError("agent_id is required")
        if self.requested_qty < 0:
            raise ValueError("requested_qty cannot be negative")
        if self.filled_qty < 0:
            raise ValueError("filled_qty cannot be negative")
        if self.fill_price is not None and self.fill_price <= 0:
            raise ValueError("fill_price must be positive when provided")
        if self.fee_cost < 0 or self.slippage_cost < 0:
            raise ValueError("fee_cost and slippage_cost cannot be negative")
        if self.latency_us < 0:
            raise ValueError("latency_us cannot be negative")


@dataclass(frozen=True)
class AgentAccountSnapshot:
    agent_id: str
    cash: float
    inventory: float
    realized_pnl: float
    unrealized_pnl: float

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise ValueError("agent_id is required")
