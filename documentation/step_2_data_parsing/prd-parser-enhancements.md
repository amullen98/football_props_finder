# Product Requirements Document: Parser Data Quality & Completeness Enhancements

## 1. Introduction/Overview

The current football data parsers successfully extract basic statistics from API responses, but contain data quality issues that limit their usefulness for database insertion and downstream analysis. Key problems include:

- **Missing team/opponent information** (returning "Unknown Team", "UNK", etc.)
- **Incomplete metadata fields** (league, season, source, player_id)
- **Inaccurate position classification** (RBs labeled as WRs in NFL boxscore)
- **Null values in critical fields** (game_time, opponent)

This PRD addresses these issues to ensure all parsed data is **database-ready** and **analysis-ready** with complete, accurate information.

## 2. Goals

1. **Eliminate "Unknown" placeholder values** in team, opponent, and other derivable fields
2. **Establish consistent metadata standards** across all parsers (league, season, source, player_id)
3. **Ensure accurate position classification** for all player records
4. **Achieve 100% field completeness** for specified required fields
5. **Create database-insertion ready data** with proper field mapping and validation
6. **Maintain parser independence** while applying consistent standards

## 3. User Stories

**As a data analyst**, I want accurate team and opponent information so that I can perform matchup analysis and correlate prop betting lines with team performance.

**As a database administrator**, I want consistent metadata fields (league, season, source) across all parsers so that I can properly categorize and query records.

**As a suggestion engine developer**, I want accurate player positions and complete game context so that I can generate relevant prop betting recommendations.

**As a data quality engineer**, I want all parsed records to have complete required fields so that downstream processes don't fail due to missing data.

## 4. Functional Requirements

### 4.1 Cross-Parser Standards

**4.1.1** All parsers MUST include these metadata fields in every record:
- `league`: "nfl", "college" 
- `season`: Integer year (e.g., 2023)
- `source`: Data source identifier (e.g., "PrizePicks", "CollegeFootballData", "RapidAPI")

**4.1.2** All parsers MUST derive actual values for team/opponent fields instead of placeholder values

**4.1.3** All parsers MUST include player_id field for record linking and deduplication

**4.1.4** All parsers MUST validate required fields and raise appropriate errors for missing data

### 4.2 Section A: PrizePicks NFL Parser Enhancement

**4.2.1** MUST derive `team` from included[] array using team relationship mapping:
```
projection.relationships.team.data.id → included[type="team"].attributes.name
```

**4.2.2** MUST derive `opponent` from market information in included[] array:
```
projection.relationships.market.data.id → included[type="market"].attributes.away_team or home_team
```

**4.2.3** MUST add `position` field from player information:
```
projection.relationships.new_player.data.id → included[type="new_player"].attributes.position
```

**4.2.4** MUST add `odds_type` field from projection attributes

**4.2.5** MUST add metadata fields:
- `league`: "nfl"
- `season`: Derived from game_time year
- `source`: "PrizePicks"
- `player_id`: Use projection.relationships.new_player.data.id

**4.2.6** MUST fix `game_time` field to use actual starts_at values instead of null

### 4.3 Section B: PrizePicks CFB Parser Enhancement

**4.3.1** MUST implement identical team/opponent derivation logic as NFL parser

**4.3.2** MUST fix `game_time` field using projection.attributes.starts_at or market.attributes.starts_at

**4.3.3** MUST add `position` field from player attributes

**4.3.4** MUST add metadata fields:
- `league`: "college"
- `season`: Derived from game_time year  
- `source`: "PrizePicks"
- `player_id`: Use projection.relationships.new_player.data.id
- `odds_type`: From projection.attributes.odds_type

### 4.4 Section C: College Football Player Stats Parser Enhancement

**4.4.1** MUST derive `team` from game data structure:
```
game.teams[].team.school where player belongs to that team
```

**4.4.2** MUST derive `opponent` by identifying the other team in the game:
```
If player.team.id == game.homeTeamId: opponent = game.awayTeam
Else if player.team.id == game.awayTeamId: opponent = game.homeTeam
```

**4.4.3** MUST add metadata fields:
- `league`: "college"
- `season`: Derived from start_time year using datetime parsing
- `source`: "CollegeFootballData"
- `player_id`: Hash of player name + team + game_id

**4.4.4** MUST populate `week` and `start_time` fields from game data instead of null values

### 4.5 Section D: NFL Boxscore Parser Enhancement

**4.5.1** MUST improve position accuracy by cross-referencing player names with team rosters or implementing position lookup logic

**4.5.2** MUST add `opponent` field by matching game_id with games data to identify opposing team

