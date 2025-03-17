use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PortfolioAllocation {
    pub btc_usdt: f64,
    pub eth_usdt: f64,
    pub ltc_usdt: f64,
    pub usdt: f64,
}

impl Default for PortfolioAllocation {
    fn default() -> Self {
        Self {
            btc_usdt: 25.0,
            eth_usdt: 15.0,
            ltc_usdt: 10.0,
            usdt: 50.0,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Config {
    pub api_key: String,
    pub api_secret: String,
    pub portfolio_allocation: PortfolioAllocation,
    pub rebalance_threshold: f64,
    pub min_usdt_inflow: f64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            api_secret: String::new(),
            portfolio_allocation: PortfolioAllocation::default(),
            rebalance_threshold: 5.0,
            min_usdt_inflow: 5.0,
        }
    }
}