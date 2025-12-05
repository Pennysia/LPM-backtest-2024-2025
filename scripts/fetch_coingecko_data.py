"""
Fetch historical price data from CoinGecko API
"""

import requests
import json
import csv
from datetime import datetime, timedelta
import time
import os
import sys

# Add src to path for coins_cache import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.data import coins_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("⚠️  Coins cache not found. Run: python scripts/build_coins_cache.py")


class CoinGeckoFetcher:
    """Fetch historical data from CoinGecko API"""
    
    def __init__(self, api_key: str):
        """
        Initialize fetcher
        
        Args:
            api_key: CoinGecko API key
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': api_key
        }
    
    def search_coin_local(self, query: str, limit: int = 10):
        """
        Search for a coin in local cache (faster, no API call)
        
        Args:
            query: Coin name or symbol
            limit: Maximum results
            
        Returns:
            List of matching coins
        """
        if not CACHE_AVAILABLE:
            print(f"⚠️  Coins cache not available")
            print("   Run: python scripts/build_coins_cache.py")
            print("   Falling back to API search...")
            return self.search_coin_api(query)
        
        try:
            # Use coins_cache module
            results = coins_cache.search(query, limit=limit)
            return results
            
        except Exception as e:
            print(f"⚠️  Cache error: {e}")
            print("   Falling back to API search...")
            return self.search_coin_api(query)
    
    def search_coin_api(self, query: str):
        """
        Search for a coin using CoinGecko API (fallback)
        
        Args:
            query: Coin name or symbol
            
        Returns:
            List of matching coins
        """
        url = f"{self.base_url}/search"
        params = {'query': query}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                return coins
            else:
                print(f"❌ Search error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def search_coin(self, query: str):
        """
        Search for a coin (tries local database first, then API)
        
        Args:
            query: Coin name or symbol
            
        Returns:
            List of matching coins
        """
        # Try local database first
        return self.search_coin_local(query)
    
    def get_coin_id(self, symbol_or_name: str):
        """
        Get CoinGecko coin ID from symbol or name
        
        Args:
            symbol_or_name: Coin symbol (e.g., "BTC") or name (e.g., "Bitcoin")
            
        Returns:
            Coin ID or None
        """
        print(f"🔍 Searching for '{symbol_or_name}'...")
        
        coins = self.search_coin(symbol_or_name)
        
        if not coins:
            print(f"❌ No coins found for '{symbol_or_name}'")
            return None
        
        # Show top matches
        print(f"\n📋 Found {len(coins)} matches:")
        for i, coin in enumerate(coins[:5], 1):
            print(f"   {i}. {coin['name']} ({coin['symbol'].upper()}) - ID: {coin['id']}")
        
        # Return the first match (usually most relevant)
        coin_id = coins[0]['id']
        print(f"\n✅ Using: {coins[0]['name']} (ID: {coin_id})")
        return coin_id
    
    def fetch_market_chart(
        self,
        coin_id: str,
        days: int = 365,
        vs_currency: str = "usd"
    ):
        """
        Fetch market chart data (price, volume, market cap)
        
        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin", "ethereum", "sonic-2")
            days: Number of days of historical data (1-365 or 'max')
            vs_currency: Currency to convert to (default "usd")
            
        Returns:
            Dictionary with prices, market_caps, total_volumes
        """
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        
        params = {
            'vs_currency': vs_currency,
            'days': days,
            'interval': 'daily' if days > 90 else 'hourly'
        }
        
        print(f"\n📡 Fetching {days} days of data for {coin_id}...")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we got data
                if 'prices' in data and len(data['prices']) > 0:
                    print(f"✅ Received {len(data['prices'])} data points")
                    return data
                else:
                    print(f"❌ No price data returned")
                    return None
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def process_market_chart(self, data):
        """
        Process market chart data into standardized format
        
        Args:
            data: Raw data from CoinGecko API
            
        Returns:
            List of processed data points
        """
        if not data:
            return []
        
        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])
        market_caps = data.get('market_caps', [])
        
        processed = []
        
        for i in range(len(prices)):
            timestamp_ms = prices[i][0]
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            
            price = prices[i][1]
            volume = volumes[i][1] if i < len(volumes) else 0
            market_cap = market_caps[i][1] if i < len(market_caps) else 0
            
            processed.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'price': price,
                'volume': volume,
                'market_cap': market_cap
            })
        
        return processed
    
    def save_to_csv(self, data, filepath):
        """
        Save data to CSV file
        
        Args:
            data: Processed data
            filepath: Output file path
        """
        if not data:
            print("❌ No data to save")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Saved to CSV: {filepath}")
    
    def save_to_json(self, data, filepath):
        """
        Save data to JSON file
        
        Args:
            data: Processed data
            filepath: Output file path
        """
        if not data:
            print("❌ No data to save")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Saved to JSON: {filepath}")
    
    def validate_coin_id(self, coin_id: str):
        """
        Validate coin ID against local cache
        
        Args:
            coin_id: CoinGecko coin ID
            
        Returns:
            Coin info dict if valid, None otherwise
        """
        if not CACHE_AVAILABLE:
            print("⚠️  Coins cache not available - skipping validation")
            return {'id': coin_id, 'symbol': '???', 'name': 'Unknown'}
        
        try:
            coin_info = coins_cache.get_coin_by_id(coin_id)
            if coin_info:
                print(f"✅ Validated: {coin_info['name']} ({coin_info['symbol'].upper()})")
                return coin_info
            else:
                print(f"❌ Token ID '{coin_id}' not found in database")
                print("💡 Find token IDs at coingecko.com (e.g., 'bitcoin', 'ethereum', 'sonic-2')")
                return None
        except Exception as e:
            print(f"⚠️  Validation error: {e}")
            return None
    
    def fetch_and_save(
        self,
        coin_identifier: str,
        days: int = 365,
        output_dir: str = "data/raw",
        use_coin_id: bool = False
    ):
        """
        Fetch data and save to both CSV and JSON
        
        Args:
            coin_identifier: Coin symbol/name (e.g., "sonic", "BTC") or coin ID if use_coin_id=True
            days: Number of days of historical data (default 365)
            output_dir: Output directory
            use_coin_id: If True, treat coin_identifier as coin ID directly
            
        Returns:
            Processed data
        """
        # Get coin ID
        if use_coin_id:
            coin_id = coin_identifier
            print(f"📊 Using coin ID: {coin_id}")
            
            # Validate the coin ID
            coin_info = self.validate_coin_id(coin_id)
            if not coin_info:
                print("❌ Invalid coin ID")
                return None
        else:
            coin_id = self.get_coin_id(coin_identifier)
            if not coin_id:
                return None
        
        # Fetch data
        raw_data = self.fetch_market_chart(coin_id, days=days)
        
        if not raw_data:
            print("❌ No data fetched")
            return None
        
        # Process data
        print("\n📊 Processing data...")
        data = self.process_market_chart(raw_data)
        
        if not data:
            print("❌ No data processed")
            return None
        
        # Generate filenames
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        safe_name = coin_id.replace(' ', '_').lower()
        csv_path = f"{output_dir}/{safe_name}_usd_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
        json_path = f"{output_dir}/{safe_name}_usd_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.json"
        
        # Save to both formats
        print("\n💾 Saving data...")
        self.save_to_csv(data, csv_path)
        self.save_to_json(data, json_path)
        
        # Print summary
        print("\n📈 Data Summary:")
        print(f"   Coin ID: {coin_id}")
        print(f"   Data points: {len(data)}")
        print(f"   Period: {days} days")
        print(f"   Start: {data[0]['timestamp']}")
        print(f"   End: {data[-1]['timestamp']}")
        print(f"   Initial price: ${data[0]['price']:.4f}")
        print(f"   Final price: ${data[-1]['price']:.4f}")
        
        price_change = ((data[-1]['price'] - data[0]['price']) / data[0]['price']) * 100
        print(f"   Price change: {price_change:+.2f}%")
        
        return data


def main():
    """Main function to fetch data"""
    
    print("=" * 80)
    print("COINGECKO DATA FETCHER")
    print("=" * 80)
    print()
    
    # Get API key from environment or prompt
    API_KEY = os.getenv('COINGECKO_API_KEY')
    
    if not API_KEY:
        print("⚠️  No API key found!")
        print("\nPlease set your CoinGecko API key:")
        print("  export COINGECKO_API_KEY='your-api-key'")
        print("\nOr pass it as an argument:")
        print("  python scripts/fetch_coingecko_data.py --api-key YOUR_KEY --coin sonic")
        print("\nGet a free API key at: https://www.coingecko.com/en/api")
        return
    
    # Initialize fetcher
    fetcher = CoinGeckoFetcher(API_KEY)
    
    # Fetch data for last 365 days
    data = fetcher.fetch_and_save(
        coin_identifier="sonic",  # Can be "sonic", "bitcoin", "BTC", etc.
        days=365,
        output_dir="data/raw"
    )
    
    if data:
        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        
        # Get the filename
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Try to get the actual coin ID used
        coin_id = fetcher.get_coin_id("sonic")
        if coin_id:
            safe_name = coin_id.replace(' ', '_').lower()
            filename = f"{safe_name}_usd_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
            print(f"\nYou can now run the simulation with:")
            print(f"  python scripts/run_simulation.py --data data/raw/{filename}")
    else:
        print("\n" + "=" * 80)
        print("❌ FAILED")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("1. Check if coin name/symbol is correct")
        print("2. Verify API key is valid")
        print("3. Try with a different coin (e.g., 'bitcoin', 'ethereum')")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch data from CoinGecko")
    parser.add_argument(
        "--api-key",
        type=str,
        help="CoinGecko API key (or set COINGECKO_API_KEY env variable)"
    )
    parser.add_argument(
        "--coin",
        type=str,
        default="sonic",
        help="Coin name, symbol, or ID (default: sonic)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of historical data (default: 365)"
    )
    parser.add_argument(
        "--use-id",
        action="store_true",
        help="Treat --coin as a CoinGecko coin ID directly"
    )
    
    args = parser.parse_args()
    
    # Get API key from argument or environment
    API_KEY = args.api_key or os.getenv('COINGECKO_API_KEY')
    
    if not API_KEY:
        print("=" * 80)
        print("❌ ERROR: No API key provided!")
        print("=" * 80)
        print("\nPlease provide your CoinGecko API key using one of these methods:")
        print("\n1. Command line argument:")
        print("   python scripts/fetch_coingecko_data.py --api-key YOUR_KEY --coin sonic")
        print("\n2. Environment variable:")
        print("   export COINGECKO_API_KEY='YOUR_KEY'")
        print("   python scripts/fetch_coingecko_data.py --coin sonic")
        print("\n3. Get a FREE API key at:")
        print("   https://www.coingecko.com/en/api")
        print("\n" + "=" * 80)
        exit(1)
    
    fetcher = CoinGeckoFetcher(API_KEY)
    
    data = fetcher.fetch_and_save(
        coin_identifier=args.coin,
        days=args.days,
        output_dir="data/raw",
        use_coin_id=args.use_id
    )
    
    if data:
        print("\n✅ Data fetched successfully!")
        
        # Generate filename
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        if args.use_id:
            safe_name = args.coin.replace(' ', '_').lower()
        else:
            coin_id = fetcher.get_coin_id(args.coin)
            safe_name = coin_id.replace(' ', '_').lower() if coin_id else args.coin.lower()
        
        filename = f"{safe_name}_usd_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
        print(f"\nRun simulation with:")
        print(f"  python scripts/run_simulation.py --data data/raw/{filename}")
