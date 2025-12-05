"""
Build a Python module with cached coins list from CoinGecko
This creates a .py file with all coins data for instant lookup
"""

import requests
import os


def fetch_and_build_cache(api_key: str):
    """
    Fetch coins list and build Python cache module
    
    Args:
        api_key: CoinGecko API key
    """
    print("=" * 80)
    print("BUILDING COINS CACHE MODULE")
    print("=" * 80)
    print()
    
    # Fetch coins list
    print("📡 Fetching coins list from CoinGecko...")
    
    url = "https://api.coingecko.com/api/v3/coins/list"
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    params = {'include_platform': 'false'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        coins = response.json()
        print(f"✅ Received {len(coins)} coins")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Build Python module
    print(f"\n📝 Building Python module...")
    
    output_path = "src/data/coins_cache.py"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        # Write header
        f.write('"""\n')
        f.write('CoinGecko Coins Cache\n')
        f.write('Auto-generated - Do not edit manually\n')
        f.write(f'Total coins: {len(coins)}\n')
        f.write('"""\n\n')
        
        # Write coins list
        f.write('# Complete list of coins from CoinGecko\n')
        f.write('COINS = [\n')
        
        for coin in coins:
            # Escape single quotes and backslashes in names and symbols
            name = coin['name'].replace("\\", "\\\\").replace("'", "\\'")
            symbol = coin['symbol'].replace("\\", "\\\\").replace("'", "\\'")
            coin_id = coin['id'].replace("\\", "\\\\").replace("'", "\\'")
            f.write(f"    {{'id': '{coin_id}', 'symbol': '{symbol}', 'name': '{name}'}},\n")
        
        f.write(']\n\n')
        
        # Write helper functions
        f.write('''
# Helper functions for quick lookup

def search_by_symbol(symbol: str, limit: int = 10):
    """
    Search coins by symbol (case-insensitive)
    
    Args:
        symbol: Token symbol (e.g., 'BTC', 'ETH')
        limit: Maximum results to return
        
    Returns:
        List of matching coins
    """
    symbol_lower = symbol.lower()
    results = []
    
    # Exact matches first
    for coin in COINS:
        if coin['symbol'].lower() == symbol_lower:
            results.append(coin)
            if len(results) >= limit:
                return results
    
    return results


def search_by_name(name: str, limit: int = 10):
    """
    Search coins by name (case-insensitive, partial match)
    
    Args:
        name: Token name (e.g., 'Bitcoin', 'Ethereum')
        limit: Maximum results to return
        
    Returns:
        List of matching coins
    """
    name_lower = name.lower()
    results = []
    
    # Exact matches first
    for coin in COINS:
        if coin['name'].lower() == name_lower:
            results.append(coin)
    
    # Then partial matches
    if len(results) < limit:
        for coin in COINS:
            if name_lower in coin['name'].lower() and coin not in results:
                results.append(coin)
                if len(results) >= limit:
                    break
    
    return results


def search(query: str, limit: int = 10):
    """
    Search coins by symbol or name
    
    Args:
        query: Search query (symbol or name)
        limit: Maximum results to return
        
    Returns:
        List of matching coins
    """
    # Try symbol first
    results = search_by_symbol(query, limit)
    
    # If no symbol matches, try name
    if not results:
        results = search_by_name(query, limit)
    
    return results


def get_coin_id(query: str):
    """
    Get coin ID from symbol or name
    
    Args:
        query: Token symbol or name
        
    Returns:
        Coin ID or None
    """
    results = search(query, limit=1)
    return results[0]['id'] if results else None


def get_all_coins():
    """Get all coins"""
    return COINS


def get_total_coins():
    """Get total number of coins"""
    return len(COINS)


def get_coin_by_id(coin_id: str):
    """
    Get coin information by CoinGecko ID
    
    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'sonic-2')
        
    Returns:
        Coin dict with id, symbol, name or None if not found
    """
    for coin in COINS:
        if coin['id'] == coin_id:
            return coin
    return None


def validate_coin_id(coin_id: str):
    """
    Validate if a coin ID exists in the database
    
    Args:
        coin_id: CoinGecko coin ID
        
    Returns:
        True if coin exists, False otherwise
    """
    return get_coin_by_id(coin_id) is not None
''')
    
    print(f"✅ Module saved to: {output_path}")
    print(f"   Total coins: {len(coins)}")
    print(f"   File size: ~{os.path.getsize(output_path) / 1024:.1f} KB")
    
    # Test the module
    print(f"\n🧪 Testing module...")
    
    # Import and test
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.data import coins_cache
    
    # Test search functionality
    test_queries = ['BTC', 'sonic', 'ethereum']
    for query in test_queries:
        results = coins_cache.search(query, limit=3)
        print(f"   Search '{query}': {len(results)} results")
        if results:
            print(f"      → {results[0]['name']} (ID: {results[0]['id']})")
    
    # Test ID lookup
    print(f"\n   Testing ID lookup:")
    test_ids = ['bitcoin', 'ethereum', 'sonic-2']
    for coin_id in test_ids:
        coin = coins_cache.get_coin_by_id(coin_id)
        if coin:
            print(f"   '{coin_id}': {coin['name']} ({coin['symbol'].upper()})")
        else:
            print(f"   '{coin_id}': Not found")
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS!")
    print("=" * 80)
    print("\nCoins cache module is ready!")
    print("\nUsage:")
    print("  from src.data.coins_cache import get_coin_by_id, validate_coin_id")
    print("  coin = get_coin_by_id('bitcoin')  # Returns {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}")
    print("  is_valid = validate_coin_id('ethereum')  # Returns True/False")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build coins cache module")
    parser.add_argument(
        "--api-key",
        type=str,
        help="CoinGecko API key (or set COINGECKO_API_KEY env variable)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    API_KEY = args.api_key or os.getenv('COINGECKO_API_KEY')
    
    if not API_KEY:
        print("=" * 80)
        print("❌ ERROR: No API key provided!")
        print("=" * 80)
        print("\nPlease provide your CoinGecko API key:")
        print("\n1. Command line:")
        print("   python scripts/build_coins_cache.py --api-key YOUR_KEY")
        print("\n2. Environment variable:")
        print("   export COINGECKO_API_KEY='YOUR_KEY'")
        print("   python scripts/build_coins_cache.py")
        print("\n3. Get a FREE API key:")
        print("   https://www.coingecko.com/en/api")
        print("\n" + "=" * 80)
        exit(1)
    
    # Build cache
    success = fetch_and_build_cache(API_KEY)
    
    if not success:
        exit(1)
