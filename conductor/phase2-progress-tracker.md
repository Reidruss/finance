# Phase 2 Progress Tracker

## Goal
Build the ABM foundation so agents can observe market state, decide actions, route to the LOB via Python-Rust bindings, and run deterministic historical simulations.

## Status Dashboard
- [ ] Sprint 1 complete
- [ ] Sprint 2 complete
- [ ] Sprint 3 complete
- [ ] Sprint 4 complete
- [ ] Sprint 5 complete
- [ ] Sprint 6 complete
- [ ] Phase 2 exit criteria validated

## Sprint Files
- [phase2-sprint1-core-abm-skeleton.md](phase2-sprint1-core-abm-skeleton.md)
- [phase2-sprint2-market-bridge-state.md](phase2-sprint2-market-bridge-state.md)
- [phase2-sprint3-archetype-framework.md](phase2-sprint3-archetype-framework.md)
- [phase2-sprint4-scheduler-multi-agent.md](phase2-sprint4-scheduler-multi-agent.md)
- [phase2-sprint5-data-driven-runner.md](phase2-sprint5-data-driven-runner.md)
- [phase2-sprint6-hardening-handoff.md](phase2-sprint6-hardening-handoff.md)

## Phase 2 Exit Criteria
- [ ] At least 3 archetypes run in the same simulation with stable behavior.
- [ ] Full episode replay works against historical slices.
- [ ] Reproducibility validated with fixed seed.
- [ ] Throughput and memory benchmark targets met.
- [ ] Integration tests cover scheduler, agent lifecycle, and LOB/friction path.

## Notes
- Keep all new interfaces stable after Sprint 4 unless change is strictly required.
- Record benchmark numbers and deterministic replay hashes in Sprint 6.
