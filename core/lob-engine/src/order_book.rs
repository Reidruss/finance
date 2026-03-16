use std::collections::HashMap;
use dashmap::DashMap;
use crate::book_side::BookSide;
use crate::event::{EventStore, OrderEvent};
use crate::iceberg::IcebergOrder;
use crate::order::Order;
use crate::stop_order::StopOrder;
use crate::types::{OrderId, OrderType, Price, Quantity, Side, Trade};
use crate::price_level::{PriceLevel};
use std::{
    collections::{BTreeMap, VecDeque}, sync::{
        atomic::{AtomicU64, AtomicU8, Ordering},
        Arc
    }
};
use crossbeam_channel::{unbounded, Sender};
use parking_lot::{Mutex, RwLock};

#[derive(Debug, Clone)]
pub enum OrderBookError {
    InvalidOrder,
    InsufficientQuantity,
}

pub struct OrderBook {
    bids: RwLock<BTreeMap<Price, Arc<PriceLevel>>>,
    asks: RwLock<BTreeMap<Price, Arc<PriceLevel>>>,
    order_lookup: DashMap<OrderId, (Side, Price, Arc<Order>)>,
    next_order_id: AtomicU64,
    trade_tx: Sender<Trade>
}

impl OrderBook {
    pub fn new(trade_tx: Sender<Trade>) -> Self {
        Self {
            bids: RwLock::new(BTreeMap::new()),
            asks: RwLock::new(BTreeMap::new()),
            order_lookup: DashMap::new(),
            next_order_id: AtomicU64::new(1),
            trade_tx: trade_tx,
        }
    }

    fn generate_order_id(&self) -> OrderId {
        self.next_order_id.fetch_add(1, Ordering::Relaxed)
    }

    /// Get the HIGHEST bid.
    pub fn best_bid(&self) -> Option<Price> {
        let bids = self.bids.read();
        bids.iter().next_back().map(|entry| entry.1.price)
    }

    pub fn best_ask(&self) -> Option<Price> {
        let asks = self.asks.read();
        asks.iter().next().map(|entry| entry.1.price)
    }

    // Get current Spread
    pub fn spread(&self) -> Option<Price> {
        match (self.best_bid(), self.best_ask()) {
            (Some(bid), Some(ask)) => Some(ask.saturating_sub(bid)),
            _ => None,
        }
    }

    /// Get total quantity at all bid levels
    pub fn total_bid_quantity(&self) -> Quantity {
        let bids = self.bids.read();
        bids.iter().map(|bid| bid.1.get_total_quantity()).sum()
    }

    /// Get total quantity of all ask levels
    pub fn total_ask_quantity(&self) -> Quantity {
        let asks = self.asks.read();
        asks.iter().map(|ask| ask.1.get_total_quantity()).sum()
    }

    pub fn total_quantity(&self) -> Quantity {
        self.total_bid_quantity() + self.total_ask_quantity()
    }

    fn get_or_create_level(map_lock: &RwLock<BTreeMap<Price, Arc<PriceLevel>>>, price: Price) -> Arc<PriceLevel> {
        {
            let map = map_lock.read();
            if let Some(level) = map.get(&price) {
                return level.clone();
            }
        }

        // Upgrade: take write lock and insert if missing.
        let mut map = map_lock.write();
        if let Some(level) = map.get(&price) {
            level.clone()
        } else {
            let level = Arc::new(PriceLevel::new(price));
            map.insert(price, level.clone());
            level
        }
    }

    pub fn submit_limit_order(
        &self,
        side: Side,
        price: Price,
        quantity: Quantity,
    ) -> Result<OrderId, OrderBookError> {
        if price == 0 {
            return Err(OrderbookError::InvalidPrice(price));
        }

        if quantity <= 0 {
            return Err(OrderBookError::IvalidQauntity(quantity))
        }
    }
}
