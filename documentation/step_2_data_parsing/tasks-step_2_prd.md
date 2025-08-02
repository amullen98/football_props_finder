# Task List: Data Parsing Module for Football Prop Insights

## Relevant Files

- `parsers/parse_prizepicks.py` - Parser for PrizePicks NFL projection data, handles complex lookup dictionaries and field extraction
- `parsers/parse_cfb_stats.py` - Parser for College Football player statistics, filters by position and extracts relevant stats
- `parsers/parse_nfl_game_ids.py` - Simple parser for NFL game ID extraction from weekly game lists
- `parsers/parse_nfl_boxscore.py` - Complex parser for NFL boxscore data, navigates nested player statistics
- `parsers/__init__.py` - Module initialization file with imports and metadata, establishes parsers as Python package
- `parsers/common.py` - Common utilities and error handling patterns used across all parsers
- `parsers/function_patterns.py` - Function signature templates and patterns for consistent parser implementation

### Notes

- All parsers will process existing JSON files from the `api_data/` directory created by Step 1 API integration
- Input files are located in: `api_data/prizepicks/`, `api_data/nfl_stats/`, `api_data/nfl_boxscore/`, `api_data/cfb_stats/`
- No unit tests required as per PRD specifications (Testing Requirements: A - No specific testing requirements)
- Each parser function should accept either file paths or pre-loaded JSON data for flexibility

## Tasks

- [ ] 1.0 Set Up Parsing Module Structure and Foundation
  - [x] 1.1 Create `parsers/` directory in project root
  - [x] 1.2 Create `parsers/__init__.py` to establish Python package
  - [x] 1.3 Define common error handling patterns for JSON parsing failures
  - [x] 1.4 Define common error handling patterns for file not found errors
  - [x] 1.5 Establish consistent function signature patterns across all parsers

- [ ] 2.0 Implement PrizePicks Parser (`parse_prizepicks.py`)
  - [ ] 2.1 Create `parse_prizepicks_data()` function with proper error handling
  - [ ] 2.2 Implement lookup dictionary creation from `included[]` array for players, teams, and markets
  - [ ] 2.3 Parse `data[]` array to extract projection records
  - [ ] 2.4 Map player references to actual player names using lookup dictionaries
  - [ ] 2.5 Map team references to team abbreviations using lookup dictionaries
  - [ ] 2.6 Extract game time and opponent information from market references
  - [ ] 2.7 Extract `stat_type`, `line_score`, and `projection_id` from projection data
  - [ ] 2.8 Return list of dictionaries matching specified output format
  - [ ] 2.9 Add function to handle both file path and JSON data inputs

- [ ] 3.0 Implement College Football Parser (`parse_cfb_stats.py`)
  - [ ] 3.1 Create `parse_cfb_player_stats()` function with proper error handling
  - [ ] 3.2 Implement position filtering logic for QB, WR, and RB positions only
  - [ ] 3.3 Extract QB-specific statistics: `passYards`, `completions`, `attempts`, `passTD`
  - [ ] 3.4 Extract WR-specific statistics: `receivingYards`, `receptions`, `targets`, `receivingTD`
  - [ ] 3.5 Extract RB receiving statistics: `receivingYards` only
  - [ ] 3.6 Parse game context data: `week`, `gameId`, `startTime`, `opponent`, `team`
  - [ ] 3.7 Handle missing optional statistics gracefully
  - [ ] 3.8 Return list of dictionaries with player and game context information
  - [ ] 3.9 Add function to handle both file path and JSON data inputs

- [ ] 4.0 Implement NFL Game ID Parser (`parse_nfl_game_ids.py`)
  - [ ] 4.1 Create `parse_nfl_game_ids()` function with proper error handling
  - [ ] 4.2 Extract `eventid` values from `items[]` array in JSON structure
  - [ ] 4.3 Parse filename or input parameters to determine week and year
  - [ ] 4.4 Return structured dictionary with `week`, `year`, and `game_ids` list
  - [ ] 4.5 Handle empty or missing items array gracefully
  - [ ] 4.6 Add function to handle both file path and JSON data inputs

- [ ] 5.0 Implement NFL Boxscore Parser (`parse_nfl_boxscore.py`)
  - [ ] 5.1 Create `parse_nfl_boxscore()` function with proper error handling
  - [ ] 5.2 Navigate the nested `boxscore.players` data structure
  - [ ] 5.3 Identify and filter players by position (QB, WR, RB)
  - [ ] 5.4 Extract QB passing statistics from the passing category: yards, completions, attempts, touchdowns, interceptions
  - [ ] 5.5 Extract WR receiving statistics from the receiving category: yards, receptions, targets, touchdowns
  - [ ] 5.6 Extract RB receiving statistics: yards only
  - [ ] 5.7 Parse game_id from filename or input parameter
  - [ ] 5.8 Include player name, team, position, game_id, and stat_type in each record
  - [ ] 5.9 Handle missing player statistics or positions gracefully
  - [ ] 5.10 Return list of dictionaries for all relevant player statistics
  - [ ] 5.11 Add function to handle both file path and JSON data inputs

- [ ] 6.0 Test and Validate All Parsers
  - [ ] 6.1 Test PrizePicks parser with actual `nfl_projections.json` files from api_data
  - [ ] 6.2 Test College Football parser with actual `players_YYYY_weekN_regular.json` files from api_data
  - [ ] 6.3 Test NFL Game ID parser with actual `games_YYYY_weekN_typeT.json` files from api_data
  - [ ] 6.4 Test NFL Boxscore parser with actual `boxscore_<eventid>.json` files from api_data
  - [ ] 6.5 Validate that all parsers return the correct dictionary structures as specified
  - [ ] 6.6 Test error handling with missing files and malformed JSON data
  - [ ] 6.7 Verify that parsers can be imported and used independently
  - [ ] 6.8 Create simple test scripts or manual validation for each parser function