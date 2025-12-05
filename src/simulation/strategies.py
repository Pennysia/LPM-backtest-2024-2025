"""
LP Strategy definitions for backtesting
"""

from typing import Dict, Literal
from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """Configuration for an LP strategy"""
    name: str
    strategy_type: Literal["hodl", "hodl_token_only", "uniswap_v2", "pennysia"]
    
    # For Pennysia strategies
    long_allocation: float = 0.0  # 0.0 to 1.0
    short_allocation: float = 0.0  # 0.0 to 1.0
    
    # Initial capital
    initial_usd: float = 10000.0
    initial_token: float = 0.0  # Will be calculated based on initial price
    
    def __post_init__(self):
        """Validate allocations"""
        if self.strategy_type == "pennysia":
            total = self.long_allocation + self.short_allocation
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError(
                    f"Long + Short allocation must equal 1.0, got {total}"
                )


class StrategyFactory:
    """Factory to create standard strategy configurations"""
    
    @staticmethod
    def create_all_strategies(
        initial_usd: float = 10000.0
    ) -> Dict[str, StrategyConfig]:
        """
        Create all 7 standard strategies
        
        Args:
            initial_usd: Initial USD amount for each strategy
            
        Returns:
            Dictionary of strategy name -> StrategyConfig
        """
        strategies = {
            "2_hodl_token_only": StrategyConfig(
                name="HODL (100% Token)",
                strategy_type="hodl_token_only",
                initial_usd=initial_usd
            ),
            
            "3_uniswap_v2": StrategyConfig(
                name="Uniswap V2 LP",
                strategy_type="uniswap_v2",
                initial_usd=initial_usd
            ),
            
            "4_pennysia_100_0": StrategyConfig(
                name="Pennysia 100% Long",  # Wins in bull market (bullish)
                strategy_type="pennysia",
                long_allocation=0.0,
                short_allocation=1.0,
                initial_usd=initial_usd
            ),
            
            "5_pennysia_75_25": StrategyConfig(
                name="Pennysia 75% Long / 25% Short",  # Matches bull market performance
                strategy_type="pennysia",
                long_allocation=0.25,
                short_allocation=0.75,
                initial_usd=initial_usd
            ),
            
            "6_pennysia_50_50": StrategyConfig(
                name="Pennysia 50% Long / 50% Short",
                strategy_type="pennysia",
                long_allocation=0.5,
                short_allocation=0.5,
                initial_usd=initial_usd
            ),
            
            "7_pennysia_25_75": StrategyConfig(
                name="Pennysia 25% Long / 75% Short",  # Matches bear market performance
                strategy_type="pennysia",
                long_allocation=0.75,
                short_allocation=0.25,
                initial_usd=initial_usd
            ),
            
            "8_pennysia_0_100": StrategyConfig(
                name="Pennysia 100% Short",  # Wins in bear market (bearish)
                strategy_type="pennysia",
                long_allocation=1.0,
                short_allocation=0.0,
                initial_usd=initial_usd
            ),
        }
        
        return strategies
    
    @staticmethod
    def create_custom_strategy(
        name: str,
        strategy_type: Literal["hodl", "uniswap_v2", "pennysia"],
        initial_usd: float = 10000.0,
        long_allocation: float = 0.0,
        short_allocation: float = 0.0
    ) -> StrategyConfig:
        """
        Create a custom strategy
        
        Args:
            name: Strategy name
            strategy_type: Type of strategy
            initial_usd: Initial USD amount
            long_allocation: Long allocation (for Pennysia)
            short_allocation: Short allocation (for Pennysia)
            
        Returns:
            StrategyConfig instance
        """
        return StrategyConfig(
            name=name,
            strategy_type=strategy_type,
            initial_usd=initial_usd,
            long_allocation=long_allocation,
            short_allocation=short_allocation
        )


@dataclass
class StrategyState:
    """Track state of a strategy over time"""
    
    # Strategy config
    config: StrategyConfig
    
    # Current holdings
    usd_balance: float = 0.0
    token_balance: float = 0.0
    
    # For LP strategies
    lp_tokens_long: float = 0.0
    lp_tokens_short: float = 0.0
    
    # Performance tracking
    total_value_usd: float = 0.0
    total_value_history: list = None
    
    # Fees earned (for LP strategies)
    fees_earned_usd: float = 0.0
    fees_earned_token: float = 0.0
    
    def __post_init__(self):
        if self.total_value_history is None:
            self.total_value_history = []
    
    def update_value(self, current_price: float, pool=None):
        """
        Update total value based on current price
        
        Args:
            current_price: Current token price in USD
            pool: Pool instance (for LP strategies)
        """
        if self.config.strategy_type == "hodl":
            # Simple: USD + (tokens * price)
            self.total_value_usd = self.usd_balance + (self.token_balance * current_price)
        
        elif self.config.strategy_type == "hodl_token_only":
            # 100% token - just token value
            self.total_value_usd = self.token_balance * current_price
        
        elif self.config.strategy_type == "uniswap_v2":
            # Get LP value from pool
            if pool and pool.total_supply > 0:
                # Calculate share from absolute LP tokens
                lp_share = self.lp_tokens_long / pool.total_supply
                # LP value = proportional share of pool (already in USD/token0 terms)
                # Use market price for accurate valuation
                lp_value = pool.get_lp_value(lp_share=lp_share, market_price=current_price)
                self.total_value_usd = lp_value
            else:
                self.total_value_usd = 0.0
        
        elif self.config.strategy_type == "pennysia":
            # Get LP value from both sides
            if pool:
                long_value = 0.0
                short_value = 0.0
                
                if self.lp_tokens_long > 0 and pool.supply_long > 0:
                    # Calculate share from absolute LP tokens
                    lp_share_long = self.lp_tokens_long / pool.supply_long
                    # Use market price for accurate valuation
                    long_value = pool.get_lp_value(side="long", lp_share=lp_share_long, market_price=current_price)
                
                if self.lp_tokens_short > 0 and pool.supply_short > 0:
                    # Calculate share from absolute LP tokens
                    lp_share_short = self.lp_tokens_short / pool.supply_short
                    # Use market price for accurate valuation
                    short_value = pool.get_lp_value(side="short", lp_share=lp_share_short, market_price=current_price)
                
                # Values are already in USD/token0 terms, don't multiply by price
                self.total_value_usd = long_value + short_value
            else:
                self.total_value_usd = 0.0
        
        # Record history
        self.total_value_history.append(self.total_value_usd)
    
    def get_return(self) -> float:
        """
        Calculate return percentage
        
        Returns:
            Return as percentage (e.g., 25.5 for 25.5%)
        """
        initial_value = self.config.initial_usd
        if initial_value == 0:
            return 0.0
        
        return ((self.total_value_usd - initial_value) / initial_value) * 100
    
    def get_summary(self) -> dict:
        """
        Get summary of strategy performance
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "name": self.config.name,
            "type": self.config.strategy_type,
            "initial_value": self.config.initial_usd,
            "final_value": self.total_value_usd,
            "return_pct": self.get_return(),
            "return_absolute": self.total_value_usd - self.config.initial_usd,
            "usd_balance": self.usd_balance,
            "token_balance": self.token_balance,
            "lp_tokens_long": self.lp_tokens_long,
            "lp_tokens_short": self.lp_tokens_short,
            "fees_earned_usd": self.fees_earned_usd,
            "fees_earned_token": self.fees_earned_token,
        }
