from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from core.abm.domain.contracts import Action, Observation, Side


@dataclass(frozen=True)
class ArchetypeParameter:
    """Named parameter spec used by config/genome mapping layers."""

    name: str
    min_value: float
    max_value: float
    default_value: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("parameter name is required")
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        if not (self.min_value <= self.default_value <= self.max_value):
            raise ValueError("default_value must be inside [min_value, max_value]")

    def to_dict(self) -> dict[str, float | str]:
        return {
            "name": self.name,
            "min": self.min_value,
            "max": self.max_value,
            "default": self.default_value,
        }


@dataclass(frozen=True)
class ArchetypeConfig:
    deterministic_mode: bool = False

    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def parameter_schema(cls) -> tuple[ArchetypeParameter, ...]:
        raise NotImplementedError

    @abstractmethod
    def to_metadata(self) -> dict[str, object]:
        raise NotImplementedError


@dataclass
class NoiseTraderState:
    step: int = 0
    order_seq: int = 0


@dataclass
class MomentumTraderState:
    step: int = 0
    order_seq: int = 0
    prices: deque[float] = field(default_factory=deque)


@dataclass
class MarketMakerState:
    step: int = 0
    order_seq: int = 0


class BaseArchetypePolicy(ABC):
    """Two-stage policy interface: observe first, then decide."""

    def __init__(self, config: ArchetypeConfig) -> None:
        self.config = config
        self._stream_rng: random.Random | None = None

    def set_random_stream(self, rng: random.Random) -> None:
        self._stream_rng = rng

    def __call__(self, observation: Observation, rng: random.Random) -> Action:
        self.observe(observation)
        active_rng = self._stream_rng if self.config.deterministic_mode and self._stream_rng is not None else rng
        return self.decide(observation, active_rng)

    @abstractmethod
    def observe(self, observation: Observation) -> None:
        raise NotImplementedError

    @abstractmethod
    def decide(self, observation: Observation, rng: random.Random) -> Action:
        raise NotImplementedError


@dataclass(frozen=True)
class NoiseTraderConfig(ArchetypeConfig):
    order_probability: float = 0.35
    min_quantity: float = 0.5
    max_quantity: float = 3.0
    price_jitter_bps: float = 5.0

    @property
    def key(self) -> str:
        return "noise"

    def __post_init__(self) -> None:
        if not (0.0 <= self.order_probability <= 1.0):
            raise ValueError("order_probability must be in [0, 1]")
        if self.min_quantity <= 0:
            raise ValueError("min_quantity must be positive")
        if self.max_quantity < self.min_quantity:
            raise ValueError("max_quantity must be >= min_quantity")
        if self.price_jitter_bps < 0:
            raise ValueError("price_jitter_bps must be non-negative")

    @classmethod
    def parameter_schema(cls) -> tuple[ArchetypeParameter, ...]:
        return (
            ArchetypeParameter("order_probability", 0.0, 1.0, 0.35),
            ArchetypeParameter("min_quantity", 0.01, 20.0, 0.5),
            ArchetypeParameter("max_quantity", 0.01, 50.0, 3.0),
            ArchetypeParameter("price_jitter_bps", 0.0, 100.0, 5.0),
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "archetype": self.key,
            "deterministic_mode": self.deterministic_mode,
            "params": {
                "order_probability": self.order_probability,
                "min_quantity": self.min_quantity,
                "max_quantity": self.max_quantity,
                "price_jitter_bps": self.price_jitter_bps,
            },
            "schema": [p.to_dict() for p in self.parameter_schema()],
        }


