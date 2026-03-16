use crossbeam_skiplist::SkipMap;
use dashmap::DashMap;
use std::{
    collections::{BTreeMap, VecDeque}, sync::{
        atomic::{AtomicU64, AtomicU8, Ordering},
        Arc
    }, thread::current, time::{SystemTime, UNIX_EPOCH}
};
use thiserror::Error;
use std::cmp::min;
use parking_lot::{Mutex, RwLock};

use crate::price_level::PriceLevel;
use crate::types::Side;
use crate::Price;

pub struct BookSide {
    pub(crate) levels: RwLock<BTreeMap<Price, Arc<PriceLevel>>>,
}

impl BookSide {
    pub fn new() -> Self {
        Self {
            levels: BTreeMap::new(),
        }
    }

    /// Get best price (highest for bids, lowest for asks)
    pub fn best_price(&self, side: Side) -> Option<u64> {
        match side {
            Side::Bid => self.levels.keys().rev().next().cloned(),
            Side::Ask => self.levels.keys().next().cloned(),
        }
    }

    pub fn insert(&mut self, order: Order) {
        let level = self
            .levels
            .entry(order.price)
            .or_insert_with(|| PriceLevel::new(order.price));
        level.add_order(order);
    }

    pub fn remove_level_if_empty(&mut self, price: u64) {
        if let Some(level) = self.levels.get(&price) {
            if level.orders.is_empty() {
                self.levels.remove(&price);
            }
        }
    }
}
