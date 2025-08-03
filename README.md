# 🏈 Football Prop Insights

A comprehensive backend ingestion system for football prop betting data and player performance statistics, supporting both NFL and College Football.

## 📖 Overview

Football Prop Insights is designed to collect, store, and analyze football betting prop data alongside player performance statistics. The system currently focuses on quarterback (QB) and wide receiver (WR) props with plans to expand to additional positions and sports.

### Current Features
- ✅ **API Connectivity**: Integrated with 4 major football data APIs
- ✅ **Automated Data Collection**: Shell script for easy data generation
- ✅ **JSON Data Persistence**: All API responses saved to organized file structure
- ✅ **Data Parsing & Validation**: Comprehensive data transformation and quality assurance
- ✅ **PostgreSQL Database**: Production-ready database storage with validation
- ✅ **Comprehensive Error Handling**: Robust error handling with detailed logging
- ✅ **Environment Management**: Secure API key handling with environment variables
- ✅ **Testing Framework**: Automated testing for all database operations

### Data Sources
- **PrizePicks API**: Prop betting lines for NFL and College Football
- **NFL API (RapidAPI)**: Professional football game IDs and detailed player boxscore statistics
- **College Football Data API**: Comprehensive college football statistics
- **Underdog Fantasy API**: (Planned for future implementation)

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip package manager
- Git
- PostgreSQL 12+ (for database functionality)

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

## 🗄️ Database Setup

### PostgreSQL Installation & Configuration

The system uses PostgreSQL for robust, scalable data storage. Follow these steps to set up the database:

#### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
- Download from [PostgreSQL.org](https://www.postgresql.org/download/windows/)
- Follow the installer instructions

#### 2. Create Database User & Database

```bash
# Connect as postgres user
sudo -u postgres psql

# Create a user (replace 'your_username' with your system username)
CREATE USER your_username WITH SUPERUSER;

# Exit PostgreSQL
\q

# Create the football_props database
createdb football_props -U your_username
```

#### 3. Verify Database Connection

```bash
psql -U your_username -d football_props -c "SELECT current_database(), current_user;"
```

Expected output:
```
 current_database | current_user 
------------------+--------------
 football_props   | your_username
(1 row)
```

#### 4. Install Python Database Dependencies

```bash
pip3 install psycopg2-binary
```

### Database Schema

The system uses 5 main tables optimized for football prop betting analysis:

#### Tables Overview

1. **`prop_lines`** - Betting projections and prop lines
2. **`player_stats`** - Actual player performance statistics  
3. **`games_processed`** - Tracking processed games to prevent duplicates
4. **`players`** - Reference table for player metadata
5. **`teams`** - Reference table for team information

#### Create Database Tables

```bash
# Navigate to project directory
cd football_props_finder

# Create all tables using the provided SQL script
psql -U your_username -d football_props -f setup_database.sql
```

#### Verify Table Creation

```bash
psql -U your_username -d football_props -c "\dt"
```

You should see all 5 tables listed:
```
           List of relations
 Schema |      Name       | Type  |    Owner     
--------+-----------------+-------+--------------
 public | games_processed | table | your_username
 public | player_stats    | table | your_username
 public | players         | table | your_username
 public | prop_lines      | table | your_username
 public | teams           | table | your_username
```

### Database Configuration

#### Environment Variables

Add database connection details to your `.env` file:

```env
# API Keys (existing)
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=nfl-api-data.p.rapidapi.com
CFB_API_KEY=your_college_football_api_key_here

# Database Configuration (new)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_props
DB_USER=your_username
# DB_PASSWORD=your_password  # Only needed if you set a password
```

#### Connection Test

Test your database connection:

```python
from src.database import get_connection_manager, check_database_connection

# Test connection
if check_database_connection():
    print("✅ Database connection successful!")
else:
    print("❌ Database connection failed!")
```

### Database Operations

#### Data Insertion

**Direct Insertion:**
```python
from src.database import insert_prop_line, cursor_context

prop_data = {
    'player_id': 'qb_mahomes_kc_2023',
    'player_name': 'Patrick Mahomes',
    'team': 'KC',
    'opponent': 'DET',
    'position': 'QB',
    'stat_type': 'Pass Yards',
    'line_score': 285.5,
    'league': 'nfl',
    'source': 'PrizePicks',
    'season': 2023
}

with cursor_context() as cursor:
    result = insert_prop_line(cursor, prop_data)
    print(f"Insertion result: {result}")
```

**Batch Insertion:**
```python
from src.database import batch_insert_prop_lines, batch_transaction

# Prepare multiple records
prop_lines = [prop_data1, prop_data2, prop_data3, ...]

with batch_transaction() as transaction:
    result = batch_insert_prop_lines(transaction, prop_lines)
    print(f"Inserted {result.inserted_count} records")
```

**Upsert (Insert or Update):**
```python
from src.database import upsert_prop_line, cursor_context

with cursor_context() as cursor:
    result = upsert_prop_line(cursor, prop_data)
    print(f"Upsert result: {result}")
```

#### Data Validation

**Validate Individual Records:**
```python
from src.database import DataValidator

validator = DataValidator()

# Validate prop line data
report = validator.validate_prop_line(prop_data)

if report.is_valid:
    print("✅ Data is valid!")
else:
    print(f"❌ Validation failed: {len(report.get_errors())} errors")
    for error in report.get_errors():
        print(f"  • {error}")
```

**Batch Validation:**
```python
# Validate multiple records
reports = validator.validate_batch(prop_lines, 'prop_lines')

success_rate = sum(1 for r in reports if r.is_valid) / len(reports) * 100
print(f"Validation success rate: {success_rate:.1f}%")
```

#### Parser Integration

**Load and Insert Parsed Data:**
```python
from src.database import load_and_route_parsed_file

# Load PrizePicks data and insert into database
result = load_and_route_parsed_file('parsed_data/prizepicks/nfl_parsed.json')
print(f"Processed {result['total_records']} records")

# Load NFL boxscore data
result = load_and_route_parsed_file('parsed_data/nfl_boxscore/boxscore_401547353_parsed.json')
print(f"Processed {result['total_records']} records")
```

**Batch Process All Parsed Files:**
```python
from src.database import load_and_route_parsed_directory

# Process entire parsed_data directory
results = load_and_route_parsed_directory('parsed_data')
for file_result in results:
    print(f"File: {file_result['file']}, Records: {file_result['total_records']}")
```

### Database Testing

#### Comprehensive Test Suite

Run the complete database test suite:

```python
from src.database import test_all_insertions

# Run all database tests
results = test_all_insertions()

print(f"Test Results:")
print(f"  Total Tests: {results['total_tests']}")
print(f"  Passed: {results['passed']}")
print(f"  Failed: {results['failed']}")
print(f"  Success Rate: {results['success_rate']:.1f}%")
```

#### Individual Test Components

**Test Data Loading:**
```python
from src.database import SampleDataLoader

loader = SampleDataLoader()

# Load sample PrizePicks data
prizepicks_data = loader.load_sample_data('prizepicks', max_records=10)
print(f"Loaded {len(prizepicks_data)} PrizePicks records")

# Load sample NFL boxscore data  
nfl_data = loader.load_sample_data('nfl_boxscore', max_records=10)
print(f"Loaded {len(nfl_data)} NFL boxscore records")
```

**Test Data Validation:**
```python
from src.database import DatabaseTester

tester = DatabaseTester()

# Test validation functions
tester.test_validation_functions()

# Test real data loading
tester.test_real_data_loading()

# Run performance tests (requires PostgreSQL)
if psycopg2_available:
    tester.test_performance_baseline()
```

### Database Maintenance

#### Check Data Quality

```sql
-- Connect to database
psql -U your_username -d football_props

-- Check record counts
SELECT 'prop_lines' as table_name, COUNT(*) as record_count FROM prop_lines
UNION ALL
SELECT 'player_stats', COUNT(*) FROM player_stats
UNION ALL  
SELECT 'games_processed', COUNT(*) FROM games_processed
UNION ALL
SELECT 'players', COUNT(*) FROM players
UNION ALL
SELECT 'teams', COUNT(*) FROM teams;

-- Check for data quality issues
SELECT COUNT(*) as missing_required_fields 
FROM prop_lines 
WHERE player_name IS NULL OR team IS NULL OR stat_type IS NULL;

-- Check statistical consistency
SELECT COUNT(*) as inconsistent_stats
FROM player_stats 
WHERE (completions > attempts AND completions IS NOT NULL AND attempts IS NOT NULL)
   OR (receptions > targets AND receptions IS NOT NULL AND targets IS NOT NULL);
```

#### Backup & Restore

**Backup Database:**
```bash
pg_dump -U your_username football_props > football_props_backup.sql
```

**Restore Database:**
```bash
dropdb football_props -U your_username
createdb football_props -U your_username  
psql -U your_username -d football_props -f football_props_backup.sql
```

## 📊 Data Generation & Parsing

### Using the Shell Script (Recommended)

The project includes a convenient shell script for generating and parsing API data:

```bash
./generate_api_data.sh <api_type> [additional_params...]
```

**What the script does:**
1. **Fetches raw JSON data** from APIs → saved to `api_data/` directory
2. **Parses data into structured format** → saved to `parsed_data/` directory

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

#### NFL Boxscore API
```bash
./generate_api_data.sh nfl-boxscore <event_id>

# Examples:
./generate_api_data.sh nfl-boxscore 401220225    # Get detailed player stats for game
./generate_api_data.sh nfl-boxscore 401547410    # Different game example
```

**Parameters:**
- `event_id`: NFL game event ID (obtained from nfl-stats command)

**Output:** Detailed player statistics including passing, rushing, receiving, defense, and special teams stats for all players in the specified game.

#### NFL Weekly Boxscore API
```bash
./generate_api_data.sh nfl-week-boxscores <year> <week> <type>

# Examples:
./generate_api_data.sh nfl-week-boxscores 2023 1 2    # ALL games from Week 1, 2023 Regular Season
./generate_api_data.sh nfl-week-boxscores 2023 5 2    # ALL games from Week 5, 2023 Regular Season
./generate_api_data.sh nfl-week-boxscores 2023 1 3    # ALL playoff games from Week 1, 2023
```

**Parameters:**
- `year`: NFL season year (e.g., 2023, 2024)
- `week`: Week number (1-18)
- `type`: Game type (1=preseason, 2=regular season, 3=postseason)

**Output:** Complete player statistics for ALL games in the specified week. This command:
- ✅ Fetches game IDs for the entire week
- ✅ Downloads detailed boxscore data for every game
- ✅ Saves individual game files: `boxscore_{event_id}.json`
- ✅ Creates a week summary: `week_summary_{year}_week{week}_type{type}.json`
- ⚠️ **Note:** Takes several minutes as it processes 15-16 games per week

**Perfect for:** Comprehensive weekly analysis, prop betting research across all games, and bulk data collection.

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

The script generates two types of output:

### Raw API Data
All API responses are automatically saved to the `api_data/` directory with the following structure:

```
api_data/
├── prizepicks/
│   ├── nfl_projections.json      # NFL prop betting lines
│   └── cfb_projections.json      # College Football prop betting lines
├── nfl_stats/
│   └── games_YYYY_weekN_typeT.json  # NFL game IDs and basic info
├── nfl_boxscore/
│   ├── boxscore_EVENT_ID.json    # Individual game detailed player stats
│   └── week_summary_YYYY_weekN_typeT.json  # Weekly processing summary
└── cfb_stats/
    └── players_YYYY_weekN_SEASON.json  # College Football player statistics
```

### Parsed Data
Structured, analyzed data is saved to the `parsed_data/` directory:

```
parsed_data/
├── prizepicks/
│   ├── nfl_parsed.json               # Structured NFL projections
│   └── cfb_parsed.json               # Structured CFB projections
├── nfl_stats/
│   └── games_YYYY_weekN_typeT_parsed.json  # Parsed NFL game IDs
├── nfl_boxscore/
│   ├── boxscore_EVENT_ID_parsed.json      # Individual parsed player stats
│   └── week_YYYY_weekN_typeT_all_parsed.json  # Combined weekly player stats
└── cfb_stats/
    └── players_YYYY_weekN_SEASON_parsed.json  # Parsed CFB player stats
```

### File Naming Conventions

- **PrizePicks**: `{league}_projections.json`
- **NFL Stats**: `games_{year}_week{week}_type{type}.json`
- **NFL Boxscore**: `boxscore_{event_id}.json`
- **NFL Week Summary**: `week_summary_{year}_week{week}_type{type}.json`
- **CFB Stats**: `players_{year}_week{week}_{season_type}.json`

### Data Samples

#### Raw PrizePicks Data Structure
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

#### Parsed PrizePicks Data Structure
```json
[
  {
    "player_name": "Jalen Hurts",
    "team": "UNK",
    "opponent": "Unknown Opponent", 
    "stat_type": "Pass Yards",
    "line_score": 249.5,
    "game_time": null,
    "projection_id": "5591188"
  }
]
```

#### Raw NFL Stats Data Structure
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

#### Raw NFL Boxscore Data Structure
```json
{
  "boxscore": {
    "teams": [
      {
        "team": {
          "id": "34",
          "name": "Texans",
          "displayName": "Houston Texans"
        }
      }
    ],
    "players": [
      {
        "team": {"name": "Texans"},
        "statistics": [
          {
            "name": "passing",
            "athletes": [
              {
                "athlete": {
                  "id": "3122840",
                  "displayName": "Deshaun Watson"
                },
                "stats": ["20/32", "253", "7.9", "1", "1", "4-11", "38.7", "84.5"]
              }
            ]
          }
        ]
      }
    ]
  }
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
│   ├── api_client.py         # Main API integration module
│   └── database/             # Database layer
│       ├── __init__.py       # Database package initialization
│       ├── connection.py     # PostgreSQL connection management
│       ├── schema.py         # Database schema management
│       ├── insert.py         # Direct insertion functions
│       ├── batch.py          # Batch insertion operations
│       ├── validation.py     # Data validation framework
│       ├── sample_data.py    # Testing and sample data utilities
│       └── parser_integration.py  # Parser-to-database integration
├── parsers/                  # Data parsing modules
│   ├── __init__.py           # Parsers package initialization
│   ├── common.py             # Common parsing utilities
│   ├── parse_prizepicks.py   # PrizePicks data parser
│   ├── parse_cfb_stats.py    # College Football data parser
│   ├── parse_nfl_game_ids.py # NFL game IDs parser
│   └── parse_nfl_boxscore.py # NFL boxscore data parser
├── documentation/            # Project documentation
│   ├── step_1_api_config/    # API configuration documentation
│   ├── step_2_data_parsing/  # Data parsing documentation
│   └── step_3_store_data_in_db/  # Database documentation
├── api_data/                 # Generated API data (auto-created)
├── parsed_data/              # Parsed, structured data (auto-created)
├── setup_database.sql        # Database schema creation script
├── generate_api_data.sh      # Data generation & parsing script
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

#### `parsers/` Package
- **`parse_prizepicks.py`**: Converts PrizePicks JSON to structured data
- **`parse_cfb_stats.py`**: Parses College Football player statistics  
- **`parse_nfl_game_ids.py`**: Extracts NFL game identifiers
- **`parse_nfl_boxscore.py`**: Processes detailed NFL player performance data
- **`common.py`**: Shared parsing utilities and error handling

#### `src/database/` Package
- **`connection.py`**: PostgreSQL connection pooling and management
- **`schema.py`**: Database table creation and schema management
- **`insert.py`**: Direct data insertion functions for all tables
- **`batch.py`**: High-performance batch insertion operations  
- **`validation.py`**: Comprehensive data validation framework
- **`sample_data.py`**: Testing utilities and sample data generators
- **`parser_integration.py`**: Seamless integration between parsers and database

### Error Handling

The system includes comprehensive error handling for:
- ✅ HTTP status codes (200, 401, 403, 404, 500)
- ✅ JSON decoding errors
- ✅ Network timeouts and connection issues
- ✅ Authentication and authorization failures
- ✅ Rate limiting and API quota management
- ✅ Invalid response structures and missing data fields

### Testing

#### API Testing
Run the complete API test suite:
```bash
python3 src/api_client.py
```

This will test all APIs and display a summary of results.

#### Parser Testing
Test all data parsing functions:
```bash
python3 parsers/test_all_parsers.py
```

#### Database Testing
Run comprehensive database tests:
```bash
python3 -m src.database.sample_data
```

This will test:
- ✅ Data validation functions
- ✅ Real data file loading from `parsed_data/`
- ✅ Database insertion operations (if PostgreSQL available)
- ✅ Query validation and data consistency checks
- ✅ Performance benchmarks for batch operations

#### Individual Component Testing
Test specific components:
```bash
# Test validation framework
python3 -m src.database.validation

# Test database connection
python3 -c "from src.database import check_database_connection; print('✅ Connected!' if check_database_connection() else '❌ Failed!')"

# Test parser on specific file
python3 -c "from parsers import parse_prizepicks_data; print(len(parse_prizepicks_data('parsed_data/prizepicks/nfl_parsed.json')), 'records parsed')"
```

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

### Phase 2: Data Parsing ✅ (Completed)
- [x] Standardize data structures across APIs
- [x] Player name matching and normalization
- [x] Stat type categorization and mapping
- [x] Data validation and quality checks
- [x] Comprehensive parsing framework for all APIs
- [x] Enhanced data quality with metadata enrichment

### Phase 3: Database Integration ✅ (Completed)
- [x] PostgreSQL schema design
- [x] Data ingestion pipelines (direct, batch, upsert)
- [x] Historical data storage with 5-table schema
- [x] Query optimization and connection pooling
- [x] Comprehensive validation framework
- [x] Testing and sample data utilities

### Phase 4: Analysis Engine (Next)
- [ ] Prop line analysis algorithms
- [ ] Player performance correlation models
- [ ] Betting suggestion algorithms
- [ ] ROI tracking and optimization
- [ ] Real-time data ingestion
- [ ] Web dashboard for insights

### Phase 5: Advanced Features (Future)
- [ ] Machine learning models for prop predictions
- [ ] Live odds comparison across multiple sportsbooks
- [ ] Automated betting strategies
- [ ] Mobile app interface
- [ ] Multi-sport expansion

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