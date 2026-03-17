use pyo3::prelude::*;
use orderbook_rs::*;

#[pyclass]
#[derive(PartialEq, Clone, Copy)]
pub enum PySide {
    Bid,
    Ask,
}

impl Into<Side> for PySide {
    fn into(self) -> Side {
        match self {
            PySide::Bid => Side::Buy,
            PySide::Ask => Side::Sell,
        }
    }
}

#[pyclass]
pub struct PyOrderBook {
    inner: Box<OrderBook>,
}

#[pymethods]
impl PyOrderBook {
    #[new]
    fn new(symbol: &str) -> Self {
        PyOrderBook {
            inner: Box::new(OrderBook::new(symbol)),
        }
    }

    fn add_limit_order(
        &self,
        order_id: u64,
        quantity: u64,
        side: PySide,
        price: u128,
    ) -> PyResult<()> {
        let result = self.inner.add_limit_order(
            Id::Sequential(order_id),
            price,
            quantity,
            side.into(),
            pricelevel::TimeInForce::Gtc,
            None,
        );
        match result {
            Ok(_) => Ok(()),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("{:?}", e))),
        }
    }

    fn best_bid(&self) -> Option<u128> {
        self.inner.best_bid()
    }

    fn best_ask(&self) -> Option<u128> {
        self.inner.best_ask()
    }
    
    fn active_order_count(&self) -> usize {
        self.inner.get_all_orders().len()
    }
}

#[pymodule]
pub fn lob_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySide>()?;
    m.add_class::<PyOrderBook>()?;
    Ok(())
}