class NoiseTraderPolicy(BaseArchetypePolicy):
    def __init__(self, config: NoiseTraderConfig) -> None:
        super().__init__(config)
        self.state = NoiseTraderState()

    @property
    def _cfg(self) -> NoiseTraderConfig:
        return self.config  # type: ignore[return-value]

    def observe(self, observation: Observation) -> None:
        _ = observation
        self.state.step += 1

    def decide(self, observation: Observation, rng: random.Random) -> Action:
        if self._cfg.deterministic_mode:
            should_trade = (self.state.step % 2) == 0
        else:
            should_trade = rng.random() <= self._cfg.order_probability
        if not should_trade:
            return Action.hold()

        side = Side.BUY if (self.state.step % 2 == 0) else Side.SELL
        mid = (observation.market.bid_price + observation.market.ask_price) / 2.0
        if self._cfg.deterministic_mode:
            quantity = (self._cfg.min_quantity + self._cfg.max_quantity) / 2.0
            price = observation.market.bid_price if side is Side.BUY else observation.market.ask_price
        else:
            quantity = rng.uniform(self._cfg.min_quantity, self._cfg.max_quantity)
            jitter = (rng.uniform(-1.0, 1.0) * self._cfg.price_jitter_bps) / 10_000.0
            price = max(0.01, mid * (1.0 + jitter))

        self.state.order_seq += 1
        return Action.place(
            side=side,
            price=price,
            quantity=quantity,
            order_id=f"noise-{self.state.order_seq}",
        )


@dataclass(frozen=True)
class MomentumTraderConfig(ArchetypeConfig):
    lookback: int = 3
    threshold_bps: float = 3.0
    quantity: float = 1.0

    @property
    def key(self) -> str:
        return "momentum"

    def __post_init__(self) -> None:
        if self.lookback < 2:
            raise ValueError("lookback must be >= 2")
        if self.threshold_bps < 0:
            raise ValueError("threshold_bps must be non-negative")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    @classmethod
    def parameter_schema(cls) -> tuple[ArchetypeParameter, ...]:
        return (
            ArchetypeParameter("lookback", 2, 128, 3),
            ArchetypeParameter("threshold_bps", 0.0, 500.0, 3.0),
            ArchetypeParameter("quantity", 0.01, 100.0, 1.0),
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "archetype": self.key,
            "deterministic_mode": self.deterministic_mode,
            "params": {
                "lookback": self.lookback,
                "threshold_bps": self.threshold_bps,
                "quantity": self.quantity,
            },
            "schema": [p.to_dict() for p in self.parameter_schema()],
        }


class MomentumTraderPolicy(BaseArchetypePolicy):
    def __init__(self, config: MomentumTraderConfig) -> None:
        super().__init__(config)
        self.state = MomentumTraderState()

    @property
    def _cfg(self) -> MomentumTraderConfig:
        return self.config  # type: ignore[return-value]

    def observe(self, observation: Observation) -> None:
        self.state.step += 1
        price = observation.market.last_trade_price
        self.state.prices.append(price)
        while len(self.state.prices) > self._cfg.lookback:
            self.state.prices.popleft()

    def decide(self, observation: Observation, rng: random.Random) -> Action:
        _ = rng
        if len(self.state.prices) < self._cfg.lookback:
            return Action.hold()

        first = self.state.prices[0]
        last = self.state.prices[-1]
        if first <= 0:
            return Action.hold()

        ret_bps = ((last - first) / first) * 10_000.0
        if ret_bps > self._cfg.threshold_bps:
            side = Side.BUY
            ref_px = observation.market.ask_price
        elif ret_bps < -self._cfg.threshold_bps:
            side = Side.SELL
            ref_px = observation.market.bid_price
        else:
            return Action.hold()

        self.state.order_seq += 1
        return Action.place(
            side=side,
            price=max(0.01, ref_px),
            quantity=self._cfg.quantity,
            order_id=f"mom-{self.state.order_seq}",
        )


@dataclass(frozen=True)
class MarketMakerConfig(ArchetypeConfig):
    spread_bps: float = 10.0
    quote_quantity: float = 1.0
    inventory_skew_bps: float = 2.0
    inventory_target: float = 0.0

    @property
    def key(self) -> str:
        return "market_maker"

    def __post_init__(self) -> None:
        if self.spread_bps < 0:
            raise ValueError("spread_bps must be non-negative")
        if self.quote_quantity <= 0:
            raise ValueError("quote_quantity must be positive")
        if self.inventory_skew_bps < 0:
            raise ValueError("inventory_skew_bps must be non-negative")

    @classmethod
    def parameter_schema(cls) -> tuple[ArchetypeParameter, ...]:
        return (
            ArchetypeParameter("spread_bps", 0.0, 500.0, 10.0),
            ArchetypeParameter("quote_quantity", 0.01, 100.0, 1.0),
            ArchetypeParameter("inventory_skew_bps", 0.0, 100.0, 2.0),
            ArchetypeParameter("inventory_target", -1000.0, 1000.0, 0.0),
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "archetype": self.key,
            "deterministic_mode": self.deterministic_mode,
            "params": {
                "spread_bps": self.spread_bps,
                "quote_quantity": self.quote_quantity,
                "inventory_skew_bps": self.inventory_skew_bps,
                "inventory_target": self.inventory_target,
            },
            "schema": [p.to_dict() for p in self.parameter_schema()],
        }


