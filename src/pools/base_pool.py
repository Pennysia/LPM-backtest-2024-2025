"""
Base pool interface for AMM implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePool(ABC):
    """Abstract base class for AMM pools"""
    
    def __init__(self, reserve0: float, reserve1: float, fee_rate: float = 0.003):
        """
        Initialize pool
        
        Args:
            reserve0: Initial reserve of token0
            reserve1: Initial reserve of token1
            fee_rate: Fee rate (default 0.003 = 0.3%)
        """
        self.reserve0 = reserve0
        self.reserve1 = reserve1
        self.fee_rate = fee_rate
        
    @abstractmethod
    def swap(self, amount_in: float, zero_for_one: bool) -> float:
        """
        Execute a swap
        
        Args:
            amount_in: Amount of input token
            zero_for_one: True if swapping token0 for token1, False otherwise
            
        Returns:
            Amount of output token
        """
        pass
    
    @abstractmethod
    def get_price(self) -> float:
        """
        Get current price (token1 / token0)
        
        Returns:
            Current price
        """
        pass
    
    @abstractmethod
    def get_reserves(self) -> Dict[str, float]:
        """
        Get current reserves
        
        Returns:
            Dictionary with reserve information
        """
        pass
    
    @abstractmethod
    def get_lp_value(self, **kwargs) -> float:
        """
        Get LP token value
        
        Returns:
            Value per LP token
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get complete pool state
        
        Returns:
            Dictionary with all pool state
        """
        return {
            "reserves": self.get_reserves(),
            "price": self.get_price(),
            "fee_rate": self.fee_rate,
        }
