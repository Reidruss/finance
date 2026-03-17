# Phase 2 Sprint 4: Scheduler and Multi-Agent Dynamics

## Objective
Build deterministic, configurable scheduling for multi-agent interactions and event-time stepping.

## Deliverables
- [ ] Implement scheduler modes: sequential, seeded-random, role-priority.
- [ ] Define intra-step event ordering contract.
- [ ] Handle timing conflicts and cancellation semantics.
- [ ] Add event-time and fixed-step clock modes.
- [ ] Add runtime profiling hooks.

## Task Breakdown

### 1) Scheduler modes
- [ ] Implement sequential activation.
- [ ] Implement seeded-random activation.
- [ ] Implement role-priority activation.

### 2) Step ordering contract
- [ ] Ingest market updates.
- [ ] Refresh observations.
- [ ] Schedule and execute agent decisions.
- [ ] Route and process actions.
- [ ] Settle accounts and emit metrics.

### 3) Conflict and timing rules
- [ ] Define tie-break behavior for same-tick submissions.
- [ ] Define cancellation timing semantics.
- [ ] Add explicit audit records for conflict resolution outcomes.

### 4) Clock models
- [ ] Implement event-time stepping from historical stream.
- [ ] Implement optional fixed-delta stepping.
- [ ] Ensure deterministic transitions between clock modes.

### 5) Profiling and observability
- [ ] Record per-step total runtime.
- [ ] Record per-agent decision latency.
- [ ] Record adapter routing latency.

### 6) Test gates
- [ ] Unit test: scheduler mode ordering rules.
- [ ] Integration test: multi-agent same-tick conflict behavior.
- [ ] Regression test: deterministic replay hash stability.

## Acceptance Criteria
- [ ] Multi-agent episodes are deterministic and auditable.
- [ ] Scheduler mode can be selected by config without code changes.
