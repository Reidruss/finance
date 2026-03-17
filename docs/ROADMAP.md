# Roadmap for Evolutionary Trading System

## Phase 1: Core Infrastructure & Data Engineering
- **Limit Order Book (LOB):** Integrate and validate the 3rd-party `orderbook-rs` matching engine.
- **Rust/Python Interop:** Develop PyO3 bindings (`core/lob-engine`) to allow the Python ecosystem to interact with the high-performance Rust LOB.
- **Data Ingestion Pipeline:** Build the tick data pipeline (`data/ingest`) to feed historical data into the system.
- **Data Storage:** Implement partitioned Parquet/Arrow storage (`data/store`) for efficient read/write of market data during simulations.
- **Friction Models:** Implement realistic fee and slippage models (`core/friction`) to ensure simulations reflect real-world trading costs.

## Phase 2: Agent-Based Modeling (ABM) Foundation
- **Mesa Integration:** Set up the Python/Mesa environment (`core/abm`) for agent scheduling and interaction.
- **Archetypes:** Define base agent templates (`genome/archetypes`) representing different market participants (e.g., market makers, noise traders, momentum traders).
- **Agent Scheduling:** Develop the engine to step agents through time, allowing them to observe the LOB and submit orders via the PyO3 bindings.

## Phase 3: Evolutionary Primitives & Genome Design
- **Genetic Representation:**
  - Implement fixed-parameter DNA arrays (`genome/encoding`) for simple continuous/discrete traits.
  - Implement Strongly Typed Genetic Programming (AST-GP) trees (`genome/ast-gp`) for evolving complex trading logic and expressions.
- **Evolutionary Operators:**
  - **Mutation:** Gaussian perturbation for arrays, subtree mutation for ASTs (`evolution/mutation`).
  - **Crossover:** Simulated Binary Crossover (SBX) for arrays, subtree crossover for ASTs (`evolution/crossover`).
- **Selection Mechanisms:** Implement tournament and fitness ranking selection (`evolution/selection`).
- **Fitness Evaluation:** Develop evaluators based on risk-adjusted metrics like Sortino and Calmar ratios (`evolution/fitness`).

## Phase 4: Machine Learning & Regime Control
- **Market Regime Classification:** Train HMM/GMM classifiers (`ml/regime`) to identify latent market states (e.g., high volatility, trending, mean-reverting).
- **Regime-Specific Gene Pools:** Establish separate evolved populations tailored to perform optimally in specific market regimes (`ml/gene-pools`).
- **RL Meta-Controller:** Develop a Reinforcement Learning agent (`ml/rl-controller`) responsible for switching between regime-specific gene pools dynamically based on real-time market conditions.

## Phase 5: High-Performance Computing (HPC) & Scaling
- **Distributed Fitness Evaluation:** Implement MPI workers (`hpc/mpi-workers`) to parallelize the computationally expensive fitness evaluation across a cluster.
- **SLURM Integration:** Create job scripts (`hpc/cluster-config`) for deployment on ISAAC-NG or similar supercomputing clusters.
- **GPU Acceleration:** Offload RL and HMM training tasks to H100 GPUs (`hpc/gpu-tasks`) to accelerate learning.

## Phase 6: Validation & Reporting
- **Walk-Forward Analysis:** Implement a robust k-fold rolling out-of-sample testing pipeline (`validation/walk-forward`) to prevent overfitting.
- **Reporting & Metrics:** Build comprehensive reporting tools (`validation/reporting`) to break down performance by market regime and provide detailed strategy metrics.
- **Experiment Configuration:** Finalize the YAML-based experiment definition system (`config/experiments`) for reproducible research runs.