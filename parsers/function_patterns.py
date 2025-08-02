"""
Function signature patterns and templates for football data parsers.

This module defines the consistent patterns that all parsers should follow
for function signatures, return types, and error handling.
"""

from typing import Any, Dict, List, Union
from .common import safe_load_json, print_parser_summary


def parser_template(data_source: Union[str, Dict, List], parser_name: str = "Generic") -> List[Dict[str, Any]]:
    """
    Template function showing the standard pattern for all parsers.
    
    Args:
        data_source: Either a file path (str) or pre-loaded JSON data (Dict/List)
        parser_name: Name of the parser for error reporting (optional)
        
    Returns:
        List[Dict[str, Any]]: List of parsed records as dictionaries
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        ParserError: For other parsing-related errors
    """
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # Step 2: Parse and extract records
        parsed_records = []
        
        # Step 3: Process each record
        # (Implementation specific to each parser)
        
        # Step 4: Print summary and return results
        print_parser_summary(parser_name, len(parsed_records), len(parsed_records))
        return parsed_records
        
    except Exception as e:
        print_parser_summary(parser_name, 0, 0, [str(e)])
        raise


# Standard function signatures for all parsers:

def parse_prizepicks_data(data_source: Union[str, Dict]) -> List[Dict[str, Any]]:
    """
    Parse PrizePicks NFL projection data.
    
    Args:
        data_source: File path to nfl_projections.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with keys: player_name, team, opponent, stat_type, 
        line_score, game_time, projection_id
    """
    pass


def parse_cfb_player_stats(data_source: Union[str, List]) -> List[Dict[str, Any]]:
    """
    Parse College Football player statistics.
    
    Args:
        data_source: File path to players_YYYY_weekN_regular.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with keys: player, team, opponent, position, week,
        game_id, start_time, and position-specific stats (passYards, receivingYards, etc.)
    """
    pass


def parse_nfl_game_ids(data_source: Union[str, Dict]) -> Dict[str, Any]:
    """
    Parse NFL game IDs from weekly game data.
    
    Args:
        data_source: File path to games_YYYY_weekN_typeT.json or pre-loaded JSON data
        
    Returns:
        Dictionary with keys: week, year, game_ids (list of event IDs)
    """
    pass


def parse_nfl_boxscore(data_source: Union[str, Dict]) -> List[Dict[str, Any]]:
    """
    Parse NFL boxscore player statistics.
    
    Args:
        data_source: File path to boxscore_<eventid>.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with keys: player, team, position, game_id, stat_type,
        and position-specific stats (yards, completions, touchdowns, etc.)
    """
    pass


# Common patterns for error handling within parsers:

def handle_parser_errors(parser_name: str):
    """
    Decorator pattern for standardizing error handling across parsers.
    
    Usage:
        @handle_parser_errors("PrizePicks")
        def parse_prizepicks_data(data_source):
            # parser implementation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print_parser_summary(parser_name, 0, 0, [str(e)])
                raise
        return wrapper
    return decorator


# Standard validation patterns:

REQUIRED_PRIZEPICKS_FIELDS = ['data', 'included']
REQUIRED_CFB_FIELDS = ['player', 'team', 'position']
REQUIRED_NFL_GAME_FIELDS = ['items']
REQUIRED_BOXSCORE_FIELDS = ['boxscore']

# Position filters
VALID_POSITIONS = ['QB', 'WR', 'RB']

# Standard field mappings
QB_STATS = ['passYards', 'completions', 'attempts', 'passTD', 'interceptions']
WR_STATS = ['receivingYards', 'receptions', 'targets', 'receivingTD']
RB_RECEIVING_STATS = ['receivingYards']