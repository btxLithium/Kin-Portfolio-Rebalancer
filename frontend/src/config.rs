use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PortfolioAllocation {
    #[serde(rename = "BTC_USDT")]
    pub BTC_USDT: f64,
    #[serde(rename = "ETH_USDT")]
    pub ETH_USDT: f64,
    #[serde(rename = "LTC_USDT")]
    pub LTC_USDT: f64,
    #[serde(rename = "USDT")]
    pub USDT: f64,
}

impl Default for PortfolioAllocation {
    fn default() -> Self {
        Self {
            BTC_USDT: 25.0,
            ETH_USDT: 15.0,
            LTC_USDT: 10.0,
            USDT: 50.0,
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
