"""
LP Strategy Backtesting Engine

SIMULATION APPROACH:
1. Price Tracking: Execute arbitrage swap to move pool price to match market price
2. Volume Simulation: Execute additional directional swaps based on Vol/TVL ratio
3. Fee Distribution: Uniswap splits equally, Pennysia gives to short side (smart contract)

HOW VOL/TVL WORKS:
- Vol/TVL = 0: Only arbitrage swap (minimal fees)
- Vol/TVL = 3: Arbitrage + 3 additional swaps (higher fees)
- Each additional swap = 50% of arbitrage swap size (keeps it realistic)
- All swaps in same direction as price movement (directional volume)

EXAMPLE (Vol/TVL = 3, Price drops 10%):
- 1 arbitrage swap to track price
- 3 additional sell swaps (50% size each)
- Total: 4 swaps, all selling
- Pennysia Short gets fees from all swaps → significant advantage
"""

import pandas as pd
from typing import Dict, List, Optional
from src.pools import UniswapV2Pool, PennysiaPool
from src.simulation.strategies import StrategyConfig, StrategyState, StrategyFactory


class SimulationEngine:
    """
    Main simulation engine
    
    Simulates multiple LP strategies over historical price data
    """
    
    def __init__(
        self,
        price_data: pd.DataFrame,
        initial_capital_usd: float = 10000.0,
        fee_rate: float = 0.003,
        pennysia_protocol_share: float = 0.2,
        volume_tvl_ratio: float = 0.0
    ):
        """
        Initialize simulation engine
        
        Args:
            price_data: DataFrame with columns: timestamp, price, volume
            initial_capital_usd: Initial capital for each strategy
            fee_rate: Unified fee rate for both Uniswap V2 and Pennysia (e.g., 0.003 = 0.3%)
            pennysia_protocol_share: Pennysia protocol fee share (e.g., 0.2 = 20%)
            volume_tvl_ratio: Trading volume as multiple of pool TVL per period
                            (e.g., 3.2 means daily volume = 3.2x pool TVL)
                            Set to 0 to disable volume simulation
        """
        self.price_data = price_data
        self.initial_capital_usd = initial_capital_usd
        self.fee_rate = fee_rate
        self.pennysia_protocol_share = pennysia_protocol_share
        self.volume_tvl_ratio = volume_tvl_ratio
        
        # Get initial price
        self.initial_price = price_data["price"].iloc[0]
        self.previous_price = self.initial_price
        
        # Calculate initial token amount (50/50 split)
        usd_for_tokens = initial_capital_usd / 2
        self.initial_token_amount = usd_for_tokens / self.initial_price
        
        # Initialize pools
        self._initialize_pools()
        
        # Initialize strategies
        self.strategies: Dict[str, StrategyState] = {}
        self._initialize_strategies()
        
        # Store initial pool TVL for volume calculation reference (after strategies add liquidity)
        self.initial_pool_tvl = (self.uniswap_pool.reserve0 + 
                                self.uniswap_pool.reserve1 * self.initial_price)
        
        # Results
        self.results = None
        
    def _initialize_pools(self):
        """
        Initialize AMM pools with initial liquidity
        
        Both pools start empty and are filled by strategies for fair comparison.
        """
        # Uniswap V2 pool - start empty, will be filled by strategy
        uniswap_pool_usd = 0.0
        uniswap_pool_tokens = 0.0
        
        self.uniswap_pool = UniswapV2Pool(
            reserve0=uniswap_pool_usd,
            reserve1=uniswap_pool_tokens,
            fee_rate=self.fee_rate
        )
        
        # Pennysia pool - initialize empty, will be filled by strategies
        # This ensures all Pennysia strategies share the same pool with realistic sizing
        self.pennysia_pool = PennysiaPool(
            reserve0=0.0,  # Will be filled by strategy liquidity
            reserve1=0.0,
            fee_rate=self.fee_rate,
            protocol_fee_share=self.pennysia_protocol_share
        )
        
    def _initialize_strategies(self):
        """Initialize all strategy states"""
        # Get all standard strategies
        configs = StrategyFactory.create_all_strategies(self.initial_capital_usd)
        
        for key, config in configs.items():
            state = StrategyState(config=config)
            
            if config.strategy_type == "hodl":
                # 50/50 split
                state.usd_balance = self.initial_capital_usd / 2
                state.token_balance = self.initial_token_amount
                
            elif config.strategy_type == "hodl_token_only":
                # 100% token - no USD
                state.usd_balance = 0.0
                state.token_balance = self.initial_capital_usd / self.initial_price
                
            elif config.strategy_type == "uniswap_v2":
                # Add liquidity to Uniswap
                usd_amount = self.initial_capital_usd / 2
                token_amount = self.initial_token_amount
                
                lp_tokens = self.uniswap_pool.add_liquidity(usd_amount, token_amount)
                # Store absolute LP tokens (not share)
                state.lp_tokens_long = lp_tokens
                
            elif config.strategy_type == "pennysia":
                # Split capital between long and short
                usd_for_long = (self.initial_capital_usd / 2) * config.long_allocation
                usd_for_short = (self.initial_capital_usd / 2) * config.short_allocation
                tokens_for_long = self.initial_token_amount * config.long_allocation
                tokens_for_short = self.initial_token_amount * config.short_allocation
                
                # Add to long side
                if config.long_allocation > 0:
                    lp_long = self.pennysia_pool.add_liquidity(
                        usd_for_long,
                        tokens_for_long,
                        side="long"
                    )
                    # Store absolute LP tokens (not share)
                    state.lp_tokens_long = lp_long
                
                # Add to short side
                if config.short_allocation > 0:
                    lp_short = self.pennysia_pool.add_liquidity(
                        usd_for_short,
                        tokens_for_short,
                        side="short"
                    )
                    # Store absolute LP tokens (not share)
                    state.lp_tokens_short = lp_short
            
            self.strategies[key] = state
    
    def _get_pool_for_strategy(self, config: StrategyConfig):
        """Get the appropriate pool for a strategy"""
        if config.strategy_type == "uniswap_v2":
            return self.uniswap_pool
        elif config.strategy_type == "pennysia":
            return self.pennysia_pool
        return None
    
    def run(self, verbose: bool = True) -> pd.DataFrame:
        """
        Run the simulation
        
        Args:
            verbose: Print progress
            
        Returns:
            DataFrame with results
        """
        if verbose:
            print(f"🚀 Starting simulation...")
            print(f"   Initial capital: ${self.initial_capital_usd:,.2f}")
            print(f"   Initial price: ${self.initial_price:.4f}")
            print(f"   Time periods: {len(self.price_data)}")
            print(f"   Strategies: {len(self.strategies)}")
            print()
        
        # Simulate each time period
        for idx, row in self.price_data.iterrows():
            timestamp = row["timestamp"]
            price = row["price"]
            
            # New approach: Calculate exact swap needed to reach target price
            # Then scale fees by volume/TVL ratio
            if self.volume_tvl_ratio > 0:
                self._process_price_change(price)
            
            # Update previous price for next iteration
            self.previous_price = price
            
            # Update all strategy values
            for key, state in self.strategies.items():
                pool = self._get_pool_for_strategy(state.config)
                state.update_value(price, pool)
            
            # Progress update
            if verbose and idx % (len(self.price_data) // 10) == 0:
                progress = (idx / len(self.price_data)) * 100
                print(f"   Progress: {progress:.0f}% (Price: ${price:.4f})")
        
        if verbose:
            print("\n✅ Simulation complete!")
            print()
        
        # Generate results
        self.results = self._generate_results()
        return self.results
    
    def _calculate_swap_to_price(self, target_price: float, pool_type: str = "uniswap") -> tuple[float, bool]:
        """
        Calculate exact swap needed to move pool price to target using xy=k formula.
        
        Math:
        - Current: reserve_usd × reserve_token = k
        - Target: price = reserve_usd / reserve_token
        - Solve: reserve_token_new = sqrt(k / target_price)
        - Swap amount = difference between current and new reserves
        
        Why: AMM pools track market price through arbitrage. This calculates
        the exact arbitrage swap needed.
        
        Args:
            target_price: Market price to match (USD per token)
            pool_type: "uniswap" or "pennysia"
            
        Returns:
            (swap_amount, zero_for_one) where zero_for_one=True means selling tokens
        """
        if pool_type == "uniswap":
            reserve_usd = self.uniswap_pool.reserve0
            reserve_token = self.uniswap_pool.reserve1
        else:
            # For Pennysia, use combined reserves
            reserve_usd = self.pennysia_pool.reserve0_long + self.pennysia_pool.reserve0_short
            reserve_token = self.pennysia_pool.reserve1_long + self.pennysia_pool.reserve1_short
        
        if reserve_token == 0 or reserve_usd == 0:
            return (0.0, True)
        
        # Current pool price (USD per token)
        current_price = reserve_usd / reserve_token
        
        if current_price == 0 or target_price == 0:
            return (0.0, True)
        
        k = reserve_usd * reserve_token
        
        # Determine swap direction
        if target_price > current_price:
            # Price going up: need to buy tokens (USD → Token)
            # This removes tokens from pool, increases USD
            # New price = reserve_usd' / reserve_token'
            # reserve_usd' * reserve_token' = k
            # target_price = reserve_usd' / reserve_token'
            # reserve_usd' = target_price * reserve_token'
            # (target_price * reserve_token') * reserve_token' = k
            # reserve_token'^2 = k / target_price
            reserve_token_new = (k / target_price) ** 0.5
            swap_amount = (reserve_token - reserve_token_new) * current_price  # USD to swap in
            zero_for_one = True  # USD → Token (buying tokens)
        else:
            # Price going down: need to sell tokens (Token → USD)
            # This adds tokens to pool, decreases USD
            # target_price = reserve_usd' / reserve_token'
            # reserve_usd' = target_price * reserve_token'
            # reserve_token'^2 = k / target_price
            reserve_token_new = (k / target_price) ** 0.5
            swap_amount = reserve_token_new - reserve_token  # Tokens to swap in
            zero_for_one = False  # Token → USD (selling tokens)
        
        return (abs(swap_amount), zero_for_one)
    
    def _process_price_change(self, target_price: float):
        """
        Simulate daily price movement and trading volume.
        
        Method:
        1. Calculate and execute swap to move pool price to market price
        2. Execute additional swaps based on Vol/TVL ratio to simulate volume
        
        Why Vol/TVL matters:
        - Vol/TVL = 3.2 means pool TVL trades 3.2 times per day
        - We execute the price-moving swap 3 times (int(3.2))
        - Each swap generates fees through pool's built-in mechanism
        - In Pennysia: winning side gets ALL input fees, losing side gets nothing
        - In Uniswap: fees split equally among all LPs
        
        Result: Higher volume = more fees = better differentiation between strategies
        
        Args:
            target_price: Market price to match
        """
        # Determine price direction for Pennysia's directional fees
        current_price = self.pennysia_pool.get_price()
        price_increasing = target_price > current_price
        
        # Step 1: Execute directional swap to reach target price
        swap_amount_uni, zero_for_one_uni = self._calculate_swap_to_price(target_price, "uniswap")
        if swap_amount_uni > 0:
            try:
                self.uniswap_pool.swap(swap_amount_uni, zero_for_one_uni)
            except:
                pass
        
        swap_amount_pen, zero_for_one_pen = self._calculate_swap_to_price(target_price, "pennysia")
        if swap_amount_pen > 0:
            try:
                self.pennysia_pool.swap(swap_amount_pen, zero_for_one_pen, price_increasing)
            except:
                pass
        
        # Step 2: Volume simulation based on Vol/TVL ratio
        # 
        # Approach: Execute additional directional swaps in the same direction as price movement
        # This simulates real trading activity that follows the trend
        # 
        # Key constraints:
        # - Only execute if Vol/TVL > 0
        # - Each swap is small (5% of TVL max) to avoid unrealistic price impact
        # - Number of swaps scales with Vol/TVL ratio
        if self.volume_tvl_ratio > 0 and swap_amount_pen > 0:
            # Execute additional swaps in the direction of price movement
            # Vol/TVL = 1.0 means 1 additional swap, 3.0 means 3 additional swaps
            num_volume_swaps = int(self.volume_tvl_ratio)
            
            # Each volume swap is a fraction of the arbitrage swap to keep it realistic
            volume_swap_fraction = 0.5  # 50% of the arbitrage swap size
            
            for _ in range(num_volume_swaps):
                volume_swap_uni = swap_amount_uni * volume_swap_fraction
                volume_swap_pen = swap_amount_pen * volume_swap_fraction
                
                # Uniswap volume swap
                if volume_swap_uni > 0:
                    try:
                        self.uniswap_pool.swap(volume_swap_uni, zero_for_one_uni)
                    except:
                        break
                
                # Pennysia volume swap
                if volume_swap_pen > 0:
                    try:
                        self.pennysia_pool.swap(volume_swap_pen, zero_for_one_pen, price_increasing)
                    except:
                        break
    
    def _process_swaps(self, buy_volume: float, sell_volume: float, current_price: float):
        """
        Process swap volume for the period by splitting into multiple smaller swaps
        
        Args:
            buy_volume: USD volume of buys (USD → Token)
            sell_volume: USD volume of sells (Token → USD)
            current_price: Current token price
        """
        # Split volume into smaller chunks to simulate distributed trading
        # Max swap size: 10% of pool reserves (realistic for aggregated trades)
        uniswap_tvl = (self.uniswap_pool.reserve0 + 
                      self.uniswap_pool.reserve1 * current_price)
        pennysia_tvl = (self.pennysia_pool.reserve0_long + self.pennysia_pool.reserve0_short +
                       (self.pennysia_pool.reserve1_long + self.pennysia_pool.reserve1_short) * current_price)
        
        # Process buys (USD → Token) in chunks
        if buy_volume > 0:
            remaining_buy_uni = buy_volume
            remaining_buy_pen = buy_volume
            
            # Process Uniswap swaps
            while remaining_buy_uni > 0:
                max_swap_uni = uniswap_tvl * 0.1
                swap_amount = min(remaining_buy_uni, max_swap_uni)
                
                try:
                    self.uniswap_pool.swap(swap_amount, zero_for_one=True)
                    remaining_buy_uni -= swap_amount
                except:
                    break  # Stop if swap fails
                
                if swap_amount < 0.01:
                    break
            
            # Process Pennysia swaps
            while remaining_buy_pen > 0:
                max_swap_pen = pennysia_tvl * 0.1
                swap_amount = min(remaining_buy_pen, max_swap_pen)
                
                try:
                    self.pennysia_pool.swap(swap_amount, zero_for_one=True)
                    remaining_buy_pen -= swap_amount
                except:
                    break  # Stop if swap fails
                
                if swap_amount < 0.01:
                    break
        
        # Process sells (Token → USD) in chunks
        if sell_volume > 0:
            remaining_sell_uni = sell_volume
            remaining_sell_pen = sell_volume
            
            # Process Uniswap swaps
            while remaining_sell_uni > 0:
                max_swap_uni = uniswap_tvl * 0.1
                swap_amount_usd = min(remaining_sell_uni, max_swap_uni)
                token_amount = swap_amount_usd / current_price
                
                try:
                    self.uniswap_pool.swap(token_amount, zero_for_one=False)
                    remaining_sell_uni -= swap_amount_usd
                except:
                    break  # Stop if swap fails
                
                if swap_amount_usd < 0.01:
                    break
            
            # Process Pennysia swaps
            while remaining_sell_pen > 0:
                max_swap_pen = pennysia_tvl * 0.1
                swap_amount_usd = min(remaining_sell_pen, max_swap_pen)
                token_amount = swap_amount_usd / current_price
                
                try:
                    self.pennysia_pool.swap(token_amount, zero_for_one=False)
                    remaining_sell_pen -= swap_amount_usd
                except:
                    break  # Stop if swap fails
                
                if swap_amount_usd < 0.01:
                    break
    
    def _generate_results(self) -> pd.DataFrame:
        """Generate results DataFrame"""
        results = []
        
        for key, state in self.strategies.items():
            summary = state.get_summary()
            summary["strategy_id"] = key
            results.append(summary)
        
        df = pd.DataFrame(results)
        
        # Sort by return
        df = df.sort_values("return_pct", ascending=False)
        
        return df
    
    def print_results(self):
        """Print formatted results"""
        if self.results is None:
            print("No results yet. Run simulation first.")
            return
        
        print("=" * 80)
        print("SIMULATION RESULTS")
        print("=" * 80)
        print()
        
        # Price info
        final_price = self.price_data["price"].iloc[-1]
        price_change = ((final_price - self.initial_price) / self.initial_price) * 100
        
        print(f"📊 Market Performance:")
        print(f"   Initial Price: ${self.initial_price:.4f}")
        print(f"   Final Price:   ${final_price:.4f}")
        print(f"   Change:        {price_change:+.2f}%")
        print()
        
        # Strategy results
        print(f"🏆 Strategy Rankings:")
        print()
        
        for idx, row in self.results.iterrows():
            rank = idx + 1
            name = row["name"]
            initial = row["initial_value"]
            final = row["final_value"]
            return_pct = row["return_pct"]
            return_abs = row["return_absolute"]
            
            print(f"   #{rank}. {name}")
            print(f"       Initial: ${initial:,.2f}")
            print(f"       Final:   ${final:,.2f}")
            print(f"       Return:  {return_pct:+.2f}% (${return_abs:+,.2f})")
            print()
        
        print("=" * 80)
    
    def get_value_history(self) -> pd.DataFrame:
        """
        Get value history for all strategies
        
        Returns:
            DataFrame with timestamp and value for each strategy
        """
        data = {"timestamp": self.price_data["timestamp"]}
        
        for key, state in self.strategies.items():
            data[state.config.name] = state.total_value_history
        
        return pd.DataFrame(data)
    
    def export_results(self, filepath: str):
        """Export results to CSV"""
        if self.results is None:
            print("No results to export. Run simulation first.")
            return
        
        self.results.to_csv(filepath, index=False)
        print(f"Results exported to {filepath}")
