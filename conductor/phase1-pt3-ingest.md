# Implementation Plan: Phase 1 Pt 3 - Data Ingestion Pipeline

## Objective
Develop a high-performance data ingestion pipeline in Python using `polars` to parse, normalize, and store historical Level 2 (L2) tick data and trades into a partitioned Parquet/Arrow format. This standardized data will feed the evolutionary simulation engine.

## Background & Motivation
The Agent-Based Model and limit order book simulations require accurate historical market data to recreate realistic trading environments. Raw data from providers (like Binance, Tardis, or Databento) often comes in disparate formats, messy CSVs, or JSON files. Normalizing this data into a strict binary format like Parquet ensures lightning-fast read speeds during distributed backtests and reduces storage footprint. Python with `polars` is chosen for its multi-threaded, out-of-core processing capabilities, bridging the gap between ease of development and high performance.

## Scope & Impact
- **Affected Subsystems:** `data/ingest`, `data/store`
- **Data Granularity:** Level 2 (L2) market depth updates (price, size, side) and public trades.
- **Language/Tooling:** Python, `polars`, `pyarrow`.
- **Changes:**
  - Create standard schema definitions for Trades and L2 Book Updates.
  - Develop parser scripts for transforming raw historical CSV/JSON files into the standard schemas.
  - Implement a storage writer that partitions the output Parquet files by `symbol` and `date`.

## Proposed Solution

### 1. Define Standard Schemas
We need a unified representation of market events.
- **Trade Schema:**
  - `timestamp` (Int64, epoch nanoseconds)
  - `symbol` (String/Categorical)
  - `side` (String/Categorical - 'bid' or 'ask')
  - `price` (Float64)
  - `size` (Float64)
  - `trade_id` (String)

- **L2 Book Update Schema:**
  - `timestamp` (Int64, epoch nanoseconds)
  - `symbol` (String/Categorical)
  - `side` (String/Categorical - 'bid' or 'ask')
  - `price` (Float64)
  - `size` (Float64 - 0 indicates a deletion/cancellation)
  - `is_snapshot` (Boolean - True if this is a full book rebuild, False for incremental updates)

### 2. The Ingestion Engine (`data/ingest`)
Create a Python module (`data/ingest/pipeline.py`) leveraging Polars:
- **Reader Modules:** Abstract base classes with specific implementations for different vendor formats (e.g., `BinanceCsvReader`, `TardisCsvReader`).
- **Transformation Pipeline:** Polars `LazyFrame` operations to map vendor-specific columns to our standard schema, cast data types, handle missing values, and sort chronologically.

### 3. The Storage Writer (`data/store`)
Create a Python module (`data/store/writer.py`):
- Takes the normalized Polars DataFrame.
- Uses `pyarrow.parquet.write_to_dataset` (or Polars native sink) to save the data.
- **Partitioning Strategy:** Save files partitioned by `symbol=XYZ` and `date=YYYY-MM-DD` (e.g., `data/store/l2_updates/symbol=BTC-USD/date=2024-01-01/data.parquet`). This allows the simulation engine to lazily load only the necessary days and pairs without scanning the whole dataset.

## Implementation Steps
1. Initialize a `pyproject.toml` or `requirements.txt` in the `data/` directory with `polars` and `pyarrow`.
2. Define the core schema models in `data/ingest/schemas.py`.
3. Create a base `Parser` interface and implement a dummy/sample parser (e.g., `GenericCsvParser`) to validate the pipeline.
4. Implement the `ParquetStore` class in `data/store/writer.py` with partitioning logic.
5. Create an entry point CLI script (`data/ingest/cli.py`) that accepts an input directory, an output directory (`data/store`), and a data format identifier.

## Verification & Testing
- **Unit Tests:** Write `pytest` cases providing an in-memory sample dataframe to the transformation pipeline to verify column renaming, data typing, and row sorting.
- **Integration Test:** Run a small CSV file through the CLI and assert that the expected directory structure (`symbol=.../date=...`) and Parquet files are generated in `data/store`.
- **Read Validation:** Use a separate script to read the generated Parquet file using Polars, asserting the schema strictly matches our definition and checking for monotonic timestamps.

## Future Considerations
- While currently focused on historical L2 data, the abstract reader interface should be designed so that we can easily plug in real-time WebSocket adapters in the future.
- If data size becomes unmanageable in memory, ensure all Polars transformations utilize `scan_csv()` and lazy execution to stream data through memory.