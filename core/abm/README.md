# Core ABM Package

This package contains the Agent-Based Modeling (ABM) engine for the trading simulation, built on top of the Mesa framework. It enforces a strict deterministic execution loop for reliable backtesting and strategy evaluation.

## Design Boundaries
- **Domain:** Defines the fundamental types (Observation, Action, ExecutionReport, AgentAccountSnapshot) and the base Mesa wrappers. It holds no business logic.
- **Runner:** Contains the Mesa `Model` shell. It is responsible for the episode loop, seeding, and advancing the global state.
- **Scheduler:** Manages the deterministic activation order of agents.
- **Policies:** Contains the actual decision-making logic for agents mapping Observations to Actions.
- **Adapters:** Translates external data (historical order books, synthetic price feeds) into standard `Observation` contracts for the runner.

## Core Contracts
Agents strictly interact with the environment via pass-by-value contracts. An agent receives an `Observation` at the start of its step and returns an `Action` (place, cancel, hold). The model processes these actions and resolves them into `ExecutionReport`s, which update the `AgentAccountSnapshot`.

## Sprint 1 Components
- `domain/contracts.py`: canonical observation/action/execution/account contracts with runtime validation.
- `domain/agent.py`: Mesa `Agent` wrapper that runs a typed policy with deterministic RNG.
- `runner/seeding.py`: global seed normalization and per-agent seed derivation.
- `scheduler/deterministic.py`: stable activation order based on sorted agent ids.
- `runner/model.py`: minimal deterministic episode loop with synthetic market ticks and telemetry.
- `policies/noop.py`: no-op policy for smoke tests and demo runs.

## Quick Run
From repository root with `.venv` active:

```bash
python -m core.abm.runner.demo
pytest core/abm/tests -q
```