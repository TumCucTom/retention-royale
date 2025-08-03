#!/usr/bin/env python3
"""
Example Usage of Clash Royale Retention Algorithm

This script demonstrates how to use the retention algorithm with sample data.
For real usage, you'll need a valid Clash Royale API token.
"""

import os
from datetime import datetime, timedelta
from retention_algorithm import RetentionAlgorithm
from deck_analyzer import DeckAnalyzer


def demo_without_api():
    """Demonstrate deck analysis without requiring API access"""
    print("=== Deck Analysis Demo (No API Required) ===\n")
    
    analyzer = DeckAnalyzer()
    
    # Example decks
    hog_deck = ["Hog Rider", "Ice Spirit", "Skeletons", "Musketeer", "Cannon", "Fireball", "Zap", "Valkyrie"]
    rg_deck = ["Royal Giant", "Lightning", "Wizard", "Valkyrie", "Musketeer", "Zap", "Cannon", "Ice Spirit"]
    
    # Identify archetypes
    hog_archetype, hog_confidence = analyzer.identify_deck_archetype(hog_deck)
    rg_archetype, rg_confidence = analyzer.identify_deck_archetype(rg_deck)
    
    print(f"Deck 1: {', '.join(hog_deck)}")
    print(f"Identified as: {hog_archetype} (confidence: {hog_confidence:.2f})")
    print()
    
    print(f"Deck 2: {', '.join(rg_deck)}")
    print(f"Identified as: {rg_archetype} (confidence: {rg_confidence:.2f})")
    print()
    
    # Analyze matchup
    win_rate = analyzer.get_matchup_win_rate(hog_archetype, rg_archetype)
    print(f"Expected win rate for {hog_archetype} vs {rg_archetype}: {win_rate:.1%}")
    print()
    
    # Get deck recommendations for winning against Royal Giant
    print("=== Deck Recommendations for Winning vs Royal Giant ===")
    recommendations = analyzer.recommend_deck_for_outcome(0.65, "Royal Giant", "intermediate")
    
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec['archetype']} (Score: {rec['recommendation_score']:.2f})")
        print(f"   Expected Win Rate: {rec['expected_win_rate']:.1%}")
        print(f"   Sample Deck: {', '.join(rec['sample_deck'])}")
        print(f"   Reasoning: {rec['reasoning']}")
        print()


def demo_with_api():
    """Demonstrate full algorithm with API access"""
    api_token = os.getenv('CLASH_ROYALE_API_TOKEN')
    
    if not api_token:
        print("=== API Demo Skipped ===")
        print("To run the full demo with real data:")
        print("1. Get an API token from https://developer.clashofclans.com/")
        print("2. Set environment variable: export CLASH_ROYALE_API_TOKEN='your_token'")
        print("3. Run this script again")
        return
    
    print("=== Full Retention Algorithm Demo ===\n")
    
    # Initialize algorithm
    algorithm = RetentionAlgorithm(api_token)
    
    # Example player tag (replace with real player tag)
    player_tag = "#8L9L9GL"
    
    try:
        print(f"Analyzing player: {player_tag}")
        
        # Analyze player retention
        profile = algorithm.analyze_player_retention(player_tag)
        
        print(f"Player Profile:")
        print(f"  Skill Level: {profile.skill_level}")
        print(f"  Play Style: {profile.play_style}")
        print(f"  Churn Risk: {profile.churn_risk:.1%}")
        print(f"  Avg Session Length: {profile.average_session_length:.1f} minutes")
        print(f"  Overall Win Rate: {profile.overall_win_rate:.1f}%")
        print()
        
        # Get retention prediction
        prediction = algorithm.predict_optimal_outcome(player_tag)
        
        print(f"Retention Prediction:")
        print(f"  Optimal Next Outcome: {prediction.optimal_outcome}")
        print(f"  Confidence: {prediction.confidence:.1%}")
        print(f"  Next Session Probability: {prediction.next_session_probability:.1%}")
        print(f"  Recommended Action: {prediction.recommended_action}")
        print()
        
        # Demo deck strategy recommendation
        opponent_deck = ["Royal Giant", "Lightning", "Wizard", "Valkyrie", 
                        "Musketeer", "Zap", "Cannon", "Ice Spirit"]
        
        print(f"Opponent Deck: {', '.join(opponent_deck)}")
        
        recommendation = algorithm.recommend_deck_strategy(player_tag, opponent_deck)
        
        deck_opt = recommendation["deck_optimization"]
        print(f"Strategy Recommendation:")
        print(f"  Target Outcome: {deck_opt['target_outcome']}")
        print(f"  Opponent Archetype: {deck_opt['opponent_archetype']}")
        print(f"  Should Change Deck: {deck_opt['should_change_deck']}")
        
        if deck_opt["recommended_change"]:
            rec = deck_opt["recommended_change"]
            print(f"  Recommended Archetype: {rec['archetype']}")
            print(f"  Expected Win Rate: {rec['expected_win_rate']:.1%}")
            print(f"  Sample Deck: {', '.join(rec['sample_deck'])}")
        
        # Export analysis
        filename = algorithm.export_player_analysis(player_tag)
        print(f"\nDetailed analysis exported to: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a valid API token and player tag.")