class InventoryAwareMarketMakerPolicy(BaseArchetypePolicy):
    def __init__(self, config: MarketMakerConfig) -> None:
        super().__init__(config)
        self.state = MarketMakerState()

    @property
    def _cfg(self) -> MarketMakerConfig:
        return self.config  # type: ignore[return-value]

    def observe(self, observation: Observation) -> None:
        _ = observation
        self.state.step += 1

    def decide(self, observation: Observation, rng: random.Random) -> Action:
        mid = (observation.market.bid_price + observation.market.ask_price) / 2.0
        inventory = float(observation.features.get("inventory", self._cfg.inventory_target))
        inv_delta = inventory - self._cfg.inventory_target

        spread = (self._cfg.spread_bps / 10_000.0) * mid
        skew = (self._cfg.inventory_skew_bps / 10_000.0) * mid * inv_delta

        bid_px = max(0.01, mid - spread - skew)
        ask_px = max(0.01, mid + spread - skew)

        if self._cfg.deterministic_mode:
            side = Side.BUY if inv_delta < 0 else Side.SELL
        else:
            side = Side.BUY if rng.random() < 0.5 else Side.SELL

        quote_px = bid_px if side is Side.BUY else ask_px
        self.state.order_seq += 1
        return Action.place(
            side=side,
            price=quote_px,
            quantity=self._cfg.quote_quantity,
            order_id=f"mm-{self.state.order_seq}",
        )


class ArchetypeRegistry:
    def __init__(self) -> None:
        self._constructors: dict[str, Callable[[ArchetypeConfig], BaseArchetypePolicy]] = {}

    def register(self, key: str, constructor: Callable[[ArchetypeConfig], BaseArchetypePolicy]) -> None:
        if not key:
            raise ValueError("registry key is required")
        self._constructors[key] = constructor

    def create(self, key: str, config: ArchetypeConfig) -> BaseArchetypePolicy:
        if key not in self._constructors:
            raise KeyError(f"unknown archetype key: {key}")
        return self._constructors[key](config)

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._constructors.keys()))


DEFAULT_ARCHETYPE_REGISTRY = ArchetypeRegistry()
DEFAULT_ARCHETYPE_REGISTRY.register("noise", lambda c: NoiseTraderPolicy(cast_config(c, NoiseTraderConfig)))
DEFAULT_ARCHETYPE_REGISTRY.register("momentum", lambda c: MomentumTraderPolicy(cast_config(c, MomentumTraderConfig)))
DEFAULT_ARCHETYPE_REGISTRY.register("market_maker", lambda c: InventoryAwareMarketMakerPolicy(cast_config(c, MarketMakerConfig)))


def cast_config(config: ArchetypeConfig, expected: type[ArchetypeConfig]) -> ArchetypeConfig:
    if not isinstance(config, expected):
        raise TypeError(f"expected config type {expected.__name__}, got {type(config).__name__}")
    return config


def create_archetype_policy(
    archetype_key: str,
    config: ArchetypeConfig,
    registry: ArchetypeRegistry | None = None,
) -> BaseArchetypePolicy:
    active_registry = registry or DEFAULT_ARCHETYPE_REGISTRY
    return active_registry.create(archetype_key, config)


__all__ = [
    "ArchetypeConfig",
    "ArchetypeParameter",
    "ArchetypeRegistry",
    "BaseArchetypePolicy",
    "DEFAULT_ARCHETYPE_REGISTRY",
    "InventoryAwareMarketMakerPolicy",
    "MarketMakerConfig",
    "MomentumTraderConfig",
    "MomentumTraderPolicy",
    "NoiseTraderConfig",
    "NoiseTraderPolicy",
    "create_archetype_policy",
]
