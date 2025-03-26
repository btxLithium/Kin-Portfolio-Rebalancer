"""
Configuration settings for the portfolio rebalancer.
"""
import os
from typing import Optional
import json

# Default portfolio allocation (in percentage)
DEFAULT_PORTFOLIO = {
    "BTC_USDT": 25.0,
    "ETH_USDT": 15.0,
    "LTC_USDT": 10.0,
    "USDT": 50.0
}

# Rebalancing threshold (in percentage)
REBALANCE_THRESHOLD = 5.0

# Minimum USDT inflow to trigger rebalancing
MIN_USDT_INFLOW = 5.0

# Default check interval (in seconds)
CHECK_INTERVAL = 60 * 5  # 5 minutes

# API configuration
API_HOST = "https://fx-api-testnet.gateio.ws/api/v4"

class Config:
    """
    Configuration class that handles loading and saving of settings.
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config with optional path to config file.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or os.path.expanduser("~/.portfolio_rebalancer.json")
        self.api_key = ""
        self.api_secret = ""
        self.portfolio_allocation = DEFAULT_PORTFOLIO.copy()
        self.rebalance_threshold = REBALANCE_THRESHOLD
        self.min_usdt_inflow = MIN_USDT_INFLOW
        self.load()
    
    def load(self) -> None:
        """
        Load configuration from file if it exists.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.api_key = data.get('api_key', '')
                    self.api_secret = data.get('api_secret', '')
                    
                    # Handle portfolio allocation - handle both formats
                    if 'portfolio_allocation' in data:
                        # If using Rust frontend format
                        portfolio_data = data['portfolio_allocation']
                        if isinstance(portfolio_data, dict):
                            # Old format from Python
                            self.portfolio_allocation = portfolio_data
                        else:
                            # New format from Rust frontend
                            self.portfolio_allocation = {
                                "BTC_USDT": portfolio_data.get('btc_usdt', DEFAULT_PORTFOLIO["BTC_USDT"]),
                                "ETH_USDT": portfolio_data.get('eth_usdt', DEFAULT_PORTFOLIO["ETH_USDT"]),
                                "LTC_USDT": portfolio_data.get('ltc_usdt', DEFAULT_PORTFOLIO["LTC_USDT"]),
                                "USDT": portfolio_data.get('usdt', DEFAULT_PORTFOLIO["USDT"])
                            }
                    
                    self.rebalance_threshold = data.get('rebalance_threshold', REBALANCE_THRESHOLD)
                    self.min_usdt_inflow = data.get('min_usdt_inflow', MIN_USDT_INFLOW)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save(self) -> None:
        """
        Save current configuration to file.
        """
        config_data = {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'portfolio_allocation': self.portfolio_allocation,
            'rebalance_threshold': self.rebalance_threshold,
            'min_usdt_inflow': self.min_usdt_inflow
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def is_configured(self) -> bool:
        """
        Check if API credentials are configured.
        """
        return bool(self.api_key and self.api_secret)