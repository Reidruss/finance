import polars as pl
from pathlib import Path
import pyarrow.dataset as ds
from datetime import datetime

class ParquetStore:
    """Handles writing normalized Polars DataFrames to partitioned Parquet storage."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.trades_path = self.base_path / "trades"
        self.l2_updates_path = self.base_path / "l2_updates"
        
        # Ensure directories exist
        self.trades_path.mkdir(parents=True, exist_ok=True)
        self.l2_updates_path.mkdir(parents=True, exist_ok=True)
        
    def write_trades(self, lf: pl.LazyFrame):
        """
        Executes the LazyFrame and writes trades partitioned by symbol and date.
        Assumes `timestamp` is epoch nanoseconds.
        """
        df = lf.collect()
        if df.is_empty():
            return
            
        # Extract date from timestamp for partitioning
        df = df.with_columns(
            pl.from_epoch(pl.col("timestamp"), time_unit="ns").dt.date().cast(pl.String).alias("date")
        )
        
        # Write dataset using pyarrow for hive partitioning
        df.write_parquet(
            self.trades_path,
            use_pyarrow=True,
            pyarrow_options={
                "partition_cols": ["symbol", "date"],
                "existing_data_behavior": "overwrite_or_ignore", # or 'error' depending on requirements
            }
        )
        
    def write_l2_updates(self, lf: pl.LazyFrame):
        """
        Executes the LazyFrame and writes L2 updates partitioned by symbol and date.
        """
        df = lf.collect()
        if df.is_empty():
            return
            
        # Extract date from timestamp for partitioning
        df = df.with_columns(
            pl.from_epoch(pl.col("timestamp"), time_unit="ns").dt.date().cast(pl.String).alias("date")
        )
        
        df.write_parquet(
            self.l2_updates_path,
            use_pyarrow=True,
            pyarrow_options={
                "partition_cols": ["symbol", "date"],
                "existing_data_behavior": "overwrite_or_ignore",
            }
        )
