"""
Football Prop Insights - Data Parsing Module

This module contains parsers for extracting structured data from various football APIs:
- PrizePicks NFL projections
- College Football player statistics  
- NFL game IDs and boxscore data

Each parser accepts JSON data and returns standardized Python dictionaries
ready for database insertion and analysis.
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
    safe_load_json,
    safe_get_nested,
    validate_required_fields,
    safe_get_list,
    print_parser_summary
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
    'safe_load_json',
    'safe_get_nested',
    'validate_required_fields',
    'safe_get_list',
    'print_parser_summary'
]

__version__ = '1.0.0'
__author__ = 'Football Prop Insights Team'