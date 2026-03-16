use crate::order::Order;
use crate::types::{OrderId, Price, Quantity};
use parking_lot::Mutex;
use std::{
    collections::VecDeque,
    sync::{
        Arc,
        atomic::{AtomicU64, Ordering},
    },
};
/// Orders at a single price level
#[derive(Debug)]
pub struct PriceLevel {
    pub price: Price,
    pub orders: Mutex<VecDeque<Arc<Order>>>,
    pub total_quantity: AtomicU64,
}

impl PriceLevel {
    pub fn new(price: u64) -> Self {
        Self {
            price: price,
            orders: Mutex::new(VecDeque::new()),
            total_quantity: AtomicU64::new(0),
        }
    }

    pub fn push_order(&self, order: Arc<Order>) {
        let vec_deque = &mut *self.orders.lock();
        let quantity = order.get_remaining_quantity();
        vec_deque.push_back(order);
        self.total_quantity.fetch_add(quantity, Ordering::AcqRel);
    }

    /// Pop the front order from this price level
    pub fn pop_front(&self) -> Option<Arc<Order>> {
        let vec_deque = &mut *self.orders.lock();
        let order = vec_deque.pop_front();
        order
    }

    pub fn remove_order(&self, order_id: OrderId) -> Option<(Arc<Order>, Quantity)> {
        let vec_deque = &mut *self.orders.lock();

        let mut i: usize = 0;
        while i < vec_deque.len() {
            if vec_deque[i].order_id == order_id {
                let curr_order = vec_deque.remove(i).unwrap();
                let curr_remaining_q = curr_order.get_remaining_quantity();
                // Subtract remaining quantity from the total quantity
                self.total_quantity
                    .fetch_sub(curr_remaining_q, Ordering::AcqRel);
                return Some((curr_order, curr_remaining_q));
            }
            i += 1;
        }
        None
    }

    /// Get approximate total quantity (maybe slightly stale)
    /// TODO: Make this more accurate
    pub fn get_total_quantity(&self) -> Quantity {
        self.total_quantity.load(Ordering::Relaxed)
    }

    pub fn is_empty(&self) -> bool {
        let vec_deque = &mut *self.orders.lock();
        vec_deque.is_empty()
    }
}
