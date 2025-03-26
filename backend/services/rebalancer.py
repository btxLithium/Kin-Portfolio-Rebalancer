# rebalancer.py
"""
Rebalancer module implementing different rebalancing strategies.
"""

from backend.config.settings import Config

class Rebalancer:
    """
    Rebalancer class implementing different rebalancing strategies.
    """
    def __init__(self, api_client, portfolio_manager):
        """
        Initialize the rebalancer.
        
        Args:
            api_client (GateIOFuturesClient): Gate.io API client
            portfolio_manager (PortfolioManager): Portfolio manager
        """
        self.api_client = api_client
        self.portfolio_manager = portfolio_manager
        self.config = Config()
    
    def _execute_trades(self, trades):
        """
        Execute a list of trades.
        
        Args:
            trades (list): List of trade dictionaries with 'contract', 'size', and 'market_price'
            
        Returns:
            list: List of executed trade details
        """
        executed_trades = []
        
        for trade in trades:
            contract = trade['contract']
            size = trade['size']
            
            # Skip trades with zero size
            if abs(size) < 0.00001:
                continue
            
            # Skip USDT "trades" since it's the base currency
            if contract == "USDT":
                continue
                
            # Determine whether we're buying or selling
            side = "buy" if size > 0 else "sell"
            
            # Set leverage first (default to 1x)
            leverage = 1
            try:
                self.api_client.set_leverage(contract, leverage)
                print(f"Set leverage for {contract} to {leverage}x")
            except Exception as e:
                print(f"Error setting leverage for {contract}: {e}")
            
            # Execute market order
            try:
                result = self.api_client.create_futures_order(
                    contract=contract,
                    size=abs(size),  # Size should be positive
                    price=None,  # Market order
                    leverage=leverage,
                    reduce_only=False
                )
                
                executed_trade = {
                    'contract': contract,
                    'side': side,
                    'amount': abs(size),
                    'price': trade.get('market_price', 0),
                    'status': 'executed'
                }
                executed_trades.append(executed_trade)
                
                print(f"Executed {side} {abs(size)} {contract} at market price")
            except Exception as e:
                print(f"Error executing {side} order for {contract}: {e}")
                executed_trade = {
                    'contract': contract,
                    'side': side,
                    'amount': abs(size),
                    'price': trade.get('market_price', 0),
                    'status': 'failed',
                    'error': str(e)
                }
                executed_trades.append(executed_trade)
        
        return executed_trades
    
    def threshold_rebalance(self):
        """
        Perform threshold-based rebalancing when asset allocation deviates from target.
        
        Returns:
            bool: True if rebalancing was performed, False otherwise
        """
        # Get current deviations
        deviations = self.portfolio_manager.calculate_deviation()
        
        # Check if any deviation exceeds the threshold
        threshold = self.config.rebalance_threshold / 100.0  # Convert to decimal
        rebalance_needed = any(abs(dev) > threshold for dev in deviations.values())
        
        if not rebalance_needed:
            return False
        
        # Get current portfolio and calculate rebalance amounts
        current_portfolio = self.portfolio_manager.get_current_portfolio()
        rebalance_amounts = self.portfolio_manager.calculate_rebalance_amounts()
        
        # Calculate trades needed
        trades = []
        for contract, value_diff in rebalance_amounts.items():
            if abs(value_diff) < 1.0:  # Skip small differences
                continue
            
            if contract == "USDT":
                continue  # USDT balance will be adjusted as a result of other trades
            
            # Get current market price
            market_price = self.api_client.get_futures_price(contract)
            
            if market_price <= 0:
                print(f"Invalid market price for {contract}: {market_price}")
                continue
            
            # Calculate size (contracts to buy/sell)
            size = value_diff / market_price
            
            trades.append({
                'contract': contract,
                'size': size,
                'market_price': market_price
            })
        
        # Execute trades
        print("Performing threshold-based rebalancing...")
        executed_trades = self._execute_trades(trades)
        
        return len(executed_trades) > 0
    
    def cash_flow_rebalance(self):
        """
        Perform cash-flow-based rebalancing when new USDT is deposited.
        
        Returns:
            bool: True if rebalancing was performed, False otherwise
        """
        # Check USDT balance
        portfolio = self.portfolio_manager.get_current_portfolio()
        usdt_balance = portfolio.get("USDT", 0)
        
        # If USDT balance is less than the minimum threshold, skip
        if usdt_balance < self.config.min_usdt_inflow:
            return False
                
        # Calculate target allocations
        target = self.portfolio_manager.get_target_portfolio()
        total_value = sum(portfolio.values())
        
        # Calculate how much to allocate to each asset
        trades = []
        for contract, target_percent in target.items():
            if contract == "USDT":
                continue  # Skip USDT as it's the base currency
                
            target_value = total_value * target_percent
            current_value = portfolio.get(contract, 0)
            value_diff = target_value - current_value
            
            if abs(value_diff) < 1.0:  # Skip small differences
                continue
            
            # Get current market price
            market_price = self.api_client.get_futures_price(contract)
            
            if market_price <= 0:
                print(f"Invalid market price for {contract}: {market_price}")
                continue
            
            # Calculate size (contracts to buy/sell)
            size = value_diff / market_price
            
            trades.append({
                'contract': contract,
                'size': size,
                'market_price': market_price
            })
        
        # Execute trades
        if trades:
            print("Performing cash-flow-based rebalancing...")
            executed_trades = self._execute_trades(trades)
            return len(executed_trades) > 0
        
        return False
