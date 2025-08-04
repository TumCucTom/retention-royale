#!/usr/bin/env python3
"""
Test script to verify data collection setup
"""

import os
import sys
from clash_royale_api_client import ClashRoyaleAPI

def test_api_connection():
    """Test basic API connection"""
    api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
    
    if not api_token:
        print("❌ CLASH_ROYALE_API_TOKEN not set")
        print("Please set your API token:")
        print("export CLASH_ROYALE_API_TOKEN='your_token_here'")
        return False
    
    try:
        print("🔗 Testing API connection...")
        api = ClashRoyaleAPI(api_token)
        
        # Test cards endpoint (doesn't require specific player data)
        print("📊 Fetching cards data...")
        cards = api.get_cards()
        print(f"✅ Successfully fetched {len(cards)} cards")
        
        # Test tournaments endpoint
        print("🏆 Fetching tournaments data...")
        tournaments = api.get_tournaments(limit=5)
        print(f"✅ Successfully fetched {len(tournaments)} tournaments")
        
        print("\n🎉 API connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your API token is correct")
        print("2. Check your internet connection")
        print("3. Ensure your token has proper permissions")
        return False

def test_data_collector():
    """Test data collector functionality"""
    try:
        print("\n📦 Testing data collector...")
        from data_collector import DataCollector
        
        api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
        if not api_token:
            print("❌ API token not available for collector test")
            return False
        
        collector = DataCollector(api_token, "test_data")
        print("✅ Data collector initialized successfully")
        
        # Test cards collection
        print("🃏 Testing cards collection...")
        cards_data = collector.collect_cards_data()
        if cards_data:
            print(f"✅ Cards collection successful: {cards_data.get('total_cards', 0)} cards")
        
        # Test tournaments collection
        print("🏆 Testing tournaments collection...")
        tournaments_data = collector.collect_tournaments_data(limit=5)
        if tournaments_data:
            print(f"✅ Tournaments collection successful: {tournaments_data.get('total_tournaments', 0)} tournaments")
        
        print("\n🎉 Data collector test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Data collector test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Clash Royale Data Collection Setup")
    print("=" * 50)
    
    # Test API connection
    api_ok = test_api_connection()
    
    # Test data collector
    collector_ok = test_data_collector()
    
    print("\n" + "=" * 50)
    if api_ok and collector_ok:
        print("✅ All tests passed! You're ready to collect data.")
        print("\nNext steps:")
        print("1. Add real player tags to run_data_collection.py")
        print("2. Run: python run_data_collection.py")
        print("3. Review the collected data in the 'data' directory")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Set your API token: export CLASH_ROYALE_API_TOKEN='your_token'")
        print("2. Get a token from: https://developer.clashofclans.com/")
        print("3. Check your internet connection")

if __name__ == "__main__":
    main() 