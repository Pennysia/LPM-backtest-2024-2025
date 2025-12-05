"""
Fetch and cache the complete list of coins from CoinGecko
This creates a local database for faster token lookup
"""

import requests
import json
import os
from datetime import datetime
import sqlite3


class CoinsListManager:
    """Manage CoinGecko coins list database"""
    
    def __init__(self, api_key: str, db_path: str = "data/coins_database.db"):
        """
        Initialize coins list manager
        
        Args:
            api_key: CoinGecko API key
            db_path: Path to SQLite database file
        """
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': api_key
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with coins table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create coins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                platforms TEXT
            )
        ''')
        
        # Create metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Create indexes for faster search
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON coins(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON coins(name)')
        
        conn.commit()
        conn.close()
    
    def fetch_coins_list(self):
        """
        Fetch complete coins list from CoinGecko
        
        Returns:
            List of coin dictionaries
        """
        url = f"{self.base_url}/coins/list"
        params = {'include_platform': 'true'}
        
        print("📡 Fetching complete coins list from CoinGecko...")
        print("   This may take a moment...")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                coins = response.json()
                print(f"✅ Received {len(coins)} coins")
                return coins
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def save_to_database(self, coins):
        """
        Save coins list to SQLite database
        
        Args:
            coins: List of coin dictionaries
        """
        if not coins:
            print("❌ No coins to save")
            return
        
        print(f"\n💾 Saving {len(coins)} coins to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM coins')
        
        # Insert coins
        for coin in coins:
            platforms = json.dumps(coin.get('platforms', {}))
            cursor.execute(
                'INSERT INTO coins (id, symbol, name, platforms) VALUES (?, ?, ?, ?)',
                (coin['id'], coin['symbol'], coin['name'], platforms)
            )
        
        # Update metadata
        cursor.execute(
            'INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
            ('last_updated', datetime.now().isoformat())
        )
        cursor.execute(
            'INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
            ('total_coins', str(len(coins)))
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database saved to: {self.db_path}")
    
    def save_to_json(self, coins, filepath: str = "data/coins_list.json"):
        """
        Save coins list to JSON file (backup)
        
        Args:
            coins: List of coin dictionaries
            filepath: Output file path
        """
        if not coins:
            print("❌ No coins to save")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Add metadata
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_coins': len(coins),
            'coins': coins
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ JSON backup saved to: {filepath}")
    
    def search_coins(self, query: str, limit: int = 10):
        """
        Search for coins in local database
        
        Args:
            query: Search query (name or symbol)
            limit: Maximum results to return
            
        Returns:
            List of matching coins
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search by symbol or name (case-insensitive)
        query_lower = query.lower()
        cursor.execute('''
            SELECT id, symbol, name, platforms
            FROM coins
            WHERE LOWER(symbol) = ? OR LOWER(name) LIKE ?
            ORDER BY 
                CASE 
                    WHEN LOWER(symbol) = ? THEN 0
                    WHEN LOWER(name) = ? THEN 1
                    ELSE 2
                END,
                name
            LIMIT ?
        ''', (query_lower, f'%{query_lower}%', query_lower, query_lower, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'platforms': json.loads(row[3]) if row[3] else {}
            })
        
        conn.close()
        return results
    
    def get_coin_by_id(self, coin_id: str):
        """
        Get coin details by ID
        
        Args:
            coin_id: CoinGecko coin ID
            
        Returns:
            Coin dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, symbol, name, platforms FROM coins WHERE id = ?',
            (coin_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'platforms': json.loads(row[3]) if row[3] else {}
            }
        return None
    
    def get_database_info(self):
        """
        Get database metadata
        
        Returns:
            Dictionary with database info
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get metadata
        cursor.execute('SELECT key, value FROM metadata')
        metadata = dict(cursor.fetchall())
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM coins')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'database_path': self.db_path,
            'total_coins': total,
            'last_updated': metadata.get('last_updated', 'Never'),
            'exists': os.path.exists(self.db_path)
        }
    
    def update_database(self):
        """
        Fetch latest coins list and update database
        
        Returns:
            True if successful, False otherwise
        """
        # Fetch coins
        coins = self.fetch_coins_list()
        
        if not coins:
            return False
        
        # Save to database
        self.save_to_database(coins)
        
        # Save JSON backup
        self.save_to_json(coins)
        
        # Print summary
        print("\n📊 Database Summary:")
        info = self.get_database_info()
        print(f"   Total coins: {info['total_coins']}")
        print(f"   Last updated: {info['last_updated']}")
        print(f"   Database: {info['database_path']}")
        
        return True


def main():
    """Main function to update coins database"""
    
    print("=" * 80)
    print("COINGECKO COINS DATABASE UPDATER")
    print("=" * 80)
    print()
    
    # Get API key
    API_KEY = os.getenv('COINGECKO_API_KEY')
    
    if not API_KEY:
        print("⚠️  No API key found!")
        print("\nPlease set your CoinGecko API key:")
        print("  export COINGECKO_API_KEY='your-api-key'")
        print("\nOr pass it as an argument:")
        print("  python scripts/update_coins_list.py --api-key YOUR_KEY")
        print("\nGet a free API key at: https://www.coingecko.com/en/api")
        return
    
    # Initialize manager
    manager = CoinsListManager(API_KEY)
    
    # Update database
    success = manager.update_database()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print("\nCoins database is ready to use!")
        print("\nYou can now search for coins offline:")
        print("  - Web interface will use local database")
        print("  - Much faster token lookup")
        print("  - No API calls needed for search")
    else:
        print("\n" + "=" * 80)
        print("❌ FAILED")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("1. Check your API key is valid")
        print("2. Check internet connection")
        print("3. Try again in a few minutes")


def test_search():
    """Test the search functionality"""
    
    print("\n" + "=" * 80)
    print("TESTING SEARCH FUNCTIONALITY")
    print("=" * 80)
    
    API_KEY = os.getenv('COINGECKO_API_KEY', 'test')
    manager = CoinsListManager(API_KEY)
    
    # Check if database exists
    info = manager.get_database_info()
    
    if info['total_coins'] == 0:
        print("\n⚠️  Database is empty. Run update first:")
        print("  python scripts/update_coins_list.py")
        return
    
    print(f"\n📊 Database has {info['total_coins']} coins")
    print(f"   Last updated: {info['last_updated']}")
    
    # Test searches
    test_queries = ['sonic', 'bitcoin', 'BTC', 'ethereum', 'ETH']
    
    for query in test_queries:
        print(f"\n🔍 Searching for '{query}'...")
        results = manager.search_coins(query, limit=5)
        
        if results:
            print(f"   Found {len(results)} matches:")
            for i, coin in enumerate(results, 1):
                print(f"   {i}. {coin['name']} ({coin['symbol'].upper()}) - ID: {coin['id']}")
        else:
            print(f"   No matches found")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update CoinGecko coins database")
    parser.add_argument(
        "--api-key",
        type=str,
        help="CoinGecko API key (or set COINGECKO_API_KEY env variable)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test search functionality"
    )
    
    args = parser.parse_args()
    
    # Set API key if provided
    if args.api_key:
        os.environ['COINGECKO_API_KEY'] = args.api_key
    
    if args.test:
        test_search()
    else:
        main()
