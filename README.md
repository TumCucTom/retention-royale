# Clash Royale Retention Algorithm

A sophisticated algorithm for analyzing player behavior and optimizing match outcomes to maximize player retention in Clash Royale. This system uses official Clash Royale API data to predict when players should win or lose their next match based on their play history, session patterns, and retention factors.

## 🎯 Overview

This project implements a comprehensive retention analysis system that:

- **Analyzes player behavior patterns** from battle history and session data
- **Predicts optimal match outcomes** (win/loss) for maximum player retention
- **Recommends deck strategies** to achieve desired win rates against specific opponents
- **Identifies player churn risk** and provides actionable insights
- **Tracks session patterns** and satisfaction scores to understand player engagement

## 🏗️ Architecture

The system consists of several key components:

### 1. Data Fetching (`clash_royale_api_client.py`)
- **ClashRoyaleAPI**: Official API client for fetching player data, battle history, and deck information
- **Battle Analysis**: Parses battle results to extract win/loss patterns, crown differences, and trophy changes
- **Player Statistics**: Comprehensive player profile data including current deck and performance metrics

### 2. Retention Modeling (`retention_models.py`)
- **SessionMetrics**: Analyzes individual play sessions, duration, and end reasons
- **RetentionFactors**: Player-specific factors that influence retention (loss tolerance, comeback potential, etc.)
- **PlayerProfile**: Comprehensive player behavioral profile with churn risk assessment

### 3. Deck Analysis (`deck_analyzer.py`)
- **Card Database**: Metadata for all Clash Royale cards including elixir cost, type, and interactions
- **Archetype Recognition**: Identifies deck archetypes (Hog Cycle, Royal Giant, etc.) from card compositions
- **Matchup Analysis**: Win rate calculations between different deck archetypes
- **Deck Recommendations**: Suggests optimal decks to achieve target win rates

