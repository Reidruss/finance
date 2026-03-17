import pytest
import polars as pl
import tempfile
from pathlib import Path
from finance_data.parsers import GenericCsvParser

def test_generic_csv_parser_trades():
    parser = GenericCsvParser(symbol="BTC-USD")
    
    # Create dummy csv
    csv_content = """timestamp,side,price,size,trade_id
1704067200000000000,bid,45000.0,1.5,t1
1704067200001000000,ask,45001.0,0.5,t2"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
        
    try:
        lf = parser.parse_trades(temp_path)
        df = lf.collect()
        
        assert len(df) == 2
        assert "symbol" in df.columns
        assert df["symbol"][0] == "BTC-USD"
        assert df["timestamp"][0] == 1704067200000000000
    finally:
        Path(temp_path).unlink()

def test_generic_csv_parser_l2():
    parser = GenericCsvParser(symbol="ETH-USD")
    
    csv_content = """timestamp,side,price,size,is_snapshot
1704067200000000000,bid,2200.0,10.0,true
1704067200001000000,ask,2201.0,5.0,false"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
        
    try:
        lf = parser.parse_l2_updates(temp_path)
        df = lf.collect()
        
        assert len(df) == 2
        assert "symbol" in df.columns
        assert df["symbol"][0] == "ETH-USD"
        assert df["is_snapshot"][0] == True
        assert df["is_snapshot"][1] == False
    finally:
        Path(temp_path).unlink()
