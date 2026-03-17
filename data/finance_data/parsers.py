import polars as pl
from abc import ABC, abstractmethod
from typing import Optional

class BaseParser(ABC):
    """Base class for all data parsers."""
    
    @abstractmethod
    def parse_trades(self, file_path: str) -> pl.LazyFrame:
        """Parse raw trade data into a normalized LazyFrame conforming to TRADE_SCHEMA."""
        pass
        
    @abstractmethod
    def parse_l2_updates(self, file_path: str) -> pl.LazyFrame:
        """Parse raw L2 data into a normalized LazyFrame conforming to L2_BOOK_UPDATE_SCHEMA."""
        pass


class GenericCsvParser(BaseParser):
    """A generic CSV parser for testing. Assumes the CSV already matches the schema names."""
    
    def __init__(self, symbol: str, separator: str = ","):
        self.symbol = symbol
        self.separator = separator
        
    def parse_trades(self, file_path: str) -> pl.LazyFrame:
        lf = pl.scan_csv(file_path, separator=self.separator)
        
        # Ensure 'symbol' column exists
        if "symbol" not in lf.collect_schema().names():
            lf = lf.with_columns(pl.lit(self.symbol).alias("symbol"))
            
        lf = lf.cast({
            "timestamp": pl.Int64,
            "symbol": pl.Categorical,
            "side": pl.Categorical,
            "price": pl.Float64,
            "size": pl.Float64,
            "trade_id": pl.String,
        })
        
        return lf.select(["timestamp", "symbol", "side", "price", "size", "trade_id"]).sort("timestamp")

    def parse_l2_updates(self, file_path: str) -> pl.LazyFrame:
        lf = pl.scan_csv(file_path, separator=self.separator)
        
        if "symbol" not in lf.collect_schema().names():
            lf = lf.with_columns(pl.lit(self.symbol).alias("symbol"))
            
        if "is_snapshot" not in lf.collect_schema().names():
            lf = lf.with_columns(pl.lit(False).alias("is_snapshot"))
            
        lf = lf.cast({
            "timestamp": pl.Int64,
            "symbol": pl.Categorical,
            "side": pl.Categorical,
            "price": pl.Float64,
            "size": pl.Float64,
            "is_snapshot": pl.Boolean,
        })
        
        return lf.select(["timestamp", "symbol", "side", "price", "size", "is_snapshot"]).sort("timestamp")
