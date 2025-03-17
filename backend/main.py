# main.py
"""
Main entry point for the portfolio rebalancing bot.
"""

import time
import traceback
from api.gate_client import GateIOFuturesClient
from portfolio_manager import PortfolioManager
from backend.services.rebalancer import Rebalancer
from backend.config.settings import CHECK_INTERVAL, TARGET_PORTFOLIO, LEVERAGE

def initialize_api_and_components():
    """
    Initialize API client and related components.
    
    Returns:
        tuple: (api_client, portfolio_manager, rebalancer)
    """
    print("Initializing Gate.io Futures API client...")
    api_client = GateIOFuturesClient()
    
    print("Initializing Portfolio Manager...")
    portfolio_manager = PortfolioManager(api_client)
    
    print("Initializing Rebalancer...")
    rebalancer = Rebalancer(api_client, portfolio_manager)
    
    return api_client, portfolio_manager, rebalancer

def display_portfolio_status(portfolio_manager):
    """
    Display current portfolio status.
    
    Args:
        portfolio_manager (PortfolioManager): Portfolio manager instance
    """
    try:
        # Get portfolio data
        portfolio = portfolio_manager.get_current_portfolio()
        percentages = portfolio_manager.get_portfolio_percentages()
        deviations = portfolio_manager.calculate_deviation()
        
        # Calculate total value
        total_value = sum(portfolio.values())
        
        # Display summary
        print("\n" + "="*50)
        print(f"PORTFOLIO SUMMARY (Total Value: {total_value:.2f} USDT)")
        print("="*50)
        
        print(f"{'Asset':<10} {'Current %':<10} {'Target %':<10} {'Deviation':<10} {'Value (USDT)':<15}")
        print("-"*55)
        
        for asset in TARGET_PORTFOLIO.keys():
            current_percent = percentages.get(asset, 0) * 100
            target_percent = TARGET_PORTFOLIO.get(asset, 0) * 100
            deviation = deviations.get(asset, 0) * 100
            value = portfolio.get(asset, 0)
            
            # Add leverage info for futures contracts
            leverage_info = ""
            if asset in LEVERAGE:
                leverage_info = f" ({LEVERAGE[asset]}x)"
            
            print(f"{asset+leverage_info:<10} {current_percent:>8.2f}% {target_percent:>8.2f}% {deviation:>8.2f}% {value:>13.2f}")
        
        print("="*50 + "\n")
    except Exception as e:
        print(f"Error displaying portfolio status: {e}")
        traceback.print_exc()

def main():
    """
    Main function to run the rebalancing bot.
    """
    print("Starting Portfolio Rebalancing Bot...")
    
    # Initialize components
    api_client, portfolio_manager, rebalancer = initialize_api_and_components()
    
    try:
        # Initial portfolio status
        display_portfolio_status(portfolio_manager)
        
        # Main loop
        while True:
            print(f"\nChecking portfolio at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                # Check for threshold-based rebalancing
                print("Checking for threshold-based rebalancing...")
                threshold_rebalanced = rebalancer.threshold_rebalance()
                
                if threshold_rebalanced:
                    print("Threshold-based rebalancing performed!")
                else:
                    print("No threshold-based rebalancing needed.")
                
                # Check for cash-flow-based rebalancing
                print("Checking for cash-flow-based rebalancing...")
                cash_flow_rebalanced = rebalancer.cash_flow_rebalance()
                
                if cash_flow_rebalanced:
                    print("Cash-flow-based rebalancing performed!")
                else:
                    print("No cash-flow-based rebalancing needed.")
                
                # Display updated portfolio status if rebalancing occurred
                if threshold_rebalanced or cash_flow_rebalanced:
                    display_portfolio_status(portfolio_manager)
                
            except Exception as e:
                print(f"Error during rebalancing cycle: {e}")
                traceback.print_exc()
            
            # Sleep until next check
            print(f"Sleeping for {CHECK_INTERVAL//60} minutes...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()