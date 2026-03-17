import friction_engine
import pytest

def test_fee_model():
    model = friction_engine.SimpleFeeModel(5.0, 10.0) # 5bps maker, 10bps taker
    
    # Taker trade: $100,000 * 10bps = $100
    result = model.calculate_friction(100000.0, 1.0, False)
    assert result.fee_cost == 100.0
    
    # Maker trade: $100,000 * 5bps = $50
    result = model.calculate_friction(100000.0, 1.0, True)
    assert result.fee_cost == 50.0

def test_slippage_model():
    # Mean slippage 2bps, std dev 1bp
    model = friction_engine.StochasticSlippageModel(2.0, 1.0)
    
    slippage = model.calculate_slippage(50000.0, 1.0)
    # 50,000 * (2bps / 10,000) = 10.0
    # Since it's stochastic, we just check it's a number and within a reasonable range (3 sigma)
    # Expected slippage is 10.0, std dev is 5.0 (1bp of 50k is 5.0)
    assert -5.0 < slippage < 25.0
