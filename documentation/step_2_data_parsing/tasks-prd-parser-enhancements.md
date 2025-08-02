## Relevant Files

- `parsers/parse_prizepicks.py` - PrizePicks parser requiring team/opponent derivation and metadata enhancements
- `parsers/parse_cfb_stats.py` - College Football player stats parser needing team/opponent fixes and metadata
- `parsers/parse_nfl_boxscore.py` - NFL boxscore parser requiring position accuracy and opponent lookup
- `parsers/common.py` - Common utilities and validation functions, may need metadata validation helpers
- `parsers/function_patterns.py` - Function patterns and decorators, may need enhanced validation patterns
- `parsers/__init__.py` - Module initialization, may need imports for new validation functions
- `parsed_data/` - Directory containing parsed output files for validation testing

### Notes

- Each parser enhancement will follow the sequential implementation approach (one parser at a time)
- Comprehensive testing with multiple data samples required for each parser before proceeding
- Breaking changes are allowed to achieve database-ready data quality standards
- All parsers must include consistent metadata fields: league, season, source, player_id

## Tasks

- [x] 1.0 Establish Cross-Parser Standards and Validation Framework
  - [x] 1.1 Create metadata validation functions in `parsers/common.py` for required fields (league, season, source, player_id)
  - [x] 1.2 Add helper functions for team/opponent derivation patterns used across multiple parsers
  - [x] 1.3 Create datetime parsing utilities for season year extraction from various date formats
  - [x] 1.4 Add enhanced error handling patterns for missing lookup data with graceful degradation
  - [x] 1.5 Create validation decorator for ensuring no "Unknown" placeholder values in final output
  - [x] 1.6 Update `parsers/function_patterns.py` with enhanced validation patterns and field requirements

- [x] 2.0 Enhance PrizePicks NFL Parser (Phase 1 Implementation)
  - [x] 2.1 Implement team derivation logic using projection.relationships.team.data.id → included[type="team"].attributes.name mapping
  - [x] 2.2 Implement opponent derivation from market data using projection.relationships.market.data.id → included[type="market"] lookup
  - [x] 2.3 Add position field extraction from projection.relationships.new_player.data.id → included[type="new_player"].attributes.position
  - [x] 2.4 Fix game_time field to use actual starts_at values instead of null from projection.attributes or market.attributes
  - [x] 2.5 Add metadata fields: league="nfl", season (from game_time year), source="PrizePicks", player_id (from new_player.data.id)
  - [x] 2.6 Add odds_type field from projection.attributes.odds_type with fallback to "standard"
  - [x] 2.7 Update field validation to ensure all required fields are populated with actual values
  - [x] 2.8 Test enhanced parser with 3+ different NFL projection data samples and validate output quality

- [ ] 3.0 Enhance PrizePicks CFB Parser (Phase 2 Implementation)
  - [ ] 3.1 Apply identical team/opponent derivation logic from NFL parser to CFB data structure
  - [ ] 3.2 Fix game_time field using projection.attributes.starts_at or market.attributes.starts_at
  - [ ] 3.3 Add position field from player attributes using same lookup pattern as NFL parser
  - [ ] 3.4 Add metadata fields: league="college", season (from game_time year), source="PrizePicks", player_id, odds_type
  - [ ] 3.5 Ensure consistent field naming and structure with NFL parser for downstream compatibility
  - [ ] 3.6 Test enhanced parser with 3+ different CFB projection data samples and validate against NFL parser patterns

- [ ] 4.0 Enhance College Football Player Stats Parser (Phase 3 Implementation)
  - [ ] 4.1 Implement team derivation from game data structure using game.teams[].team.school where player belongs
  - [ ] 4.2 Implement opponent derivation logic: if player.team.id == game.homeTeamId then opponent = game.awayTeam, else opponent = game.homeTeam
  - [ ] 4.3 Add metadata fields: league="college", season (from start_time year using datetime parsing), source="CollegeFootballData"
  - [ ] 4.4 Create player_id using hash of player name + team + game_id for unique identification
  - [ ] 4.5 Populate week and start_time fields from game data instead of null values
  - [ ] 4.6 Ensure team/opponent relationships are validated (not the same team, both have actual values)
  - [ ] 4.7 Test enhanced parser with 3+ different CFB stats data samples focusing on team/opponent accuracy

- [ ] 5.0 Enhance NFL Boxscore Parser (Phase 4 Implementation)
  - [ ] 5.1 Improve position accuracy by implementing logic to distinguish RB vs WR for receiving statistics
  - [ ] 5.2 Add opponent field by cross-referencing game_id with games data to identify opposing team
  - [ ] 5.3 Add metadata fields: league="nfl", season=2023 (or derive from game context), source="RapidAPI"
  - [ ] 5.4 Create player_id using hash of player_name + team + game_id for unique identification
  - [ ] 5.5 Implement position classification logic or lookup table for accurate RB/WR/TE distinction
  - [ ] 5.6 Validate that receiving statistics are properly attributed to correct positions
  - [ ] 5.7 Test enhanced parser with 3+ different NFL boxscore samples containing RBs and WRs with receiving stats

- [ ] 6.0 Comprehensive Testing and Data Quality Validation
  - [ ] 6.1 Execute comprehensive testing of all enhanced parsers with multiple data samples per parser
  - [ ] 6.2 Validate 0% "Unknown" values across all team, opponent, and derivable fields in all parsers
  - [ ] 6.3 Verify 100% field population for required metadata (league, season, source, player_id) across all parsers
  - [ ] 6.4 Spot-check team/opponent relationships against known correct values for accuracy validation
  - [ ] 6.5 Validate database insertion compatibility by testing parsed data structure requirements
  - [ ] 6.6 Create before/after comparison samples demonstrating data quality improvements
  - [ ] 6.7 Verify analysis-ready data format with no preprocessing required for downstream use
  - [ ] 6.8 Document any remaining open questions or edge cases discovered during testing