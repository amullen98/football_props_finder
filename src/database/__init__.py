"""
Football Props Finder - Database Module

This module provides comprehensive database functionality for storing and retrieving
football prop betting lines and player performance statistics.

## Architecture

The database module is organized into several specialized modules:

- `connection.py`: PostgreSQL connection management and pooling
- `schema.py`: Database schema creation and management
- `insert.py`: Direct insertion functions for individual records
- `batch.py`: Batch insertion operations with transaction support
- `validation.py`: Data validation and quality assurance
- `sample_data.py`: Sample data insertion and testing utilities
- `parser_integration.py`: Integration with existing data parsers

## Database Schema

The system uses 5 main tables:

1. **prop_lines**: Betting projections from PrizePicks and other sources
2. **player_stats**: Actual player performance statistics 
3. **games_processed**: Tracking processed games to prevent duplicates
4. **players**: Reference table for player metadata
5. **teams**: Reference table for team information

## Usage Examples

```python
from src.database import connection, insert, validation

# Establish database connection
conn = connection.get_connection()

# Insert prop line data
prop_data = {
    'player_id': 'abc123',
    'player_name': 'Patrick Mahomes',
    'team': 'KC',
    'position': 'QB',
    'stat_type': 'Pass Yards',
    'line_score': 285.5,
    'league': 'nfl',
    'source': 'PrizePicks',
    'season': 2023
}

# Validate and insert
if validation.validate_prop_line(prop_data):
    insert.insert_prop_line(conn, prop_data)
```

## Configuration

Default connection parameters:
- Host: localhost
- Port: 5432
- Database: football_props
- User: andrew (system user)
- Authentication: peer (no password required)

## Error Handling

All database operations include comprehensive error handling:
- Connection failures with graceful fallback
- SQL execution errors with detailed logging
- Data validation errors with specific field information
- Transaction rollback on batch operation failures

## Testing

Use the sample_data module for testing database operations:

```python
from src.database import sample_data

# Test with sample data from parsed files
sample_data.test_all_insertions()
```
"""

# Database module version
__version__ = "1.0.0"
__author__ = "Football Props Finder Team"

# Import key components for easy access
try:
    from .connection import (
        get_connection,
        get_connection_manager,
        connection_context,
        cursor_context,
        execute_query,
        check_database_connection,
        DatabaseConfig,
        ConnectionManager
    )
    from .schema import create_all_tables, drop_all_tables, verify_schema
    from .insert import (
        InsertError,
        insert_prop_line,
        insert_player_stats,
        insert_game_processed,
        insert_player,
        insert_team,
        upsert_prop_line,
        upsert_player_stats,
        upsert_game_processed,
        upsert_player,
        upsert_team
    )
    from .batch import (
        BatchInsertResult,
        batch_insert_prop_lines,
        batch_insert_player_stats,
        batch_insert_games_processed,
        batch_insert_mixed_data,
        batch_transaction
    )
    from .validation import (
        ValidationSeverity,
        ValidationResult,
        ValidationReport,
        ValidationError,
        DataValidator
    )
    from .parser_integration import (
        DataRouter,
        route_prizepicks_data,
        route_nfl_boxscore_data,
        route_cfb_stats_data,
        route_nfl_game_ids_data,
        load_and_route_parsed_file,
        load_and_route_parsed_directory
    )
    from .sample_data import (
        SampleDataLoader,
        DatabaseTester,
        test_all_insertions,
        load_sample_prizepicks_data,
        load_sample_nfl_boxscore_data
    )
    
    __all__ = [
        # Connection management
        'get_connection',
        'get_connection_manager',
        'connection_context',
        'cursor_context', 
        'execute_query',
        'check_database_connection',
        'DatabaseConfig',
        'ConnectionManager',
        # Schema management
        'create_all_tables',
        'drop_all_tables',
        'verify_schema',
        # Insertion functions
        'InsertError',
        'insert_prop_line',
        'insert_player_stats',
        'insert_game_processed',
        'insert_player',
        'insert_team',
        'upsert_prop_line',
        'upsert_player_stats',
        'upsert_game_processed',
        'upsert_player',
        'upsert_team',
        # Batch operations
        'BatchInsertResult',
        'batch_insert_prop_lines',
        'batch_insert_player_stats',
        'batch_insert_games_processed',
        'batch_insert_mixed_data',
        'batch_transaction',
        # Validation
        'ValidationSeverity',
        'ValidationResult',
        'ValidationReport',
        'ValidationError',
        'DataValidator',
        # Parser integration
        'DataRouter',
        'route_prizepicks_data',
        'route_nfl_boxscore_data',
        'route_cfb_stats_data',
        'route_nfl_game_ids_data',
        'load_and_route_parsed_file',
        'load_and_route_parsed_directory',
        # Sample data and testing
        'SampleDataLoader',
        'DatabaseTester',
        'test_all_insertions',
        'load_sample_prizepicks_data',
        'load_sample_nfl_boxscore_data'
    ]
    
except ImportError:
    # Modules not yet created - will be available after full implementation
    __all__ = []

# Package-level constants
DEFAULT_CONNECTION_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'football_props',
    'user': 'andrew'
}

SUPPORTED_LEAGUES = ['nfl', 'college']
SUPPORTED_POSITIONS = ['QB', 'WR', 'RB', 'TE']
SUPPORTED_STAT_TYPES = ['passing', 'receiving', 'rushing']
VALID_SOURCES = ['PrizePicks', 'CollegeFootballData', 'RapidAPI']