#!/usr/bin/env python3
"""
Clash Royale Retention Algorithm

This is the main algorithm that integrates player data analysis, retention modeling,
and deck recommendations to determine optimal match outcomes for maximum player retention.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict

from clash_royale_api_client import ClashRoyaleAPI, analyze_play_patterns
from retention_models import (
    RetentionAnalyzer, PlayerProfile, RetentionFactors, SessionMetrics,
    RetentionPrediction, SessionEndReason
)
from deck_analyzer import DeckAnalyzer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetentionAlgorithm:
    """
    Main retention algorithm that determines optimal match outcomes
    """
    
    def __init__(self, api_token: str):
        """
        Initialize the retention algorithm
        
        Args:
            api_token: Clash Royale API token
        """
        self.api = ClashRoyaleAPI(api_token)
        self.retention_analyzer = RetentionAnalyzer()
        self.deck_analyzer = DeckAnalyzer()
        self.player_profiles: Dict[str, PlayerProfile] = {}
        
        # Algorithm parameters
        self.min_battles_for_analysis = 10
        self.frustration_threshold = 0.3  # Satisfaction score below which player is frustrated
        self.comfort_zone_threshold = 0.8  # Win rate above which player might be bored
        self.engagement_sweet_spot = (0.45, 0.65)  # Optimal win rate range for engagement
    
    def analyze_player_retention(self, player_tag: str, force_refresh: bool = False) -> PlayerProfile:
        """
        Comprehensive analysis of a player's retention patterns
        
        Args:
            player_tag: Player's tag
            force_refresh: Whether to force refresh data from API
            
        Returns:
            PlayerProfile with complete retention analysis
        """
        if player_tag in self.player_profiles and not force_refresh:
            return self.player_profiles[player_tag]
        
        logger.info(f"Analyzing retention for player {player_tag}")
        
        # Fetch fresh data from API
        try:
            player_stats = self.api.get_player(player_tag)
            battles = self.api.get_player_battles(player_tag, limit=25)
        except Exception as e:
            logger.error(f"Failed to fetch data for {player_tag}: {e}")
            raise
        
        # Convert battles to dict format for session analysis
        battle_dicts = []
        for battle in battles:
            battle_dict = {
                'battle_time': battle.battle_time.isoformat() + 'Z',
                'is_win': battle.is_win,
                'crowns': battle.crowns,
                'opponent_crowns': battle.opponent_crowns,
                'trophy_change': battle.trophy_change,
                'type': battle.type
            }
            battle_dicts.append(battle_dict)
        
        # Identify play sessions
        sessions = self.retention_analyzer.identify_sessions(battle_dicts)
        
        # Determine skill level based on trophies and card levels
        skill_level = self._determine_skill_level(player_stats)
        
        # Determine play style based on deck and battle patterns
        play_style = self._determine_play_style(player_stats, battles)
        
        # Calculate retention factors
        retention_factors = self._calculate_retention_factors(player_stats, sessions, battles)
        
        # Create player profile
        profile = PlayerProfile(
            player_tag=player_tag,
            skill_level=skill_level,
            play_style=play_style,
            retention_factors=retention_factors,
            historical_sessions=sessions,
            last_active=battles[0].battle_time if battles else None
        )
        
        # Calculate churn risk
        profile.churn_risk = 1.0 - self.retention_analyzer.calculate_retention_score(profile)
        
        self.player_profiles[player_tag] = profile
        return profile
    
    def _determine_skill_level(self, player_stats) -> str:
        """Determine player skill level based on stats"""
        trophies = player_stats.trophies
        
        if trophies < 2000:
            return "beginner"
        elif trophies < 4000:
            return "intermediate"
        elif trophies < 6000:
            return "advanced"
        else:
            return "expert"
    
    def _determine_play_style(self, player_stats, battles) -> str:
        """Determine player style based on deck and battle patterns"""
        if not player_stats.current_deck:
            return "balanced"
        
        avg_elixir = player_stats.current_deck.average_elixir
        
        # Analyze battle patterns
        avg_crown_diff = sum(b.crown_difference for b in battles) / len(battles) if battles else 0
        
        if avg_elixir < 3.5 and avg_crown_diff > 0:
            return "aggressive"
        elif avg_elixir > 4.0:
            return "defensive"
        elif len(set(card.name for card in player_stats.current_deck.cards)) > 6:
            return "experimental"
        else:
            return "balanced"
    
    def _calculate_retention_factors(self, player_stats, sessions: List[SessionMetrics], 
                                   battles) -> RetentionFactors:
        """Calculate detailed retention factors for the player"""
        if not sessions:
            # Default factors for new players
            return RetentionFactors(
                win_rate_consistency=0.5,
                session_length_preference=15.0,
                loss_tolerance=3,
                comeback_potential=0.6,
                close_match_preference=0.7,
                trophy_sensitivity=0.5,
                time_of_day_patterns={},
                deck_experimentation=0.3,
                meta_adaptation=0.4
            )
        
        # Calculate win rate consistency
        session_win_rates = [s.win_rate for s in sessions]
        win_rate_std = max(0.1, min(50, sum((r - sum(session_win_rates)/len(session_win_rates))**2 for r in session_win_rates)**0.5))
        win_rate_consistency = max(0, 1 - (win_rate_std / 50))
        
        # Session length preference
        session_lengths = [s.duration_minutes for s in sessions]
        avg_session_length = sum(session_lengths) / len(session_lengths)
        
        # Loss tolerance - analyze session end patterns
        frustration_endings = sum(1 for s in sessions if s.end_reason == SessionEndReason.FRUSTRATION_LOSS)
        loss_tolerance = max(1, 5 - (frustration_endings / len(sessions) * 4))
        
        # Comeback potential - how often they continue after losses
        comeback_sessions = 0
        for session in sessions:
            if session.losses >= 2 and session.wins > 0:  # Had losses but continued to win
                comeback_sessions += 1
        comeback_potential = min(1.0, comeback_sessions / max(1, len(sessions)))
        
        # Close match preference
        total_close_matches = sum(s.close_matches for s in sessions)
        total_battles = sum(s.total_battles for s in sessions)
        close_match_rate = total_close_matches / max(1, total_battles)
        close_match_preference = min(1.0, close_match_rate * 2)  # Scale to preference
        
        # Trophy sensitivity
        trophy_changes = [b.trophy_change for b in battles if b.trophy_change is not None]
        if trophy_changes:
            trophy_volatility = sum(abs(change) for change in trophy_changes) / len(trophy_changes)
            trophy_sensitivity = min(1.0, trophy_volatility / 50)  # Normalize
        else:
            trophy_sensitivity = 0.5
        
        # Time patterns (simplified)
        time_patterns = {}
        for session in sessions:
            hour = session.start_time.hour
            time_patterns[hour] = time_patterns.get(hour, 0) + 1
        
        # Normalize time patterns
        if time_patterns:
            max_count = max(time_patterns.values())
            time_patterns = {h: count/max_count for h, count in time_patterns.items()}
        
        return RetentionFactors(
            win_rate_consistency=win_rate_consistency,
            session_length_preference=avg_session_length,
            loss_tolerance=int(loss_tolerance),
            comeback_potential=comeback_potential,
            close_match_preference=close_match_preference,
            trophy_sensitivity=trophy_sensitivity,
            time_of_day_patterns=time_patterns,
            deck_experimentation=0.3,  # Would need deck history to calculate
            meta_adaptation=0.4  # Would need longer-term data
        )
    
    def predict_optimal_outcome(self, player_tag: str, opponent_deck: Optional[List[str]] = None) -> RetentionPrediction:
        """
        Predict the optimal match outcome for maximum retention
        
        Args:
            player_tag: Player's tag
            opponent_deck: Opponent's deck cards (if known)
            
        Returns:
            RetentionPrediction with recommended outcome
        """
        profile = self.analyze_player_retention(player_tag)
        
        # Analyze current state
        if not profile.historical_sessions:
            return RetentionPrediction(
                next_session_probability=0.8,
                next_day_probability=0.7,
                next_week_probability=0.9,
                optimal_outcome="win",
                confidence=0.6,
                factors={"new_player": 1.0},
                recommended_action="Provide positive first experience"
            )
        
        recent_session = profile.historical_sessions[-1] if profile.historical_sessions else None
        if not recent_session:
            return self._default_prediction()
        
        # Decision factors
        factors = {}
        
        # Factor 1: Recent satisfaction
        satisfaction = recent_session.player_satisfaction_score
        factors["recent_satisfaction"] = satisfaction
        
        # Factor 2: Session end reason
        end_reason_weight = {
            SessionEndReason.FRUSTRATION_LOSS: -0.8,  # Strongly favor win
            SessionEndReason.SATISFACTION_WIN: 0.2,   # Slight favor for loss (challenge)
            SessionEndReason.CLOSE_MATCH_HIGH: 0.1,   # Slight favor for another close match
            SessionEndReason.TROPHY_GOAL_REACHED: 0.0,  # Neutral
            SessionEndReason.TIME_CONSTRAINT: 0.0,   # Neutral
            SessionEndReason.BOREDOM: -0.3,          # Favor engaging match
            SessionEndReason.UNKNOWN: 0.0
        }.get(recent_session.end_reason, 0.0)
        factors["end_reason"] = end_reason_weight
        
        # Factor 3: Recent win rate (avoid comfort zone and frustration)
        recent_win_rate = recent_session.win_rate / 100
        if recent_win_rate < self.engagement_sweet_spot[0]:
            win_rate_factor = 0.6  # Favor win
        elif recent_win_rate > self.engagement_sweet_spot[1]:
            win_rate_factor = -0.4  # Favor loss
        else:
            win_rate_factor = 0.1  # Slight favor for win in sweet spot
        factors["win_rate_factor"] = win_rate_factor
        
        # Factor 4: Comeback potential
        comeback_factor = (profile.retention_factors.comeback_potential - 0.5) * 0.3
        factors["comeback_potential"] = comeback_factor
        
        # Factor 5: Loss tolerance
        recent_losses = recent_session.losses
        if recent_losses >= profile.retention_factors.loss_tolerance:
            loss_tolerance_factor = 0.7  # Strongly favor win
        else:
            loss_tolerance_factor = -0.1 * recent_losses  # Slight favor for loss if not too many
        factors["loss_tolerance"] = loss_tolerance_factor
        
        # Factor 6: Churn risk
        churn_factor = profile.churn_risk * 0.5  # Higher churn risk favors wins
        factors["churn_risk"] = churn_factor
        
        # Calculate overall recommendation
        total_score = sum(factors.values())
        
        # Decision logic
        if total_score > 0.2:
            optimal_outcome = "win"
            confidence = min(0.95, 0.5 + abs(total_score))
        elif total_score < -0.2:
            optimal_outcome = "loss"
            confidence = min(0.95, 0.5 + abs(total_score))
        else:
            # Close call - default to slight win bias for retention
            optimal_outcome = "win"
            confidence = 0.5
        
        # Calculate session probabilities
        base_retention = 1.0 - profile.churn_risk
        satisfaction_multiplier = 1.0 + (satisfaction - 0.5) * 0.4
        
        next_session_prob = min(0.95, base_retention * satisfaction_multiplier * 0.8)
        next_day_prob = min(0.9, base_retention * 0.7)
        next_week_prob = min(0.95, base_retention * 0.9)
        
        # Generate action recommendation
        if optimal_outcome == "win":
            if confidence > 0.8:
                action = "Provide strong positive experience - player needs confidence boost"
            else:
                action = "Provide slight advantage - maintain engagement without being obvious"
        else:
            if confidence > 0.8:
                action = "Provide engaging challenge - player can handle difficulty"
            else:
                action = "Provide close competitive match - maintain tension"
        
        return RetentionPrediction(
            next_session_probability=next_session_prob,
            next_day_probability=next_day_prob,
            next_week_probability=next_week_prob,
            optimal_outcome=optimal_outcome,
            confidence=confidence,
            factors=factors,
            recommended_action=action
        )
    
    def recommend_deck_strategy(self, player_tag: str, opponent_deck: List[str]) -> Dict:
        """
        Recommend deck strategy to achieve optimal outcome
        
        Args:
            player_tag: Player's tag
            opponent_deck: Opponent's deck
            
        Returns:
            Dictionary with deck recommendations and strategy
        """
        # Get retention prediction
        prediction = self.predict_optimal_outcome(player_tag, opponent_deck)
        
        # Get player profile
        profile = self.player_profiles.get(player_tag)
        if not profile:
            profile = self.analyze_player_retention(player_tag)
        
        # Get player's current deck
        try:
            player_stats = self.api.get_player(player_tag)
            if player_stats.current_deck:
                current_deck = [card.name for card in player_stats.current_deck.cards]
            else:
                current_deck = []
        except:
            current_deck = []
        
        # Use deck analyzer to get recommendations
        player_data = {
            "skill_level": profile.skill_level,
            "win_rate": profile.overall_win_rate,
            "play_style": profile.play_style
        }
        
        deck_optimization = self.deck_analyzer.optimize_deck_for_retention(
            current_deck, opponent_deck, prediction.optimal_outcome, player_data
        )
        
        return {
            "retention_prediction": asdict(prediction),
            "deck_optimization": deck_optimization,
            "current_deck": current_deck,
            "player_profile_summary": {
                "skill_level": profile.skill_level,
                "play_style": profile.play_style,
                "churn_risk": profile.churn_risk,
                "avg_session_length": profile.average_session_length,
                "overall_win_rate": profile.overall_win_rate
            }
        }
    
    def _default_prediction(self) -> RetentionPrediction:
        """Default prediction for edge cases"""
        return RetentionPrediction(
            next_session_probability=0.7,
            next_day_probability=0.6,
            next_week_probability=0.8,
            optimal_outcome="win",
            confidence=0.5,
            factors={"default": 1.0},
            recommended_action="Provide balanced experience"
        )
    
    def export_player_analysis(self, player_tag: str, filename: Optional[str] = None) -> str:
        """
        Export complete player analysis to JSON file
        
        Args:
            player_tag: Player's tag
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Filename of exported data
        """
        profile = self.analyze_player_retention(player_tag)
        prediction = self.predict_optimal_outcome(player_tag)
        
        export_data = {
            "player_tag": player_tag,
            "analysis_timestamp": datetime.now().isoformat(),
            "player_profile": asdict(profile),
            "retention_prediction": asdict(prediction),
            "algorithm_version": "1.0",
            "summary": {
                "churn_risk": profile.churn_risk,
                "optimal_next_outcome": prediction.optimal_outcome,
                "confidence": prediction.confidence,
                "key_factors": list(prediction.factors.keys())
            }
        }
        
        if not filename:
            filename = f"player_analysis_{player_tag.replace('#', '')}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported player analysis to {filename}")
        return filename


def main():
    """Example usage of the retention algorithm"""
    api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
    
    if not api_token:
        print("Please set CLASH_ROYALE_API_TOKEN environment variable")
        print("Get your token from: https://developer.clashofclans.com/")
        return
    
    # Initialize algorithm
    algorithm = RetentionAlgorithm(api_token)
    
    # Example player tag
    player_tag = "#8L9L9GL"  # Replace with actual player tag
    
    try:
        print(f"=== Retention Analysis for {player_tag} ===")
        
        # Analyze player
        profile = algorithm.analyze_player_retention(player_tag)
        print(f"Player Skill Level: {profile.skill_level}")
        print(f"Play Style: {profile.play_style}")
        print(f"Churn Risk: {profile.churn_risk:.1%}")
        print(f"Average Session Length: {profile.average_session_length:.1f} minutes")
        print(f"Overall Win Rate: {profile.overall_win_rate:.1f}%")
        
        # Get retention prediction
        prediction = algorithm.predict_optimal_outcome(player_tag)
        print(f"\n=== Retention Prediction ===")
        print(f"Optimal Next Outcome: {prediction.optimal_outcome}")
        print(f"Confidence: {prediction.confidence:.1%}")
        print(f"Next Session Probability: {prediction.next_session_probability:.1%}")
        print(f"Recommended Action: {prediction.recommended_action}")
        
        # Example deck recommendation
        opponent_deck = ["Royal Giant", "Lightning", "Wizard", "Valkyrie", 
                        "Musketeer", "Zap", "Cannon", "Ice Spirit"]
        
        recommendation = algorithm.recommend_deck_strategy(player_tag, opponent_deck)
        
        print(f"\n=== Deck Strategy vs Opponent ===")
        deck_opt = recommendation["deck_optimization"]
        print(f"Opponent Archetype: {deck_opt['opponent_archetype']}")
        print(f"Target Outcome: {deck_opt['target_outcome']}")
        print(f"Should Change Deck: {deck_opt['should_change_deck']}")
        
        if deck_opt["recommended_change"]:
            rec = deck_opt["recommended_change"]
            print(f"Recommended Archetype: {rec['archetype']}")
            print(f"Expected Win Rate: {rec['expected_win_rate']:.1%}")
        
        # Export analysis
        filename = algorithm.export_player_analysis(player_tag)
        print(f"\nFull analysis exported to: {filename}")
        
    except Exception as e:
        logger.error(f"Error in retention analysis: {e}")


if __name__ == "__main__":
    main()