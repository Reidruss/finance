import polars as pl
from enum import Enum

class Side(str, Enum):
    BID = "bid"
    ASK = "ask"

# Schema definitions using Polars datatypes
TRADE_SCHEMA = {
    "timestamp": pl.Int64,    # Epoch nanoseconds
    "symbol": pl.Categorical,
    "side": pl.Categorical,
    "price": pl.Float64,
    "size": pl.Float64,
    "trade_id": pl.String,
}

L2_BOOK_UPDATE_SCHEMA = {
    "timestamp": pl.Int64,    # Epoch nanoseconds
    "symbol": pl.Categorical,
    "side": pl.Categorical,
    "price": pl.Float64,
    "size": pl.Float64,       # 0 indicates deletion
    "is_snapshot": pl.Boolean, # True if this row is part of a full book snapshot
}
