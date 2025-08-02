# Product Requirements Document: Step 1 - API Connectivity & Data Validation

## Introduction/Overview

Step 1 of the Football Prop Insights project focuses on establishing reliable connectivity to all external data sources. This foundational step ensures that we can successfully retrieve data from both prop betting platforms (PrizePicks, Underdog Fantasy) and player performance statistics APIs (NFL via RapidAPI, College Football Data API).

The primary goal is to validate API integration points and examine raw data structures before implementing data parsing and database storage in subsequent steps. This step serves as the critical foundation for the entire data ingestion pipeline.

## Goals

1. **Establish API Connectivity**: Successfully connect to all four external APIs with proper authentication where required
2. **Validate Data Retrieval**: Confirm that each API returns expected data structures and reasonable data volumes
3. **Error Handling Implementation**: Create robust error handling with detailed logging for debugging and monitoring
4. **Testing Framework**: Build independent test functions that can validate each API integration point
5. **Documentation**: Generate comprehensive output showing raw data structures for downstream development

## User Stories

**As a Developer:**
- I want to test each API connection independently so that I can isolate integration issues
- I want to see full sample records from each API so that I can understand the data structure for parsing
- I want detailed error messages when API calls fail so that I can quickly diagnose connection issues
- I want to validate that APIs return expected fields so that I can proceed confidently to data parsing

**As a Project Stakeholder:**
- I want confirmation that all data sources are accessible so that I know the project can proceed as planned
- I want to see sample data from each source so that I can verify data quality and completeness

## Functional Requirements

### 1. PrizePicks API Integration
1.1. **Function**: Create `fetch_prizepicks_data()` function
1.2. **Endpoint**: `https://api.prizepicks.com/projections?league_id=9&per_page=250&single_stat=true&in_game=true&state_code=FL&game_mode=pickem`
1.3. **Authentication**: No authentication required
1.4. **Response Validation**: Verify response contains expected fields (player data, stat types, projections)
1.5. **Output**: Print total record count, full sample record, and connection status

### 2. Underdog Fantasy API Integration
2.1. **Function**: Create `fetch_underdog_data()` function  
2.2. **Endpoint**: `https://api.underdogfantasy.com/beta/v6/over_under_lines`
2.3. **Authentication**: No authentication required
2.4. **Response Validation**: Verify response contains expected fields (player data, over/under lines)
2.5. **Output**: Print total record count, full sample record, and connection status

### 3. NFL Player Stats API Integration
3.1. **Function**: Create `fetch_nfl_game_ids()` function
3.2. **Endpoint**: `https://nfl-api-data.p.rapidapi.com/nfl-weeks-events?year=2023&week=1&type=2`
3.3. **Authentication**: Requires `x-rapidapi-key` and `x-rapidapi-host` headers from environment variables
3.4. **Response Validation**: Verify response contains game events and player data structures
3.5. **Output**: Print total games count, full sample game record, and connection status

### 4. College Football Data API Integration
4.1. **Function**: Create `fetch_cfb_player_data()` function
4.2. **Endpoint**: `https://api.collegefootballdata.com/games/players?year=2023&week=1&seasonType=regular`
4.3. **Authentication**: Requires `Authorization: Bearer <API_KEY>` header using `CFB_API_KEY` environment variable
4.4. **Response Validation**: Verify response contains game and player statistics
4.5. **Output**: Print total games count, full sample player stat record, and connection status

### 5. Error Handling Requirements
5.1. **HTTP Status Code Logging**: Log detailed HTTP status codes (200, 403, 404, 500, etc.)
5.2. **Response Analysis**: Analyze and log response content for debugging
5.3. **Connection Error Handling**: Handle network timeouts, DNS failures, and connection refused errors
5.4. **Authentication Error Detection**: Specifically detect and report authentication failures
5.5. **Clear Error Messages**: Provide human-readable error descriptions for common issues

### 6. Environment Configuration
6.1. **Environment Variables**: Support for `RAPIDAPI_KEY`, `RAPIDAPI_HOST`, and `CFB_API_KEY`
6.2. **Requirements File**: Create `requirements.txt` with all necessary dependencies
6.3. **Setup Documentation**: Include clear instructions for environment variable configuration
6.4. **Variable Validation**: Check for required environment variables before making API calls

### 7. Testing Framework
7.1. **Independent Execution**: Each function must be callable independently via `if __name__ == "__main__"` block
7.2. **Console Output**: All results must be visible in terminal/console logs
7.3. **Success Validation**: Clear indication of successful vs. failed API calls
7.4. **Sample Data Display**: Full sample record output for data structure analysis

## Non-Goals (Out of Scope)

- **Data Parsing**: Raw data parsing into structured formats (Step 2)
- **Database Integration**: Database schema creation or data storage (Step 3)
- **Data Transformation**: Any modification or cleaning of raw API responses
- **Rate Limiting Implementation**: Active rate limiting or request throttling (documented only)
- **VPN Integration**: VPN connectivity setup (future step)
- **Retry Logic**: Automatic retry mechanisms for failed requests
- **Data Caching**: Temporary or persistent caching of API responses
- **Multiple Parameter Testing**: Testing different years, weeks, or query parameters
- **Production Error Handling**: Advanced error handling beyond development testing

## Design Considerations

### Output Format
- **Console-First**: All output designed for terminal/console visibility
- **Structured Logging**: Consistent format for success/failure messages
- **Full Record Display**: Complete sample records printed for analysis
- **Clear Separators**: Visual separation between different API test results

### Code Organization
- **Modular Functions**: Each API gets its own dedicated function
- **Shared Utilities**: Common error handling and logging patterns
- **Environment Separation**: Clear separation of configuration from logic

## Technical Considerations

### Dependencies
- **requests**: HTTP client for API calls
- **python-dotenv**: Environment variable management
- **json**: JSON response parsing (built-in)

### Environment Variables Required
```bash
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=nfl-api-data.p.rapidapi.com
CFB_API_KEY=your_cfb_api_key_here
```

### Rate Limiting Considerations
- **PrizePicks**: No documented rate limits, but recommend 1-2 second delays between calls
- **Underdog Fantasy**: No documented rate limits, standard web scraping courtesy applies
- **RapidAPI**: Check subscription tier rate limits (typically 100-1000 requests/day)
- **College Football Data**: 200 requests per hour for free tier

### Response Structure Validation
Each function should verify the presence of key fields:
- **PrizePicks**: `projections`, `attributes`, `player_name`
- **Underdog**: `over_under_lines`, `player`, `stat_type`
- **NFL**: `events`, `competitions`, `competitors`
- **CFB**: `games`, `teams`, `statistics`

## Success Metrics

1. **API Connectivity**: 100% successful connection to all four APIs
2. **Data Validation**: All APIs return expected data structures with required fields
3. **Error Handling**: Clear, actionable error messages for all failure scenarios
4. **Documentation Quality**: Complete sample records available for downstream development
5. **Test Independence**: Each function can be executed independently without dependencies
6. **Setup Simplicity**: Environment can be configured and tested within 10 minutes

## Open Questions

1. **Sample Data Volume**: Should we limit sample record output if responses are very large (>1000 lines)?
2. **API Key Validation**: Should we implement API key validation checks before making requests?
3. **Response Timeout**: What timeout values should we use for each API (30s, 60s)?
4. **Logging Format**: Should we use Python's logging module or stick with print statements for this step?
5. **Error Recovery**: Should failed API calls be logged to a file for later analysis?

---

**Next Steps**: Upon completion of Step 1, proceed to Step 2 (Data Parsing) with validated API connections and documented response structures.