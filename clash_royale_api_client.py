#!/usr/bin/env python3
"""
Clash Royale API Client for Retention Analysis

This script fetches and parses data from the official Clash Royale API
to support player retention analysis and deck recommendation algorithms.

API Documentation: https://developer.clashofclans.com/
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from urllib.parse import quote


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Card:
    """Represents a Clash Royale card"""
    id: int
    name: str
    level: int
    max_level: int
    rarity: str
    elixir_cost: int
    icon_url: Optional[str] = None


@dataclass
class Deck:
    """Represents a Clash Royale deck (8 cards)"""
    cards: List[Card]
    average_elixir: float
    
    def __post_init__(self):
        if len(self.cards) != 8:
            raise ValueError("A deck must contain exactly 8 cards")
        self.average_elixir = sum(card.elixir_cost for card in self.cards) / 8


@dataclass
class Battle:
    """Represents a Clash Royale battle"""
    type: str  # ladder, tournament, challenge, etc.
    battle_time: datetime
    is_ladder_tournament: bool
    arena: Dict
    game_mode: Dict
    deck_selection: str
    team: List[Dict]  # Player's team
    opponent: List[Dict]  # Opponent's team
    is_win: bool
    crowns: int
    opponent_crowns: int
    trophy_change: Optional[int] = None
    
    @property
    def crown_difference(self) -> int:
        """Returns the crown difference (positive = winning margin, negative = losing margin)"""
        return self.crowns - self.opponent_crowns
    
    @property
    def is_close_match(self) -> bool:
        """Returns True if the match was decided by 1 crown or less"""
        return abs(self.crown_difference) <= 1


@dataclass
class PlayerStats:
    """Represents player statistics and profile data"""
    tag: str
    name: str
    level: int
    trophies: int
    best_trophies: int
    wins: int
    losses: int
    total_donations: int
    clan: Optional[Dict] = None
    arena: Optional[Dict] = None
    current_deck: Optional[Deck] = None
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        total_games = self.wins + self.losses
        return (self.wins / total_games * 100) if total_games > 0 else 0.0


class ClashRoyaleAPI:
    """
    Official Clash Royale API client
    
    API Base URL: https://api.clashroyale.com/v1
    Documentation: https://developer.clashofclans.com/
    """
    
    BASE_URL = "https://api.clashroyale.com/v1"
    
    def __init__(self, api_token: str):
        """
        Initialize the API client
        
        Args:
            api_token: Your API token from https://developer.clashofclans.com/
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
            "User-Agent": "ClashRoyaleRetentionAnalyzer/1.0"
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a rate-limited request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            logger.debug(f"API Request: {url} - Status: {response.status_code}")
            return response.json()
            
        except requests.HTTPError as e:
            logger.error(f"API request failed: {url} - {e}")
            if response.status_code == 404:
                logger.error("Player/Clan not found")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                time.sleep(1)  # Wait before retrying
            raise
    
    def get_player(self, player_tag: str) -> PlayerStats:
        """
        Get player information
        
        Args:
            player_tag: Player tag (with or without #)
            
        Returns:
            PlayerStats object with player information
        """
        # Ensure proper tag formatting
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag}"
        
        # URL encode the tag
        encoded_tag = quote(player_tag, safe='')
        
        data = self._make_request(f"/players/{encoded_tag}")
        
        # Parse current deck if available
        current_deck = None
        if 'currentDeck' in data:
            deck_cards = []
            for card_data in data['currentDeck']:
                card = Card(
                    id=card_data['id'],
                    name=card_data['name'],
                    level=card_data['level'],
                    max_level=card_data['maxLevel'],
                    rarity=card_data.get('rarity', 'common'),
                    elixir_cost=card_data.get('elixirCost', 0),
                    icon_url=card_data.get('iconUrls', {}).get('medium')
                )
                deck_cards.append(card)
            
            if len(deck_cards) == 8:
                current_deck = Deck(cards=deck_cards, average_elixir=0)  # Will be calculated in __post_init__
        
        return PlayerStats(
            tag=data['tag'],
            name=data['name'],
            level=data['expLevel'],
            trophies=data['trophies'],
            best_trophies=data['bestTrophies'],
            wins=data['wins'],
            losses=data['losses'],
            total_donations=data['totalDonations'],
            clan=data.get('clan'),
            arena=data.get('arena'),
            current_deck=current_deck
        )
    
    def get_player_battles(self, player_tag: str, limit: int = 25) -> List[Battle]:
        """
        Get player's recent battle log
        
        Args:
            player_tag: Player tag (with or without #)
            limit: Number of battles to retrieve (max 25)
            
        Returns:
            List of Battle objects
        """
        # Ensure proper tag formatting
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag}"
        
        # URL encode the tag
        encoded_tag = quote(player_tag, safe='')
        
        data = self._make_request(f"/players/{encoded_tag}/battlelog")
        
        battles = []
        for battle_data in data[:limit]:
            # Parse battle time
            battle_time = datetime.strptime(battle_data['battleTime'], '%Y%m%dT%H%M%S.%fZ')
            
            # Determine if player won
            team_crowns = battle_data['team'][0]['crowns']
            opponent_crowns = battle_data['opponent'][0]['crowns']
            is_win = team_crowns > opponent_crowns
            
            # Get trophy change if available (ladder matches)
            trophy_change = None
            if 'trophyChange' in battle_data['team'][0]:
                trophy_change = battle_data['team'][0]['trophyChange']
            
            battle = Battle(
                type=battle_data['type'],
                battle_time=battle_time,
                is_ladder_tournament=battle_data.get('isLadderTournament', False),
                arena=battle_data.get('arena', {}),
                game_mode=battle_data.get('gameMode', {}),
                deck_selection=battle_data.get('deckSelection', 'collection'),
                team=battle_data['team'],
                opponent=battle_data['opponent'],
                is_win=is_win,
                crowns=team_crowns,
                opponent_crowns=opponent_crowns,
                trophy_change=trophy_change
            )
            battles.append(battle)
        
        return battles
    
    def get_cards(self) -> List[Dict]:
        """
        Get all available cards
        
        Returns:
            List of card data dictionaries
        """
        return self._make_request("/cards")['items']
    
    def get_tournaments(self, name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Search for tournaments
        
        Args:
            name: Tournament name to search for
            limit: Number of results to return
            
        Returns:
            List of tournament data
        """
        params = {'limit': limit}
        if name:
            params['name'] = name
            
        return self._make_request("/tournaments", params=params)['items']
    
    def get_global_tournaments(self) -> List[Dict]:
        """
        Get global tournament information
        
        Returns:
            List of global tournaments
        """
        return self._make_request("/globaltournaments")['items']


class RoyaleAPIClient:
    """
    Alternative API client using RoyaleAPI (community-maintained)
    Note: RoyaleAPI has discontinued their public API as of 2020
    This is kept here for reference and potential future use
    """
    
    BASE_URL = "https://royaleapi.com/api"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize RoyaleAPI client
        Note: Public API is discontinued
        """
        logger.warning("RoyaleAPI has discontinued their public API as of March 2020")
        self.api_token = api_token


def analyze_play_patterns(battles: List[Battle]) -> Dict:
    """
    Analyze play patterns from battle history
    
    Args:
        battles: List of Battle objects
        
    Returns:
        Dictionary with analysis results
    """
    if not battles:
        return {}
    
    total_battles = len(battles)
    wins = sum(1 for b in battles if b.is_win)
    losses = total_battles - wins
    
    # Calculate streaks
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    current_streak_type = None
    
    win_streaks = []
    loss_streaks = []
    
    for battle in battles:
        if current_streak_type is None:
            current_streak_type = 'win' if battle.is_win else 'loss'
            current_streak = 1
        elif (current_streak_type == 'win' and battle.is_win) or \
             (current_streak_type == 'loss' and not battle.is_win):
            current_streak += 1
        else:
            # Streak ended
            if current_streak_type == 'win':
                win_streaks.append(current_streak)
                max_win_streak = max(max_win_streak, current_streak)
            else:
                loss_streaks.append(current_streak)
                max_loss_streak = max(max_loss_streak, current_streak)
            
            current_streak_type = 'win' if battle.is_win else 'loss'
            current_streak = 1
    
    # Don't forget the last streak
    if current_streak_type == 'win':
        win_streaks.append(current_streak)
        max_win_streak = max(max_win_streak, current_streak)
    else:
        loss_streaks.append(current_streak)
        max_loss_streak = max(max_loss_streak, current_streak)
    
    # Analyze crown differences
    crown_diffs = [b.crown_difference for b in battles]
    close_matches = sum(1 for b in battles if b.is_close_match)
    
    # Trophy changes (ladder only)
    trophy_changes = [b.trophy_change for b in battles if b.trophy_change is not None]
    
    # Time patterns
    battle_times = [b.battle_time for b in battles]
    time_gaps = []
    for i in range(1, len(battle_times)):
        gap = (battle_times[i-1] - battle_times[i]).total_seconds() / 60  # minutes
        time_gaps.append(gap)
    
    return {
        'total_battles': total_battles,
        'wins': wins,
        'losses': losses,
        'win_rate': (wins / total_battles * 100) if total_battles > 0 else 0,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'avg_win_streak': sum(win_streaks) / len(win_streaks) if win_streaks else 0,
        'avg_loss_streak': sum(loss_streaks) / len(loss_streaks) if loss_streaks else 0,
        'close_matches': close_matches,
        'close_match_rate': (close_matches / total_battles * 100) if total_battles > 0 else 0,
        'avg_crown_difference': sum(crown_diffs) / len(crown_diffs) if crown_diffs else 0,
        'avg_trophy_change': sum(trophy_changes) / len(trophy_changes) if trophy_changes else 0,
        'avg_time_between_battles': sum(time_gaps) / len(time_gaps) if time_gaps else 0,
        'session_data': {
            'time_gaps': time_gaps,
            'battle_times': [t.isoformat() for t in battle_times]
        }
    }


def main():
    """
    Example usage of the Clash Royale API client
    """
    # You need to get your API token from https://developer.clashofclans.com/
    api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
    
    if not api_token:
        print("Please set CLASH_ROYALE_API_TOKEN environment variable")
        print("Get your token from: https://developer.clashofclans.com/")
        return
    
    # Initialize API client
    api = ClashRoyaleAPI(api_token)
    
    # Example player tag (replace with actual player tag)
    player_tag = "#8L9L9GL"  # This is just an example
    
    try:
        # Get player information
        print(f"Fetching player data for {player_tag}...")
        player = api.get_player(player_tag)
        print(f"Player: {player.name}")
        print(f"Level: {player.level}")
        print(f"Trophies: {player.trophies} (Best: {player.best_trophies})")
        print(f"Win Rate: {player.win_rate:.1f}%")
        
        if player.current_deck:
            print(f"Current Deck Average Elixir: {player.current_deck.average_elixir:.1f}")
        
        # Get battle history
        print(f"\nFetching battle history...")
        battles = api.get_player_battles(player_tag, limit=25)
        print(f"Retrieved {len(battles)} battles")
        
        # Analyze play patterns
        analysis = analyze_play_patterns(battles)
        print(f"\nPlay Pattern Analysis:")
        print(f"Recent Win Rate: {analysis['win_rate']:.1f}%")
        print(f"Max Win Streak: {analysis['max_win_streak']}")
        print(f"Max Loss Streak: {analysis['max_loss_streak']}")
        print(f"Close Matches: {analysis['close_match_rate']:.1f}%")
        print(f"Average Time Between Battles: {analysis['avg_time_between_battles']:.1f} minutes")
        
        # Save data for further analysis
        output_data = {
            'player': asdict(player),
            'battles': [asdict(battle) for battle in battles],
            'analysis': analysis,
            'fetched_at': datetime.now().isoformat()
        }
        
        with open(f'player_data_{player_tag.replace("#", "")}.json', 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\nData saved to player_data_{player_tag.replace('#', '')}.json")
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()