**4.5.3** MUST add metadata fields:
- `league`: "nfl"
- `season`: 2023 (or derive from game context)
- `source`: "RapidAPI"
- `player_id`: Hash of player_name + team + game_id

**4.5.4** MUST distinguish between RB and WR positions for receiving statistics

## 5. Non-Goals (Out of Scope)

- **Historical data correction**: Only new parsed data will have enhanced fields
- **API response modification**: Changes are parser-side only
- **Real-time position verification**: Will use available data rather than external lookups
- **Advanced player identification**: Basic hash-based player_id sufficient for now
- **Performance optimization**: Focus is on data quality, not speed

## 6. Design Considerations

### 6.1 Breaking Changes Approach
- **Allow breaking changes** to current parsed data structure for improved quality
- New fields will be added to existing records
- Field names may be standardized (e.g., consistent naming conventions)

### 6.2 Error Handling Strategy
- Graceful degradation for missing lookup data
- Clear error messages for validation failures  
- Fallback values only when derivation is impossible

### 6.3 Validation Framework
- Required field validation for each parser
- Data type validation for all fields
- Relationship validation (e.g., team/opponent are different)

## 7. Technical Considerations

### 7.1 Implementation Dependencies
- Requires `datetime` module for season year parsing
- May need additional lookup logic for position classification
- Relationship mapping logic for included[] array processing

### 7.2 Data Structure Changes
- Additional fields will increase parsed file sizes
- Field standardization may require downstream code updates
- Database schema updates needed for new metadata fields

### 7.3 Sequential Implementation
- Implement one parser section at a time for easier testing
- Validate each parser completely before moving to next
- Maintain existing parsers during enhancement process

## 8. Testing & Validation Framework

### 8.1 Validation Requirements (5B: Comprehensive testing with multiple data samples)

**8.1.1** Each parser MUST be tested with minimum 3 different data samples

**8.1.2** Validation MUST verify all enhanced fields contain actual values (no "Unknown" placeholders)

**8.1.3** Team/opponent derivation MUST be spot-checked against known correct values

**8.1.4** Metadata fields MUST be validated for proper data types and reasonable values

### 8.2 Test Cases
- **PrizePicks**: Test with both NFL and CFB projection data
- **CFB Stats**: Test with games containing multiple teams and positions  
- **NFL Boxscore**: Test with games containing RBs and WRs with receiving stats
- **Edge Cases**: Test with missing relationships, incomplete data

### 8.3 Success Validation
- Compare before/after parsed data samples
- Verify database insertion compatibility
- Validate analysis-ready data structure

## 9. Success Metrics

### 9.1 Data Completeness Metrics
- **0% "Unknown" values** in team, opponent fields across all parsers
- **100% field population** for required metadata (league, season, source, player_id)
- **100% accurate position classification** in NFL boxscore data

### 9.2 Data Quality Metrics  
- **Validated team/opponent relationships** using spot-checking
- **Consistent field naming and structure** across all parsers
- **Database insertion success rate** of 100% for enhanced records

### 9.3 Usability Metrics (6D: Improved data usability)
- **Analysis-ready data** with no preprocessing required
- **Suggestion engine compatibility** with complete player/team context
- **Query performance** improvement due to consistent metadata

## 10. Implementation Plan

### 10.1 Phased Approach (2D: Fix one parser completely before moving to next)

**Phase 1**: PrizePicks NFL Parser Enhancement
- Implement team/opponent derivation
- Add metadata fields
- Comprehensive testing and validation

**Phase 2**: PrizePicks CFB Parser Enhancement  
- Apply NFL parser patterns to CFB data
- Fix game_time derivation
- Testing and validation

**Phase 3**: College Football Player Stats Parser Enhancement
- Implement team/opponent logic for CFB API structure
- Add metadata and fix null fields
- Testing and validation

**Phase 4**: NFL Boxscore Parser Enhancement
- Improve position accuracy
- Add opponent lookup and metadata
- Final comprehensive testing

### 10.2 Success Criteria per Phase
- All validation tests pass for the enhanced parser
- Sample data review confirms accuracy improvements  
- No regression in existing functionality
- Ready for production use before moving to next phase

## 11. Open Questions

1. **Position Classification**: Should NFL boxscore parser use a static position lookup table or attempt dynamic classification?

2. **Historical Compatibility**: Do we need a migration path for existing parsed data, or is forward-only enhancement acceptable?

3. **Performance Impact**: Are there acceptable performance trade-offs for improved data quality?

4. **Field Standardization**: Should field names be standardized across parsers (e.g., "receiving_yards" vs "receivingYards")?

---

**Document Status**: Draft  
**Created**: 2024-08-02  
**Target Implementation**: Sequential by parser section  
**Priority**: High - Required for database integration and suggestion engine development