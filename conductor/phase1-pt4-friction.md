# Implementation Plan: Phase 1 Pt 4 - Friction Models

## Objective
Implement realistic fee and slippage models in the `core/friction` module to ensure that simulations accurately reflect the real-world costs of trading. This is critical for preventing the evolution of "over-optimized" strategies that ignore market frictions.

## Background & Motivation
In high-frequency or high-volume trading simulations, ignoring small costs like exchange fees or subtle slippage leads to inflated performance metrics. For an evolutionary system, this is dangerous: the "fitness" of agents will be driven by their ability to exploit zero-cost transactions, which do not exist in reality. We need modular friction models that can be swapped depending on the exchange being simulated (e.g., Binance, Coinbase, or decentralized exchanges).

## Scope & Impact
- **Affected Subsystem:** `core/friction`
- **Language:** Rust (for performance and direct integration with `lob-engine`).
- **Functionality:**
  - Define a common `FrictionModel` trait.
  - Implement a `FixedFeeModel` (e.g., 10 basis points per trade).
  - Implement a `TieredFeeModel` (maker/taker rebates and tiers).
  - Implement a `LatencySlippageModel` (stochastic order execution delay).

## Proposed Solution

### 1. The `FrictionModel` Trait
Define a Rust trait that takes a trade execution and calculates the total cost.
- **Input:** `Trade` (from `lob-engine`), `Side`, `OrderType`.
- **Output:** `FrictionResult` (including `fee_cost` and `estimated_slippage`).

### 2. Fee Models
- **Percentage-based:** A simple `x%` of notional value.
- **Maker/Taker:** Different rates for orders that provide liquidity (maker) vs. those that take it (taker).

### 3. Slippage Models (Stochastic)
While `lob-engine` handles price-impact slippage, we need to model:
- **Execution Latency:** Modeling a random delay between order submission and matching. If the best bid/ask moves during this window, the agent suffers slippage.

## Implementation Steps
1. Create a new Rust crate in `core/friction`.
2. Define the `FrictionModel` trait.
3. Implement `SimpleFeeModel`.
4. Integrate with the existing `PyOrderBook` or create a new `FrictionEvaluator` that can be used from Python.
5. Add unit tests verifying that fees are correctly calculated for various trade sizes and sides.

## Verification & Testing
- **Unit Tests:** Verify that a 10bps fee on a $50,000 trade results in exactly $50.
- **Regression:** Ensure that adding friction doesn't break the existing `lob-engine` tests.
- **Agent Integration:** Create a small Python script to verify that agents can query their "realized profit" after accounting for friction.
