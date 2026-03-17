use pyo3::prelude::*;
use rand::prelude::*;
use rand_distr::Normal;
use serde::{Deserialize, Serialize};

/// Result of a friction calculation.
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrictionResult {
    /// Total fees incurred (e.g., as a percentage of notional or fixed).
    #[pyo3(get)]
    pub fee_cost: f64,
    /// Estimated slippage cost (e.g., from market impact or execution delay).
    #[pyo3(get)]
    pub estimated_slippage: f64,
}

/// A simple percentage-based fee model (e.g., 0.1% or 10 bps).
#[pyclass]
pub struct SimpleFeeModel {
    pub maker_fee_bps: f64,
    pub taker_fee_bps: f64,
}

#[pymethods]
impl SimpleFeeModel {
    #[new]
    pub fn new(maker_fee_bps: f64, taker_fee_bps: f64) -> Self {
        Self {
            maker_fee_bps,
            taker_fee_bps,
        }
    }

    /// Calculate friction for a trade execution.
    fn calculate_friction(
        &self,
        price: f64,
        quantity: f64,
        is_maker: bool,
    ) -> FrictionResult {
        let notional = price * quantity;
        let bps = if is_maker {
            self.maker_fee_bps
        } else {
            self.taker_fee_bps
        };
        
        let fee_cost = notional * (bps / 10000.0);
        
        FrictionResult {
            fee_cost,
            estimated_slippage: 0.0,
        }
    }
}

/// A stochastic slippage model that adds a random execution cost.
/// This can simulate price moves while an order is "in flight".
#[pyclass]
pub struct StochasticSlippageModel {
    mean_bps: f64,
    std_dev_bps: f64,
}

#[pymethods]
impl StochasticSlippageModel {
    #[new]
    pub fn new(mean_bps: f64, std_dev_bps: f64) -> Self {
        Self {
            mean_bps,
            std_dev_bps,
        }
    }

    fn calculate_slippage(&self, price: f64, quantity: f64) -> f64 {
        let mut rng = rand::thread_rng();
        let normal = Normal::new(self.mean_bps, self.std_dev_bps).unwrap();
        let slippage_bps: f64 = normal.sample(&mut rng);
        
        // Slippage cost in currency units
        (price * quantity) * (slippage_bps / 10000.0)
    }
}

#[pymodule]
fn friction_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FrictionResult>()?;
    m.add_class::<SimpleFeeModel>()?;
    m.add_class::<StochasticSlippageModel>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_fee_calculation() {
        let model = SimpleFeeModel::new(5.0, 10.0);
        let result = model.calculate_friction(50000.0, 1.0, false);
        assert_eq!(result.fee_cost, 50.0);
    }
}
