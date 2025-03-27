"""
Portfolio Manager for handling portfolio-related operations.
"""
from typing import Dict, Tuple
from backend.config.settings import Config

class PortfolioManager:
    """
    Portfolio Manager class responsible for portfolio data operations.
    纯数据层：负责获取投资组合数据、资产价格和保证金使用情况
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
        获取当前投资组合，基于全仓模式下的保证金使用情况
        
        Returns:
            Dict mapping asset to margin value in USDT
        """
        # 获取账户信息
        account = self.api_client.get_futures_account()
        try:
            total_assets = float(account.get("total", "0"))
        except (ValueError, TypeError):
            total_assets = 0.0
            print("Warning: Could not convert account total to float.")

        # 获取持仓信息
        positions = self.api_client.get_futures_positions()
        
        # 初始化投资组合
        portfolio = {asset: 0.0 for asset in self.supported_assets}
        
        # 计算已使用的保证金
        used_margin = 0.0
        
        # 计算每个仓位
        for position in positions:
            contract = position.get("contract")
            if contract in self.supported_assets:
                try:
                    size = float(position.get("size", "0"))
                    mark_price = float(position.get("mark_price", "0"))
                    LEVERAGE = 3  # 默认3倍杠杆
                    
                    if mark_price <= 0:
                        print(f"Warning: Invalid mark price ({mark_price}) for {contract}. Skipping.")
                        continue
                    
                    # 计算使用的保证金
                    position_value = abs(size) * mark_price
                    margin_used = position_value / LEVERAGE
                    used_margin += margin_used
                    
                    print(f"Position {contract}: Size={size}, Price={mark_price}, Leverage={LEVERAGE}, Value={position_value:.2f}, Margin={margin_used:.2f}")
                    
                    portfolio[contract] = margin_used
                    
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not calculate margin for {contract}: {e}. Skipping.")
                    continue
        
        # 可用保证金记为USDT
        portfolio["USDT"] = max(0.0, total_assets - used_margin)
        
        # 打印总结
        print(f"\n== 账户保证金状态 ==")
        print(f"总资产: {total_assets:.2f} USDT")
        print(f"已用保证金: {used_margin:.2f} USDT")
        print(f"可用保证金: {portfolio['USDT']:.2f} USDT")
        
        return portfolio
    
    def get_target_portfolio(self) -> Dict[str, float]:
        """
        获取目标投资组合配置
        
        Returns:
            Dict mapping asset to target percentage (0.0-1.0)
        """
        # 读取配置文件中的配置比例，不使用USDT的比例（将自动计算）
        targets = {
            "BTC_USDT": self.config.portfolio_allocation.BTC_USDT / 100.0,
            "ETH_USDT": self.config.portfolio_allocation.ETH_USDT / 100.0,
            "LTC_USDT": self.config.portfolio_allocation.LTC_USDT / 100.0,
        }
        
        # 计算剩余百分比给USDT
        crypto_total = sum(targets.values())
        targets["USDT"] = max(0.0, 1.0 - crypto_total)
        
        return targets
    
    def get_market_prices(self) -> Dict[str, float]:
        """
        获取所有支持资产的市场价格
        
        Returns:
            Dict mapping asset to current market price
        """
        prices = {}
        for asset in self.supported_assets:
            if asset == "USDT":
                prices[asset] = 1.0  # USDT的价格固定为1
                continue
                
            price = self.api_client.get_futures_price(asset)
            if price <= 0:
                print(f"Warning: Invalid market price for {asset}: {price}")
                prices[asset] = 0.0
            else:
                prices[asset] = price
                
        return prices
    
    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合汇总信息，包括当前配置、目标配置和偏差
        
        Returns:
            Dict containing portfolio summary information
        """
        current_portfolio = self.get_current_portfolio()
        target_allocations = self.get_target_portfolio()
        
 
        # 计算当前百分比
        current_percentages = {}
        for asset, value in current_portfolio.items():
            current_percentages[asset] = (value / sum(current_portfolio.values())) if sum(current_portfolio.values()) > 0 else 0.0
        
        # 计算偏差
        deviations = {}
        for asset in self.supported_assets:
            current_pct = current_percentages.get(asset, 0.0)
            target_pct = target_allocations.get(asset, 0.0)
            deviations[asset] = current_pct - target_pct
        
        # 打印当前状态
        print("\n== 当前投资组合 ==")
        print(f"{'资产':<10} {'保证金 (USDT)':<15} {'当前比例':<10} {'目标比例':<10} {'偏差':<10}")
        print("-" * 60)
        for asset in self.supported_assets:
            current_value = current_portfolio.get(asset, 0)
            current_pct = current_percentages.get(asset, 0) * 100
            target_pct = target_allocations.get(asset, 0) * 100
            dev_pct = deviations.get(asset, 0) * 100
            print(f"{asset:<10} {current_value:>15.2f} {current_pct:>9.2f}% {target_pct:>9.2f}% {dev_pct:>9.2f}%")
        print(f"总资产: {sum(current_portfolio.values()):.2f} USDT\n")
        
        return {
            "current_portfolio": current_portfolio,
            "target_allocations": target_allocations,
            "current_percentages": current_percentages,
            "deviations": deviations,
            "total_assets": sum(current_portfolio.values()),
            "used_margin": sum(current_portfolio.values()) - current_portfolio["USDT"]
        }