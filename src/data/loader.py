"""
Data loader for historical price and volume data
Supports CoinGecko API and CSV files
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime, timedelta


class PriceDataLoader:
    """Load and process historical price data"""
    
    def __init__(self):
        self.data = None
        
    def load_from_csv(
        self,
        filepath: str,
        date_column: str = "timestamp",
        price_column: str = "price",
        volume_column: Optional[str] = "volume"
    ) -> pd.DataFrame:
        """
        Load price data from CSV file
        
        Args:
            filepath: Path to CSV file
            date_column: Name of date/timestamp column
            price_column: Name of price column
            volume_column: Name of volume column (optional)
            
        Returns:
            DataFrame with processed data
        """
        df = pd.read_csv(filepath)
        
        # Parse dates
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column).reset_index(drop=True)
        
        # Rename columns to standard names
        df = df.rename(columns={
            date_column: "timestamp",
            price_column: "price"
        })
        
        if volume_column and volume_column in df.columns:
            df = df.rename(columns={volume_column: "volume"})
        else:
            # If no volume data, set to 0
            df["volume"] = 0.0
        
        self.data = df
        return df
    
    def load_from_coingecko_format(
        self,
        filepath: str
    ) -> pd.DataFrame:
        """
        Load data from CoinGecko CSV export format
        
        Expected columns: timestamp, price, market_cap, volume
        
        Args:
            filepath: Path to CoinGecko CSV file
            
        Returns:
            DataFrame with processed data
        """
        df = pd.read_csv(filepath)
        
        # CoinGecko format typically has: timestamp, price, market_cap, volume
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        elif "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
        else:
            raise ValueError("No timestamp or date column found")
        
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Ensure required columns exist
        if "price" not in df.columns:
            raise ValueError("No price column found")
        
        if "volume" not in df.columns:
            df["volume"] = 0.0
        
        # Keep only needed columns
        df = df[["timestamp", "price", "volume"]]
        
        self.data = df
        return df
    
    def generate_synthetic_data(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2025-12-31",
        initial_price: float = 1.0,
        volatility: float = 0.02,
        trend: float = 0.0001,
        mean_reversion: float = 0.1,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Generate synthetic price data using geometric Brownian motion
        with mean reversion
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_price: Starting price
            volatility: Daily volatility (e.g., 0.02 = 2%)
            trend: Daily drift (e.g., 0.0001 = 0.01%)
            mean_reversion: Mean reversion strength (0 to 1)
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with synthetic price data
        """
        np.random.seed(seed)
        
        # Generate date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.date_range(start, end, freq="1H")  # Hourly data
        
        n = len(dates)
        prices = np.zeros(n)
        prices[0] = initial_price
        
        # Generate prices with mean reversion
        for i in range(1, n):
            # Mean reversion component
            mean_rev = mean_reversion * (initial_price - prices[i-1])
            
            # Random shock
            shock = np.random.normal(0, volatility)
            
            # Update price
            prices[i] = prices[i-1] * (1 + trend + mean_rev + shock)
            
            # Ensure price stays positive
            prices[i] = max(prices[i], 0.01)
        
        # Generate synthetic volume (correlated with price changes)
        price_changes = np.abs(np.diff(prices, prepend=prices[0]))
        base_volume = 10000
        volumes = base_volume * (1 + price_changes / prices * 100)
        
        df = pd.DataFrame({
            "timestamp": dates,
            "price": prices,
            "volume": volumes
        })
        
        self.data = df
        return df
    
    def resample_data(
        self,
        frequency: str = "1D"
    ) -> pd.DataFrame:
        """
        Resample data to different frequency
        
        Args:
            frequency: Pandas frequency string (e.g., "1H", "1D", "1W")
            
        Returns:
            Resampled DataFrame
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data first.")
        
        df = self.data.set_index("timestamp")
        
        # Resample
        resampled = df.resample(frequency).agg({
            "price": "last",  # Last price in period
            "volume": "sum"   # Sum of volume
        }).reset_index()
        
        # Remove NaN values
        resampled = resampled.dropna()
        
        self.data = resampled
        return resampled
    
    def add_swap_events(
        self,
        volume_per_period: float = 1000.0,
        buy_sell_ratio: float = 0.5
    ) -> pd.DataFrame:
        """
        Add synthetic swap events based on volume
        
        Args:
            volume_per_period: Average volume per time period
            buy_sell_ratio: Ratio of buys to total (0.5 = balanced)
            
        Returns:
            DataFrame with swap events
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data first.")
        
        df = self.data.copy()
        
        # If volume is 0, use volume_per_period
        if df["volume"].sum() == 0:
            df["volume"] = volume_per_period
        
        # Split volume into buys and sells
        df["buy_volume"] = df["volume"] * buy_sell_ratio
        df["sell_volume"] = df["volume"] * (1 - buy_sell_ratio)
        
        # Calculate number of swaps (assume average swap size)
        avg_swap_size = 100  # USD
        df["num_buys"] = (df["buy_volume"] / avg_swap_size).astype(int)
        df["num_sells"] = (df["sell_volume"] / avg_swap_size).astype(int)
        
        self.data = df
        return df
    
    def get_summary(self) -> dict:
        """
        Get summary statistics of loaded data
        
        Returns:
            Dictionary with summary stats
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        df = self.data
        
        return {
            "start_date": df["timestamp"].min(),
            "end_date": df["timestamp"].max(),
            "num_periods": len(df),
            "initial_price": df["price"].iloc[0],
            "final_price": df["price"].iloc[-1],
            "min_price": df["price"].min(),
            "max_price": df["price"].max(),
            "mean_price": df["price"].mean(),
            "price_change": (df["price"].iloc[-1] / df["price"].iloc[0] - 1) * 100,
            "volatility": df["price"].pct_change().std() * 100,
            "total_volume": df["volume"].sum() if "volume" in df.columns else 0,
        }
    
    def save_to_csv(self, filepath: str):
        """Save processed data to CSV"""
        if self.data is None:
            raise ValueError("No data loaded")
        
        self.data.to_csv(filepath, index=False)
        print(f"Data saved to {filepath}")


def load_price_data(
    source: str = "synthetic",
    **kwargs
) -> Tuple[pd.DataFrame, dict]:
    """
    Convenience function to load price data
    
    Args:
        source: "synthetic", "csv", or "coingecko"
        **kwargs: Additional arguments for specific loaders
        
    Returns:
        (DataFrame, summary_dict) tuple
    """
    loader = PriceDataLoader()
    
    if source == "synthetic":
        df = loader.generate_synthetic_data(**kwargs)
    elif source == "csv":
        df = loader.load_from_csv(**kwargs)
    elif source == "coingecko":
        df = loader.load_from_coingecko_format(**kwargs)
    else:
        raise ValueError(f"Unknown source: {source}")
    
    summary = loader.get_summary()
    
    return df, summary
