"""
Mathematical utilities for AMM calculations
"""

import math
from typing import Union


def sqrt(x: Union[int, float]) -> float:
    """
    Calculate square root (matching Solidity behavior)
    
    Args:
        x: Input value
        
    Returns:
        Square root of x
    """
    if x < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(x)


def safe_div(a: Union[int, float], b: Union[int, float]) -> float:
    """
    Safe division with zero check
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        a / b
        
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero")
    return a / b


def min_value(*args: Union[int, float]) -> Union[int, float]:
    """
    Return minimum value
    
    Args:
        *args: Values to compare
        
    Returns:
        Minimum value
    """
    return min(args)


def max_value(*args: Union[int, float]) -> Union[int, float]:
    """
    Return maximum value
    
    Args:
        *args: Values to compare
        
    Returns:
        Maximum value
    """
    return max(args)


def calculate_price(reserve0: float, reserve1: float) -> float:
    """
    Calculate price (reserve1 / reserve0)
    
    Args:
        reserve0: Reserve of token0
        reserve1: Reserve of token1
        
    Returns:
        Price of token0 in terms of token1
    """
    return safe_div(reserve1, reserve0)


def calculate_k(reserve0: float, reserve1: float) -> float:
    """
    Calculate constant product k = reserve0 * reserve1
    
    Args:
        reserve0: Reserve of token0
        reserve1: Reserve of token1
        
    Returns:
        Constant product k
    """
    return reserve0 * reserve1


def calculate_liquidity(amount0: float, amount1: float) -> float:
    """
    Calculate liquidity (geometric mean)
    L = sqrt(amount0 * amount1)
    
    Args:
        amount0: Amount of token0
        amount1: Amount of token1
        
    Returns:
        Liquidity value
    """
    return sqrt(amount0 * amount1)


def proportional_amounts(
    liquidity: float,
    total_liquidity: float,
    reserve0: float,
    reserve1: float
) -> tuple[float, float]:
    """
    Calculate proportional token amounts for given liquidity
    
    Args:
        liquidity: Liquidity amount
        total_liquidity: Total liquidity in pool
        reserve0: Reserve of token0
        reserve1: Reserve of token1
        
    Returns:
        (amount0, amount1) tuple
    """
    if total_liquidity == 0:
        return (0.0, 0.0)
    
    amount0 = (liquidity * reserve0) / total_liquidity
    amount1 = (liquidity * reserve1) / total_liquidity
    
    return (amount0, amount1)
