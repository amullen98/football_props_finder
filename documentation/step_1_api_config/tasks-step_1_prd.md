# Task List: Step 1 - API Connectivity & Data Validation

## Relevant Files

- `src/api_client.py` - Main module containing all four API integration functions ✅ Created (with env validation + PrizePicks + NFL functions)
- `requirements.txt` - Python dependencies (requests, python-dotenv) ✅ Created
- `.env` - Environment variables for API keys and configuration ✅ Created
- `env.example` - Example environment file with placeholder values ✅ Created
- `setup.md` - Documentation for environment setup and configuration ✅ Created
- `test_api_client.py` - Independent test runner for validating all API functions
- `logs/api_test_results.txt` - Optional log file for capturing test outputs

### Notes

- All API functions should be contained in a single module for Step 1 simplicity
- Each function must be independently testable via `if __name__ == "__main__"` blocks
- Environment variables must be validated before making API calls
- Console output should include clear separators between different API test results
- **SCOPE UPDATE**: Underdog Fantasy API integration deferred - focusing on PrizePicks only for now

## Tasks

- [x] 1.0 Environment Setup & Dependencies Configuration
  - [x] 1.1 Create `requirements.txt` with requests, python-dotenv dependencies
  - [x] 1.2 Create `env.example` file with placeholder API key variables
  - [x] 1.3 Create actual `.env` file with provided API keys (RAPIDAPI_KEY, CFB_API_KEY, RAPIDAPI_HOST)
  - [x] 1.4 Create `setup.md` documentation with clear instructions for environment variable configuration
  - [x] 1.5 Add environment variable validation function to check for required keys before API calls

- [x] 2.0 PrizePicks API Integration & Testing
  - [x] 2.1 Create `fetch_prizepicks_data(league='nfl')` function in `api_client.py` with league parameter
  - [x] 2.2 Implement GET request to PrizePicks NFL endpoint (league_id=9, per_page=250, state_code=CA, game_mode=prizepools)
  - [x] 2.3 Implement GET request to PrizePicks College Football endpoint (league_id=15, per_page=250, state_code=CA, game_mode=prizepools)
  - [x] 2.4 Add response validation to verify expected fields (projections, attributes, player_name)
  - [x] 2.5 Implement console output showing total record count and full sample record for both leagues
  - [x] 2.6 Add independent test execution capability with clear success/failure status for both NFL and CFB

- [ ] ~~3.0 Underdog Fantasy API Integration & Testing~~ (DEFERRED - Focusing on PrizePicks only)
  - [ ] ~~3.1 Create `fetch_underdog_data()` function in `api_client.py`~~ (DEFERRED)
  - [ ] ~~3.2 Implement GET request to Underdog Fantasy over_under_lines endpoint~~ (DEFERRED)
  - [ ] ~~3.3 Add response validation to verify expected fields (over_under_lines, player, stat_type)~~ (DEFERRED)
  - [ ] ~~3.4 Implement console output showing total record count and full sample record~~ (DEFERRED)
  - [ ] ~~3.5 Add independent test execution capability with clear success/failure status~~ (DEFERRED)

- [x] 3.0 NFL Player Stats API Integration & Testing
  - [x] 3.1 Create `fetch_nfl_game_ids()` function in `api_client.py`
  - [x] 3.2 Implement RapidAPI authentication headers (x-rapidapi-key, x-rapidapi-host)
  - [x] 3.3 Implement GET request to NFL weeks events endpoint (year=2023, week=1, type=2)
  - [x] 3.4 Add response validation to verify expected fields (items, count, pageIndex)
  - [x] 3.5 Implement console output showing total games count and full sample game record
  - [x] 3.6 Add independent test execution capability with authentication error detection

- [x] 4.0 College Football Data API Integration & Testing
  - [x] 4.1 Create `fetch_cfb_player_data()` function in `api_client.py`
  - [x] 4.2 Implement Bearer token authentication using CFB_API_KEY environment variable
  - [x] 4.3 Implement GET request to games/players endpoint (year=2023, week=1, seasonType=regular)
  - [x] 4.4 Add response validation to verify expected fields (list format, teams, statistics)
  - [x] 4.5 Implement console output showing total games count and full sample player stat record
  - [x] 4.6 Add independent test execution capability with Bearer token validation

- [ ] 5.0 Error Handling & Validation Framework
  - [ ] 5.1 Implement detailed HTTP status code logging (200, 403, 404, 500, etc.) for all functions
  - [ ] 5.2 Add response content analysis and logging for debugging purposes
  - [ ] 5.3 Handle connection errors (timeouts, DNS failures, connection refused) with clear messages
  - [ ] 5.4 Implement specific authentication error detection and reporting
  - [ ] 5.5 Create consistent error message format with human-readable descriptions
  - [ ] 5.6 Add visual separators in console output between different API test results