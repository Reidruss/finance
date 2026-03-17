# Phase 2 Sprint 5: Data-Driven Episode Runner

## Objective
Connect ABM runner to historical datasets and experiment configs for reproducible scenario execution.

## Deliverables
- [ ] Load historical market slices from data/store.
- [ ] Implement scenario loader for symbol/date/warmup/episode-length.
- [ ] Integrate YAML experiment config path.
- [ ] Capture per-step and per-episode metrics.
- [ ] Add end-to-end replay tests.

## Task Breakdown

### 1) Data integration
- [ ] Build loader for partitioned historical slices.
- [ ] Validate schema compatibility before episode start.
- [ ] Enforce monotonic time ordering in loaded events.

### 2) Scenario loader
- [ ] Add symbol/date selector.
- [ ] Add warmup window support.
- [ ] Add episode length and max-step controls.

### 3) Experiment configuration
- [ ] Define ABM experiment schema in config/experiments.
- [ ] Validate required fields and defaults.
- [ ] Persist config hash in run metadata.

### 4) Metrics pipeline
- [ ] Record PnL decomposition, inventory, turnover, and fill quality.
- [ ] Emit both per-agent and aggregate metrics.
- [ ] Write run summaries for later fitness consumption.

### 5) Test gates
- [ ] Integration test: real historical slice drives full episode.
- [ ] Validation test: malformed config fails with clear errors.
- [ ] Regression test: fixed seed + fixed slice produces stable summary.

## Acceptance Criteria
- [ ] End-to-end ABM run works with historical data and configuration file only.
- [ ] Metrics output is complete enough for Phase 3 fitness modules.
