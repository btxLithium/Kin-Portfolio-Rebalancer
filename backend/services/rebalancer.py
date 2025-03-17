# rebalancer.py
"""
Rebalancer module implementing different rebalancing strategies.
"""

from backend.config.settings import THRESHOLD_PERCENT, CASH_FLOW_THRESHOLD, FUTURES_SETTLE, LEVERAGE
from sheets_logger import SheetsLogger

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
        self.sheets_logger = SheetsLogger()
        self.settle = FUTURES_SETTLE
    
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
            
            # Determine whether we're buying or selling
            side = "buy" if size > 0 else "sell"
            
            # Set leverage first
            if contract != "USDT":
                try:
                    leverage = LEVERAGE.get(contract, 1)
                    self.api_client.set_leverage(contract, leverage)
                    print(f"Set leverage for {contract} to {leverage}x")
                except Exception as e:
                    print(f"Error setting leverage for {contract}: {e}")
            
            # Execute market order
            try:
                result = self.api_client.create_futures_order(
                    contract=contract,
                    size=size,
                    price=None  # Market order
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
        rebalance_needed = any(abs(dev) > THRESHOLD_PERCENT for dev in deviations.values())
        
        if not rebalance_needed:
            return False
        
        # Get current portfolio and target allocations
        current_portfolio = self.portfolio_manager.get_current_portfolio()
        target_portfolio = self.portfolio_manager.get_rebalance_targets()
        
        # Calculate trades needed
        trades = []
        for contract, target_value in target_portfolio.items():
            current_value = current_portfolio.get(contract, 0)
            value_diff = target_value - current_value
            
            if abs(value_diff) < 1.0:  # Skip small differences
                continue
            
            if contract == "USDT":
                continue  # USDT balance will be adjusted as a result of other trades
            
            # Get current market price
            ticker = self.api_client.get_ticker(contract)
            market_price = float(ticker.get('last', 0))
            
            if market_price <= 0:
                print(f"Invalid market price for {contract}: {market_price}")
                continue
            
            # Calculate size (considering leverage)
            leverage = LEVERAGE.get(contract, 1)
            size = value_diff * leverage / market_price
            
            trades.append({
                'contract': contract,
                'size': size,
                'market_price': market_price
            })
        
        # Execute trades
        print("Performing threshold-based rebalancing...")
        executed_trades = self._execute_trades(trades)
        
        # Get final portfolio after rebalancing
        final_portfolio = self.portfolio_manager.get_current_portfolio()
        
        # Log the rebalancing operation
        self.sheets_logger.log_rebalance(
            'threshold',
            current_portfolio,
            final_portfolio,
            executed_trades
        )
        
        return True
    
    def cash_flow_rebalance(self):
        """
        Perform cash-flow-based rebalancing when new USDT is deposited.
        
        Returns:
            bool: True if rebalancing was performed, False otherwise
        """
        # Check recent deposits
        try:
            transfers = self.api_client.get_wallet_transfers()
            
            # Filter for recent USDT deposits
            recent_deposits = [
                t for t in transfers
                if t.get('currency') == 'USDT' and
                t.get('direction') == 'in' and
                float(t.get('amount', 0)) >= CASH_FLOW_THRESHOLD
            ]
            
            if not recent_deposits:
                return False
                
            # Get current portfolio and target allocations
            current_portfolio = self.portfolio_manager.get_current_portfolio()
            target_portfolio = self.portfolio_manager.get_rebalance_targets()
            
            # Calculate trades needed
            trades = []
            for contract, target_value in target_portfolio.items():
                if contract == "USDT":
                    continue  # USDT balance will be adjusted as a result of other trades
                    
                current_value = current_portfolio.get(contract, 0)
                value_diff = target_value - current_value
                
                if abs(value_diff) < 1.0:  # Skip small differences
                    continue
                
                # Get current market price
                ticker = self.api_client.get_ticker(contract)
                market_price = float(ticker.get('last', 0))
                
                if market_price <= 0:
                    print(f"Invalid market price for {contract}: {market_price}")
                    continue
                
                # Calculate size (considering leverage)
                leverage = LEVERAGE.get(contract, 1)
                size = value_diff * leverage / market_price
                
                trades.append({
                    'contract': contract,
                    'size': size,
                    'market_price': market_price
                })
            
            # Execute trades
            print("Performing cash-flow-based rebalancing...")
            executed_trades = self._execute_trades(trades)
            
            # Get final portfolio after rebalancing
            final_portfolio = self.portfolio_manager.get_current_portfolio()
            
            # Log the rebalancing operation
            self.sheets_logger.log_rebalance(
                'cash_flow',
                current_portfolio,
                final_portfolio,
                executed_trades
            )
            
            return True
            
        except Exception as e:
            print(f"Error checking for cash flow rebalancing: {e}")
            return False
