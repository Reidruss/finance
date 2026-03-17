# Core ABM Package

This package contains the Agent-Based Modeling (ABM) engine for the trading simulation, built on top of the Mesa framework. It enforces a strict deterministic execution loop for reliable backtesting and strategy evaluation.

## Environment Convention
Use the single repository-level Python virtual environment at `.venv/` (repo root).
Do not create or use a nested environment in `core/abm/.venv`.
Setup and migration steps are documented in `docs/PYTHON_ENVIRONMENT.md`.

## Design Boundaries
- **Domain:** Defines the fundamental types (Observation, Action, ExecutionReport, AgentAccountSnapshot) and the base Mesa wrappers. It holds no business logic.
- **Runner:** Contains the Mesa `Model` shell. It is responsible for the episode loop, seeding, and advancing the global state.
- **Scheduler:** Manages the deterministic activation order of agents.
- **Policies:** Contains the actual decision-making logic for agents mapping Observations to Actions.
- **Adapters:** Translates external data (historical order books, synthetic price feeds) into standard `Observation` contracts for the runner.

## Core Contracts
Agents strictly interact with the environment via pass-by-value contracts. An agent receives an `Observation` at the start of its step and returns an `Action` (place, cancel, hold). The model processes these actions and resolves them into `ExecutionReport`s, which update the `AgentAccountSnapshot`.