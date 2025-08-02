# Task List: Data Parsing Module for Football Prop Insights

## Relevant Files

- `parsers/parse_prizepicks.py` - ✅ COMPLETE - Parser for PrizePicks NFL projection data, handles complex lookup dictionaries and field extraction
- `parsers/parse_cfb_stats.py` - ✅ COMPLETE - Parser for College Football player statistics, filters by position and extracts relevant stats
- `parsers/parse_nfl_game_ids.py` - ✅ COMPLETE - Simple parser for NFL game ID extraction from weekly game lists
- `parsers/parse_nfl_boxscore.py` - ✅ COMPLETE - Complex parser for NFL boxscore data, navigates nested player statistics
- `parsers/__init__.py` - Module initialization file with imports and metadata, establishes parsers as Python package
- `parsers/common.py` - Common utilities and error handling patterns used across all parsers
- `parsers/function_patterns.py` - Function signature templates and patterns for consistent parser implementation

### Notes

- All parsers will process existing JSON files from the `api_data/` directory created by Step 1 API integration
- Input files are located in: `api_data/prizepicks/`, `api_data/nfl_stats/`, `api_data/nfl_boxscore/`, `api_data/cfb_stats/`
- No unit tests required as per PRD specifications (Testing Requirements: A - No specific testing requirements)
- Each parser function should accept either file paths or pre-loaded JSON data for flexibility

## Tasks

- [x] 1.0 Set Up Parsing Module Structure and Foundation
  - [x] 1.1 Create `parsers/` directory in project root
  - [x] 1.2 Create `parsers/__init__.py` to establish Python package
  - [x] 1.3 Define common error handling patterns for JSON parsing failures
  - [x] 1.4 Define common error handling patterns for file not found errors
  - [x] 1.5 Establish consistent function signature patterns across all parsers

- [x] 2.0 Implement PrizePicks Parser (`parse_prizepicks.py`)
  - [x] 2.1 Create `parse_prizepicks_data()` function with proper error handling
  - [x] 2.2 Implement lookup dictionary creation from `included[]` array for players, teams, and markets
  - [x] 2.3 Parse `data[]` array to extract projection records
  - [x] 2.4 Map player references to actual player names using lookup dictionaries
  - [x] 2.5 Map team references to team abbreviations using lookup dictionaries
  - [x] 2.6 Extract game time and opponent information from market references
  - [x] 2.7 Extract `stat_type`, `line_score`, and `projection_id` from projection data
  - [x] 2.8 Return list of dictionaries matching specified output format
  - [x] 2.9 Add function to handle both file path and JSON data inputs

- [x] 3.0 Implement College Football Parser (`parse_cfb_stats.py`)
  - [x] 3.1 Create `parse_cfb_player_stats()` function with proper error handling
  - [x] 3.2 Implement position filtering logic for QB, WR, and RB positions only
  - [x] 3.3 Extract QB-specific statistics: `passYards`, `completions`, `attempts`, `passTD`
  - [x] 3.4 Extract WR-specific statistics: `receivingYards`, `receptions`, `targets`, `receivingTD`
  - [x] 3.5 Extract RB receiving statistics: `receivingYards` only
  - [x] 3.6 Parse game context data: `week`, `gameId`, `startTime`, `opponent`, `team`
  - [x] 3.7 Handle missing optional statistics gracefully
  - [x] 3.8 Return list of dictionaries with player and game context information
  - [x] 3.9 Add function to handle both file path and JSON data inputs

- [x] 4.0 Implement NFL Game ID Parser (`parse_nfl_game_ids.py`)
  - [x] 4.1 Create `parse_nfl_game_ids()` function with proper error handling
  - [x] 4.2 Extract `eventid` values from `items[]` array in JSON structure
  - [x] 4.3 Parse filename or input parameters to determine week and year
  - [x] 4.4 Return structured dictionary with `week`, `year`, and `game_ids` list
  - [x] 4.5 Handle empty or missing items array gracefully
  - [x] 4.6 Add function to handle both file path and JSON data inputs

- [x] 5.0 Implement NFL Boxscore Parser (`parse_nfl_boxscore.py`)
  - [x] 5.1 Create `parse_nfl_boxscore()` function with proper error handling
  - [x] 5.2 Navigate the nested `boxscore.players` data structure
  - [x] 5.3 Identify and filter players by position (QB, WR, RB)
  - [x] 5.4 Extract QB passing statistics from the passing category: yards, completions, attempts, touchdowns, interceptions
  - [x] 5.5 Extract WR receiving statistics from the receiving category: yards, receptions, targets, touchdowns
  - [x] 5.6 Extract RB receiving statistics: yards only
  - [x] 5.7 Parse game_id from filename or input parameter
  - [x] 5.8 Include player name, team, position, game_id, and stat_type in each record
  - [x] 5.9 Handle missing player statistics or positions gracefully
  - [x] 5.10 Return list of dictionaries for all relevant player statistics
  - [x] 5.11 Add function to handle both file path and JSON data inputs

- [x] 6.0 Test and Validate All Parsers
  - [x] 6.1 Test PrizePicks parser with actual `nfl_projections.json` files from api_data
  - [x] 6.2 Test College Football parser with actual `players_YYYY_weekN_regular.json` files from api_data
  - [x] 6.3 Test NFL Game ID parser with actual `games_YYYY_weekN_typeT.json` files from api_data
  - [x] 6.4 Test NFL Boxscore parser with actual `boxscore_<eventid>.json` files from api_data
  - [x] 6.5 Validate that all parsers return the correct dictionary structures as specified
  - [x] 6.6 Test error handling with missing files and malformed JSON data
  - [x] 6.7 Verify that parsers can be imported and used independently
  - [x] 6.8 Create simple test scripts or manual validation for each parser function