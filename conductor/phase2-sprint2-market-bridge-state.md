# Phase 2 Sprint 2: Market Bridge and State Hydration

## Objective
Connect ABM actions to the Rust LOB path and hydrate agent observations from market state.

## Deliverables
- [ ] Implement ABM to LOB adapter.
- [ ] Convert ABM actions to order add/cancel calls.
- [ ] Build observation hydrator from top-of-book, depth, and trade stream.
- [ ] Integrate friction-aware accounting updates.
- [ ] Add integration tests for order lifecycle.

## Task Breakdown

### 1) Market adapter
- [ ] Implement adapter interface for add/cancel/query operations.
- [ ] Add robust error handling and reason codes for rejected actions.
- [ ] Capture latency metrics around adapter calls.

### 2) Action translation
- [ ] Map place actions to engine order format.
- [ ] Map cancel actions to engine cancel format.
- [ ] Validate action limits before routing.

### 3) Observation hydration
- [ ] Build market snapshot extractor from LOB state.
- [ ] Include spread, midpoint, imbalance, and short return features.
- [ ] Attach recent trade context to observations.

### 4) Friction-aware accounting
- [ ] Apply fee/slippage model outputs to realized PnL.
- [ ] Separate realized and unrealized updates per step.
- [ ] Add reasoned logging for accounting deltas.

### 5) Test gates
- [ ] Integration test: place and cancel behavior updates book as expected.
- [ ] Integration test: crossing orders produce fills and account deltas.
- [ ] Unit test: friction adjustment math for representative scenarios.

## Acceptance Criteria
- [ ] Single agent can place, cancel, and receive fills through real adapter path.
- [ ] Observation payloads are complete and consistent at each step.
