import pytest
import lob_engine

def test_lob_basic():
    book = lob_engine.PyOrderBook("BTC-USD")
    
    # Test adding limit orders
    book.add_limit_order(1, 100, lob_engine.PySide.Bid, 50000)
    assert book.best_bid() == 50000
    assert book.get_volume_at_price(lob_engine.PySide.Bid, 50000) == 100
    
    book.add_limit_order(2, 50, lob_engine.PySide.Ask, 50010)
    assert book.best_ask() == 50010
    assert book.get_volume_at_price(lob_engine.PySide.Ask, 50010) == 50
    assert book.active_order_count() == 2
    
    # Test canceling
    assert book.cancel_order(2) == True
    assert book.best_ask() is None
    assert book.get_volume_at_price(lob_engine.PySide.Ask, 50010) == 0
    assert book.active_order_count() == 1
    
    # Re-add ask
    book.add_limit_order(3, 50, lob_engine.PySide.Ask, 50010)
    assert book.active_order_count() == 2
    
    # Test market order execution
    # A market buy of 25 should take half of the ask
    book.add_market_order(4, 25, lob_engine.PySide.Bid)
    
    assert book.best_ask() == 50010
    assert book.get_volume_at_price(lob_engine.PySide.Ask, 50010) == 25

    # Test full execution with a limit order
    book.add_limit_order(5, 25, lob_engine.PySide.Bid, 50010)
    assert book.best_ask() is None
    assert book.get_volume_at_price(lob_engine.PySide.Ask, 50010) == 0
    assert book.best_bid() == 50000

