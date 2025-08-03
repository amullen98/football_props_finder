"""
Database Direct Insertion Functions

This module provides direct insertion functions for each table in the Football Props
Finder database. Each function handles individual record insertion with validation
and error handling.

Functions:
- insert_prop_line: Insert betting projection data
- insert_player_stats: Insert player performance data  
- insert_game_processed: Insert processed game tracking
- insert_player: Insert player metadata
- insert_team: Insert team metadata
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

from .connection import get_connection_manager, PSYCOPG2_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsertError(Exception):
    """Custom exception for insertion errors."""
    pass


def _validate_required_fields(data: Dict[str, Any], required_fields: list, table_name: str) -> None:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Dictionary containing record data
        required_fields: List of required field names
        table_name: Name of target table for error context
        
    Raises:
        InsertError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise InsertError(f"Missing required fields for {table_name}: {missing_fields}")


def _prepare_insert_query(table_name: str, data: Dict[str, Any]) -> tuple:
    """
    Prepare INSERT query and parameters from data dictionary.
    
    Args:
        table_name: Name of target table
        data: Dictionary containing record data
        
    Returns:
        Tuple of (query_string, parameters_tuple)
    """
    # Filter out None values and id field (auto-generated)
    filtered_data = {k: v for k, v in data.items() if v is not None and k != 'id'}
    
    if not filtered_data:
        raise InsertError(f"No valid data provided for {table_name}")
    
    columns = list(filtered_data.keys())
    placeholders = ['%s'] * len(columns)
    
    query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING id
    """
    
    parameters = tuple(filtered_data.values())
    
    return query, parameters


