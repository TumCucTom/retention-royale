#!/usr/bin/env python3
"""
Deck Analysis and Recommendation System for Clash Royale

This module analyzes deck compositions, card synergies, and meta matchups
to recommend decks that can achieve desired win/loss outcomes for retention optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from datetime import datetime
import statistics


logger = logging.getLogger(__name__)


@dataclass
class Card:
    """Represents a Clash Royale card with metadata"""
    id: int
    name: str
    elixir_cost: int
    rarity: str
    type: str  # spell, building, troop
    target: str  # air, ground, both
    damage_type: str  # area, single, both
    range: str  # melee, ranged, long
    speed: str  # slow, medium, fast, very_fast
    hit_points: int
    damage: int
    evolves: bool = False
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class DeckArchetype:
    """Represents a deck archetype with common cards and characteristics"""
    name: str
    core_cards: List[str]  # Cards that define this archetype
    common_cards: List[str]  # Cards often seen in this archetype
    playstyle: str  # control, beatdown, cycle, bait, etc.
    avg_elixir: float
    win_condition: str  # primary win condition card
    counter_archetypes: List[str]  # archetypes this counters
    countered_by: List[str]  # archetypes that counter this
    meta_viability: float  # 0.0 to 1.0, current meta strength


@dataclass
class MatchupData:
    """Data about specific deck vs deck matchups"""
    archetype_a: str
    archetype_b: str
    win_rate_a: float  # Win rate for archetype A against B
    sample_size: int
    confidence: float
    key_interactions: List[str]
    last_updated: datetime


class CardDatabase:
    """Database of all Clash Royale cards and their properties"""
    
    def __init__(self):
        self.cards: Dict[str, Card] = {}
        self.cards_by_id: Dict[int, Card] = {}
        self._load_default_cards()
    
    def _load_default_cards(self):
        """Load default card data (in a real system, this would come from the API)"""
        # This is a simplified set - in production you'd fetch from the API
        default_cards = [
            # Win Conditions
            {"id": 1, "name": "Hog Rider", "elixir_cost": 4, "rarity": "rare", "type": "troop", 
             "target": "ground", "damage_type": "single", "range": "melee", "speed": "very_fast",
             "hit_points": 1400, "damage": 260},
            {"id": 2, "name": "Royal Giant", "elixir_cost": 6, "rarity": "common", "type": "troop",
             "target": "both", "damage_type": "single", "range": "long", "speed": "slow",
             "hit_points": 2500, "damage": 270},
            {"id": 3, "name": "Giant", "elixir_cost": 5, "rarity": "rare", "type": "troop",
             "target": "ground", "damage_type": "single", "range": "melee", "speed": "slow",
             "hit_points": 3000, "damage": 200},
            {"id": 4, "name": "Balloon", "elixir_cost": 5, "rarity": "epic", "type": "troop",
             "target": "ground", "damage_type": "area", "range": "melee", "speed": "medium",
             "hit_points": 1200, "damage": 800},
            
            # Spells
            {"id": 10, "name": "Fireball", "elixir_cost": 4, "rarity": "rare", "type": "spell",
             "target": "both", "damage_type": "area", "range": "long", "speed": "fast",
             "hit_points": 0, "damage": 570},
            {"id": 11, "name": "Zap", "elixir_cost": 2, "rarity": "common", "type": "spell",
             "target": "both", "damage_type": "area", "range": "medium", "speed": "fast",
             "hit_points": 0, "damage": 180},
            {"id": 12, "name": "Lightning", "elixir_cost": 6, "rarity": "epic", "type": "spell",
             "target": "both", "damage_type": "single", "range": "long", "speed": "medium",
             "hit_points": 0, "damage": 870},
            
            # Support Cards
            {"id": 20, "name": "Wizard", "elixir_cost": 5, "rarity": "rare", "type": "troop",
             "target": "both", "damage_type": "area", "range": "ranged", "speed": "medium",
             "hit_points": 600, "damage": 280},
            {"id": 21, "name": "Musketeer", "elixir_cost": 4, "rarity": "rare", "type": "troop",
             "target": "both", "damage_type": "single", "range": "ranged", "speed": "medium",
             "hit_points": 650, "damage": 200},
            {"id": 22, "name": "Valkyrie", "elixir_cost": 4, "rarity": "rare", "type": "troop",
             "target": "ground", "damage_type": "area", "range": "melee", "speed": "medium",
             "hit_points": 1200, "damage": 180},
            
            # Defensive Cards
            {"id": 30, "name": "Cannon", "elixir_cost": 3, "rarity": "common", "type": "building",
             "target": "ground", "damage_type": "single", "range": "ranged", "speed": "fast",
             "hit_points": 800, "damage": 180},
            {"id": 31, "name": "Tesla", "elixir_cost": 4, "rarity": "common", "type": "building",
             "target": "both", "damage_type": "single", "range": "ranged", "speed": "fast",
             "hit_points": 900, "damage": 220},
            
            # Cycle Cards
            {"id": 40, "name": "Ice Spirit", "elixir_cost": 1, "rarity": "common", "type": "troop",
             "target": "both", "damage_type": "area", "range": "melee", "speed": "very_fast",
             "hit_points": 200, "damage": 180},
            {"id": 41, "name": "Skeletons", "elixir_cost": 1, "rarity": "common", "type": "troop",
             "target": "ground", "damage_type": "single", "range": "melee", "speed": "fast",
             "hit_points": 80, "damage": 80},
        ]
        
        for card_data in default_cards:
            card = Card(**card_data)
            self.cards[card.name] = card
            self.cards_by_id[card.id] = card
    
    def get_card(self, identifier: str) -> Optional[Card]:
        """Get card by name or ID"""
        if isinstance(identifier, int) or identifier.isdigit():
            return self.cards_by_id.get(int(identifier))
        return self.cards.get(identifier)
    
    def get_all_cards(self) -> List[Card]:
        """Get all cards in the database"""
        return list(self.cards.values())


class ArchetypeDatabase:
    """Database of deck archetypes and their characteristics"""
    
    def __init__(self):
        self.archetypes: Dict[str, DeckArchetype] = {}
        self._load_default_archetypes()
    
    def _load_default_archetypes(self):
        """Load default archetype data"""
        default_archetypes = [
            {
                "name": "Hog Cycle",
                "core_cards": ["Hog Rider", "Ice Spirit", "Skeletons"],
                "common_cards": ["Musketeer", "Cannon", "Fireball", "Zap"],
                "playstyle": "cycle",
                "avg_elixir": 2.8,
                "win_condition": "Hog Rider",
                "counter_archetypes": ["Beatdown", "Spell Bait"],
                "countered_by": ["Building Spam", "Heavy Control"],
                "meta_viability": 0.75
            },
            {
                "name": "Royal Giant",
                "core_cards": ["Royal Giant", "Lightning"],
                "common_cards": ["Wizard", "Valkyrie", "Musketeer", "Zap"],
                "playstyle": "beatdown",
                "avg_elixir": 4.2,
                "win_condition": "Royal Giant",
                "counter_archetypes": ["Building Decks", "Cycle Decks"],
                "countered_by": ["Heavy Beatdown", "Air Decks"],
                "meta_viability": 0.65
            },
            {
                "name": "Giant Beatdown",
                "core_cards": ["Giant", "Wizard"],
                "common_cards": ["Musketeer", "Valkyrie", "Fireball", "Zap"],
                "playstyle": "beatdown",
                "avg_elixir": 4.0,
                "win_condition": "Giant",
                "counter_archetypes": ["Cycle", "Bridge Spam"],
                "countered_by": ["Air Decks", "Heavy Control"],
                "meta_viability": 0.70
            },
            {
                "name": "LavaLoon",
                "core_cards": ["Balloon", "Lightning"],
                "common_cards": ["Wizard", "Valkyrie", "Tesla", "Zap"],
                "playstyle": "beatdown",
                "avg_elixir": 4.3,
                "win_condition": "Balloon",
                "counter_archetypes": ["Ground Heavy", "Building Spam"],
                "countered_by": ["Air Defense", "Fast Cycle"],
                "meta_viability": 0.60
            }
        ]
        
        for archetype_data in default_archetypes:
            archetype = DeckArchetype(**archetype_data)
            self.archetypes[archetype.name] = archetype
    
    def get_archetype(self, name: str) -> Optional[DeckArchetype]:
        """Get archetype by name"""
        return self.archetypes.get(name)
    
    def get_all_archetypes(self) -> List[DeckArchetype]:
        """Get all archetypes"""
        return list(self.archetypes.values())


class DeckAnalyzer:
    """Analyzes deck compositions and provides recommendations"""
    
    def __init__(self):
        self.card_db = CardDatabase()
        self.archetype_db = ArchetypeDatabase()
        self.matchup_data: Dict[Tuple[str, str], MatchupData] = {}
        self._load_matchup_data()
    
    def _load_matchup_data(self):
        """Load matchup win rates between archetypes"""
        # Simplified matchup data - in production this would come from real statistics
        matchups = [
            ("Hog Cycle", "Royal Giant", 0.45, 1000),
            ("Hog Cycle", "Giant Beatdown", 0.55, 800),
            ("Hog Cycle", "LavaLoon", 0.35, 600),
            ("Royal Giant", "Giant Beatdown", 0.50, 900),
            ("Royal Giant", "LavaLoon", 0.60, 700),
            ("Giant Beatdown", "LavaLoon", 0.40, 500),
        ]
        
        for archetype_a, archetype_b, win_rate, sample_size in matchups:
            key = (archetype_a, archetype_b)
            self.matchup_data[key] = MatchupData(
                archetype_a=archetype_a,
                archetype_b=archetype_b,
                win_rate_a=win_rate,
                sample_size=sample_size,
                confidence=min(1.0, sample_size / 1000),  # More samples = higher confidence
                key_interactions=[],
                last_updated=datetime.now()
            )
            
            # Add reverse matchup
            reverse_key = (archetype_b, archetype_a)
            self.matchup_data[reverse_key] = MatchupData(
                archetype_a=archetype_b,
                archetype_b=archetype_a,
                win_rate_a=1.0 - win_rate,
                sample_size=sample_size,
                confidence=min(1.0, sample_size / 1000),
                key_interactions=[],
                last_updated=datetime.now()
            )
    
    def identify_deck_archetype(self, deck_cards: List[str]) -> Tuple[str, float]:
        """
        Identify the archetype of a given deck
        
        Args:
            deck_cards: List of card names in the deck
            
        Returns:
            Tuple of (archetype_name, confidence_score)
        """
        if len(deck_cards) != 8:
            return "Unknown", 0.0
        
        best_match = "Unknown"
        best_score = 0.0
        
        for archetype in self.archetype_db.get_all_archetypes():
            score = self._calculate_archetype_match_score(deck_cards, archetype)
            if score > best_score:
                best_score = score
                best_match = archetype.name
        
        return best_match, best_score
    
    def _calculate_archetype_match_score(self, deck_cards: List[str], archetype: DeckArchetype) -> float:
        """Calculate how well a deck matches an archetype"""
        deck_set = set(deck_cards)
        
        # Core cards are essential
        core_matches = len(set(archetype.core_cards) & deck_set)
        core_score = core_matches / len(archetype.core_cards) if archetype.core_cards else 0
        
        # Common cards add to the score
        common_matches = len(set(archetype.common_cards) & deck_set)
        common_score = common_matches / max(1, len(archetype.common_cards))
        
        # Win condition must be present for high score
        win_con_score = 1.0 if archetype.win_condition in deck_set else 0.0
        
        # Combine scores with weights
        total_score = (core_score * 0.5 + common_score * 0.3 + win_con_score * 0.2)
        
        return total_score
    
    def get_matchup_win_rate(self, player_archetype: str, opponent_archetype: str) -> float:
        """Get expected win rate for player archetype vs opponent archetype"""
        key = (player_archetype, opponent_archetype)
        if key in self.matchup_data:
            return self.matchup_data[key].win_rate_a
        
        # Default to 50% if no specific data
        return 0.50
    
    def analyze_deck_vs_meta(self, deck_cards: List[str], meta_archetypes: List[str]) -> Dict:
        """
        Analyze how a deck performs against the current meta
        
        Args:
            deck_cards: List of card names in the deck
            meta_archetypes: List of common archetypes in current meta
            
        Returns:
            Dictionary with analysis results
        """
        player_archetype, confidence = self.identify_deck_archetype(deck_cards)
        
        matchup_results = {}
        total_win_rate = 0.0
        
        for opponent_archetype in meta_archetypes:
            win_rate = self.get_matchup_win_rate(player_archetype, opponent_archetype)
            matchup_results[opponent_archetype] = win_rate
            total_win_rate += win_rate
        
        avg_win_rate = total_win_rate / len(meta_archetypes) if meta_archetypes else 0.50
        
        # Calculate deck stats
        cards = [self.card_db.get_card(name) for name in deck_cards]
        valid_cards = [c for c in cards if c is not None]
        
        avg_elixir = sum(c.elixir_cost for c in valid_cards) / len(valid_cards) if valid_cards else 0
        
        return {
            "identified_archetype": player_archetype,
            "archetype_confidence": confidence,
            "average_elixir": avg_elixir,
            "meta_win_rate": avg_win_rate,
            "matchup_breakdown": matchup_results,
            "deck_analysis": {
                "win_conditions": [c.name for c in valid_cards if c.damage > 200 and c.hit_points > 800],
                "spells": [c.name for c in valid_cards if c.type == "spell"],
                "buildings": [c.name for c in valid_cards if c.type == "building"],
                "air_targeting": [c.name for c in valid_cards if c.target in ["air", "both"]],
            }
        }
    
    def recommend_deck_for_outcome(self, target_win_rate: float, opponent_archetype: str, 
                                   player_skill_level: str = "intermediate") -> List[Dict]:
        """
        Recommend decks that have the target win rate against opponent archetype
        
        Args:
            target_win_rate: Desired win rate (0.0 to 1.0)
            opponent_archetype: The archetype we're playing against
            player_skill_level: Player's skill level affects recommendations
            
        Returns:
            List of deck recommendations sorted by suitability
        """
        recommendations = []
        
        for archetype in self.archetype_db.get_all_archetypes():
            win_rate = self.get_matchup_win_rate(archetype.name, opponent_archetype)
            
            # Calculate how close this is to target
            win_rate_delta = abs(win_rate - target_win_rate)
            
            # Skill level adjustment
            skill_multiplier = {
                "beginner": 0.8,
                "intermediate": 1.0,
                "advanced": 1.2,
                "expert": 1.4
            }.get(player_skill_level, 1.0)
            
            # Meta viability matters
            meta_score = archetype.meta_viability
            
            # Calculate overall recommendation score
            score = (
                (1.0 - win_rate_delta) * 0.5 +  # How close to target
                meta_score * 0.3 +  # Current meta strength
                skill_multiplier * 0.2  # Skill level fit
            )
            
            # Generate sample deck for this archetype
            sample_deck = self._generate_sample_deck(archetype)
            
            recommendation = {
                "archetype": archetype.name,
                "sample_deck": sample_deck,
                "expected_win_rate": win_rate,
                "win_rate_delta": win_rate_delta,
                "meta_viability": meta_score,
                "recommendation_score": score,
                "playstyle": archetype.playstyle,
                "average_elixir": archetype.avg_elixir,
                "reasoning": self._generate_recommendation_reasoning(
                    archetype, win_rate, target_win_rate, opponent_archetype
                )
            }
            
            recommendations.append(recommendation)
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _generate_sample_deck(self, archetype: DeckArchetype) -> List[str]:
        """Generate a sample deck for an archetype"""
        deck = []
        
        # Add core cards
        deck.extend(archetype.core_cards)
        
        # Fill remaining slots with common cards
        remaining_slots = 8 - len(deck)
        common_cards = [card for card in archetype.common_cards if card not in deck]
        
        # Add common cards up to remaining slots
        deck.extend(common_cards[:remaining_slots])
        
        # If still need cards, add some defaults
        if len(deck) < 8:
            default_cards = ["Zap", "Fireball", "Musketeer", "Valkyrie", "Cannon"]
            for card in default_cards:
                if card not in deck and len(deck) < 8:
                    deck.append(card)
        
        return deck[:8]
    
    def _generate_recommendation_reasoning(self, archetype: DeckArchetype, 
                                           expected_win_rate: float, target_win_rate: float,
                                           opponent_archetype: str) -> str:
        """Generate human-readable reasoning for recommendation"""
        if abs(expected_win_rate - target_win_rate) < 0.05:
            return f"{archetype.name} has excellent matchup vs {opponent_archetype} " \
                   f"(~{expected_win_rate:.0%} win rate), perfectly matching your target."
        elif expected_win_rate > target_win_rate:
            return f"{archetype.name} over-performs vs {opponent_archetype} " \
                   f"(~{expected_win_rate:.0%} win rate), which may be too strong for retention goals."
        else:
            return f"{archetype.name} is slightly unfavored vs {opponent_archetype} " \
                   f"(~{expected_win_rate:.0%} win rate), creating engaging challenge."
    
    def optimize_deck_for_retention(self, current_deck: List[str], opponent_deck: List[str],
                                    target_outcome: str, player_data: Dict) -> Dict:
        """
        Optimize deck selection for player retention
        
        Args:
            current_deck: Player's current deck
            opponent_deck: Opponent's deck
            target_outcome: "win" or "loss" 
            player_data: Player statistics and preferences
            
        Returns:
            Recommendation with deck and reasoning
        """
        # Identify opponent archetype
        opp_archetype, opp_confidence = self.identify_deck_archetype(opponent_deck)
        
        # Set target win rate based on desired outcome
        if target_outcome == "win":
            target_win_rate = 0.65  # Favorable but not guaranteed
        else:
            target_win_rate = 0.35  # Challenging but winnable
        
        # Get recommendations
        recommendations = self.recommend_deck_for_outcome(
            target_win_rate, opp_archetype, player_data.get("skill_level", "intermediate")
        )
        
        # Analyze current deck
        current_analysis = self.analyze_deck_vs_meta(current_deck, [opp_archetype])
        
        best_recommendation = recommendations[0] if recommendations else None
        
        return {
            "target_outcome": target_outcome,
            "opponent_archetype": opp_archetype,
            "opponent_confidence": opp_confidence,
            "current_deck_analysis": current_analysis,
            "recommended_change": best_recommendation,
            "should_change_deck": (
                best_recommendation and 
                best_recommendation["recommendation_score"] > 0.7 and
                abs(current_analysis["meta_win_rate"] - target_win_rate) > 0.15
            ),
            "all_options": recommendations[:3]  # Top 3 options
        }


def main():
    """Example usage of the deck analyzer"""
    analyzer = DeckAnalyzer()
    
    # Example: Analyze a hog cycle deck
    hog_deck = ["Hog Rider", "Ice Spirit", "Skeletons", "Musketeer", "Cannon", "Fireball", "Zap", "Valkyrie"]
    
    print("=== Deck Analysis Example ===")
    archetype, confidence = analyzer.identify_deck_archetype(hog_deck)
    print(f"Deck Archetype: {archetype} (confidence: {confidence:.2f})")
    
    # Analyze against meta
    meta_archetypes = ["Royal Giant", "Giant Beatdown", "LavaLoon"]
    analysis = analyzer.analyze_deck_vs_meta(hog_deck, meta_archetypes)
    print(f"Meta Win Rate: {analysis['meta_win_rate']:.1%}")
    print(f"Average Elixir: {analysis['average_elixir']:.1f}")
    
    # Get recommendations for winning vs Royal Giant
    print("\n=== Deck Recommendations vs Royal Giant ===")
    recommendations = analyzer.recommend_deck_for_outcome(0.65, "Royal Giant")
    
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec['archetype']} (Score: {rec['recommendation_score']:.2f})")
        print(f"   Expected Win Rate: {rec['expected_win_rate']:.1%}")
        print(f"   Sample Deck: {', '.join(rec['sample_deck'])}")
        print(f"   Reasoning: {rec['reasoning']}")
        print()
    
    # Example retention optimization
    print("=== Retention Optimization Example ===")
    opponent_deck = ["Royal Giant", "Lightning", "Wizard", "Valkyrie", "Musketeer", "Zap", "Cannon", "Ice Spirit"]
    player_data = {"skill_level": "intermediate", "win_rate": 55.0}
    
    optimization = analyzer.optimize_deck_for_retention(
        hog_deck, opponent_deck, "win", player_data
    )
    
    print(f"Target Outcome: {optimization['target_outcome']}")
    print(f"Opponent Archetype: {optimization['opponent_archetype']}")
    print(f"Should Change Deck: {optimization['should_change_deck']}")
    
    if optimization['recommended_change']:
        rec = optimization['recommended_change']
        print(f"Recommended: {rec['archetype']} (Win Rate: {rec['expected_win_rate']:.1%})")


if __name__ == "__main__":
    main()