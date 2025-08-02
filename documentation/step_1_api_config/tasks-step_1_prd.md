# Task List: Step 1 - API Connectivity & Data Validation

## Relevant Files

- `src/api_client.py` - Main module containing all four API integration functions ✅ Created (with env validation)
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

## Tasks

- [ ] 1.0 Environment Setup & Dependencies Configuration
  - [x] 1.1 Create `requirements.txt` with requests, python-dotenv dependencies
  - [x] 1.2 Create `env.example` file with placeholder API key variables
  - [x] 1.3 Create actual `.env` file with provided API keys (RAPIDAPI_KEY, CFB_API_KEY, RAPIDAPI_HOST)
  - [x] 1.4 Create `setup.md` documentation with clear instructions for environment variable configuration
  - [x] 1.5 Add environment variable validation function to check for required keys before API calls

- [ ] 2.0 PrizePicks API Integration & Testing
  - [ ] 2.1 Create `fetch_prizepicks_data()` function in `api_client.py`
  - [ ] 2.2 Implement GET request to PrizePicks endpoint with specified parameters (league_id=9, per_page=250, etc.)
  - [ ] 2.3 Add response validation to verify expected fields (projections, attributes, player_name)
  - [ ] 2.4 Implement console output showing total record count and full sample record
  - [ ] 2.5 Add independent test execution capability with clear success/failure status

- [ ] 3.0 Underdog Fantasy API Integration & Testing
  - [ ] 3.1 Create `fetch_underdog_data()` function in `api_client.py`
  - [ ] 3.2 Implement GET request to Underdog Fantasy over_under_lines endpoint
  - [ ] 3.3 Add response validation to verify expected fields (over_under_lines, player, stat_type)
  - [ ] 3.4 Implement console output showing total record count and full sample record
  - [ ] 3.5 Add independent test execution capability with clear success/failure status

- [ ] 4.0 NFL Player Stats API Integration & Testing
  - [ ] 4.1 Create `fetch_nfl_game_ids()` function in `api_client.py`
  - [ ] 4.2 Implement RapidAPI authentication headers (x-rapidapi-key, x-rapidapi-host)
  - [ ] 4.3 Implement GET request to NFL weeks events endpoint (year=2023, week=1, type=2)
  - [ ] 4.4 Add response validation to verify expected fields (events, competitions, competitors)
  - [ ] 4.5 Implement console output showing total games count and full sample game record
  - [ ] 4.6 Add independent test execution capability with authentication error detection

- [ ] 5.0 College Football Data API Integration & Testing
  - [ ] 5.1 Create `fetch_cfb_player_data()` function in `api_client.py`
  - [ ] 5.2 Implement Bearer token authentication using CFB_API_KEY environment variable
  - [ ] 5.3 Implement GET request to games/players endpoint (year=2023, week=1, seasonType=regular)
  - [ ] 5.4 Add response validation to verify expected fields (games, teams, statistics)
  - [ ] 5.5 Implement console output showing total games count and full sample player stat record
  - [ ] 5.6 Add independent test execution capability with Bearer token validation

- [ ] 6.0 Error Handling & Validation Framework
  - [ ] 6.1 Implement detailed HTTP status code logging (200, 403, 404, 500, etc.) for all functions
  - [ ] 6.2 Add response content analysis and logging for debugging purposes
  - [ ] 6.3 Handle connection errors (timeouts, DNS failures, connection refused) with clear messages
  - [ ] 6.4 Implement specific authentication error detection and reporting
  - [ ] 6.5 Create consistent error message format with human-readable descriptions
  - [ ] 6.6 Add visual separators in console output between different API test results