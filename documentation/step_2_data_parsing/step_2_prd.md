# PRD: Data Parsing Module for Football Prop Insights

## Introduction/Overview

This PRD defines the implementation of data parsing functionality for the Football Prop Insights project. The parsing module will extract structured data from raw JSON responses collected by our API integration system (Step 1) and transform them into standardized Python dictionaries ready for database insertion and analysis.

The parsing module addresses the need to convert complex, nested JSON responses from multiple football data APIs (PrizePicks, NFL RapidAPI, College Football Data API) into clean, consistent data structures that can be used by downstream components like the suggestion engine and database layer.

**Goal:** Create a set of independent parsing functions that transform raw API JSON data into structured dictionaries suitable for football prop betting analysis.

## Goals

1. **Data Standardization**: Convert varied API response formats into consistent Python dictionary structures
2. **Position-Specific Extraction**: Focus on quarterback (QB) and wide receiver (WR) statistics, with limited running back (RB) receiving data
3. **Modular Design**: Create independent parsing functions that can be used separately or together
4. **Error Resilience**: Handle common JSON parsing errors and missing data gracefully
5. **Developer Readiness**: Output structured data ready for database insertion without additional transformation

## User Stories

1. **As a data analyst**, I want to parse PrizePicks projection data so that I can extract player names, betting lines, and game context in a standardized format.

2. **As a developer**, I want to parse College Football player statistics so that I can identify QB passing performance and WR receiving stats for prop betting analysis.

3. **As a system administrator**, I want to extract NFL game IDs from weekly data so that I can track which games are available for detailed analysis.

4. **As a data scientist**, I want to parse NFL boxscore data so that I can access individual player performance statistics for QB and WR positions.

5. **As a backend developer**, I want parsing functions that handle errors gracefully so that missing or malformed data doesn't crash the analysis pipeline.

## Functional Requirements

### General Requirements
1. The system must create a `parsers/` directory containing four parsing modules
2. Each parser must accept JSON data as input and return a list of Python dictionaries
3. All parsers must include basic error handling for file not found and JSON parsing errors
4. Each parser must be executable independently without dependencies on other parsers

### PrizePicks Parser (`parse_prizepicks.py`)
5. The system must parse `nfl_projections.json` files containing PrizePicks betting data
6. The parser must create lookup dictionaries from the `included[]` array for players, teams, and markets
7. The parser must extract the following fields for each projection:
   - `player_name` (from new_player reference)
   - `team` (from team reference)  
   - `opponent` (from market reference)
   - `stat_type` and `line_score` (from projection data)
   - `game_time` (from market reference)
   - `projection_id` (unique identifier)
8. The parser must return dictionaries matching the specified output format

### College Football Parser (`parse_cfb_stats.py`)
9. The system must parse `players_YYYY_weekN_regular.json` files from College Football Data API
10. The parser must filter data to include only QB, WR, and RB positions
11. For QB positions, the parser must extract: `passYards`, `completions`, `attempts`, `passTD`
12. For WR positions, the parser must extract: `receivingYards`, `receptions`, `targets`, `receivingTD`
13. For RB positions, the parser must extract only: `receivingYards`
14. The parser must include game context: `week`, `gameId`, `startTime`, `opponent`, `team`

### NFL Game ID Parser (`parse_nfl_game_ids.py`)
15. The system must parse `games_YYYY_weekN_typeT.json` files containing NFL game listings
16. The parser must extract `eventid` values from the `items[]` array
17. The parser must return a structured dictionary with `week`, `year`, and `game_ids` list

### NFL Boxscore Parser (`parse_nfl_boxscore.py`)
18. The system must parse `boxscore_<eventid>.json` files containing detailed NFL game statistics
19. The parser must iterate through the `players` data structure to find individual player stats
20. For QB positions, the parser must extract passing statistics: `yards`, `completions`, `attempts`, `touchdowns`, `interceptions`
21. For WR positions, the parser must extract receiving statistics: `yards`, `receptions`, `targets`, `touchdowns`
22. For RB positions, the parser must extract only receiving statistics: `yards`
23. Each parsed record must include: `player`, `team`, `position`, `game_id`, `stat_type`

## Non-Goals (Out of Scope)

1. **Database Integration**: Parsers will not directly insert data into databases
2. **API Data Fetching**: Parsers will not make API calls or download data
3. **Data Validation**: Complex business rule validation beyond basic type checking
4. **Performance Optimization**: Advanced caching or optimization for large datasets
5. **Non-Target Positions**: Parsing statistics for positions other than QB, WR, and RB receiving
6. **Real-time Processing**: Parsers are designed for batch processing of saved JSON files
7. **Unit Testing**: Comprehensive test suites are not included in this implementation
8. **Configuration Management**: Advanced configuration files or settings
9. **Logging Framework**: Detailed logging beyond basic error output

## Design Considerations

- **File Organization**: Each parser should be in a separate `.py` file within the `parsers/` directory
- **Function Naming**: Use descriptive function names like `parse_prizepicks_data()`, `parse_cfb_player_stats()`
- **Input Flexibility**: Functions should accept either file paths or pre-loaded JSON data
- **Output Consistency**: All parsers should return lists of dictionaries for consistent downstream processing
- **Error Messages**: Provide clear, helpful error messages that indicate the source and nature of parsing issues

## Technical Considerations

- **Dependencies**: Parsers should use only Python standard library (json, os modules)
- **JSON Structure Assumptions**: Parsers assume the JSON structures match the documented API response formats
- **Memory Usage**: Designed for processing individual game/week files, not massive datasets
- **Compatibility**: Functions should work with Python 3.7+ 
- **Integration Point**: Parsers can be imported and used by the existing `src/api_client.py` system when needed

## Success Metrics

1. **Functionality**: All four parsers successfully extract data from their respective JSON file formats
2. **Data Integrity**: Parsed dictionaries contain all required fields as specified in the requirements
3. **Error Handling**: Parsers gracefully handle missing files and malformed JSON without crashing
4. **Output Quality**: Generated dictionaries match the exact format specifications provided
5. **Modularity**: Each parser can be executed independently without requiring other components
6. **Developer Usability**: Junior developers can understand and modify the parsing logic

## Open Questions

1. **File Path Handling**: Should parsers accept relative paths, absolute paths, or both?
2. **Missing Data Strategy**: How should parsers handle optional fields that are missing from API responses?
3. **Performance Expectations**: What is the expected file size range for each JSON input type?
4. **Future Extensibility**: Should the parser design accommodate additional positions or statistics in the future?
5. **Integration Timeline**: When will these parsers need to integrate with the database layer?