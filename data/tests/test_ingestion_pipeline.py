import pytest
import polars as pl
import os
import shutil
from pathlib import Path
from finance_data.parsers import GenericCsvParser
from finance_data.writer import ParquetStore

@pytest.fixture
def tmp_dir():
    path = Path("data/tests/tmp_ingest")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    yield path
    shutil.rmtree(path)

def test_generic_csv_parser_trades(tmp_dir):
    csv_path = tmp_dir / "trades.csv"
    # Create sample trade data
    # timestamp,side,price,size,trade_id
    # Using 2024-01-01 00:00:00 UTC = 1704067200000000000 ns
    content = "timestamp,side,price,size,trade_id\n1704067200000000000,bid,50000.0,0.1,t1\n1704067201000000000,ask,50001.0,0.2,t2"
    csv_path.write_text(content)
    
    parser = GenericCsvParser(symbol="BTC-USD")
    lf = parser.parse_trades(str(csv_path))
    df = lf.collect()
    
    assert df.shape == (2, 6)
    assert df["symbol"][0] == "BTC-USD"
    assert df["side"][0] == "bid"
    assert df["price"][0] == 50000.0
    assert df["timestamp"][0] == 1704067200000000000

def test_parquet_store_integration(tmp_dir):
    csv_path = tmp_dir / "l2.csv"
    store_path = tmp_dir / "store"
    # timestamp,side,price,size
    content = "timestamp,side,price,size\n1704067200000000000,bid,49999.0,1.5\n1704067200100000000,ask,50001.0,2.0"
    csv_path.write_text(content)
    
    parser = GenericCsvParser(symbol="ETH-USD")
    lf = parser.parse_l2_updates(str(csv_path))
    
    store = ParquetStore(str(store_path))
    # We need to ensure we collect symbol and date for partition if write_parquet expects it
    store.write_l2_updates(lf)
    
    # Check partition structure
    # Based on Hive partitioning, symbol and date are part of the directory structure
    symbol_dir = store_path / "l2_updates" / "symbol=ETH-USD"
    date_dir = symbol_dir / "date=2024-01-01"
    
    assert symbol_dir.exists()
    assert date_dir.exists()
    assert any(date_dir.glob("*.parquet"))
    
    # Read back and verify
    # When reading a hive-partitioned dataset, polars scan_parquet can include the partition columns
    df_read = pl.scan_parquet(store_path / "l2_updates").collect()
    assert "symbol" in df_read.columns
    assert "date" in df_read.columns
    assert df_read.filter(pl.col("symbol") == "ETH-USD").height == 2
