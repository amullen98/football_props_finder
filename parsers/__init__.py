"""
Football Prop Insights - Data Parsing Module

This module contains parsers for extracting structured data from various football APIs:
- PrizePicks NFL projections
- College Football player statistics  
- NFL game IDs and boxscore data

Each parser accepts JSON data and returns standardized Python dictionaries
ready for database insertion and analysis.

## Testing

Use `test_all_parsers.py` for comprehensive manual validation:
    python3 parsers/test_all_parsers.py

Or run individual parser test scripts in each module.
"""

from .parse_prizepicks import parse_prizepicks_data
from .parse_cfb_stats import parse_cfb_player_stats
from .parse_nfl_game_ids import parse_nfl_game_ids
from .parse_nfl_boxscore import parse_nfl_boxscore
from .common import (
    ParserError,
    JSONParseError,
    FileNotFoundError,
    DataStructureError,
    MetadataValidationError,
    PlaceholderValueError,
    safe_load_json,
    safe_get_nested,
    validate_required_fields,
    safe_get_list,
    print_parser_summary,
    validate_metadata_fields,
    validate_no_placeholder_values,
    create_player_id,
    extract_season_from_datetime,
    add_standard_metadata,
    derive_team_from_prizepicks,
    derive_opponent_from_prizepicks,
    derive_position_from_prizepicks,
    derive_game_time_from_prizepicks,
    validate_no_placeholders,
    require_valid_data,
    detect_placeholder_values,
    GracefulParser
)

__all__ = [
    'parse_prizepicks_data',
    'parse_cfb_player_stats', 
    'parse_nfl_game_ids',
    'parse_nfl_boxscore',
    'ParserError',
    'JSONParseError',
    'FileNotFoundError', 
    'DataStructureError',
    'MetadataValidationError',
    'PlaceholderValueError',
    'safe_load_json',
    'safe_get_nested',
    'validate_required_fields',
    'safe_get_list',
    'print_parser_summary',
    'validate_metadata_fields',
    'validate_no_placeholder_values',
    'create_player_id',
    'extract_season_from_datetime',
    'add_standard_metadata',
    'derive_team_from_prizepicks',
    'derive_opponent_from_prizepicks',
    'derive_position_from_prizepicks',
    'derive_game_time_from_prizepicks',
    'validate_no_placeholders',
    'require_valid_data',
    'detect_placeholder_values',
    'GracefulParser'
]

__version__ = '1.0.0'
__author__ = 'Football Prop Insights Team'