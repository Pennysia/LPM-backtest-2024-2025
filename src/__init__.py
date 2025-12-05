"""
Pennysia Backtest Framework
Comparing Pennysia vs Uniswap V2 AMM performance
"""

__version__ = "0.1.0"
__author__ = "Pennysia Team"

from src.pools import UniswapV2Pool, PennysiaPool
from src.simulation import SimulationEngine

__all__ = [
    "UniswapV2Pool",
    "PennysiaPool",
    "SimulationEngine",
]
