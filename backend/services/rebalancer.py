# rebalancer.py
"""
Rebalancer module implementing different rebalancing strategies.
"""

from typing import Dict, List
from backend.config.settings import Config
import time

class Rebalancer:
    """
    Rebalancer class implementing different rebalancing strategies.
    策略层：负责再平衡决策逻辑和交易执行
    """
    def __init__(self, api_client, portfolio_manager):
        """
        Initialize the rebalancer.
        
        Args:
            api_client (GateFuturesClient): Gate.io API client using official library
            portfolio_manager (PortfolioManager): Portfolio manager for data operations
        """
        self.api_client = api_client
        self.portfolio_manager = portfolio_manager
        self.config = Config()
        self.leverage = 3  # 固定使用3倍杠杆
    
    def _calculate_rebalance_amounts(self, portfolio_data: Dict) -> Dict[str, float]:
        """
        计算需要再平衡的保证金金额
        
        Args:
            portfolio_data: 投资组合数据，包含current_portfolio, target_allocations等

        Returns:
            Dict: 每个资产需要调整的保证金金额
        """
        current_portfolio = portfolio_data["current_portfolio"]
        target_allocations = portfolio_data["target_allocations"]
        total_assets = portfolio_data["total_assets"]
        
        # 计算每个资产的目标保证金和需要调整的金额
        rebalance_amounts = {}
        
        # 最小调整金额
        min_adjustment = 10.0
        
        for asset in self.portfolio_manager.supported_assets:
            if asset == "USDT":
                # USDT不需要主动调整，会根据其他资产的调整自动变化
                continue
            
            current_margin = current_portfolio.get(asset, 0)
            target_margin = total_assets * target_allocations.get(asset, 0)
            diff = target_margin - current_margin
            time.sleep(0.1)
            
            # 如果调整金额太小，跳过
            if abs(diff) < min_adjustment:
                print(f"资产 {asset} 的调整金额 ({diff:.2f} USDT) 低于最小阈值 ({min_adjustment} USDT)，跳过")
                diff = 0
                
            rebalance_amounts[asset] = diff
        
        # 添加USDT的调整金额（负数表示从USDT转出）
        rebalance_amounts["USDT"] = -sum(v for k, v in rebalance_amounts.items() if k != "USDT")
        
        return rebalance_amounts
    
    def _calculate_trades(self, rebalance_amounts: Dict[str, float]) -> List[Dict]:
        """
        根据再平衡金额计算需要执行的交易
        
        Args:
            rebalance_amounts: 每个资产需要调整的保证金金额

        Returns:
            List[Dict]: 需要执行的交易列表
        """
        # 获取市场价格
        market_prices = self.portfolio_manager.get_market_prices()
        
        trades = []
        for contract, amount_diff in rebalance_amounts.items():
            if abs(amount_diff) < 1.0 or contract == "USDT":
                continue
            
            market_price = market_prices.get(contract, 0)
            if market_price <= 0:
                print(f"无效的市场价格: {contract}: {market_price}")
                continue
            
            # 计算合约数量（固定杠杆下，合约价值 = 保证金 * 杠杆）
            # 调整金额为目标保证金与当前保证金的差值
            # 合约数量 = (保证金差值 * 杠杆) / 市场价格
            size = (amount_diff * self.leverage) / market_price
            
            trades.append({
                'contract': contract,
                'size': size,
                'market_price': market_price
            })
        
        return trades
    
    def _execute_trades(self, trades):
        """
        执行交易列表（全仓模式）
        
        Args:
            trades (list): 包含'contract', 'size', 'market_price'的交易字典列表
            
        Returns:
            list: 已执行的交易详情列表
        """
        executed_trades = []
        
        # 打印计划执行的交易
        print("\n计划执行的交易:")
        print(f"{'合约':<10} {'方向':<6} {'数量':<10} {'预估价值 (USDT)':<15} {'保证金 (USDT)':<15}")
        print("-" * 65)
        for trade in trades:
            contract = trade['contract']
            size = trade['size']
            market_price = trade['market_price']
            side = "买入" if size > 0 else "卖出"
            value = abs(size) * market_price
            margin = value / self.leverage
            print(f"{contract:<10} {side:<6} {abs(size):<10.4f} {value:<15.2f} {margin:<15.2f}")
        print("")
        
        for trade in trades:
            contract = trade['contract']
            size = trade['size']
            market_price = trade['market_price']
            
            # 跳过零大小的交易
            if abs(size) < 0.00001:
                continue
            
            # 跳过USDT "交易"
            if contract == "USDT":
                continue
                
            # 确定买卖方向
            side = "buy" if size > 0 else "sell"

            # 设置杠杆为固定值（Gate.io API会自动使用全仓模式）
            if not self.api_client.set_leverage(contract, self.leverage):
                print(f"无法设置 {contract} 为{self.leverage}倍杠杆。跳过交易。")
                continue

            # 执行市价单
            order_result = self.api_client.create_futures_order(
                contract=contract,
                size=size,
                price=None,  # 市价单
                reduce_only=False
            )

            # 检查结果
            if order_result and order_result.get('status') != 'open':
                executed_size = float(order_result.get('size', size))
                executed_trade = {
                    'contract': contract,
                    'side': side,
                    'amount': abs(executed_size),
                    'price': float(order_result.get('fill_price', market_price)),
                    'status': 'executed',
                    'order_id': order_result.get('id')
                }
                executed_trades.append(executed_trade)
                print(f"已执行 {side} {abs(executed_size)} {contract} @ {executed_trade['price']} (订单ID: {order_result.get('id')})")
            else:
                print(f"执行 {contract} {side} 订单失败，大小: {size}")
        
        return executed_trades
    
    def threshold_rebalance(self):
        """
        执行基于阈值的再平衡策略：
        当资产的实际配置偏离目标配置超过设定阈值时触发再平衡
        
        Returns:
            bool: 如果执行了再平衡则返回True，否则返回False
        """
        # 获取投资组合数据
        portfolio_data = self.portfolio_manager.get_portfolio_summary()
        deviations = portfolio_data["deviations"]
        
        # 阈值百分比转换为小数
        threshold = self.config.rebalance_threshold / 100.0
        
        # 分析偏差并决定是否需要再平衡
        print("\n== 阈值再平衡分析 ==")
        print(f"{'资产':<10} {'偏差':<10} {'阈值':<10} {'需要再平衡':<10}")
        print("-" * 45)
        
        needs_rebalance = False
        for asset, dev in deviations.items():
            dev_pct = dev * 100
            threshold_pct = self.config.rebalance_threshold
            needs_rebal = abs(dev) > threshold
            if needs_rebal:
                needs_rebalance = True
            print(f"{asset:<10} {dev_pct:>9.2f}% {threshold_pct:>9.2f}% {'是' if needs_rebal else '否':^10}")
        
        if not needs_rebalance:
            print("\n没有资产超过再平衡阈值，跳过再平衡")
            return False
        
        # 计算需要调整的保证金金额
        rebalance_amounts = self._calculate_rebalance_amounts(portfolio_data)
        
        # 计算需要执行的交易
        trades = self._calculate_trades(rebalance_amounts)
        
        # 执行交易
        print("\n执行基于阈值的再平衡...")
        if not trades:
            print("没有需要执行的交易")
            return False
            
        executed_trades = self._execute_trades(trades)
        
        # 显示再平衡后的组合
                
        return len(executed_trades) > 0
    
    def cash_flow_rebalance(self):
        """
        执行基于现金流入的再平衡策略：
        当USDT余额高于设定最小值时，按目标配置比例购买资产
        
        Returns:
            bool: 如果执行了再平衡则返回True，否则返回False
        """
        # 获取投资组合数据
        portfolio_data = self.portfolio_manager.get_portfolio_summary()
        current_portfolio = portfolio_data["current_portfolio"]
        
        # 检查USDT余额
        usdt_balance = current_portfolio.get("USDT", 0)
        
        # 如果USDT余额低于最小阈值，跳过
        min_usdt = self.config.min_usdt_inflow
        if usdt_balance < min_usdt:
            print(f"\nUSDT余额 ({usdt_balance:.2f}) 低于最小流入阈值 ({min_usdt:.2f})，跳过现金流再平衡")
            return False
                
        print(f"\nUSDT余额 ({usdt_balance:.2f}) 高于最小流入阈值 ({min_usdt:.2f})，执行现金流再平衡")
        
        # 计算需要调整的保证金金额
        rebalance_amounts = self._calculate_rebalance_amounts(portfolio_data)
        
        # 计算需要执行的交易
        trades = self._calculate_trades(rebalance_amounts)
        
        # 执行交易
        if not trades:
            print("没有需要执行的交易")
            return False
            
        print("\n执行基于现金流的再平衡...")
        executed_trades = self._execute_trades(trades)
        
        # 显示再平衡后的组合
                
        return len(executed_trades) > 0
