# Phase 2 Sprint 3: Archetype Framework

## Objective
Implement reusable Mesa-compatible archetype policy framework and baseline market participant archetypes.

## Deliverables
- [x] Define archetype policy interface and registration mechanism.
- [x] Implement noise trader archetype.
- [x] Implement momentum trader archetype.
- [x] Implement inventory-aware market maker archetype.
- [x] Add deterministic mode for policy testing.

## Task Breakdown

### 1) Framework design
- [x] Create policy interface with observe and decide stages.
- [x] Define immutable config vs mutable runtime state.
- [x] Add archetype registry and factory creation flow.
- [x] Implement base archetype classes using Mesa Agent inheritance.

### 2) Baseline archetypes
- [x] Noise trader policy with configurable order frequency and size distribution.
- [x] Momentum policy with configurable lookback and threshold behavior.
- [x] Market maker policy with spread target and inventory rebalancing rules.

### 3) Parameter schema for future evolution
- [x] Define parameter objects compatible with Phase 3 genome mapping.
- [x] Add validation constraints for parameter ranges.
- [x] Serialize archetype configs into experiment metadata.

### 4) Deterministic behavior controls
- [x] Provide deterministic random stream assignment per agent.
- [x] Add test mode to force deterministic output for regression tests.

### 5) Test gates
- [x] Unit test: archetype registry resolves expected class by key.
- [x] Unit test: each archetype emits valid action sets.
- [x] Regression test: deterministic mode reproduces exact action traces.

## Acceptance Criteria
- [x] Three archetypes run concurrently with isolated state.
- [x] Archetype parameters are persisted and reproducible across runs.
