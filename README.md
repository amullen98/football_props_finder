# 🏈 Football Prop Insights

A comprehensive backend ingestion system for football prop betting data and player performance statistics, supporting both NFL and College Football.

## 📖 Overview

Football Prop Insights is designed to collect, store, and analyze football betting prop data alongside player performance statistics. The system currently focuses on quarterback (QB) and wide receiver (WR) props with plans to expand to additional positions and sports.

### Current Features
- ✅ **API Connectivity**: Integrated with 4 major football data APIs
- ✅ **Automated Data Collection**: Shell script for easy data generation
- ✅ **JSON Data Persistence**: All API responses saved to organized file structure
- ✅ **Comprehensive Error Handling**: Robust error handling with detailed logging
- ✅ **Environment Management**: Secure API key handling with environment variables

### Data Sources
- **PrizePicks API**: Prop betting lines for NFL and College Football
- **NFL API (RapidAPI)**: Professional football player statistics and game data
- **College Football Data API**: Comprehensive college football statistics
- **Underdog Fantasy API**: (Planned for future implementation)

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip package manager
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd football_props_finder
   ```

2. **Install dependencies**
   ```bash
   pip3 install --break-system-packages --user -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   RAPIDAPI_KEY=your_rapidapi_key_here
   RAPIDAPI_HOST=nfl-api-data.p.rapidapi.com
   CFB_API_KEY=your_college_football_api_key_here
   ```

4. **Test the setup**
   ```bash
   python3 src/api_client.py
   ```

## 🔑 API Keys Setup

### Required API Keys

1. **RapidAPI Key** (for NFL data)
   - Sign up at [RapidAPI.com](https://rapidapi.com)
   - Subscribe to "NFL API Data" by API Sports
   - **Rate Limit**: 5,000 requests per day
   - Add to `.env` as `RAPIDAPI_KEY`

2. **College Football Data API Key** (for CFB data)
   - Sign up at [CollegeFootballData.com](https://collegefootballdata.com)
   - Generate API key in your account settings
   - **Rate Limit**: 1,000 requests per month (free tier)
   - Add to `.env` as `CFB_API_KEY`

3. **PrizePicks API** (no authentication required)
   - Public API, no key needed
   - **Rate Limit**: No documented limit

## 📊 Data Generation

### Using the Shell Script (Recommended)

The project includes a convenient shell script for generating API data:

```bash
./generate_api_data.sh <api_type> [additional_params...]
```

### Available Commands

#### PrizePicks APIs
```bash
# NFL Props
./generate_api_data.sh prizepicks-nfl

# College Football Props  
./generate_api_data.sh prizepicks-cfb
```

#### NFL Player Stats API
```bash
./generate_api_data.sh nfl-stats <year> <week> <type>

# Examples:
./generate_api_data.sh nfl-stats 2023 1 2    # 2023 Season, Week 1, Regular Season
./generate_api_data.sh nfl-stats 2023 5 2    # 2023 Season, Week 5, Regular Season
./generate_api_data.sh nfl-stats 2023 1 3    # 2023 Season, Week 1, Postseason
```

**Parameters:**
- `year`: NFL season year (e.g., 2023, 2024)
- `week`: Week number (1-18)
- `type`: Game type (1=preseason, 2=regular season, 3=postseason)

#### College Football Data API
```bash
./generate_api_data.sh cfb-stats <year> <week> <season_type>

# Examples:
./generate_api_data.sh cfb-stats 2023 1 regular     # 2023 Season, Week 1, Regular Season
./generate_api_data.sh cfb-stats 2023 5 regular     # 2023 Season, Week 5, Regular Season
./generate_api_data.sh cfb-stats 2023 1 postseason  # 2023 Season, Week 1, Postseason
```

**Parameters:**
- `year`: CFB season year (e.g., 2023, 2024)
- `week`: Week number (1-15)
- `season_type`: Season type (`regular`, `postseason`, `both`)

#### Run All APIs
```bash
./generate_api_data.sh all  # Runs all APIs with default parameters
```

#### Help
```bash
./generate_api_data.sh help
```

### Using Python Directly

You can also call the APIs directly using Python:

```python
from src.api_client import fetch_prizepicks_data, fetch_nfl_game_ids, fetch_cfb_player_data

# PrizePicks
result = fetch_prizepicks_data('nfl')  # or 'cfb'
print(f"Success: {result['success']}, Records: {result.get('record_count', 0)}")

# NFL Stats
result = fetch_nfl_game_ids(2023, 1, 2)
print(f"Success: {result['success']}, Games: {result.get('game_count', 0)}")

# College Football
result = fetch_cfb_player_data(2023, 1, 'regular')
print(f"Success: {result['success']}, Games: {result.get('game_count', 0)}")
```

## 📁 Data Structure

All API responses are automatically saved to the `api_data/` directory with the following structure:

```
api_data/
├── prizepicks/
│   ├── nfl_projections.json      # NFL prop betting lines
│   └── cfb_projections.json      # College Football prop betting lines
├── nfl_stats/
│   └── games_YYYY_weekN_typeT.json  # NFL game data and player stats
└── cfb_stats/
    └── players_YYYY_weekN_SEASON.json  # College Football player statistics
