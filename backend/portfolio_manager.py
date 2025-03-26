"""
Portfolio Manager for handling portfolio-related operations.
"""
from typing import Dict, List, Any
from backend.config.settings import Config

class PortfolioManager:
    """
    Portfolio Manager class responsible for portfolio-related operations.
    """
    def __init__(self, api_client):
        """
        Initialize Portfolio Manager.
        
        Args:
            api_client: Gate.io API client instance
        """
        self.api_client = api_client
        self.config = Config()
        self.supported_assets = ["BTC_USDT", "ETH_USDT", "LTC_USDT", "USDT"]
    
    def get_current_portfolio(self) -> Dict[str, float]:
        """
        Get current portfolio with asset values in USDT.
        
        Returns:
            Dict mapping asset to value in USDT
        """
        # Get futures account
        account = self.api_client.get_futures_account()
        total = float(account.get("total", 0))
        
        # Get positions
        positions = self.api_client.get_futures_positions()
        
        # Initialize portfolio with all supported assets at 0
        portfolio = {asset: 0.0 for asset in self.supported_assets}
        
        # Set USDT balance
        portfolio["USDT"] = total
        
        # Add position values
        for position in positions:
            contract = position.get("contract")
            if contract in self.supported_assets:
                # For futures positions, use size * mark_price
                size = float(position.get("size", 0))
                mark_price = float(position.get("mark_price", 0))
                value = abs(size) * mark_price
                
                # Subtract the value from USDT since futures use margin
                portfolio["USDT"] -= value
                portfolio[contract] = value
        
        return portfolio
    
    def get_portfolio_percentages(self) -> Dict[str, float]:
        """
        Get current portfolio allocation percentages.
        
        Returns:
            Dict mapping asset to percentage (0.0-1.0)
        """
        portfolio = self.get_current_portfolio()
        total_value = sum(portfolio.values())
        
        if total_value == 0:
            return {asset: 0.0 for asset in self.supported_assets}
        
        return {asset: value / total_value for asset, value in portfolio.items()}
    
    def get_target_portfolio(self) -> Dict[str, float]:
        """
        Get target portfolio allocation percentages.
        
        Returns:
            Dict mapping asset to target percentage (0.0-1.0)
        """
        return {
            "BTC_USDT": self.config.portfolio_allocation["BTC_USDT"] / 100.0,
            "ETH_USDT": self.config.portfolio_allocation["ETH_USDT"] / 100.0,
            "LTC_USDT": self.config.portfolio_allocation["LTC_USDT"] / 100.0,
            "USDT": self.config.portfolio_allocation["USDT"] / 100.0
        }
    
    def calculate_deviation(self) -> Dict[str, float]:
        """
        Calculate deviation from target portfolio.
        
        Returns:
            Dict mapping asset to deviation percentage (-1.0 to 1.0)
        """
        current = self.get_portfolio_percentages()
        target = self.get_target_portfolio()
        
        return {asset: current.get(asset, 0) - target.get(asset, 0) for asset in self.supported_assets}
    
    def calculate_rebalance_amounts(self) -> Dict[str, float]:
        """
        Calculate amounts needed to rebalance portfolio to target allocation.
        Positive values mean buy, negative values mean sell.
        
        Returns:
            Dict mapping asset to amount in USDT to buy/sell
        """
        portfolio = self.get_current_portfolio()
        total_value = sum(portfolio.values())
        target = self.get_target_portfolio()
        
        rebalance_amounts = {}
        
        for asset in self.supported_assets:
            current_value = portfolio.get(asset, 0)
            target_value = total_value * target.get(asset, 0)
            rebalance_amounts[asset] = target_value - current_value
        
        return rebalance_amounts
