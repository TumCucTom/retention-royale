#!/usr/bin/env python3
"""
Quick start script for data collection

This script helps you quickly start collecting data for retention analysis.
"""

import os
import sys
from data_collector import DataCollector

def main():
    """Quick start data collection"""
    
    # Check for API token
    api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
    if not api_token:
        print("❌ Error: CLASH_ROYALE_API_TOKEN environment variable not set")
        print("Please set your API token:")
        print("1. Get your token from: https://developer.clashofclans.com/")
        print("2. Set the environment variable:")
        print("   export CLASH_ROYALE_API_TOKEN='your_token_here'")
        return
    
    # Sample player tags for testing
    # Replace these with real player tags you want to analyze
    sample_player_tags = [
        "#8L9L9GL",  # Example tag 1
        "#2L0L0GL",  # Example tag 2
        "#9L9L9GL",  # Example tag 3
    ]
    
    print("🚀 Starting Clash Royale data collection...")
    print(f"📊 Will collect data for {len(sample_player_tags)} players")
    print("📁 Data will be saved to the 'data' directory")
    
    # Initialize collector
    collector = DataCollector(api_token, "data")
    
    try:
        # Collect player data
        print("\n📈 Collecting player data...")
        collected_data = collector.collect_player_data(sample_player_tags, max_battles=25)
        
        print(f"✅ Successfully collected data for {collected_data['summary']['successful_collections']} players")
        print(f"📊 Total battles collected: {collected_data['summary']['total_battles']}")
        print(f"🃏 Unique cards used: {collected_data['summary']['unique_cards']}")
        
        # Collect cards data
        print("\n🃏 Collecting cards data...")
        collector.collect_cards_data()
        
        # Collect tournaments data
        print("\n🏆 Collecting tournaments data...")
        collector.collect_tournaments_data(limit=20)
        
        # Create analysis datasets
        print("\n📊 Creating analysis datasets...")
        analysis_summary = collector.create_analysis_datasets()
        
        print("\n🎉 Data collection complete!")
        print("\n📁 Files created:")
        print("  - data/collected_data.json (raw data)")
        print("  - data/analysis/players_analysis.csv")
        print("  - data/analysis/battles_analysis.csv")
        print("  - data/analysis/sessions_analysis.csv")
        print("  - data/analysis/retention_indicators.csv")
        print("  - data/cards/all_cards.json")
        print("  - data/tournaments/tournaments.json")
        
        print("\n🔧 Next steps:")
        print("1. Review the collected data in the 'data' directory")
        print("2. Modify sample_players.txt with real player tags")
        print("3. Run the retention algorithm development scripts")
        
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        print("Please check your API token and try again.")


if __name__ == "__main__":
    main() 