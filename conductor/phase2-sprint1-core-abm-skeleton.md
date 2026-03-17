# Phase 2 Sprint 1: Core ABM Skeleton

## Objective
Create the base Mesa ABM package structure and deterministic simulation shell.

## Deliverables
- [ ] Create package layout in core/abm.
- [ ] Add Mesa dependency and pin version in project configuration.
- [ ] Define canonical contracts for observation, action, execution report, and account snapshot.
- [ ] Implement deterministic seed management utilities.
- [ ] Implement a minimal episode loop with one no-op agent.
- [ ] Add unit tests for schema validation and seed reproducibility.

## Task Breakdown

### 1) Package and module structure
- [ ] Create core/abm package with clear submodules for domain, policies, scheduler, adapters, and runner.
- [ ] Add module-level README describing contracts and design boundaries.
- [ ] Create Mesa model shell and base agent class wrappers.

### 2) Domain contracts
- [ ] Define Observation type with market snapshot and feature fields.
- [ ] Define Action type with place/cancel/hold semantics.
- [ ] Define Fill/ExecutionReport type with enough detail for accounting.
- [ ] Define AgentAccountSnapshot with realized/unrealized PnL and inventory.

### 3) Deterministic controls
- [ ] Implement global simulation seed plumbing.
- [ ] Derive per-agent random streams from global seed.
- [ ] Add deterministic iteration ordering in collections.

### 4) Minimal simulation loop
- [ ] Build basic step loop with synthetic market state input.
- [ ] Register one no-op agent and execute full episode.
- [ ] Wire minimal Mesa Model.step flow to deterministic seed plumbing.
- [ ] Emit basic per-step telemetry.

### 5) Test gates
- [ ] Unit test: identical seed produces identical action sequence.
- [ ] Unit test: schema contracts reject malformed values.
- [ ] Unit test: no-op episode completes without errors.
- [ ] Integration test: Mesa model bootstraps and steps one tick with no agents failing.

## Acceptance Criteria
- [ ] Sprint 1 demo script runs end-to-end.
- [ ] Test suite for Sprint 1 passes in CI/local.
