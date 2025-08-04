# Data Collection for Clash Royale Retention Analysis

This guide explains how to collect the data needed to develop retention algorithms for Clash Royale.

## 🚀 Quick Start

### 1. Get Your API Token

1. Go to [Clash of Clans Developer Portal](https://developer.clashofclans.com/)
2. Create an account and log in
3. Create a new application
4. Copy your API token

### 2. Set Environment Variable

```bash
export CLASH_ROYALE_API_TOKEN='your_token_here'
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Data Collection

```bash
python run_data_collection.py
```

## 📊 What Data is Collected

### Player Data
- **Profile Information**: Level, trophies, win rate, clan
- **Current Deck**: Cards, levels, average elixir cost
- **Battle History**: Recent battles with detailed statistics
- **Session Analysis**: Play patterns and session duration

### Battle Data
- **Match Details**: Win/loss, crowns, trophy changes
- **Deck Information**: Cards used in each battle
- **Game Context**: Arena, game mode, tournament status
- **Performance Metrics**: Crown differences, close matches

### Cards Data
- **All Available Cards**: Complete card database
- **Card Properties**: Rarity, elixir cost, levels
- **Meta Information**: Card usage patterns

### Tournament Data
- **Active Tournaments**: Current and upcoming tournaments
- **Global Tournaments**: Special event information
- **Tournament Statistics**: Participation and performance

## 📁 Output Files

After running data collection, you'll find these files:

```
data/
├── collected_data.json          # Raw collected data
├── players/                     # Individual player data
│   └── player_[TAG].json
├── battles/                     # Battle history
│   └── battles_[TAG].json
├── cards/                       # Cards database
│   ├── all_cards.json
│   └── all_cards.csv
├── tournaments/                 # Tournament data
│   └── tournaments.json
└── analysis/                    # Analysis-ready datasets
    ├── players_analysis.csv
    ├── battles_analysis.csv
    ├── sessions_analysis.csv
    ├── retention_indicators.csv
    └── analysis_summary.json
```

## 🔧 Customizing Data Collection

### Using Your Own Player Tags

1. Edit `sample_players.txt` with real player tags
2. Or modify `run_data_collection.py` with your tags:

```python
sample_player_tags = [
    "#YOUR_PLAYER_TAG_1",
    "#YOUR_PLAYER_TAG_2",
    "#YOUR_PLAYER_TAG_3",
]
```

### Advanced Usage

Use the command-line interface for more control:

```bash
python data_collector.py \
    --api-token YOUR_TOKEN \
    --player-tags "#TAG1" "#TAG2" "#TAG3" \
    --max-battles 50 \
    --collect-cards \
    --collect-tournaments \
    --create-analysis
```

## 📈 Data Analysis Features

### Retention Indicators

The system automatically calculates retention risk factors:

- **Win Rate**: Overall and recent performance
- **Session Patterns**: Play frequency and duration
- **Trophy Volatility**: Stability of progression
- **Engagement Metrics**: Close matches, battle frequency
- **Risk Score**: 0-100 retention risk assessment

### Session Analysis

- **Session Duration**: Time spent in each play session
- **Battles per Session**: Engagement intensity
- **Performance Trends**: Win rates within sessions
- **Break Patterns**: Time between sessions

### Battle Analysis

- **Match Outcomes**: Win/loss patterns
- **Performance Metrics**: Crown differences, trophy changes
- **Deck Usage**: Card combinations and effectiveness
- **Game Context**: Arena levels, tournament participation

## 🎯 Retention Algorithm Development

The collected data supports various retention analysis approaches:

### 1. Player Segmentation
- **Skill Levels**: Based on trophies and win rates
- **Engagement Types**: Casual vs. competitive players
- **Risk Categories**: High/medium/low retention risk

### 2. Behavioral Patterns
- **Play Frequency**: Daily/weekly activity patterns
- **Session Behavior**: Duration and intensity
- **Progression Patterns**: Trophy gain/loss trends

### 3. Performance Analysis
- **Win Rate Trends**: Improving or declining performance
- **Deck Effectiveness**: Card combination success rates
- **Match Quality**: Close vs. one-sided games

### 4. Predictive Models
- **Churn Prediction**: Likelihood of player leaving
- **Engagement Forecasting**: Future activity levels
- **Intervention Opportunities**: When to provide support

## 🔍 Data Quality Notes

### API Limitations
- **Rate Limits**: 100ms between requests
- **Data Availability**: Recent battles only (max 25 per player)
- **Player Privacy**: Some data may be restricted

### Data Validation
- **Missing Data**: Some players may have incomplete profiles
- **API Errors**: Network issues or invalid player tags
- **Data Consistency**: Verify collected data quality

## 🛠️ Troubleshooting

### Common Issues

1. **API Token Error**
   ```
   Error: CLASH_ROYALE_API_TOKEN environment variable not set
   ```
   Solution: Set your API token as shown above

2. **Player Not Found**
   ```
   Failed to collect data for #TAG: 404 Not Found
   ```
   Solution: Verify player tag is correct and player exists

3. **Rate Limit Exceeded**
   ```
   Rate limit exceeded
   ```
   Solution: Wait and retry, or reduce number of players

4. **Network Errors**
   ```
   Connection timeout
   ```
   Solution: Check internet connection and retry

### Getting Help

- Check the API documentation: https://developer.clashofclans.com/
- Verify your API token has proper permissions
- Ensure player tags are in correct format (#TAG)

## 📚 Next Steps

After collecting data:

1. **Review the Data**: Examine `data/analysis/` files
2. **Develop Models**: Use the data for retention algorithms
3. **Validate Results**: Test predictions against new data
4. **Iterate**: Collect more data and refine models

The collected data provides a solid foundation for developing sophisticated retention algorithms and player engagement strategies. 