### 4. Main Algorithm (`retention_algorithm.py`)
- **RetentionAlgorithm**: Core algorithm that integrates all components
- **Outcome Prediction**: Determines whether a player should win or lose their next match
- **Strategy Optimization**: Combines retention prediction with deck recommendations

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Clash Royale API Token from [Supercell Developer Portal](https://developer.clashofclans.com/)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd clash-royale-retention-algorithm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API token:
```bash
export CLASH_ROYALE_API_TOKEN="your_api_token_here"
```

Or create a `.env` file:
```
CLASH_ROYALE_API_TOKEN=your_api_token_here
```

### Getting an API Token

1. Visit [https://developer.clashofclans.com/](https://developer.clashofclans.com/)
2. Create an account and log in
3. Create a new API key
4. Use your server's IP address (for local development, use your public IP)
5. Copy the generated token

## 📖 Usage

### Basic Analysis

```python
from retention_algorithm import RetentionAlgorithm

# Initialize with your API token
algorithm = RetentionAlgorithm("your_api_token")

# Analyze a player's retention patterns
player_tag = "#8L9L9GL"  # Replace with actual player tag
profile = algorithm.analyze_player_retention(player_tag)

print(f"Churn Risk: {profile.churn_risk:.1%}")
print(f"Skill Level: {profile.skill_level}")
print(f"Play Style: {profile.play_style}")
```

### Predicting Optimal Outcomes

```python
# Get retention prediction for next match
prediction = algorithm.predict_optimal_outcome(player_tag)

print(f"Optimal Outcome: {prediction.optimal_outcome}")
print(f"Confidence: {prediction.confidence:.1%}")
print(f"Reasoning: {prediction.recommended_action}")
```

### Deck Strategy Recommendations

```python
# Recommend deck strategy against specific opponent
opponent_deck = ["Royal Giant", "Lightning", "Wizard", "Valkyrie", 
                "Musketeer", "Zap", "Cannon", "Ice Spirit"]

recommendation = algorithm.recommend_deck_strategy(player_tag, opponent_deck)

deck_opt = recommendation["deck_optimization"]
print(f"Target Outcome: {deck_opt['target_outcome']}")
print(f"Should Change Deck: {deck_opt['should_change_deck']}")

if deck_opt["recommended_change"]:
    rec = deck_opt["recommended_change"]
    print(f"Recommended: {rec['archetype']} ({rec['expected_win_rate']:.1%} win rate)")
```

### Command Line Usage

Run the main script for a complete analysis:

```bash
python retention_algorithm.py
```

This will:
1. Fetch player data from the API
2. Analyze retention patterns
3. Generate predictions
4. Export detailed analysis to JSON

## 🧠 Algorithm Details

### Retention Analysis

The algorithm considers multiple factors when determining optimal outcomes:

1. **Recent Session Analysis**
   - Session end reasons (frustration, satisfaction, time constraints)
   - Win/loss patterns and streaks
   - Crown differences and match quality

2. **Player Behavioral Factors**
   - Loss tolerance (how many losses before likely to quit)
   - Comeback potential (likelihood to continue after losses)
   - Win rate consistency over time
   - Session length preferences

3. **Engagement Optimization**
   - Sweet spot win rate (45-65%) for maximum engagement
   - Avoiding comfort zone (too many wins = boredom)
   - Preventing frustration zone (too many losses = quit)

### Decision Logic

The algorithm uses a weighted scoring system:

```python
# Simplified decision logic
if total_score > 0.2:
    optimal_outcome = "win"  # Player needs positive experience
elif total_score < -0.2:
    optimal_outcome = "loss"  # Player can handle challenge
else:
    optimal_outcome = "win"  # Default to retention-positive outcome
```

### Deck Recommendations

The system analyzes deck matchups using:
- **Archetype Recognition**: Identifies deck types from card compositions
- **Meta Analysis**: Current win rates between archetype matchups
- **Player Skill Adjustment**: Recommendations based on player skill level
- **Target Win Rate**: Suggests decks that achieve desired outcomes

## 📊 Data Models

### SessionMetrics
```python
@dataclass
class SessionMetrics:
    session_id: str
    start_time: datetime
    end_time: datetime
    total_battles: int
    wins: int
    losses: int
    trophy_change: int
    end_reason: SessionEndReason
    player_satisfaction_score: float  # 0.0 to 1.0
```

### RetentionPrediction
```python
@dataclass
class RetentionPrediction:
    next_session_probability: float
    next_day_probability: float
    next_week_probability: float
    optimal_outcome: str  # "win" or "loss"
    confidence: float
    factors: Dict[str, float]
    recommended_action: str
```

## 🔧 Configuration

### Algorithm Parameters

Key parameters can be adjusted in `RetentionAlgorithm.__init__()`:

```python
self.min_battles_for_analysis = 10
self.frustration_threshold = 0.3
self.comfort_zone_threshold = 0.8
self.engagement_sweet_spot = (0.45, 0.65)
```

### Session Analysis

Session identification parameters in `RetentionAnalyzer.__init__()`:

```python
self.session_gap_threshold = 30  # minutes between sessions
self.frustration_loss_threshold = 3  # consecutive losses
self.satisfaction_win_threshold = 2  # consecutive wins
```

## 📈 Example Output

```
=== Retention Analysis for #8L9L9GL ===
Player Skill Level: intermediate
Play Style: aggressive
Churn Risk: 23.5%
Average Session Length: 18.3 minutes
Overall Win Rate: 52.1%

=== Retention Prediction ===
Optimal Next Outcome: win
Confidence: 73.2%
Next Session Probability: 84.1%
Recommended Action: Provide slight advantage - maintain engagement without being obvious

=== Deck Strategy vs Opponent ===
Opponent Archetype: Royal Giant
Target Outcome: win
Should Change Deck: True
Recommended Archetype: Hog Cycle (Expected Win Rate: 67.3%)
```

## 🔄 API Integration

For integration into a matchmaking system, the key function is:

```python
def get_optimal_outcome(player_tag: str, opponent_deck: List[str]) -> Dict:
    """
    Get the optimal match outcome for maximum retention
    
    Returns:
        {
            "should_win": bool,
            "confidence": float,
            "reasoning": str,
            "deck_recommendation": Dict
        }
    """
    algorithm = RetentionAlgorithm(api_token)
    result = algorithm.recommend_deck_strategy(player_tag, opponent_deck)
    
    prediction = result["retention_prediction"]
    return {
        "should_win": prediction["optimal_outcome"] == "win",
        "confidence": prediction["confidence"],
        "reasoning": prediction["recommended_action"],
        "deck_recommendation": result["deck_optimization"]
    }
```

## 🧪 Testing

### Sample Data

The system includes sample data for testing:
- Default card database with common Clash Royale cards
- Archetype definitions for major deck types
- Simulated matchup data for algorithm testing

### Running Tests

```bash
# Test individual components
python clash_royale_api_client.py
python deck_analyzer.py
python retention_algorithm.py
```

## 🚨 Limitations

1. **API Rate Limits**: The Clash Royale API has rate limits; implement caching for production use
2. **Battle History**: Limited to 25 most recent battles per player
3. **Sample Data**: Card and archetype data is simplified; production systems should use comprehensive databases
4. **Real-time Data**: Algorithm assumes access to opponent deck data, which may not be available in real-time

## 🔮 Future Enhancements

1. **Machine Learning**: Replace rule-based decisions with trained ML models
2. **Real-time Analytics**: Stream processing for live match analysis
3. **A/B Testing**: Framework for testing different retention strategies
4. **Comprehensive Card DB**: Full card database with evolution data
5. **Advanced Metrics**: More sophisticated player behavioral modeling
6. **Clan Analysis**: Factor in clan activity and social elements

## 📚 References

- [Clash Royale API Documentation](https://developer.clashofclans.com/)
- [RoyaleAPI Community Data](https://royaleapi.com/)
- Player retention research in mobile gaming
- Matchmaking algorithms and player experience optimization

## 📄 License

This project is for educational and research purposes. Clash Royale is a trademark of Supercell Oy.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

For questions or suggestions, please open an issue or contact the maintainers.