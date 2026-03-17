# Implementation Plan: Phase 1 Pt 2 - Rust/Python Interop (PyO3)

## Objective
Develop PyO3 bindings for the high-performance Rust Limit Order Book (`orderbook-rs`) in the `core/lob-engine` crate. This will allow the Python ecosystem (specifically Mesa for Agent-Based Modeling and RL frameworks) to natively instantiate and interact with the matching engine.

## Background & Motivation
The trading system requires a nanosecond-latency matching engine to accurately simulate market microstructure. By using Rust for the engine and Python for the intelligent agents, we get the best of both worlds: performance and flexibility. However, these systems need a low-latency communication bridge. Native FFI via PyO3 is significantly faster than using IPC (like gRPC or ZeroMQ) because it avoids network stack overhead and heavy serialization.

## Scope & Impact
- **Affected Subsystem:** `core/lob-engine`
- **Changes:**
  - Modify `Cargo.toml` to support PyO3 (adding dependencies and changing the crate type to `cdylib`).
  - Implement Python-compatible wrappers (`#[pyclass]`) for core types: `OrderBook`, `Order`, `OrderType`, `Side`, and `Trade`.
  - Expose a `#[pymodule]` that can be compiled and imported directly into Python (e.g., `import lob_engine`).

## Proposed Solution
1. **Dependency & Build Setup:** 
   - Add `pyo3 = { version = "0.21", features = ["extension-module"] }` to `core/lob-engine/Cargo.toml`.
   - Update `[lib]` to specify `crate-type = ["cdylib", "rlib"]`.

2. **Type Mapping & Wrappers:**
   - **Enums:** Map `orderbook_rs::Side` (Bid/Ask) and `OrderType` (Limit, Market, etc.) to Python enums using `#[pyclass(eq, eq_int)]`.
   - **Structs:** Create PyO3 wrappers for data objects such as `PyOrder` and `PyTrade`. Since Python will need to read these, we will expose their fields using `#[pyo3(get, set)]`.
   - **Engine Wrapper:** Create a `PyOrderBook` struct that holds the underlying `orderbook_rs::OrderBook`. 
     - Expose methods: `add_order`, `cancel_order`, `get_best_bid`, `get_best_ask`, and `get_volume_at_price`.
     - We will handle GIL release using `py.allow_threads(|| ...)` for computationally heavy match operations if needed, though most LOB operations are sub-microsecond.

3. **Module Definition:**
   - Define a `#[pymodule]` named `lob_engine` in `src/lib.rs` and add all classes and enums to it.

## Alternatives Considered
- **gRPC / WebSockets / ZeroMQ:** Avoided due to serialization/deserialization latency and context-switching overhead. FFI is strictly necessary for high-throughput evolutionary runs where millions of orders are simulated per second.
- **Ctypes / CFFI:** Avoided because writing manual C-ABI bindings for Rust is error-prone. PyO3 is much safer, more idiomatic, and provides automatic type conversions.

## Implementation Steps
1. Update `Cargo.toml` with PyO3 configurations.
2. Create `src/bindings.rs` to keep the PyO3 wrapper logic isolated from the core Rust logic.
3. Implement `PySide` and `PyOrderType`.
4. Implement `PyOrder` and `PyTrade` (Execution Reports).
5. Implement `PyOrderBook` with the core `open`, `cancel`, and top-of-book retrieval methods.
6. Register the module in `src/lib.rs`.
7. Configure a minimal `pyproject.toml` using `maturin` to facilitate easy building and installation (`maturin develop`).

## Verification & Testing
- **Compilation:** Ensure `cargo build` and `maturin develop` run without errors.
- **Integration Test:** Write a simple Python script (`tests/test_lob.py`) that:
  - Imports `lob_engine`.
  - Instantiates the `OrderBook`.
  - Submits crossing Bid and Ask orders.
  - Asserts that a trade was generated and the top-of-book reflects the correct remaining size.
- **Performance:** Run a baseline Python benchmark submitting 100,000 orders to ensure the FFI overhead is within acceptable limits (target: < 1-2 microseconds per insertion from Python).

## Migration & Rollback
- Since this is a new feature with no existing Python consumers, there is no migration risk. If PyO3 proves problematic (e.g., GIL contention issues during multi-agent simulations), we can encapsulate the engine in a background Rust thread and communicate with the Python GIL via `crossbeam-channel` or fall back to IPC.