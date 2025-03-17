"""
Gate.io API client for interacting with the exchange.
This module handles all communication with the Gate.io API.
"""
import time
import hashlib
import hmac
import base64
import requests
from typing import Dict, List, Optional, Any, Union
import json

from ..config.settings import API_HOST

class GateAPIError(Exception):
    """
    Exception raised for Gate.io API errors.
    """
    pass

class GateClient:
    """
    Client for interacting with Gate.io API.
    """
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the Gate.io API client.
        
        Args:
            api_key: Gate.io API key
            api_secret: Gate.io API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = API_HOST
    
    def _generate_signature(self, method: str, url: str, query_string: str = '', body: str = '') -> Dict[str, str]:
        """
        Generate signature for API request according to Gate.io authentication requirements.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: API endpoint URL
            query_string: URL query string
            body: Request body for POST requests
            
        Returns:
            Dict containing the required headers for authentication
        """
        timestamp = str(int(time.time()))
        hashed_payload = hashlib.sha512(body.encode()).hexdigest()
        
        signature_string = f"{method}\n{url}\n{query_string}\n{hashed_payload}\n{timestamp}"
        signature = hmac.new(
            self.api_secret.encode(),
            signature_string.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return {
            "KEY": self.api_key,
            "Timestamp": timestamp,
            "SIGN": signature
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
        """
        Make an API request to Gate.io.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data for POST requests
            
        Returns:
            API response data
        """
        url = f"{self.host}{endpoint}"
        query_string = '&'.join([f"{k}={v}" for k, v in (params or {}).items()])
        body_string = json.dumps(data) if data else ''
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add authentication headers
        signature_url = endpoint
        auth_headers = self._generate_signature(method, signature_url, query_string, body_string)
        headers.update(auth_headers)
        
        response = requests.request(
            method=method,
            url=url,
            params=params,
            data=body_string,
            headers=headers
        )
        
        if response.status_code not in (200, 201, 204):
            raise GateAPIError(f"API Error: {response.status_code}, {response.text}")
        
        return response.json() if response.text else {}
    
    def get_spot_account(self) -> List[Dict]:
        """
        Get spot account balances.
        
        Returns:
            List of account balances by currency
        """
        return self._make_request("GET", "/spot/accounts")
    
    def get_ticker(self, currency_pair: str) -> Dict:
        """
        Get ticker information for a currency pair.
        
        Args:
            currency_pair: Currency pair symbol (e.g., "BTC_USDT")
            
        Returns:
            Ticker information
        """
        return self._make_request("GET", "/spot/tickers", {"currency_pair": currency_pair})
    
    def get_currency_pairs(self) -> List[Dict]:
        """
        Get all supported currency pairs.
        
        Returns:
            List of currency pairs information
        """
        return self._make_request("GET", "/spot/currency_pairs")
    
    def create_order(self, 
                     currency_pair: str, 
                     side: str, 
                     amount: str, 
                     price: str = None, 
                     order_type: str = "limit") -> Dict:
        """
        Create a new order.
        
        Args:
            currency_pair: Currency pair symbol (e.g., "BTC_USDT")
            side: "buy" or "sell"
            amount: Amount to buy or sell
            price: Price (optional for market orders)
            order_type: Order type ("limit" or "market")
            
        Returns:
            Order creation response
        """
        data = {
            "currency_pair": currency_pair,
            "side": side,
            "amount": amount,
            "type": order_type
        }
        
        if price is not None:
            data["price"] = price
        
        return self._make_request("POST", "/spot/orders", data=data)
    
    def get_order(self, order_id: str) -> Dict:
        """
        Get order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details
        """
        return self._make_request("GET", f"/spot/orders/{order_id}")
    
    def get_balances(self) -> Dict[str, float]:
        """
        Get account balances in a simplified format.
        
        Returns:
            Dict mapping currency symbols to their available balance
        """
        accounts = self.get_spot_account()
        balances = {}
        
        for account in accounts:
            currency = account.get("currency")
            available = float(account.get("available", "0"))
            if available > 0:
                balances[currency] = available
        
        return balances
    
    def get_price(self, currency_pair: str) -> float:
        """
        Get current price for a currency pair.
        
        Args:
            currency_pair: Currency pair symbol (e.g., "BTC_USDT")
            
        Returns:
            Current price as float
        """
        ticker = self.get_ticker(currency_pair)
        return float(ticker[0].get("last", "0"))