# main.py
"""
Main entry point for the portfolio rebalancing bot.
"""

import time
import traceback
import argparse
import os  # Add os import for environment variables
from backend.api.gate_client import GateFuturesClient # Updated client name
from backend.portfolio_manager import PortfolioManager # Corrected import path
from backend.services.rebalancer import Rebalancer
from backend.config.settings import Config

# Default check interval in seconds
CHECK_INTERVAL = 60 * 5  # 5 minutes

def initialize_api_and_components(config_path=None):
    """
    Initialize API client and related components.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        tuple: (api_client, portfolio_manager, rebalancer)
    """
    # Initialize config
    config = Config(config_path)
    
    print("Initializing Gate.io Futures API client...")
    # The new client loads config internally via backend.config.settings.Config
    api_client = GateFuturesClient() 
    
    print("Initializing Portfolio Manager...")
    portfolio_manager = PortfolioManager(api_client)
    
    print("Initializing Rebalancer...")
    rebalancer = Rebalancer(api_client, portfolio_manager)
    
    return api_client, portfolio_manager, rebalancer

def main():
    """
    Main function to run the rebalancing bot.
    """
    # Get config from environment or parse args
    config_path = os.environ.get('PORTFOLIO_CONFIG')
    
    # If not in environment, parse command line
    if not config_path:
        parser = argparse.ArgumentParser(description='Portfolio Rebalancer')
        parser.add_argument('--config', type=str, help='Path to config file')
        args = parser.parse_args()
        config_path = args.config
    
    print(f"Starting Portfolio Rebalancing Bot with config: {config_path}")
    
    # Initialize components
    api_client, portfolio_manager, rebalancer = initialize_api_and_components(config_path)
    
    try:
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
