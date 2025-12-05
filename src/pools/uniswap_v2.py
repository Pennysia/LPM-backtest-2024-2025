"""
Uniswap V2 pool implementation
"""

from typing import Dict
from src.pools.base_pool import BasePool
from src.utils.math import sqrt, calculate_price, calculate_k


class UniswapV2Pool(BasePool):
    """Uniswap V2 constant product AMM"""
    
    def __init__(self, reserve0: float, reserve1: float, fee_rate: float = 0.003):
        """
        Initialize Uniswap V2 pool
        
        Args:
            reserve0: Initial reserve of token0
            reserve1: Initial reserve of token1
            fee_rate: Fee rate (default 0.003 = 0.3%)
        """
        super().__init__(reserve0, reserve1, fee_rate)
        
        # Calculate initial liquidity
        self.total_supply = sqrt(reserve0 * reserve1)
        
        # Track cumulative fees
        self.cumulative_fees0 = 0.0
        self.cumulative_fees1 = 0.0
        
    def swap(self, amount_in: float, zero_for_one: bool) -> float:
        """
        Execute swap using constant product formula
        x * y = k
        
        Args:
            amount_in: Amount of input token
            zero_for_one: True if swapping token0 for token1
            
        Returns:
            Amount of output token
        """
        if amount_in <= 0:
            raise ValueError("Amount in must be positive")
        
        # Calculate fee
        amount_in_with_fee = amount_in * (1 - self.fee_rate)
        
        if zero_for_one:
            # Swapping token0 for token1
            reserve_in = self.reserve0
            reserve_out = self.reserve1
        else:
            # Swapping token1 for token0
            reserve_in = self.reserve1
            reserve_out = self.reserve0
        
        # Constant product formula
        # (reserve_in + amount_in_with_fee) * (reserve_out - amount_out) = k
        # amount_out = reserve_out - k / (reserve_in + amount_in_with_fee)
        
        k = calculate_k(reserve_in, reserve_out)
        amount_out = reserve_out - (k / (reserve_in + amount_in_with_fee))
        
        if amount_out <= 0 or amount_out >= reserve_out:
            raise ValueError("Insufficient liquidity")
        
        # Update reserves
        if zero_for_one:
            self.reserve0 += amount_in
            self.reserve1 -= amount_out
            self.cumulative_fees0 += amount_in * self.fee_rate
        else:
            self.reserve1 += amount_in
            self.reserve0 -= amount_out
            self.cumulative_fees1 += amount_in * self.fee_rate
        
        return amount_out
    
    def get_price(self) -> float:
        """
        Get current price (reserve1 / reserve0)
        
        Returns:
            Current price
        """
        return calculate_price(self.reserve0, self.reserve1)
    
    def get_reserves(self) -> Dict[str, float]:
        """
        Get current reserves
        
        Returns:
            Dictionary with reserve information
        """
        return {
            "reserve0": self.reserve0,
            "reserve1": self.reserve1,
            "total_supply": self.total_supply,
        }
    
    def get_lp_value(self, lp_share: float = 1.0, market_price: float | None = None) -> float:
        """
        Get LP token value
        
        Args:
            lp_share: Share of total liquidity (default 1.0 = 100%)
            market_price: Market price to use for valuation (if None, uses pool price)
            
        Returns:
            Value of LP position in token0 (USD) terms
        """
        if self.total_supply == 0:
            return 0.0
        
        # Use market price if provided, otherwise use pool price
        price = market_price if market_price is not None else self.get_price()
        
        # LP owns (lp_share * USD_reserves) + (lp_share * token_reserves * market_price)
        value = (lp_share * self.reserve0) + (lp_share * self.reserve1 * price)
        
        return value
    
    def add_liquidity(self, amount0: float, amount1: float) -> float:
        """
        Add liquidity to pool
        
        Args:
            amount0: Amount of token0 to add
            amount1: Amount of token1 to add
            
        Returns:
            Liquidity tokens minted
        """
        if amount0 <= 0 or amount1 <= 0:
            raise ValueError("Amounts must be positive")
        
        # Calculate liquidity to mint
        liquidity = sqrt(amount0 * amount1)
        
        # Update reserves
        self.reserve0 += amount0
        self.reserve1 += amount1
        self.total_supply += liquidity
        
        return liquidity
    
    def remove_liquidity(self, liquidity: float) -> tuple[float, float]:
        """
        Remove liquidity from pool
        
        Args:
            liquidity: Amount of liquidity tokens to burn
            
        Returns:
            (amount0, amount1) tuple
        """
        if liquidity <= 0 or liquidity > self.total_supply:
            raise ValueError("Invalid liquidity amount")
        
        # Calculate proportional amounts
        share = liquidity / self.total_supply
        amount0 = share * self.reserve0
        amount1 = share * self.reserve1
        
        # Update reserves
        self.reserve0 -= amount0
        self.reserve1 -= amount1
        self.total_supply -= liquidity
        
        return (amount0, amount1)
    
    def get_state(self) -> Dict[str, any]:
        """
        Get complete pool state
        
        Returns:
            Dictionary with all pool state
        """
        state = super().get_state()
        state.update({
            "cumulative_fees0": self.cumulative_fees0,
            "cumulative_fees1": self.cumulative_fees1,
            "k": calculate_k(self.reserve0, self.reserve1),
        })
        return state
