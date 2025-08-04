#!/usr/bin/env python3
"""
Data Collector for Clash Royale Retention Analysis

This script downloads comprehensive data from the Clash Royale API
to support retention algorithm development and analysis.

Data collected:
- Player profiles and statistics
- Battle history and patterns
- Card information and meta data
- Tournament data
- Play session analysis
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
import pandas as pd

from clash_royale_api_client import ClashRoyaleAPI, PlayerStats, Battle, Card, Deck


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollector:
    """Comprehensive data collector for Clash Royale retention analysis"""
    
    def __init__(self, api_token: str, output_dir: str = "data"):
        """
        Initialize the data collector
        
        Args:
            api_token: Clash Royale API token
            output_dir: Directory to save collected data
        """
        self.api = ClashRoyaleAPI(api_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "players").mkdir(exist_ok=True)
        (self.output_dir / "battles").mkdir(exist_ok=True)
        (self.output_dir / "cards").mkdir(exist_ok=True)
        (self.output_dir / "tournaments").mkdir(exist_ok=True)
        (self.output_dir / "analysis").mkdir(exist_ok=True)
        
        logger.info(f"Data will be saved to: {self.output_dir}")
    
    def collect_player_data(self, player_tags: List[str], max_battles: int = 50) -> Dict:
        """
        Collect comprehensive data for multiple players
        
        Args:
            player_tags: List of player tags to collect data for
            max_battles: Maximum number of battles to collect per player
            
        Returns:
            Dictionary with collection summary
        """
        logger.info(f"Starting data collection for {len(player_tags)} players")
        
        collected_data = {
            'players': [],
            'battles': [],
            'cards_used': set(),
            'collection_time': datetime.now().isoformat(),
            'summary': {
                'total_players': len(player_tags),
                'successful_collections': 0,
                'failed_collections': 0,
                'total_battles': 0,
                'unique_cards': 0
            }
        }
        
        for i, player_tag in enumerate(player_tags, 1):
            logger.info(f"Collecting data for player {i}/{len(player_tags)}: {player_tag}")
            
            try:
                # Get player profile
                player = self.api.get_player(player_tag)
                player_data = {
                    'tag': player.tag,
                    'name': player.name,
                    'level': player.level,
                    'trophies': player.trophies,
                    'best_trophies': player.best_trophies,
                    'wins': player.wins,
                    'losses': player.losses,
                    'win_rate': player.win_rate,
                    'total_donations': player.total_donations,
                    'clan': player.clan,
                    'arena': player.arena,
                    'current_deck': None
                }
                
                # Add current deck if available
                if player.current_deck:
                    player_data['current_deck'] = {
                        'cards': [{'id': card.id, 'name': card.name, 'level': card.level, 
                                  'elixir_cost': card.elixir_cost} for card in player.current_deck.cards],
                        'average_elixir': player.current_deck.average_elixir
                    }
                
                collected_data['players'].append(player_data)
                
                # Get battle history
                battles = self.api.get_player_battles(player_tag, limit=max_battles)
                
                for battle in battles:
                    battle_data = {
                        'player_tag': player_tag,
                        'battle_time': battle.battle_time.isoformat(),
                        'type': battle.type,
                        'is_ladder_tournament': battle.is_ladder_tournament,
                        'arena': battle.arena,
                        'game_mode': battle.game_mode,
                        'deck_selection': battle.deck_selection,
                        'is_win': battle.is_win,
                        'crowns': battle.crowns,
                        'opponent_crowns': battle.opponent_crowns,
                        'trophy_change': battle.trophy_change,
                        'crown_difference': battle.crown_difference,
                        'is_close_match': battle.is_close_match,
                        'team': battle.team,
                        'opponent': battle.opponent
                    }
                    
                    collected_data['battles'].append(battle_data)
                    
                    # Track cards used
                    for player_data in battle.team:
                        if 'cards' in player_data:
                            for card in player_data['cards']:
                                collected_data['cards_used'].add(card['name'])
                
                collected_data['summary']['successful_collections'] += 1
                collected_data['summary']['total_battles'] += len(battles)
                
                # Save individual player data
                player_file = self.output_dir / "players" / f"player_{player_tag.replace('#', '')}.json"
                with open(player_file, 'w') as f:
                    json.dump(player_data, f, indent=2)
                
                # Save individual battle data
                battles_file = self.output_dir / "battles" / f"battles_{player_tag.replace('#', '')}.json"
                with open(battles_file, 'w') as f:
                    json.dump([battle_data for battle_data in collected_data['battles'] 
                             if battle_data['player_tag'] == player_tag], f, indent=2)
                
                logger.info(f"Collected {len(battles)} battles for {player.name}")
                
                # Rate limiting between players
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to collect data for {player_tag}: {e}")
                collected_data['summary']['failed_collections'] += 1
        
        collected_data['summary']['unique_cards'] = len(collected_data['cards_used'])
        collected_data['cards_used'] = list(collected_data['cards_used'])
        
        # Save comprehensive data
        with open(self.output_dir / "collected_data.json", 'w') as f:
            json.dump(collected_data, f, indent=2)
        
        logger.info(f"Data collection complete. Summary: {collected_data['summary']}")
        return collected_data
    
    def collect_cards_data(self) -> Dict:
        """
        Collect all available cards data
        
        Returns:
            Dictionary with cards data
        """
        logger.info("Collecting cards data...")
        
        try:
            cards = self.api.get_cards()
            
            cards_data = {
                'cards': cards,
                'collection_time': datetime.now().isoformat(),
                'total_cards': len(cards)
            }
            
            # Save cards data
            with open(self.output_dir / "cards" / "all_cards.json", 'w') as f:
                json.dump(cards_data, f, indent=2)
            
            # Create CSV for easier analysis
            cards_df = pd.DataFrame(cards)
            cards_df.to_csv(self.output_dir / "cards" / "all_cards.csv", index=False)
            
            logger.info(f"Collected data for {len(cards)} cards")
            return cards_data
            
        except Exception as e:
            logger.error(f"Failed to collect cards data: {e}")
            return {}
    
    def collect_tournaments_data(self, limit: int = 50) -> Dict:
        """
        Collect tournament data
        
        Args:
            limit: Number of tournaments to collect
            
        Returns:
            Dictionary with tournaments data
        """
        logger.info("Collecting tournaments data...")
        
        try:
            tournaments = self.api.get_tournaments(limit=limit)
            global_tournaments = self.api.get_global_tournaments()
            
            tournaments_data = {
                'tournaments': tournaments,
                'global_tournaments': global_tournaments,
                'collection_time': datetime.now().isoformat(),
                'total_tournaments': len(tournaments),
                'total_global_tournaments': len(global_tournaments)
            }
            
            # Save tournaments data
            with open(self.output_dir / "tournaments" / "tournaments.json", 'w') as f:
                json.dump(tournaments_data, f, indent=2)
            
            logger.info(f"Collected data for {len(tournaments)} tournaments and {len(global_tournaments)} global tournaments")
            return tournaments_data
            
        except Exception as e:
            logger.error(f"Failed to collect tournaments data: {e}")
            return {}
    
    def create_analysis_datasets(self) -> Dict:
        """
        Create analysis-ready datasets from collected data
        
        Returns:
            Dictionary with analysis datasets
        """
        logger.info("Creating analysis datasets...")
        
        # Load collected data
        try:
            with open(self.output_dir / "collected_data.json", 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error("No collected data found. Run data collection first.")
            return {}
        
        # Create player analysis dataset
        players_df = pd.DataFrame(data['players'])
        players_df.to_csv(self.output_dir / "analysis" / "players_analysis.csv", index=False)
        
        # Create battles analysis dataset
        battles_df = pd.DataFrame(data['battles'])
        if not battles_df.empty:
            battles_df['battle_time'] = pd.to_datetime(battles_df['battle_time'])
            battles_df.to_csv(self.output_dir / "analysis" / "battles_analysis.csv", index=False)
        
        # Create session analysis
        session_data = self._analyze_sessions(data['battles'])
        session_df = pd.DataFrame(session_data)
        if not session_df.empty:
            session_df.to_csv(self.output_dir / "analysis" / "sessions_analysis.csv", index=False)
        
        # Create retention indicators
        retention_data = self._create_retention_indicators(data)
        retention_df = pd.DataFrame(retention_data)
        if not retention_df.empty:
            retention_df.to_csv(self.output_dir / "analysis" / "retention_indicators.csv", index=False)
        
        analysis_summary = {
            'players_analysis': len(players_df),
            'battles_analysis': len(battles_df),
            'sessions_analysis': len(session_df),
            'retention_indicators': len(retention_df),
            'created_at': datetime.now().isoformat()
        }
        
        with open(self.output_dir / "analysis" / "analysis_summary.json", 'w') as f:
            json.dump(analysis_summary, f, indent=2)
        
        logger.info("Analysis datasets created successfully")
        return analysis_summary
    
    def _analyze_sessions(self, battles: List[Dict]) -> List[Dict]:
        """Analyze play sessions from battle data"""
        sessions = []
        
        # Group battles by player and analyze sessions
        player_battles = {}
        for battle in battles:
            player_tag = battle['player_tag']
            if player_tag not in player_battles:
                player_battles[player_tag] = []
            player_battles[player_tag].append(battle)
        
        for player_tag, player_battles_list in player_battles.items():
            # Sort battles by time
            player_battles_list.sort(key=lambda x: x['battle_time'])
            
            current_session = []
            session_start = None
            
            for battle in player_battles_list:
                battle_time = datetime.fromisoformat(battle['battle_time'])
                
                if not current_session:
                    # Start new session
                    current_session = [battle]
                    session_start = battle_time
                else:
                    # Check if this battle is within 30 minutes of the last one
                    last_battle_time = datetime.fromisoformat(current_session[-1]['battle_time'])
                    time_diff = (battle_time - last_battle_time).total_seconds() / 60
                    
                    if time_diff <= 30:
                        # Continue current session
                        current_session.append(battle)
                    else:
                        # End current session and start new one
                        if current_session:
                            session_data = self._analyze_session(current_session, session_start)
                            sessions.append(session_data)
                        
                        current_session = [battle]
                        session_start = battle_time
            
            # Don't forget the last session
            if current_session:
                session_data = self._analyze_session(current_session, session_start)
                sessions.append(session_data)
        
        return sessions
    
    def _analyze_session(self, session_battles: List[Dict], session_start: datetime) -> Dict:
        """Analyze a single play session"""
        wins = sum(1 for battle in session_battles if battle['is_win'])
        losses = len(session_battles) - wins
        win_rate = (wins / len(session_battles) * 100) if session_battles else 0
        
        # Calculate session duration
        session_end = datetime.fromisoformat(session_battles[-1]['battle_time'])
        duration_minutes = (session_end - session_start).total_seconds() / 60
        
        # Calculate trophy change
        trophy_changes = [battle['trophy_change'] for battle in session_battles 
                         if battle['trophy_change'] is not None]
        net_trophy_change = sum(trophy_changes) if trophy_changes else 0
        
        return {
            'player_tag': session_battles[0]['player_tag'],
            'session_start': session_start.isoformat(),
            'session_end': session_end.isoformat(),
            'duration_minutes': duration_minutes,
            'battles_count': len(session_battles),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'net_trophy_change': net_trophy_change,
            'avg_crown_difference': sum(battle['crown_difference'] for battle in session_battles) / len(session_battles),
            'close_matches': sum(1 for battle in session_battles if battle['is_close_match'])
        }
    
    def _create_retention_indicators(self, data: Dict) -> List[Dict]:
        """Create retention-related indicators for each player"""
        retention_data = []
        
        for player in data['players']:
            player_battles = [b for b in data['battles'] if b['player_tag'] == player['tag']]
            
            if not player_battles:
                continue
            
            # Calculate retention indicators
            recent_battles = sorted(player_battles, key=lambda x: x['battle_time'])[-10:]
            recent_win_rate = sum(1 for b in recent_battles if b['is_win']) / len(recent_battles) * 100
            
            # Session frequency (battles per day)
            battle_times = [datetime.fromisoformat(b['battle_time']) for b in player_battles]
            if len(battle_times) > 1:
                time_span = (max(battle_times) - min(battle_times)).days + 1
                battles_per_day = len(player_battles) / time_span
            else:
                battles_per_day = 1
            
            # Engagement indicators
            close_matches_rate = sum(1 for b in player_battles if b['is_close_match']) / len(player_battles) * 100
            trophy_volatility = sum(abs(b['trophy_change']) for b in player_battles if b['trophy_change'] is not None)
            
            retention_data.append({
                'player_tag': player['tag'],
                'player_name': player['name'],
                'level': player['level'],
                'trophies': player['trophies'],
                'overall_win_rate': player['win_rate'],
                'recent_win_rate': recent_win_rate,
                'battles_per_day': battles_per_day,
                'close_matches_rate': close_matches_rate,
                'trophy_volatility': trophy_volatility,
                'total_battles': len(player_battles),
                'has_current_deck': player['current_deck'] is not None,
                'retention_risk_score': self._calculate_retention_risk(player, player_battles)
            })
        
        return retention_data
    
    def _calculate_retention_risk(self, player: Dict, battles: List[Dict]) -> float:
        """Calculate a retention risk score (0-100, higher = higher risk)"""
        risk_score = 0
        
        # Factors that increase retention risk
        if player['win_rate'] < 40:
            risk_score += 20
        elif player['win_rate'] < 50:
            risk_score += 10
        
        if player['level'] < 10:
            risk_score += 15
        
        if len(battles) < 5:
            risk_score += 25
        
        # Recent performance
        if battles:
            recent_battles = sorted(battles, key=lambda x: x['battle_time'])[-5:]
            recent_wins = sum(1 for b in recent_battles if b['is_win'])
            if recent_wins == 0:
                risk_score += 30
            elif recent_wins <= 1:
                risk_score += 15
        
        # Trophy loss streak
        if battles:
            trophy_changes = [b['trophy_change'] for b in battles if b['trophy_change'] is not None]
            if trophy_changes and sum(trophy_changes) < -100:
                risk_score += 20
        
        return min(risk_score, 100)


def main():
    """Main function to run data collection"""
    parser = argparse.ArgumentParser(description='Collect Clash Royale data for retention analysis')
    parser.add_argument('--api-token', required=True, help='Clash Royale API token')
    parser.add_argument('--output-dir', default='data', help='Output directory for data')
    parser.add_argument('--player-tags', nargs='+', help='Player tags to collect data for')
    parser.add_argument('--max-battles', type=int, default=50, help='Maximum battles per player')
    parser.add_argument('--collect-cards', action='store_true', help='Collect cards data')
    parser.add_argument('--collect-tournaments', action='store_true', help='Collect tournaments data')
    parser.add_argument('--create-analysis', action='store_true', help='Create analysis datasets')
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = DataCollector(args.api_token, args.output_dir)
    
    # Collect player data if tags provided
    if args.player_tags:
        collector.collect_player_data(args.player_tags, args.max_battles)
    
    # Collect additional data
    if args.collect_cards:
        collector.collect_cards_data()
    
    if args.collect_tournaments:
        collector.collect_tournaments_data()
    
    # Create analysis datasets
    if args.create_analysis:
        collector.create_analysis_datasets()
    
    logger.info("Data collection complete!")


if __name__ == "__main__":
    main() 