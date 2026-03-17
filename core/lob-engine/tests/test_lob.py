import lob_engine

def test_lob_basic():
    print("Testing lob_engine initialization...")
    ob = lob_engine.PyOrderBook("BTC/USD")
    
    print("Adding orders...")
    # order_id, quantity, side, price
    ob.add_limit_order(1, 10, lob_engine.PySide.Bid, 50000)
    ob.add_limit_order(2, 5, lob_engine.PySide.Ask, 50010)
    
    bid = ob.best_bid()
    ask = ob.best_ask()
    count = ob.active_order_count()
    
    print(f"Best Bid: {bid}, Best Ask: {ask}, Active Orders: {count}")
    
    assert bid == 50000, f"Expected best bid to be 50000, got {bid}"
    assert ask == 50010, f"Expected best ask to be 50010, got {ask}"
    assert count == 2, f"Expected active order count to be 2, got {count}"
    
    print("Test passed successfully!")

if __name__ == "__main__":
    test_lob_basic()
