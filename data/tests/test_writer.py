import pytest
import polars as pl
import tempfile
from pathlib import Path
from finance_data.writer import ParquetStore

def test_parquet_store_trades():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ParquetStore(tmpdir)
        
        # Create dummy data
        df = pl.DataFrame({
            "timestamp": [1704067200000000000, 1704153600000000000], # Jan 1 and Jan 2
            "symbol": ["BTC-USD", "BTC-USD"],
            "side": ["bid", "ask"],
            "price": [45000.0, 45001.0],
            "size": [1.5, 0.5],
            "trade_id": ["t1", "t2"]
        })
        
        store.write_trades(df.lazy())
        
        # Check files were created with correct partitioning
        base_path = Path(tmpdir)
        assert (base_path / "trades" / "symbol=BTC-USD" / "date=2024-01-01").exists()
        assert (base_path / "trades" / "symbol=BTC-USD" / "date=2024-01-02").exists()

def test_parquet_store_l2_updates():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ParquetStore(tmpdir)
        
        # Create dummy data
        df = pl.DataFrame({
            "timestamp": [1704067200000000000, 1704153600000000000],
            "symbol": ["ETH-USD", "ETH-USD"],
            "side": ["bid", "ask"],
            "price": [2200.0, 2201.0],
            "size": [10.0, 5.0],
            "is_snapshot": [True, False]
        })
        
        store.write_l2_updates(df.lazy())
        
        # Check files were created
        base_path = Path(tmpdir)
        assert (base_path / "l2_updates" / "symbol=ETH-USD" / "date=2024-01-01").exists()
        assert (base_path / "l2_updates" / "symbol=ETH-USD" / "date=2024-01-02").exists()
