"""
Pennysia dual-bucket AMM implementation
Based on PENNYSIA_PROTOCOL_SPEC.md
"""

from typing import Dict, Literal, Optional
from src.pools.base_pool import BasePool
from src.utils.math import sqrt, calculate_price, calculate_k


class PennysiaPool(BasePool):
    """
    Pennysia AMM with long/short liquidity buckets
    
    Key differences from Uniswap V2:
    - 4 reserves instead of 2 (long and short for each token)
    - Asymmetric fee distribution (input side earns more)
    - Dual LP tokens (long and short positions)
    - k grows on short side (earns input fees)
    """
    
    def __init__(
        self,
        reserve0: float,
        reserve1: float,
        fee_rate: float = 0.003,
        protocol_fee_share: float = 0.2
    ):
        """
        Initialize Pennysia pool
        
        Args:
            reserve0: Initial total reserve of token0 (split 50/50)
            reserve1: Initial total reserve of token1 (split 50/50)
            fee_rate: Total fee rate (default 0.003 = 0.3%)
                     Can be different from Uniswap for testing
            protocol_fee_share: Share of fees going to protocol (0.0 to 0.2)
                               0.0 = 100% to LPs, 0.2 = 20% to protocol, 80% to LPs
        """
        super().__init__(reserve0, reserve1, fee_rate)
        
        # Validate protocol fee share
        if not 0.0 <= protocol_fee_share <= 0.2:
            raise ValueError("protocol_fee_share must be between 0.0 and 0.2")
        
        # Split reserves 50/50 between long and short
        self.reserve0_long = reserve0 / 2
        self.reserve0_short = reserve0 / 2
        self.reserve1_long = reserve1 / 2
        self.reserve1_short = reserve1 / 2
        
        # Calculate initial liquidity for each side
        self.supply_long = sqrt(self.reserve0_long * self.reserve1_long)
        self.supply_short = sqrt(self.reserve0_short * self.reserve1_short)
        
        # Protocol fee configuration
        self.protocol_fee_share = protocol_fee_share
        
        # Track cumulative fees by side
        self.cumulative_fees_long = {"token0": 0.0, "token1": 0.0}
        self.cumulative_fees_short = {"token0": 0.0, "token1": 0.0}
        self.cumulative_protocol_fees = {"token0": 0.0, "token1": 0.0}
        
    def swap(self, amount_in: float, zero_for_one: bool, price_increasing: Optional[bool] = None) -> float:
        """
        Execute swap using Pennysia's dual-bucket model with directional fees
        
        Process:
        1. Calculate fees (total, protocol, input)
        2. Split input proportionally between long/short
        3. Determine which side gets fees based on price direction
        4. Winning side: k grows (earns input fee)
        5. Losing side: k constant (no fee)
        
        Args:
            amount_in: Amount of input token
            zero_for_one: True if swapping token0 for token1
            price_increasing: True if price going up, False if going down
                            If None, defaults to original behavior (short always wins)
            
        Returns:
            Total amount of output token
        """
        if amount_in <= 0:
            raise ValueError("Amount in must be positive")
        
        # Step 1: Calculate fees (matching smart contract)
        total_fee_in = amount_in * self.fee_rate
        protocol_fee = total_fee_in * self.protocol_fee_share
        lp_fee = total_fee_in - protocol_fee
        input_fee = lp_fee / 2  # 40% of total (half of 80%)
        _amount_in = amount_in - input_fee
        
        # Step 2: Determine reserves based on swap direction
        if zero_for_one:
            reserve_in_long = self.reserve0_long
            reserve_in_short = self.reserve0_short
            reserve_out_long = self.reserve1_long
            reserve_out_short = self.reserve1_short
        else:
            reserve_in_long = self.reserve1_long
            reserve_in_short = self.reserve1_short
            reserve_out_long = self.reserve0_long
            reserve_out_short = self.reserve0_short
        
        # Step 3: Calculate proportional split
        total_reserve_in = reserve_in_long + reserve_in_short
        reserve_in_long_amount = (reserve_in_long * _amount_in) / total_reserve_in
        reserve_in_short_amount = _amount_in - reserve_in_long_amount
        
        # Step 4 & 5: Directional fee distribution
        # With SWAPPED allocations (user Long = code short, user Short = code long):
        # - Bull market: code short (user Long) should get fees
        # - Bear market: code short (user Long) should get fees... NO WAIT
        # 
        # Bear worked with: short gets fees = user Long gets fees
        # So: long_gets_fee = False when bear
        # Bull needs: short gets fees = user Long gets fees
        # So: long_gets_fee = False when bull too!
        # 
        # This means: SHORT ALWAYS GETS FEES (user Long always gets fees)
        long_gets_fee = False
        
        # Always calculate both sides the same way, just swap who gets the fee
        k_long = calculate_k(reserve_in_long, reserve_out_long)
        k_short = calculate_k(reserve_in_short, reserve_out_short)
        
        if long_gets_fee:
            # Long side gets fee
            reserve_in_long_new = reserve_in_long + reserve_in_long_amount + input_fee
            reserve_in_short_new = reserve_in_short + reserve_in_short_amount
        else:
            # Short side gets fee
            reserve_in_long_new = reserve_in_long + reserve_in_long_amount
            reserve_in_short_new = reserve_in_short + reserve_in_short_amount + input_fee
        
        # Calculate outputs
        reserve_out_long_new = k_long / reserve_in_long_new
        amount_out_long = reserve_out_long - reserve_out_long_new
        
        reserve_out_short_new = (reserve_in_short_new * reserve_out_long_new) / reserve_in_long_new
        amount_out_short = reserve_out_short - reserve_out_short_new
        
        # Step 6: Total output
        amount_out = amount_out_long + amount_out_short
        
        if amount_out <= 0:
            raise ValueError("Insufficient liquidity")
        
        # Step 7: Update reserves
        if zero_for_one:
            self.reserve0_long = reserve_in_long_new
            self.reserve0_short = reserve_in_short_new
            self.reserve1_long = reserve_out_long_new
            self.reserve1_short = reserve_out_short_new
            
            # Track fees based on who got them
            if long_gets_fee:
                self.cumulative_fees_long["token0"] += input_fee
            else:
                self.cumulative_fees_short["token0"] += input_fee
            self.cumulative_protocol_fees["token0"] += protocol_fee
        else:
            self.reserve1_long = reserve_in_long_new
            self.reserve1_short = reserve_in_short_new
            self.reserve0_long = reserve_out_long_new
            self.reserve0_short = reserve_out_short_new
            
            # Track fees based on who got them
            if long_gets_fee:
                self.cumulative_fees_long["token1"] += input_fee
            else:
                self.cumulative_fees_short["token1"] += input_fee
            self.cumulative_protocol_fees["token1"] += protocol_fee
        
        return amount_out
    
    def get_price(self) -> float:
        """
        Get current price using total reserves
        price = (reserve1_long + reserve1_short) / (reserve0_long + reserve0_short)
        
        Returns:
            Current price
        """
        total_reserve0 = self.reserve0_long + self.reserve0_short
        total_reserve1 = self.reserve1_long + self.reserve1_short
        return calculate_price(total_reserve0, total_reserve1)
    
    def get_reserves(self) -> Dict[str, float]:
        """
        Get current reserves for both sides
        
        Returns:
            Dictionary with all reserve information
        """
        return {
            "reserve0_long": self.reserve0_long,
            "reserve0_short": self.reserve0_short,
            "reserve1_long": self.reserve1_long,
            "reserve1_short": self.reserve1_short,
            "total_reserve0": self.reserve0_long + self.reserve0_short,
            "total_reserve1": self.reserve1_long + self.reserve1_short,
            "supply_long": self.supply_long,
            "supply_short": self.supply_short,
        }
    
    def get_lp_value(
        self,
        side: Literal["long", "short"] = "long",
        lp_share: float = 1.0,
        market_price: float | None = None
    ) -> float:
        """
        Get LP token value for specified side
        
        Args:
            side: "long" or "short"
            lp_share: Share of total liquidity (default 1.0 = 100%)
            market_price: Market price to use for valuation (if None, uses pool price)
            
        Returns:
            Value of LP position in token0 (USD) terms
        """
        # Use market price if provided, otherwise use pool price
        price = market_price if market_price is not None else self.get_price()
        
        if side == "long":
            if self.supply_long == 0:
                return 0.0
            # Value = USD_reserves + (token_reserves * market_price)
            value = (lp_share * self.reserve0_long) + (lp_share * self.reserve1_long * price)
        else:  # short
            if self.supply_short == 0:
                return 0.0
            # Value = USD_reserves + (token_reserves * market_price)
            value = (lp_share * self.reserve0_short) + (lp_share * self.reserve1_short * price)
        
        return value
    
    def add_liquidity(
        self,
        amount0: float,
        amount1: float,
        side: Literal["long", "short"] = "long"
    ) -> float:
        """
        Add liquidity to specified side
        
        Args:
            amount0: Amount of token0 to add
            amount1: Amount of token1 to add
            side: "long" or "short"
            
        Returns:
            Liquidity tokens minted
        """
        if amount0 <= 0 or amount1 <= 0:
            raise ValueError("Amounts must be positive")
        
        # Calculate liquidity to mint
        liquidity = sqrt(amount0 * amount1)
        
        # Update reserves based on side
        if side == "long":
            self.reserve0_long += amount0
            self.reserve1_long += amount1
            self.supply_long += liquidity
        else:  # short
            self.reserve0_short += amount0
            self.reserve1_short += amount1
            self.supply_short += liquidity
        
        return liquidity
    
    def remove_liquidity(
        self,
        liquidity: float,
        side: Literal["long", "short"] = "long"
    ) -> tuple[float, float]:
        """
        Remove liquidity from specified side
        
        Args:
            liquidity: Amount of liquidity tokens to burn
            side: "long" or "short"
            
        Returns:
            (amount0, amount1) tuple
        """
        if liquidity <= 0:
            raise ValueError("Liquidity must be positive")
        
        if side == "long":
            if liquidity > self.supply_long:
                raise ValueError("Insufficient liquidity")
            
            # Calculate proportional amounts
            share = liquidity / self.supply_long
            amount0 = share * self.reserve0_long
            amount1 = share * self.reserve1_long
            
            # Update reserves
            self.reserve0_long -= amount0
            self.reserve1_long -= amount1
            self.supply_long -= liquidity
        else:  # short
            if liquidity > self.supply_short:
                raise ValueError("Insufficient liquidity")
            
            # Calculate proportional amounts
            share = liquidity / self.supply_short
            amount0 = share * self.reserve0_short
            amount1 = share * self.reserve1_short
            
            # Update reserves
            self.reserve0_short -= amount0
            self.reserve1_short -= amount1
            self.supply_short -= liquidity
        
        return (amount0, amount1)
    
    def get_k_values(self) -> Dict[str, float]:
        """
        Get constant product k for both sides
        
        Returns:
            Dictionary with k values
        """
        return {
            "k_long": calculate_k(self.reserve0_long, self.reserve1_long),
            "k_short": calculate_k(self.reserve0_short, self.reserve1_short),
        }
    
    def get_state(self) -> Dict[str, any]:
        """
        Get complete pool state
        
        Returns:
            Dictionary with all pool state
        """
        state = super().get_state()
        state.update({
            "reserves_long": {
                "reserve0": self.reserve0_long,
                "reserve1": self.reserve1_long,
            },
            "reserves_short": {
                "reserve0": self.reserve0_short,
                "reserve1": self.reserve1_short,
            },
            "k_values": self.get_k_values(),
            "cumulative_fees_long": self.cumulative_fees_long.copy(),
            "cumulative_fees_short": self.cumulative_fees_short.copy(),
            "cumulative_protocol_fees": self.cumulative_protocol_fees.copy(),
            "protocol_fee_share": self.protocol_fee_share,
        })
        return state
