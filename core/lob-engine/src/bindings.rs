#![allow(unsafe_op_in_unsafe_fn)]

use orderbook_rs::*;
use pyo3::prelude::*;

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
#[derive(PartialEq, Clone, Copy)]
pub enum PyOrderType {
    Limit,
    Market,
}

#[pyclass]
#[derive(Clone)]
pub struct PyOrder {
    #[pyo3(get)]
    pub id: u64,
    #[pyo3(get)]
    pub price: u128,
    #[pyo3(get)]
    pub quantity: u64,
    #[pyo3(get)]
    pub side: PySide,
}

#[pyclass]
#[derive(Clone)]
pub struct PyTrade {
    #[pyo3(get)]
    pub maker_order_id: String,
    #[pyo3(get)]
    pub taker_order_id: String,
    #[pyo3(get)]
    pub price: u128,
    #[pyo3(get)]
    pub quantity: u64,
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

    fn add_market_order(
        &self,
        order_id: u64,
        quantity: u64,
        side: PySide,
    ) -> PyResult<()> {
        let result = self.inner.match_market_order(
            Id::Sequential(order_id),
            quantity,
            side.into(),
        );
        match result {
            Ok(_) => Ok(()),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("{:?}", e))),
        }
    }

    fn cancel_order(&self, order_id: u64) -> PyResult<bool> {
        let result = self.inner.cancel_order(Id::Sequential(order_id));
        match result {
            Ok(Some(_)) => Ok(true),
            Ok(None) => Ok(false),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("{:?}", e))),
        }
    }

    fn best_bid(&self) -> Option<u128> {
        self.inner.best_bid()
    }

    fn best_ask(&self) -> Option<u128> {
        self.inner.best_ask()
    }

    fn get_volume_at_price(&self, side: PySide, price: u128) -> u64 {
        self.inner.liquidity_in_range(price, price, side.into())
    }

    fn active_order_count(&self) -> usize {
        self.inner.active_order_count()
    }
}

#[pymodule]
pub fn lob_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySide>()?;
    m.add_class::<PyOrderType>()?;
    m.add_class::<PyOrder>()?;
    m.add_class::<PyTrade>()?;
    m.add_class::<PyOrderBook>()?;
    Ok(())
}