def insert_prop_line(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert a prop betting line record.
    
    Args:
        data: Dictionary containing prop line data with keys:
            - player_id (required): Player identifier
            - player_name (required): Player's full name
            - team (required): Team abbreviation
            - position (required): Player position (QB, WR, RB, TE)
            - stat_type (required): Type of statistic
            - league (required): League (nfl, college)
            - source (required): Data source
            - season (required): Season year
            - opponent: Opponent team
            - line_score: Betting line value
            - game_time: Game datetime
            - odds_type: Type of odds (default: standard)
            - projection_id: Original projection ID
        connection: Optional database connection to use
        
    Returns:
        ID of inserted record or None if failed
        
    Raises:
        InsertError: If required fields missing or insertion fails
    """
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'league', 'source', 'season']
    table_name = 'prop_lines'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Validate position
        valid_positions = ['QB', 'WR', 'RB', 'TE']
        if data['position'] not in valid_positions:
            raise InsertError(f"Invalid position '{data['position']}'. Must be one of: {valid_positions}")
        
        # Validate league
        valid_leagues = ['nfl', 'college']
        if data['league'] not in valid_leagues:
            raise InsertError(f"Invalid league '{data['league']}'. Must be one of: {valid_leagues}")
        
        # Add default values
        data_with_defaults = data.copy()
        if 'odds_type' not in data_with_defaults:
            data_with_defaults['odds_type'] = 'standard'
        
        # Prepare query
        query, parameters = _prepare_insert_query(table_name, data_with_defaults)
        
        # Execute insertion
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock insertion into {table_name}: {data['player_name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to insert prop line for {data.get('player_name', 'unknown')}: {e}")
        raise InsertError(f"Prop line insertion failed: {e}") from e


def insert_player_stats(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert a player statistics record.
    
    Args:
        data: Dictionary containing player stats with keys:
            - player_id (required): Player identifier
            - player_name (required): Player's full name  
            - team (required): Team abbreviation
            - position (required): Player position
            - stat_type (required): Statistic type (passing, receiving, rushing)
            - game_id (required): Game identifier
            - season (required): Season year
            - league (required): League (nfl, college)
            - source (required): Data source
            - opponent: Opponent team
            - week: Week number
            - game_date: Game date
            - passing_yards, completions, attempts, passing_touchdowns, interceptions: QB stats
            - sacks, sack_yards_lost: QB sack stats
            - receiving_yards, receptions, targets, receiving_touchdowns: WR/RB stats
            - rushing_yards, rushing_attempts, rushing_touchdowns: RB stats
        connection: Optional database connection to use
        
    Returns:
        ID of inserted record or None if failed
        
    Raises:
        InsertError: If required fields missing or insertion fails
    """
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'game_id', 'season', 'league', 'source']
    table_name = 'player_stats'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Validate stat_type
        valid_stat_types = ['passing', 'receiving', 'rushing']
        if data['stat_type'] not in valid_stat_types:
            raise InsertError(f"Invalid stat_type '{data['stat_type']}'. Must be one of: {valid_stat_types}")
        
        # Validate league
        valid_leagues = ['nfl', 'college']
        if data['league'] not in valid_leagues:
            raise InsertError(f"Invalid league '{data['league']}'. Must be one of: {valid_leagues}")
        
        # Prepare query
        query, parameters = _prepare_insert_query(table_name, data)
        
        # Execute insertion
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock insertion into {table_name}: {data['player_name']} - {data['stat_type']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to insert player stats for {data.get('player_name', 'unknown')}: {e}")
        raise InsertError(f"Player stats insertion failed: {e}") from e


def insert_game_processed(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert a processed game tracking record.
    
    Args:
        data: Dictionary containing game processing data with keys:
            - game_id (required): Unique game identifier
            - week (required): Week number
            - year (required): Season year
            - league (required): League (nfl, college)
            - source (required): Data source
            - game_type: Game type (1=preseason, 2=regular, 3=postseason)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted record or None if failed
        
    Raises:
        InsertError: If required fields missing or insertion fails
    """
    required_fields = ['game_id', 'week', 'year', 'league', 'source']
    table_name = 'games_processed'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Validate league
        valid_leagues = ['nfl', 'college']
        if data['league'] not in valid_leagues:
            raise InsertError(f"Invalid league '{data['league']}'. Must be one of: {valid_leagues}")
        
        # Add default game_type
        data_with_defaults = data.copy()
        if 'game_type' not in data_with_defaults:
            data_with_defaults['game_type'] = 2  # Regular season
        
        # Prepare query
        query, parameters = _prepare_insert_query(table_name, data_with_defaults)
        
        # Execute insertion
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock insertion into {table_name}: {data['game_id']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to insert game processed for {data.get('game_id', 'unknown')}: {e}")
        raise InsertError(f"Game processed insertion failed: {e}") from e


def insert_player(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert a player metadata record.
    
    Args:
        data: Dictionary containing player data with keys:
            - player_id (required): Unique player identifier
            - name (required): Player's full name
            - league (required): League (nfl, college)
            - source (required): Data source
            - position: Player position
            - team: Team abbreviation
            - is_active: Whether player is active (default: True)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted record or None if failed
        
    Raises:
        InsertError: If required fields missing or insertion fails
    """
    required_fields = ['player_id', 'name', 'league', 'source']
    table_name = 'players'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Validate league
        valid_leagues = ['nfl', 'college']
        if data['league'] not in valid_leagues:
            raise InsertError(f"Invalid league '{data['league']}'. Must be one of: {valid_leagues}")
        
        # Add default values
        data_with_defaults = data.copy()
        if 'is_active' not in data_with_defaults:
            data_with_defaults['is_active'] = True
        
        # Prepare query
        query, parameters = _prepare_insert_query(table_name, data_with_defaults)
        
        # Execute insertion
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock insertion into {table_name}: {data['name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to insert player for {data.get('name', 'unknown')}: {e}")
        raise InsertError(f"Player insertion failed: {e}") from e


def insert_team(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert a team metadata record.
    
    Args:
        data: Dictionary containing team data with keys:
            - name (required): Team's full name
            - abbreviation (required): Team abbreviation
            - league (required): League (nfl, college)
            - source (required): Data source
            - conference: Conference name
            - division: Division name
            - is_active: Whether team is active (default: True)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted record or None if failed
        
    Raises:
        InsertError: If required fields missing or insertion fails
    """
    required_fields = ['name', 'abbreviation', 'league', 'source']
    table_name = 'teams'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Validate league
        valid_leagues = ['nfl', 'college']
        if data['league'] not in valid_leagues:
            raise InsertError(f"Invalid league '{data['league']}'. Must be one of: {valid_leagues}")
        
        # Add default values
        data_with_defaults = data.copy()
        if 'is_active' not in data_with_defaults:
            data_with_defaults['is_active'] = True
        
        # Prepare query
        query, parameters = _prepare_insert_query(table_name, data_with_defaults)
        
        # Execute insertion
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock insertion into {table_name}: {data['name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to insert team for {data.get('name', 'unknown')}: {e}")
        raise InsertError(f"Team insertion failed: {e}") from e


# ============================================================================
# UPSERT FUNCTIONS - Handle duplicate data gracefully
# ============================================================================

def _prepare_upsert_query(table_name: str, data: Dict[str, Any], 
                         conflict_columns: list, update_columns: list = None) -> tuple:
    """
    Prepare UPSERT query using ON CONFLICT clause.
    
    Args:
        table_name: Name of target table
        data: Dictionary containing record data
        conflict_columns: Columns that determine uniqueness
        update_columns: Columns to update on conflict (defaults to all except conflict columns)
        
    Returns:
        Tuple of (query_string, parameters_tuple)
    """
    # Filter out None values and id field
    filtered_data = {k: v for k, v in data.items() if v is not None and k != 'id'}
    
    if not filtered_data:
        raise InsertError(f"No valid data provided for upsert into {table_name}")
    
    columns = list(filtered_data.keys())
    placeholders = ['%s'] * len(columns)
    
    # Determine update columns
    if update_columns is None:
        update_columns = [col for col in columns if col not in conflict_columns]
    
    # Build conflict resolution clause
    if update_columns:
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        conflict_action = f"DO UPDATE SET {update_clause}"
    else:
        conflict_action = "DO NOTHING"
    
    query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT ({', '.join(conflict_columns)}) {conflict_action}
        RETURNING id
    """
    
    parameters = tuple(filtered_data.values())
    
    return query, parameters


def upsert_prop_line(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert or update a prop betting line record.
    
    Handles duplicates based on player_id + stat_type + projection_id uniqueness.
    
    Args:
        data: Dictionary containing prop line data (same as insert_prop_line)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted/updated record or None if failed
        
    Raises:
        InsertError: If required fields missing or upsert fails
    """
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'league', 'source', 'season']
    table_name = 'prop_lines'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Add default values
        data_with_defaults = data.copy()
        if 'odds_type' not in data_with_defaults:
            data_with_defaults['odds_type'] = 'standard'
        
        # Define conflict resolution
        conflict_columns = ['player_id', 'stat_type', 'season', 'source']
        update_columns = ['player_name', 'team', 'opponent', 'position', 'line_score', 
                         'game_time', 'odds_type', 'projection_id']
        
        # Prepare upsert query
        query, parameters = _prepare_upsert_query(table_name, data_with_defaults, 
                                                 conflict_columns, update_columns)
        
        # Execute upsert
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock upsert into {table_name}: {data['player_name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to upsert prop line for {data.get('player_name', 'unknown')}: {e}")
        raise InsertError(f"Prop line upsert failed: {e}") from e


def upsert_player_stats(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert or update a player statistics record.
    
    Handles duplicates based on player_id + game_id + stat_type uniqueness.
    
    Args:
        data: Dictionary containing player stats (same as insert_player_stats)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted/updated record or None if failed
        
    Raises:
        InsertError: If required fields missing or upsert fails
    """
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'game_id', 'season', 'league', 'source']
    table_name = 'player_stats'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Define conflict resolution
        conflict_columns = ['player_id', 'game_id', 'stat_type']
        update_columns = ['player_name', 'team', 'opponent', 'position', 'week', 'game_date',
                         'passing_yards', 'completions', 'attempts', 'passing_touchdowns', 'interceptions',
                         'sacks', 'sack_yards_lost', 'receiving_yards', 'receptions', 'targets',
                         'receiving_touchdowns', 'rushing_yards', 'rushing_attempts', 'rushing_touchdowns']
        
        # Prepare upsert query
        query, parameters = _prepare_upsert_query(table_name, data, conflict_columns, update_columns)
        
        # Execute upsert
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock upsert into {table_name}: {data['player_name']} - {data['stat_type']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to upsert player stats for {data.get('player_name', 'unknown')}: {e}")
        raise InsertError(f"Player stats upsert failed: {e}") from e


def upsert_game_processed(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert or update a processed game tracking record.
    
    Handles duplicates based on game_id uniqueness.
    
    Args:
        data: Dictionary containing game processing data (same as insert_game_processed)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted/updated record or None if failed
        
    Raises:
        InsertError: If required fields missing or upsert fails
    """
    required_fields = ['game_id', 'week', 'year', 'league', 'source']
    table_name = 'games_processed'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Add default game_type
        data_with_defaults = data.copy()
        if 'game_type' not in data_with_defaults:
            data_with_defaults['game_type'] = 2  # Regular season
        
        # Define conflict resolution
        conflict_columns = ['game_id']
        update_columns = ['week', 'year', 'league', 'source', 'game_type']
        
        # Prepare upsert query
        query, parameters = _prepare_upsert_query(table_name, data_with_defaults, 
                                                 conflict_columns, update_columns)
        
        # Execute upsert
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock upsert into {table_name}: {data['game_id']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to upsert game processed for {data.get('game_id', 'unknown')}: {e}")
        raise InsertError(f"Game processed upsert failed: {e}") from e


def upsert_player(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert or update a player metadata record.
    
    Handles duplicates based on player_id uniqueness.
    
    Args:
        data: Dictionary containing player data (same as insert_player)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted/updated record or None if failed
        
    Raises:
        InsertError: If required fields missing or upsert fails
    """
    required_fields = ['player_id', 'name', 'league', 'source']
    table_name = 'players'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Add default values
        data_with_defaults = data.copy()
        if 'is_active' not in data_with_defaults:
            data_with_defaults['is_active'] = True
        
        # Define conflict resolution
        conflict_columns = ['player_id']
        update_columns = ['name', 'position', 'team', 'league', 'source', 'is_active']
        
        # Prepare upsert query
        query, parameters = _prepare_upsert_query(table_name, data_with_defaults, 
                                                 conflict_columns, update_columns)
        
        # Execute upsert
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock upsert into {table_name}: {data['name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to upsert player for {data.get('name', 'unknown')}: {e}")
        raise InsertError(f"Player upsert failed: {e}") from e


def upsert_team(data: Dict[str, Any], connection=None) -> Optional[int]:
    """
    Insert or update a team metadata record.
    
    Handles duplicates based on abbreviation + league uniqueness.
    
    Args:
        data: Dictionary containing team data (same as insert_team)
        connection: Optional database connection to use
        
    Returns:
        ID of inserted/updated record or None if failed
        
    Raises:
        InsertError: If required fields missing or upsert fails
    """
    required_fields = ['name', 'abbreviation', 'league', 'source']
    table_name = 'teams'
    
    try:
        # Validate required fields
        _validate_required_fields(data, required_fields, table_name)
        
        # Add default values
        data_with_defaults = data.copy()
        if 'is_active' not in data_with_defaults:
            data_with_defaults['is_active'] = True
        
        # Define conflict resolution
        conflict_columns = ['abbreviation', 'league']
        update_columns = ['name', 'conference', 'division', 'source', 'is_active']
        
        # Prepare upsert query
        query, parameters = _prepare_upsert_query(table_name, data_with_defaults, 
                                                 conflict_columns, update_columns)
        
        # Execute upsert
        manager = get_connection_manager()
        
        if connection:
            # Use provided connection
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        else:
            # Use connection manager
            if not PSYCOPG2_AVAILABLE:
                logger.info(f"Mock upsert into {table_name}: {data['name']}")
                return 1  # Mock ID
            
            with manager.get_cursor_context() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchone()
                return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to upsert team for {data.get('name', 'unknown')}: {e}")
        raise InsertError(f"Team upsert failed: {e}") from e


if __name__ == "__main__":
    """Test the direct insertion functions."""
    
    print("📝 Football Props Finder - Direct Insertion Functions")
    print("=" * 60)
    
    # Test data
    test_prop_line = {
        'player_id': 'test123',
        'player_name': 'Patrick Mahomes',
        'team': 'KC',
        'opponent': 'DET',
        'position': 'QB',
        'stat_type': 'Pass Yards',
        'line_score': 285.5,
        'league': 'nfl',
        'source': 'PrizePicks',
        'season': 2023,
        'projection_id': 'pp_123456'
    }
    
    test_player_stats = {
        'player_id': 'test123',
        'player_name': 'Patrick Mahomes',
        'team': 'KC',
        'opponent': 'DET', 
        'position': 'QB',
        'stat_type': 'passing',
        'passing_yards': 295,
        'completions': 24,
        'attempts': 35,
        'passing_touchdowns': 2,
        'interceptions': 0,
        'game_id': 'nfl_2023_w1_kc_det',
        'week': 1,
        'season': 2023,
        'league': 'nfl',
        'source': 'RapidAPI'
    }
    
    test_game_processed = {
        'game_id': 'nfl_2023_w1_kc_det',
        'week': 1,
        'year': 2023,
        'league': 'nfl',
        'source': 'RapidAPI',
        'game_type': 2
    }
    
    test_player = {
        'player_id': 'test123',
        'name': 'Patrick Mahomes',
        'position': 'QB',
        'team': 'KC',
        'league': 'nfl',
        'source': 'RapidAPI'
    }
    
    test_team = {
        'name': 'Kansas City Chiefs',
        'abbreviation': 'KC',
        'league': 'nfl',
        'conference': 'AFC',
        'division': 'West',
        'source': 'RapidAPI'
    }
    
    # Test insertions
    print("\n1. Testing prop line insertion...")
    try:
        prop_id = insert_prop_line(test_prop_line)
        print(f"✅ Prop line inserted with ID: {prop_id}")
    except Exception as e:
        print(f"❌ Prop line insertion failed: {e}")
    
    print("\n2. Testing player stats insertion...")
    try:
        stats_id = insert_player_stats(test_player_stats)
        print(f"✅ Player stats inserted with ID: {stats_id}")
    except Exception as e:
        print(f"❌ Player stats insertion failed: {e}")
    
    print("\n3. Testing game processed insertion...")
    try:
        game_id = insert_game_processed(test_game_processed)
        print(f"✅ Game processed inserted with ID: {game_id}")
    except Exception as e:
        print(f"❌ Game processed insertion failed: {e}")
    
    print("\n4. Testing player insertion...")
    try:
        player_id = insert_player(test_player)
        print(f"✅ Player inserted with ID: {player_id}")
    except Exception as e:
        print(f"❌ Player insertion failed: {e}")
    
    print("\n5. Testing team insertion...")
    try:
        team_id = insert_team(test_team)
        print(f"✅ Team inserted with ID: {team_id}")
    except Exception as e:
        print(f"❌ Team insertion failed: {e}")
    
    print("\n6. Testing validation...")
    try:
        # This should fail due to missing required fields
        invalid_prop = {'player_name': 'Test Player'}
        insert_prop_line(invalid_prop)
        print("❌ Validation failed - should have thrown error")
    except InsertError as e:
        print(f"✅ Validation working: {e}")
    
    print("\n7. Testing upsert functions...")
    try:
        # Test upsert - should work like insert for new records
        upsert_id = upsert_prop_line(test_prop_line)
        print(f"✅ Prop line upsert inserted with ID: {upsert_id}")
        
        # Test upsert - should update existing record (mock scenario)
        test_prop_line['line_score'] = 300.0  # Changed value
        upsert_id2 = upsert_prop_line(test_prop_line)
        print(f"✅ Prop line upsert updated with ID: {upsert_id2}")
        
        # Test other upserts
        player_upsert_id = upsert_player_stats(test_player_stats)
        print(f"✅ Player stats upsert with ID: {player_upsert_id}")
        
        game_upsert_id = upsert_game_processed(test_game_processed)
        print(f"✅ Game processed upsert with ID: {game_upsert_id}")
        
    except Exception as e:
        print(f"❌ Upsert testing failed: {e}")
    
    print("\n🎉 Direct insertion and upsert testing complete!")