```

### File Naming Conventions

- **PrizePicks**: `{league}_projections.json`
- **NFL Stats**: `games_{year}_week{week}_type{type}.json`
- **CFB Stats**: `players_{year}_week{week}_{season_type}.json`

### Data Samples

#### PrizePicks Data Structure
```json
{
  "data": [
    {
      "type": "projection",
      "id": "5591188",
      "attributes": {
        "line_score": 249.5,
        "stat_type": "Pass Yards",
        "description": "DAL",
        "start_time": "2025-09-04T20:20:00-04:00"
      },
      "relationships": {
        "new_player": {"data": {"type": "new_player", "id": "206300"}},
        "game": {"data": {"type": "game", "id": "69615"}}
      }
    }
  ]
}
```

#### NFL Stats Data Structure
```json
{
  "items": [
    {
      "event": {
        "id": "401547439",
        "name": "Buffalo Bills at New York Jets",
        "date": "2023-09-11T20:15Z"
      }
    }
  ],
  "count": 16
}
```

#### College Football Data Structure
```json
[
  {
    "id": 401520109,
    "teams": [
      {
        "school": "North Carolina State",
        "statistics": [
          {
            "name": "passing",
            "types": [
              {
                "name": "YDS",
                "athletes": [
                  {"id": "4431091", "name": "Ben Finley", "stat": "289"}
                ]
              }
            ]
          }
        ]
      }
    ]
  }
]
```

## 🛠️ Development

### Project Structure
```
football_props_finder/
├── src/
│   └── api_client.py         # Main API integration module
├── documentation/
│   └── step_1_api_config/    # API configuration documentation
├── api_data/                 # Generated API data (auto-created)
├── generate_api_data.sh      # Data generation script
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables template
├── setup.md                 # Setup documentation
└── README.md                # This file
```

### Key Components

#### `src/api_client.py`
- **`fetch_prizepicks_data(league)`**: Fetches PrizePicks projections
- **`fetch_nfl_game_ids(year, week, type)`**: Fetches NFL game data
- **`fetch_cfb_player_data(year, week, season_type)`**: Fetches CFB player stats
- **`save_api_data(data, folder, filename)`**: Saves API responses to JSON files
- **`validate_environment_variables()`**: Validates API key configuration

### Error Handling

The system includes comprehensive error handling for:
- ✅ HTTP status codes (200, 401, 403, 404, 500)
- ✅ JSON decoding errors
- ✅ Network timeouts and connection issues
- ✅ Authentication and authorization failures
- ✅ Rate limiting and API quota management
- ✅ Invalid response structures and missing data fields

### Testing

Run the complete test suite:
```bash
python3 src/api_client.py
```

This will test all APIs and display a summary of results.

## 📈 Rate Limits & Usage

| API | Free Tier Limit | Notes |
|-----|----------------|-------|
| NFL API (RapidAPI) | 5,000/day | Sufficient for development |
| College Football Data | 1,000/month | Can upgrade if needed |
| PrizePicks | No documented limit | Public API |

## 🔧 Troubleshooting

### Common Issues

1. **403 Forbidden from PrizePicks**
   - The system automatically includes browser-like headers to bypass bot protection
   - If issues persist, check for API endpoint changes

2. **Missing API Keys**
   - Ensure all required keys are in `.env` file
   - Run `python3 src/api_client.py` to validate environment

3. **Rate Limit Exceeded**
   - NFL API: Wait for daily reset or upgrade plan
   - CFB API: Wait for monthly reset or upgrade plan

4. **Module Not Found Errors**
   - Install dependencies: `pip3 install -r requirements.txt`
   - Use `--break-system-packages --user` flags if needed

### Debug Mode

For detailed debugging, modify the API functions to include verbose logging:
```python
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
```

## 🚧 Roadmap

### Phase 1: API Connectivity ✅ (Completed)
- [x] PrizePicks API integration
- [x] NFL API integration  
- [x] College Football Data API integration
- [x] Error handling and validation
- [x] Data persistence and file organization

### Phase 2: Data Parsing (Next)
- [ ] Standardize data structures across APIs
- [ ] Player name matching and normalization
- [ ] Stat type categorization and mapping
- [ ] Data validation and quality checks

### Phase 3: Database Integration
- [ ] PostgreSQL schema design
- [ ] Data ingestion pipelines
- [ ] Historical data storage
- [ ] Query optimization

### Phase 4: Analysis Engine
- [ ] Prop line analysis
- [ ] Player performance correlation
- [ ] Betting suggestion algorithms
- [ ] ROI tracking and optimization

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📞 Support

For questions, issues, or feature requests, please open an issue in the GitHub repository.

---

**Built with ❤️ for football analytics and prop betting insights**