def simulate_retention_scenario():
    """Simulate different retention scenarios"""
    print("=== Retention Scenarios Simulation ===\n")
    
    scenarios = [
        {
            "name": "Frustrated Player",
            "description": "Player lost 4 games in a row, satisfaction very low",
            "factors": {
                "recent_satisfaction": 0.2,
                "end_reason": -0.8,  # FRUSTRATION_LOSS
                "win_rate_factor": 0.6,  # Below sweet spot
                "loss_tolerance": 0.7,  # Exceeded tolerance
                "churn_risk": 0.4
            }
        },
        {
            "name": "Comfortable Player", 
            "description": "Player winning too much, might get bored",
            "factors": {
                "recent_satisfaction": 0.8,
                "end_reason": 0.2,  # SATISFACTION_WIN
                "win_rate_factor": -0.4,  # Above sweet spot
                "loss_tolerance": -0.1,
                "churn_risk": 0.1
            }
        },
        {
            "name": "Engaged Player",
            "description": "Player in optimal engagement zone",
            "factors": {
                "recent_satisfaction": 0.6,
                "end_reason": 0.1,  # CLOSE_MATCH_HIGH
                "win_rate_factor": 0.1,  # In sweet spot
                "loss_tolerance": -0.2,
                "churn_risk": 0.2
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        
        # Calculate recommendation score
        total_score = sum(scenario['factors'].values())
        
        if total_score > 0.2:
            recommendation = "WIN"
            reasoning = "Player needs positive experience"
        elif total_score < -0.2:
            recommendation = "LOSS" 
            reasoning = "Player can handle challenge"
        else:
            recommendation = "WIN (default)"
            reasoning = "Slight win bias for retention"
        
        confidence = min(95, 50 + abs(total_score) * 100)
        
        print(f"  Recommendation: {recommendation}")
        print(f"  Confidence: {confidence:.0f}%")
        print(f"  Reasoning: {reasoning}")
        print(f"  Total Score: {total_score:.2f}")
        print()


def main():
    """Run all demo functions"""
    print("🎮 Clash Royale Retention Algorithm Demo\n")
    
    # Demo 1: Deck analysis (works without API)
    demo_without_api()
    
    print("\n" + "="*60 + "\n")
    
    # Demo 2: Retention scenarios
    simulate_retention_scenario()
    
    print("="*60 + "\n")
    
    # Demo 3: Full API demo (requires token)
    demo_with_api()
    
    print("\n" + "="*60)
    print("Demo completed! Check the README.md for more details.")


if __name__ == "__main__":
    main()