"""
Gate.io API client for interacting with the exchange futures market using the official gate-api library.
"""
import logging
from typing import Dict, List, Optional, Any

# Use official gate_api library
from gate_api import ApiClient, Configuration, FuturesApi, FuturesOrder
from gate_api.exceptions import ApiException, GateApiException

from backend.config.settings import Config

logger = logging.getLogger(__name__)

# Define the settlement currency
SETTLE_CURRENCY = "usdt"
# Define the host for the testnet
TESTNET_HOST = "https://fx-api-testnet.gateio.ws/api/v4"

class GateAPIError(Exception):
    """Custom exception for Gate API errors."""
    pass

class GateFuturesClient:
    """
    Client for interacting with Gate.io Futures API using the official library.
    Focuses on USDT settled perpetual contracts.
    """
    def __init__(self):
        """
        Initialize the Gate.io Futures API client.
        Loads API key and secret from the configuration file.
        """
        try:
            config_loader = Config()
            if not config_loader.is_configured():
                raise GateAPIError("API key and secret are not configured in ~/.portfolio_rebalancer.json")

            self.api_key = config_loader.api_key
            self.api_secret = config_loader.api_secret
            # Use testnet host by default as per original code and example
            self.host = TESTNET_HOST

            # Initialize gate-api client
            self.configuration = Configuration(key=self.api_key, secret=self.api_secret, host=self.host)
            self.api_client = ApiClient(self.configuration)
            self.futures_api = FuturesApi(self.api_client)

            logger.info("GateFuturesClient initialized successfully for host: %s", self.host)

        except Exception as e:
            logger.error("Failed to initialize GateFuturesClient: %s", e)
            raise GateAPIError(f"Failed to initialize GateFuturesClient: {e}") from e

    def _handle_api_exception(self, error: ApiException, context: str) -> GateAPIError:
        """Helper to log and wrap ApiException."""
        logger.error("Gate API Exception in %s: Status %s, Reason: %s, Body: %s",
                     context, error.status, error.reason, error.body)
        # Try to parse body for GateApiException label
        label = "UNKNOWN_ERROR"
        if isinstance(error, GateApiException):
            label = error.label
        return GateAPIError(f"API Error in {context}: {label} - {error.reason}")

    def get_futures_account(self) -> Dict[str, Any]:
        """
        Get futures account information for the settlement currency.

        Returns:
            Dict of account information.
        """
        try:
            account_info = self.futures_api.list_futures_accounts(settle=SETTLE_CURRENCY)
            # The API returns a FuturesAccount object, convert to dict if needed or use attributes directly
            # For simplicity, returning the raw object might be okay if downstream code adapts.
            # Let's return its dictionary representation for compatibility potential.
            # Assuming FuturesAccount has a to_dict() method or similar, otherwise access attributes.
            # Based on gate-api structure, it should have attributes like .total, .available etc.
            # Let's simulate a dictionary structure similar to the old client's expected output
            return {
                "total": getattr(account_info, 'total', '0'),
                "available": getattr(account_info, 'available', '0'),
                # Add other relevant fields if needed by portfolio_manager
            }
        except ApiException as e:
            raise self._handle_api_exception(e, "get_futures_account") from e

    def get_futures_positions(self) -> List[Dict[str, Any]]:
        """
        Get all current futures positions for the settlement currency.

        Returns:
            List of position information dictionaries.
        """
        try:
            positions = self.futures_api.list_positions(settle=SETTLE_CURRENCY)
            # Convert list of Position objects to list of dictionaries
            return [pos.to_dict() for pos in positions]
        except ApiException as e:
            raise self._handle_api_exception(e, "get_futures_positions") from e

    def get_futures_position(self, contract: str) -> Dict[str, Any]:
        """
        Get position information for a specific contract.

        Args:
            contract: Contract name (e.g., "BTC_USDT")

        Returns:
            Position information dictionary.
        """
        try:
            position = self.futures_api.get_position(settle=SETTLE_CURRENCY, contract=contract)
            return position.to_dict()
        except GateApiException as e:
            # Handle case where position doesn't exist gracefully
            if e.label == "POSITION_NOT_FOUND":
                logger.warning("No position found for contract %s", contract)
                # Return a default-like structure or None, depending on how caller handles it
                return {"contract": contract, "size": 0} # Example default
            raise self._handle_api_exception(e, f"get_futures_position({contract})") from e
        except ApiException as e:
            raise self._handle_api_exception(e, f"get_futures_position({contract})") from e


    def get_futures_price(self, contract: str) -> float:
        """
        Get the last traded price for a futures contract.

        Args:
            contract: Contract name (e.g., "BTC_USDT")

        Returns:
            Current price as a float. Returns 0.0 if fetching fails.
        """
        try:
            tickers = self.futures_api.list_futures_tickers(settle=SETTLE_CURRENCY, contract=contract)
            if tickers and len(tickers) > 0:
                # Assuming the first ticker is the relevant one
                return float(tickers[0].last)
            else:
                logger.warning("No ticker data received for contract %s", contract)
                return 0.0
        except ApiException as e:
            logger.error("Failed to get price for %s: %s", contract, e)
            # Don't raise, return 0.0 as per original behavior indication
            return 0.0
        except ValueError as e:
            logger.error("Error converting price to float for %s: %s", contract, e)
            return 0.0

    def set_leverage(self, contract: str, leverage: int) -> bool:
        """
        Set leverage for a specific contract and ensure cross margin mode.

        Args:
            contract: Contract name (e.g., "BTC_USDT")
            leverage: Leverage value (e.g., 3 for 3x). Must be passed as string to API.

        Returns:
            True if successful, False otherwise.
        """
        if leverage < 1:
            logger.error("Leverage must be at least 1.")
            return False
        try:
            # 直接设置杠杆，Gate.io API不支持直接设置全仓/逐仓模式
            # 但是我们默认使用全仓模式
            self.futures_api.update_position_leverage(settle=SETTLE_CURRENCY, contract=contract, leverage=str(leverage))
            logger.info("Successfully set leverage for %s to %sx", contract, leverage)
            return True
        except ApiException as e:
            self._handle_api_exception(e, f"set_leverage({contract}, {leverage})")
            return False

    def set_margin_mode(self, contract: str, mode: str) -> bool:
        """
        Set margin mode for a specific contract.
        Note: Gate.io API doesn't have a direct method to set margin mode.
        This method is a no-op that always returns True.

        Args:
            contract: Contract name (e.g., "BTC_USDT")
            mode: Margin mode ("cross" or "isolated") - not used

        Returns:
            Always returns True
        """
        # Gate.io API 接口中没有直接设置保证金模式的方法
        # 根据官方文档，保证金模式可能在创建仓位时就已确定
        # 我们假设杠杆设置时已经确定了保证金模式
        logger.info("Setting margin mode is not directly supported by Gate.io API. Assuming %s for %s", mode, contract)
        return True

    def create_futures_order(self,
                             contract: str,
                             size: float,
                             price: Optional[float] = None,
                             reduce_only: bool = False) -> Optional[Dict[str, Any]]:
        """
        Create a futures order (market or limit).

        Args:
            contract: Contract name (e.g., "BTC_USDT")
            size: Order size. Positive for buy/long, negative for sell/short.
                  The API requires integer size, representing number of contracts.
                  THIS NEEDS CAREFUL CONVERSION based on contract value if size is in USDT.
                  Assuming 'size' here means number of contracts for now, matching example.
            price: Order price. If None, a market order is placed.
            reduce_only: Whether this order should only reduce the position size.

        Returns:
            Order creation response dictionary if successful, None otherwise.
        """
        if size == 0:
            logger.warning("Attempted to create order with size 0 for %s", contract)
            return None
            
        # 定义最小订单大小
        min_sizes = {
            "BTC_USDT": 1,   # 比特币最小1合约
            "ETH_USDT": 1,   # 以太坊最小1合约
            "LTC_USDT": 1,   # 莱特币最小1合约
        }
        
        # 确保订单大小至少达到最小要求
        min_size = min_sizes.get(contract, 1)
        if abs(size) < min_size:
            # 如果订单小于最小值，使用最小值，保持原方向
            logger.warning("Order size for %s is too small: %s, using minimum size: %s", 
                           contract, size, min_size)
            size = min_size if size > 0 else -min_size

        # The gate-api expects size as an integer number of contracts.
        # 向下取整，确保不为零
        order_size_int = int(size)
        if order_size_int == 0:
            # 如果整数化后为0，使用最小单位，保持原方向
            order_size_int = 1 if size > 0 else -1
            logger.warning("Order size for %s is too small after integer conversion: %s, using %d", 
                           contract, size, order_size_int)


        order = FuturesOrder(
            contract=contract,
            size=order_size_int, # Must be integer
            reduce_only=reduce_only
        )

        if price is not None:
            # Limit order
            order.price = str(price)
            order.tif = 'gtc'  # Good Till Cancel
        else:
            # Market order - price should be "0" or None? Example uses "0". Let's use "0".
            order.price = "0"
            order.tif = 'ioc'  # Immediate Or Cancel

        try:
            created_order = self.futures_api.create_futures_order(settle=SETTLE_CURRENCY, futures_order=order)
            logger.info("Successfully created order for %s: ID %s, Size %s, Status %s",
                        contract, created_order.id, created_order.size, created_order.status)
            return created_order.to_dict()
        except ApiException as e:
            self._handle_api_exception(e, f"create_futures_order({contract}, size={size})")
            return None

# Example usage (optional, for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        client = GateFuturesClient()

        # Test getting account info
        account = client.get_futures_account()
        logger.info("Futures Account Info: %s", account)

        # Test getting positions
        positions = client.get_futures_positions()
        logger.info("Current Positions: %s", positions)
        if positions:
             pos_dict = positions[0] # Use the dict directly
             logger.info("First position contract: %s, size: %s", pos_dict.get('contract'), pos_dict.get('size'))


        # Test getting price
        btc_price = client.get_futures_price("BTC_USDT")
        logger.info("BTC_USDT Price: %s", btc_price)

        # Test setting leverage (use a known contract)
        # client.set_leverage("BTC_USDT", 3)

        # Test creating a small market order (adjust size as needed for testnet minimums)
        # Example: Buy 1 contract of BTC_USDT (size=1)
        # order_result = client.create_futures_order("BTC_USDT", size=1)
        # logger.info("Create Order Result: %s", order_result)

        # Example: Sell 1 contract of BTC_USDT (size=-1)
        # order_result = client.create_futures_order("BTC_USDT", size=-1)
        # logger.info("Create Order Result: %s", order_result)

    except GateAPIError as e:
        logger.error("Error during example usage: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred during example usage.")
