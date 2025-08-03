#!/usr/bin/env python3
"""
Data Models for Clash Royale Retention Analysis

This module contains specialized data structures for analyzing player retention
patterns and calculating retention scores based on play behavior.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import statistics


class SessionEndReason(Enum):
    """Reasons why a play session might end"""
    FRUSTRATION_LOSS = "frustration_loss"  # Lost multiple games in a row
    SATISFACTION_WIN = "satisfaction_win"  # Won and felt satisfied
    TIME_CONSTRAINT = "time_constraint"  # Had to stop for external reasons
    BOREDOM = "boredom"  # Stopped due to repetitive gameplay
    CLOSE_MATCH_HIGH = "close_match_high"  # Stopped after exciting close match
    TROPHY_GOAL_REACHED = "trophy_goal_reached"  # Reached desired trophy count
    UNKNOWN = "unknown"


class MatchQuality(Enum):
    """Quality assessment of individual matches"""
    EXCELLENT = "excellent"  # Close, competitive match
    GOOD = "good"  # Fair match with some challenge
    AVERAGE = "average"  # Standard match
    POOR = "poor"  # One-sided or unbalanced
    TERRIBLE = "terrible"  # Completely unfair matchup


@dataclass
class SessionMetrics:
    """Metrics for a single play session"""
    session_id: str
    start_time: datetime
    end_time: datetime
    total_battles: int
    wins: int
    losses: int
    total_crowns_earned: int
    total_crowns_lost: int
    trophy_change: int
    close_matches: int
    avg_match_duration: float  # estimated in seconds
    end_reason: SessionEndReason
    player_satisfaction_score: float  # 0.0 to 1.0
    
    @property
    def duration_minutes(self) -> float:
        """Session duration in minutes"""
        return (self.end_time - self.start_time).total_seconds() / 60
    
    @property
    def win_rate(self) -> float:
        """Win rate for this session"""
        return (self.wins / self.total_battles * 100) if self.total_battles > 0 else 0
    
    @property
    def crown_ratio(self) -> float:
        """Ratio of crowns earned to crowns lost"""
        return (self.total_crowns_earned / self.total_crowns_lost) if self.total_crowns_lost > 0 else float('inf')


@dataclass
class RetentionFactors:
    """Factors that influence player retention"""
    win_rate_consistency: float  # How consistent is their win rate over time
    session_length_preference: float  # Preferred session length in minutes
    loss_tolerance: int  # How many losses before likely to quit
    comeback_potential: float  # Likelihood to continue after losses
    close_match_preference: float  # How much they enjoy close matches
    trophy_sensitivity: float  # How much trophy changes affect them
    time_of_day_patterns: Dict[int, float]  # Hour -> play frequency
    deck_experimentation: float  # How often they try new decks
    meta_adaptation: float  # How quickly they adapt to meta changes


@dataclass
class PlayerProfile:
    """Comprehensive player profile for retention analysis"""
    player_tag: str
    skill_level: str  # beginner, intermediate, advanced, expert
    play_style: str  # aggressive, defensive, balanced, experimental
    retention_factors: RetentionFactors
    historical_sessions: List[SessionMetrics]
    current_session: Optional[SessionMetrics] = None
    last_active: Optional[datetime] = None
    churn_risk: float = 0.0  # 0.0 = low risk, 1.0 = high risk
    
    @property
    def average_session_length(self) -> float:
        """Average session length in minutes"""
        if not self.historical_sessions:
            return 0.0
        return statistics.mean([s.duration_minutes for s in self.historical_sessions])
    
    @property
    def overall_win_rate(self) -> float:
        """Overall win rate across all sessions"""
        total_wins = sum(s.wins for s in self.historical_sessions)
        total_battles = sum(s.total_battles for s in self.historical_sessions)
        return (total_wins / total_battles * 100) if total_battles > 0 else 0


@dataclass
class MatchupAnalysis:
    """Analysis of deck matchups and their outcomes"""
    player_deck_archetype: str
    opponent_deck_archetype: str
    theoretical_win_rate: float  # Based on meta analysis
    actual_win_rate: float  # Player's historical performance
    sample_size: int
    last_updated: datetime
    key_interactions: List[str]  # Important card interactions
    
    @property
    def performance_delta(self) -> float:
        """How much better/worse player performs vs theory"""
        return self.actual_win_rate - self.theoretical_win_rate


@dataclass
class DeckRecommendation:
    """Recommendation for a deck to achieve desired outcome"""
    deck_cards: List[str]  # Card names
    archetype: str
    target_win_probability: float
    confidence_score: float  # How confident we are in this recommendation
    reasoning: str  # Why this deck is recommended
    meta_viability: float  # How good this deck is in current meta
    player_familiarity: float  # How familiar player is with this archetype
    
    @property
    def overall_score(self) -> float:
        """Combined score considering all factors"""
        return (self.target_win_probability * 0.4 + 
                self.confidence_score * 0.2 + 
                self.meta_viability * 0.2 + 
                self.player_familiarity * 0.2)


@dataclass
class RetentionPrediction:
    """Prediction about player retention"""
    next_session_probability: float  # Probability of playing another session today
    next_day_probability: float  # Probability of playing tomorrow
    next_week_probability: float  # Probability of playing this week
    optimal_outcome: str  # "win" or "loss" for next match
    confidence: float  # Confidence in the prediction
    factors: Dict[str, float]  # Contributing factors and their weights
    recommended_action: str  # What the algorithm suggests


class RetentionAnalyzer:
    """Main class for analyzing player retention patterns"""
    
    def __init__(self):
        self.session_gap_threshold = 30  # minutes between sessions
        self.frustration_loss_threshold = 3  # consecutive losses
        self.satisfaction_win_threshold = 2  # consecutive wins
    
    def identify_sessions(self, battles: List[Dict]) -> List[SessionMetrics]:
        """
        Identify distinct play sessions from battle history
        
        Args:
            battles: List of battle data dictionaries
            
        Returns:
            List of SessionMetrics objects
        """
        if not battles:
            return []
        
        sessions = []
        current_session_battles = []
        
        for i, battle in enumerate(battles):
            if not current_session_battles:
                current_session_battles.append(battle)
                continue
            
            # Check time gap between battles
            current_time = datetime.fromisoformat(battle['battle_time'].replace('Z', '+00:00'))
            last_time = datetime.fromisoformat(current_session_battles[-1]['battle_time'].replace('Z', '+00:00'))
            gap_minutes = (last_time - current_time).total_seconds() / 60
            
            if gap_minutes > self.session_gap_threshold:
                # End current session and start new one
                session = self._create_session_from_battles(current_session_battles, len(sessions))
                sessions.append(session)
                current_session_battles = [battle]
            else:
                current_session_battles.append(battle)
        
        # Don't forget the last session
        if current_session_battles:
            session = self._create_session_from_battles(current_session_battles, len(sessions))
            sessions.append(session)
        
        return sessions
    
    def _create_session_from_battles(self, battles: List[Dict], session_id: int) -> SessionMetrics:
        """Create a SessionMetrics object from a list of battles"""
        if not battles:
            raise ValueError("Cannot create session from empty battle list")
        
        start_time = datetime.fromisoformat(battles[-1]['battle_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(battles[0]['battle_time'].replace('Z', '+00:00'))
        
        wins = sum(1 for b in battles if b['is_win'])
        losses = len(battles) - wins
        
        total_crowns_earned = sum(b['crowns'] for b in battles)
        total_crowns_lost = sum(b['opponent_crowns'] for b in battles)
        
        trophy_changes = [b.get('trophy_change', 0) for b in battles if b.get('trophy_change') is not None]
        trophy_change = sum(trophy_changes)
        
        close_matches = sum(1 for b in battles if abs(b['crowns'] - b['opponent_crowns']) <= 1)
        
        # Estimate match duration (average CR match is 3-4 minutes)
        avg_match_duration = 210  # 3.5 minutes in seconds
        
        # Determine end reason
        end_reason = self._determine_end_reason(battles)
        
        # Calculate satisfaction score
        satisfaction_score = self._calculate_satisfaction_score(battles, end_reason)
        
        return SessionMetrics(
            session_id=f"session_{session_id}",
            start_time=start_time,
            end_time=end_time,
            total_battles=len(battles),
            wins=wins,
            losses=losses,
            total_crowns_earned=total_crowns_earned,
            total_crowns_lost=total_crowns_lost,
            trophy_change=trophy_change,
            close_matches=close_matches,
            avg_match_duration=avg_match_duration,
            end_reason=end_reason,
            player_satisfaction_score=satisfaction_score
        )
    
    def _determine_end_reason(self, battles: List[Dict]) -> SessionEndReason:
        """Determine why a session likely ended based on battle patterns"""
        if len(battles) < 2:
            return SessionEndReason.UNKNOWN
        
        # Check for frustration (multiple losses at end)
        last_3_results = [b['is_win'] for b in battles[:3]]
        if len(last_3_results) >= 3 and not any(last_3_results):
            return SessionEndReason.FRUSTRATION_LOSS
        
        # Check for satisfaction (win at end)
        if battles[0]['is_win']:
            # Check if it was a close match
            crown_diff = abs(battles[0]['crowns'] - battles[0]['opponent_crowns'])
            if crown_diff <= 1:
                return SessionEndReason.CLOSE_MATCH_HIGH
            else:
                return SessionEndReason.SATISFACTION_WIN
        
        # Check for trophy goals
        trophy_changes = [b.get('trophy_change', 0) for b in battles if b.get('trophy_change') is not None]
        if trophy_changes and sum(trophy_changes) > 0:
            return SessionEndReason.TROPHY_GOAL_REACHED
        
        return SessionEndReason.UNKNOWN
    
    def _calculate_satisfaction_score(self, battles: List[Dict], end_reason: SessionEndReason) -> float:
        """Calculate player satisfaction score for a session"""
        base_score = 0.5
        
        # Win rate impact
        win_rate = sum(1 for b in battles if b['is_win']) / len(battles)
        base_score += (win_rate - 0.5) * 0.4
        
        # Close matches are generally more satisfying
        close_matches = sum(1 for b in battles if abs(b['crowns'] - b['opponent_crowns']) <= 1)
        close_match_rate = close_matches / len(battles)
        base_score += close_match_rate * 0.2
        
        # End reason impact
        end_reason_scores = {
            SessionEndReason.SATISFACTION_WIN: 0.2,
            SessionEndReason.CLOSE_MATCH_HIGH: 0.15,
            SessionEndReason.TROPHY_GOAL_REACHED: 0.1,
            SessionEndReason.TIME_CONSTRAINT: 0.0,
            SessionEndReason.BOREDOM: -0.1,
            SessionEndReason.FRUSTRATION_LOSS: -0.3,
            SessionEndReason.UNKNOWN: 0.0
        }
        base_score += end_reason_scores.get(end_reason, 0.0)
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def calculate_retention_score(self, player_profile: PlayerProfile) -> float:
        """
        Calculate overall retention score for a player
        
        Args:
            player_profile: Player's profile with historical data
            
        Returns:
            Retention score between 0.0 (high churn risk) and 1.0 (high retention)
        """
        if not player_profile.historical_sessions:
            return 0.5  # Default for new players
        
        recent_sessions = player_profile.historical_sessions[-10:]  # Last 10 sessions
        
        # Factor 1: Recent satisfaction trend
        satisfaction_scores = [s.player_satisfaction_score for s in recent_sessions]
        avg_satisfaction = statistics.mean(satisfaction_scores)
        satisfaction_trend = self._calculate_trend(satisfaction_scores)
        
        # Factor 2: Session frequency
        if len(recent_sessions) >= 2:
            time_gaps = []
            for i in range(1, len(recent_sessions)):
                gap = (recent_sessions[i-1].start_time - recent_sessions[i].end_time).total_seconds() / 3600  # hours
                time_gaps.append(gap)
            avg_gap = statistics.mean(time_gaps)
            frequency_score = max(0, 1 - (avg_gap / 24))  # Normalize to daily play = 1.0
        else:
            frequency_score = 0.5
        
        # Factor 3: Win rate stability
        win_rates = [s.win_rate for s in recent_sessions]
        win_rate_stability = 1 - (statistics.stdev(win_rates) / 100 if len(win_rates) > 1 else 0)
        
        # Factor 4: Session length consistency
        session_lengths = [s.duration_minutes for s in recent_sessions]
        avg_length = statistics.mean(session_lengths)
        length_consistency = 1 - (statistics.stdev(session_lengths) / avg_length if avg_length > 0 and len(session_lengths) > 1 else 0)
        
        # Combine factors
        retention_score = (
            avg_satisfaction * 0.35 +
            satisfaction_trend * 0.15 +
            frequency_score * 0.25 +
            win_rate_stability * 0.15 +
            length_consistency * 0.10
        )
        
        return max(0.0, min(1.0, retention_score))
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in a series of values"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend
        x = list(range(len(values)))
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return max(-1.0, min(1.0, slope))  # Normalize between -1 and 1
    
    def should_player_win_next(self, player_profile: PlayerProfile) -> Tuple[bool, float, str]:
        """
        Determine if player should win their next match for optimal retention
        
        Args:
            player_profile: Player's profile with historical data
            
        Returns:
            Tuple of (should_win, confidence, reasoning)
        """
        if not player_profile.historical_sessions:
            return True, 0.5, "New player - default to positive experience"
        
        recent_battles = []
        for session in player_profile.historical_sessions[-3:]:  # Last 3 sessions
            # This would need battle details, simplified for now
            pass
        
        # Analyze recent performance and satisfaction
        recent_session = player_profile.historical_sessions[-1]
        
        # If last session ended in frustration, they should probably win
        if recent_session.end_reason == SessionEndReason.FRUSTRATION_LOSS:
            return True, 0.8, "Last session ended in frustration - needs positive experience"
        
        # If they're on a winning streak, a close loss might be engaging
        if recent_session.win_rate > 70:
            return False, 0.6, "Player on winning streak - close loss maintains engagement"
        
        # If satisfaction is low, they need a win
        if recent_session.player_satisfaction_score < 0.4:
            return True, 0.7, "Low satisfaction score - needs confidence boost"
        
        # Default to win for retention
        return True, 0.5, "Default positive experience"