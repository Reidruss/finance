# Phase 2 Sprint 3: Archetype Framework

## Objective
Implement reusable Mesa-compatible archetype policy framework and baseline market participant archetypes.

## Deliverables
- [ ] Define archetype policy interface and registration mechanism.
- [ ] Implement noise trader archetype.
- [ ] Implement momentum trader archetype.
- [ ] Implement inventory-aware market maker archetype.
- [ ] Add deterministic mode for policy testing.

## Task Breakdown

### 1) Framework design
- [ ] Create policy interface with observe and decide stages.
- [ ] Define immutable config vs mutable runtime state.
- [ ] Add archetype registry and factory creation flow.
- [ ] Implement base archetype classes using Mesa Agent inheritance.

### 2) Baseline archetypes
- [ ] Noise trader policy with configurable order frequency and size distribution.
- [ ] Momentum policy with configurable lookback and threshold behavior.
- [ ] Market maker policy with spread target and inventory rebalancing rules.

### 3) Parameter schema for future evolution
- [ ] Define parameter objects compatible with Phase 3 genome mapping.
- [ ] Add validation constraints for parameter ranges.
- [ ] Serialize archetype configs into experiment metadata.

### 4) Deterministic behavior controls
- [ ] Provide deterministic random stream assignment per agent.
- [ ] Add test mode to force deterministic output for regression tests.

### 5) Test gates
- [ ] Unit test: archetype registry resolves expected class by key.
- [ ] Unit test: each archetype emits valid action sets.
- [ ] Regression test: deterministic mode reproduces exact action traces.

## Acceptance Criteria
- [ ] Three archetypes run concurrently with isolated state.
- [ ] Archetype parameters are persisted and reproducible across runs.
