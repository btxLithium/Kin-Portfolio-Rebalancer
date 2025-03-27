"""
Configuration settings for the portfolio rebalancer.
"""
import os
from typing import Optional
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("portfolio_rebalancer")

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

class PortfolioAllocation:
    """Portfolio allocation model."""
    def __init__(self, BTC_USDT=20.0, ETH_USDT=15.0, LTC_USDT=5.0):
        """
        初始化投资组合配置
        
        Args:
            BTC_USDT: BTC_USDT的分配百分比 (默认: 20.0%)
            ETH_USDT: ETH_USDT的分配百分比 (默认: 15.0%)
            LTC_USDT: LTC_USDT的分配百分比 (默认: 5.0%)
        """
        self.BTC_USDT = BTC_USDT
        self.ETH_USDT = ETH_USDT
        self.LTC_USDT = LTC_USDT
        # USDT比例通过计算得出，不再作为配置项
        self._validate()
    
    def _validate(self):
        """验证配置的有效性"""
        total = self.BTC_USDT + self.ETH_USDT + self.LTC_USDT
        if total > 100.0:
            raise ValueError(f"资产配置总和不能超过100%，当前总和: {total}%")
    
    @property
    def USDT(self):
        """计算USDT的分配比例"""
        return max(0.0, 100.0 - self.BTC_USDT - self.ETH_USDT - self.LTC_USDT)
    
    def as_dict(self):
        """转换为字典"""
        return {
            "BTC_USDT": self.BTC_USDT,
            "ETH_USDT": self.ETH_USDT,
            "LTC_USDT": self.LTC_USDT,
            "USDT": self.USDT
        }
        
    def __repr__(self):
        """字符串表示"""
        return f"PortfolioAllocation(BTC_USDT={self.BTC_USDT}, ETH_USDT={self.ETH_USDT}, LTC_USDT={self.LTC_USDT}, USDT={self.USDT})"

class Config:
    """
    Configuration class that handles loading and saving of settings.
    """
    def __init__(self, config_file=None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = config_file or os.path.expanduser("~/.portfolio_rebalancer.json")
        self.api_key = ""
        self.api_secret = ""
        self.portfolio_allocation = PortfolioAllocation()
        self.rebalance_threshold = 5.0  # 默认再平衡阈值 5%
        self.min_usdt_inflow = 50.0  # 默认最小USDT流入 50
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # 获取API配置
                self.api_key = config_data.get("api_key", "")
                self.api_secret = config_data.get("api_secret", "")
                
                # 获取投资组合配置
                allocation = config_data.get("portfolio_allocation", {})
                btc_pct = allocation.get("BTC_USDT", 20.0)
                eth_pct = allocation.get("ETH_USDT", 15.0)
                ltc_pct = allocation.get("LTC_USDT", 5.0)
                
                self.portfolio_allocation = PortfolioAllocation(
                    BTC_USDT=btc_pct,
                    ETH_USDT=eth_pct,
                    LTC_USDT=ltc_pct
                )
                
                # 获取其他设置
                self.rebalance_threshold = config_data.get("rebalance_threshold", 5.0)
                self.min_usdt_inflow = config_data.get("min_usdt_inflow", 50.0)
                
            except Exception as e:
                logger.error("加载配置文件失败: %s", e)
                # 使用默认配置
        else:
            logger.warning("配置文件 %s 不存在，使用默认配置", self.config_file)
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "portfolio_allocation": {
                "BTC_USDT": self.portfolio_allocation.BTC_USDT,
                "ETH_USDT": self.portfolio_allocation.ETH_USDT,
                "LTC_USDT": self.portfolio_allocation.LTC_USDT,
                # USDT比例不再保存，通过计算得出
            },
            "rebalance_threshold": self.rebalance_threshold,
            "min_usdt_inflow": self.min_usdt_inflow
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info("配置已保存到 %s", self.config_file)
            return True
        except Exception as e:
            logger.error("保存配置失败: %s", e)
            return False
    
    def is_configured(self):
        """检查API是否已配置"""
        return bool(self.api_key and self.api_secret)
