"""
Common utilities and error handling patterns for football data parsers.

This module provides standardized error handling patterns and utility functions
that are used across all parsers in the football prop insights system.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Union, Optional


class ParserError(Exception):
    """Base exception class for parser-related errors."""
    pass


class JSONParseError(ParserError):
    """Raised when JSON parsing fails."""
    pass


class FileNotFoundError(ParserError):
    """Raised when input file cannot be found."""
    pass


class DataStructureError(ParserError):
    """Raised when expected data structure is missing or invalid."""
    pass


class MetadataValidationError(ParserError):
    """Raised when metadata fields fail validation."""
    pass


class PlaceholderValueError(ParserError):
    """Raised when placeholder values like 'Unknown' are found in final output."""
    pass


def safe_load_json(file_path_or_data: Union[str, Dict, List]) -> Any:
    """
    Safely load JSON data from file path or pre-loaded data.
    
    Args:
        file_path_or_data: Either a file path string or pre-loaded JSON data
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
    """
    # If it's already parsed data (dict or list), return as-is
    if isinstance(file_path_or_data, (dict, list)):
        return file_path_or_data
    
    # If it's a string, treat as file path
    if isinstance(file_path_or_data, str):
        if not os.path.exists(file_path_or_data):
            raise FileNotFoundError(f"Input file not found: {file_path_or_data}")
        
        try:
            with open(file_path_or_data, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Failed to parse JSON from {file_path_or_data}: {e}")
        except Exception as e:
            raise ParserError(f"Unexpected error loading {file_path_or_data}: {e}")
    
    raise ParserError(f"Invalid input type: expected str, dict, or list, got {type(file_path_or_data)}")


def safe_get_nested(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary values with error handling.
    
    Args:
        data: Dictionary to search
        keys: List of keys to traverse (e.g., ['boxscore', 'players'])
        default: Default value if key path doesn't exist
        
    Returns:
        Value at the nested key path or default value
    """
    try:
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except (TypeError, KeyError):
        return default


def validate_required_fields(data: Dict, required_fields: List[str], context: str = "") -> None:
    """
    Validate that required fields exist in data dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context string for error messages
        
    Raises:
        DataStructureError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        context_str = f" in {context}" if context else ""
        raise DataStructureError(f"Missing required fields{context_str}: {missing_fields}")


def safe_get_list(data: Dict, key: str, default: List = None) -> List:
    """
    Safely get a list value from dictionary with validation.
    
    Args:
        data: Dictionary to search
        key: Key to look for
        default: Default value if key doesn't exist or isn't a list
        
    Returns:
        List value or default
    """
    if default is None:
        default = []
    
    value = data.get(key, default)
    return value if isinstance(value, list) else default


def print_parser_summary(parser_name: str, total_records: int, success_count: int, errors: List[str] = None):
    """
    Print a standardized summary of parser results.
    
    Args:
        parser_name: Name of the parser (e.g., "PrizePicks")
        total_records: Total number of records processed
        success_count: Number of successfully parsed records
        errors: List of error messages (optional)
    """
    print(f"\n{parser_name} Parser Results:")
    print(f"  📊 Total Records Found: {total_records}")
    print(f"  ✅ Successfully Parsed: {success_count}")
    
    if total_records > 0:
        success_rate = (success_count / total_records) * 100
        print(f"  📈 Success Rate: {success_rate:.1f}%")
    
    if errors:
        print(f"  ❌ Errors: {len(errors)}")
        for error in errors[:3]:  # Show first 3 errors
            print(f"    - {error}")
        if len(errors) > 3:
            print(f"    ... and {len(errors) - 3} more errors")
    
    print()


# ============================================================================
# METADATA VALIDATION FUNCTIONS (Task 1.1)
# ============================================================================

def validate_metadata_fields(record: Dict[str, Any], parser_name: str = "Unknown") -> None:
    """
    Validate that all required metadata fields are present and correctly formatted.
    
    Args:
        record: Dictionary containing parsed record data
        parser_name: Name of parser for error context
        
    Raises:
        MetadataValidationError: If any metadata field is missing or invalid
    """
    required_metadata = ['league', 'season', 'source', 'player_id']
    
    # Check for missing fields
    missing_fields = [field for field in required_metadata if field not in record or record[field] is None]
    if missing_fields:
        raise MetadataValidationError(f"{parser_name}: Missing required metadata fields: {missing_fields}")
    
    # Validate league field
    valid_leagues = ['nfl', 'college']
    if record['league'] not in valid_leagues:
        raise MetadataValidationError(f"{parser_name}: Invalid league '{record['league']}'. Must be one of: {valid_leagues}")
    
    # Validate season field
    if not isinstance(record['season'], int) or record['season'] < 2000 or record['season'] > 2030:
        raise MetadataValidationError(f"{parser_name}: Invalid season '{record['season']}'. Must be integer between 2000-2030")
    
    # Validate source field
    valid_sources = ['PrizePicks', 'CollegeFootballData', 'RapidAPI']
    if record['source'] not in valid_sources:
        raise MetadataValidationError(f"{parser_name}: Invalid source '{record['source']}'. Must be one of: {valid_sources}")
    
    # Validate player_id field
    if not isinstance(record['player_id'], str) or len(record['player_id']) == 0:
        raise MetadataValidationError(f"{parser_name}: Invalid player_id '{record['player_id']}'. Must be non-empty string")


def validate_no_placeholder_values(record: Dict[str, Any], parser_name: str = "Unknown") -> None:
    """
    Validate that no placeholder values like 'Unknown' or 'UNK' exist in critical fields.
    
    Args:
        record: Dictionary containing parsed record data
        parser_name: Name of parser for error context
        
    Raises:
        PlaceholderValueError: If placeholder values are found
    """
    placeholder_patterns = [
        'unknown', 'unk', 'unknown team', 'unknown opponent', 
        'unknown player', 'n/a', 'na', 'null', 'none'
    ]
    
    critical_fields = ['team', 'opponent', 'player', 'player_name']
    
    for field in critical_fields:
        if field in record and record[field] is not None:
            value = str(record[field]).lower().strip()
            if value in placeholder_patterns or value == '':
                raise PlaceholderValueError(f"{parser_name}: Placeholder value '{record[field]}' found in field '{field}'")


def create_player_id(player_name: str, team: str, game_id: str = None, league: str = None) -> str:
    """
    Create a consistent player_id hash for record linking and deduplication.
    
    Args:
        player_name: Name of the player
        team: Team abbreviation or name
        game_id: Game identifier (optional)
        league: League identifier (optional)
        
    Returns:
        SHA-256 hash string for use as player_id
    """
    # Normalize inputs
    player_clean = str(player_name).strip().lower()
    team_clean = str(team).strip().lower()
    
    # Create composite key
    if game_id:
        key_parts = [player_clean, team_clean, str(game_id)]
    else:
        key_parts = [player_clean, team_clean]
    
    if league:
        key_parts.append(str(league).lower())
    
    composite_key = "_".join(key_parts)
    
    # Generate hash
    hash_object = hashlib.sha256(composite_key.encode('utf-8'))
    return hash_object.hexdigest()[:16]  # Use first 16 chars for readability


def extract_season_from_datetime(date_string: str, default_season: int = 2023) -> int:
    """
    Extract season year from various datetime string formats.
    
    Args:
        date_string: Date/time string in various formats
        default_season: Default season if parsing fails
        
    Returns:
        Integer year representing the season
    """
    if not date_string or date_string == 'null':
        return default_season
    
    try:
        # Try common formats
        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%f', 
                   '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S',
                   '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
            try:
                parsed_date = datetime.strptime(date_string.replace('Z', '').split('+')[0] if 'T' in date_string else date_string, fmt)
                return parsed_date.year
            except ValueError:
                continue
        
        # Try ISO format parsing
        if 'T' in date_string:
            date_part = date_string.split('T')[0]
            year = int(date_part.split('-')[0])
            if 2000 <= year <= 2030:
                return year
                
    except (ValueError, IndexError, AttributeError):
        pass
    
    return default_season


def add_standard_metadata(record: Dict[str, Any], league: str, source: str, 
                         game_time: str = None, player_name: str = None, 
                         team: str = None, game_id: str = None) -> Dict[str, Any]:
    """
    Add standard metadata fields to a parsed record.
    
    Args:
        record: Existing parsed record dictionary
        league: League identifier ("nfl" or "college")
        source: Data source identifier
        game_time: Game time string for season extraction (optional)
        player_name: Player name for ID generation (optional)
        team: Team name for ID generation (optional)  
        game_id: Game ID for player ID generation (optional)
        
    Returns:
        Updated record dictionary with metadata fields
    """
    # Add league
    record['league'] = league.lower()
    
    # Add source
    record['source'] = source
    
    # Add season
    if game_time:
        record['season'] = extract_season_from_datetime(game_time)
    else:
        record['season'] = 2023  # Default for current data
    
    # Add player_id
    if player_name and team:
        record['player_id'] = create_player_id(player_name, team, game_id, league)
    elif 'player_name' in record and 'team' in record:
        record['player_id'] = create_player_id(record['player_name'], record['team'], game_id, league)
    elif 'player' in record and 'team' in record:
        record['player_id'] = create_player_id(record['player'], record['team'], game_id, league)
    else:
        record['player_id'] = "missing_data_" + str(hash(str(record)))[:8]
    
    return record


# ============================================================================
# TEAM/OPPONENT DERIVATION HELPER FUNCTIONS (Task 1.2)
# ============================================================================

def find_included_item_by_type_and_id(included_data: List[Dict], item_type: str, item_id: str) -> Optional[Dict]:
    """
    Find an item in PrizePicks included[] array by type and id.
    
    Args:
        included_data: List of included items from PrizePicks API
        item_type: Type to search for (e.g., "team", "market", "new_player")
        item_id: ID to match
        
    Returns:
        Matching item dictionary or None if not found
    """
    if not included_data or not item_id:
        return None
    
    for item in included_data:
        if (item.get('type') == item_type and 
            item.get('id') == str(item_id)):
            return item
    
    return None


def derive_team_from_prizepicks(projection: Dict, included_data: List[Dict]) -> str:
    """
    Derive team name from PrizePicks projection using player data in included[] lookup.
    
    Args:
        projection: Individual projection from PrizePicks API
        included_data: Included array from PrizePicks API response
        
    Returns:
        Team abbreviation or "Unknown Team" if derivation fails
    """
    try:
        # Get player ID from projection relationships  
        player_id = safe_get_nested(projection, ['relationships', 'new_player', 'data', 'id'])
        if not player_id:
            return "Unknown Team"
        
        # Find player in included data
        player_item = find_included_item_by_type_and_id(included_data, 'new_player', player_id)
        if not player_item:
            return "Unknown Team"
        
        # Extract team abbreviation from player data
        team_abbr = safe_get_nested(player_item, ['attributes', 'team'])
        if team_abbr:
            return team_abbr
        
        # Fallback to team_name if abbreviation not available
        team_name = safe_get_nested(player_item, ['attributes', 'team_name'])
        return team_name if team_name else "Unknown Team"
        
    except Exception:
        return "Unknown Team"


def derive_opponent_from_prizepicks(projection: Dict, included_data: List[Dict]) -> str:
    """
    Derive opponent name from PrizePicks projection. 
    Note: PrizePicks data structure doesn't include market objects with opponent info.
    This function provides a placeholder implementation for now.
    
    Args:
        projection: Individual projection from PrizePicks API
        included_data: Included array from PrizePicks API response
        
    Returns:
        Opponent name or "TBD" if derivation not possible
    """
    try:
        # PrizePicks data structure doesn't include direct opponent information
        # in the relationships or included data. The opponent would need to be
        # derived from game data or external sources.
        
        # For now, return "TBD" to indicate this needs to be populated
        # from a different data source or logic
        return "TBD"
        
    except Exception:
        return "TBD"


def derive_position_from_prizepicks(projection: Dict, included_data: List[Dict]) -> str:
    """
    Derive player position from PrizePicks projection using player lookup.
    
    Args:
        projection: Individual projection from PrizePicks API
        included_data: Included array from PrizePicks API response
        
    Returns:
        Player position or "Unknown Position" if derivation fails
    """
    try:
        # Get player ID from projection relationships
        player_id = safe_get_nested(projection, ['relationships', 'new_player', 'data', 'id'])
        if not player_id:
            return "Unknown Position"
        
        # Find player in included data
        player_item = find_included_item_by_type_and_id(included_data, 'new_player', player_id)
        if not player_item:
            return "Unknown Position"
        
        # Extract position
        position = safe_get_nested(player_item, ['attributes', 'position'])
        
        return position if position else "Unknown Position"
        
    except Exception:
        return "Unknown Position"


def derive_game_time_from_prizepicks(projection: Dict, included_data: List[Dict]) -> Optional[str]:
    """
    Derive game time from PrizePicks projection, trying multiple sources.
    
    Args:
        projection: Individual projection from PrizePicks API
        included_data: Included array from PrizePicks API response
        
    Returns:
        Game time string or None if not found
    """
    try:
        # Try projection attributes first
        game_time = safe_get_nested(projection, ['attributes', 'starts_at'])
        if game_time:
            return game_time
        
        game_time = safe_get_nested(projection, ['attributes', 'start_time'])
        if game_time:
            return game_time
        
        # Try market information
        market_id = safe_get_nested(projection, ['relationships', 'market', 'data', 'id'])
        if market_id:
            market_item = find_included_item_by_type_and_id(included_data, 'market', market_id)
            if market_item:
                game_time = safe_get_nested(market_item, ['attributes', 'starts_at'])
                if game_time:
                    return game_time
                
                game_time = safe_get_nested(market_item, ['attributes', 'start_time'])
                if game_time:
                    return game_time
        
        return None
        
    except Exception:
        return None


def derive_team_and_opponent_from_cfb_game(game_data: Dict, team_name: str) -> tuple[str, str]:
    """
    Derive team and opponent from CFB game data structure.
    
    Args:
        game_data: Game data from College Football API
        team_name: Team name we're looking for
        
    Returns:
        Tuple of (team_name, opponent_name)
    """
    try:
        teams = safe_get_list(game_data, 'teams', [])
        if len(teams) < 2:
            return "Unknown Team", "Unknown Opponent"
        
        # Find our team and the opponent
        our_team = None
        opponent_team = None
        
        for team in teams:
            # CFB API uses 'team' field not 'school'
            if team.get('team') == team_name:
                our_team = team
            else:
                opponent_team = team
        
        if not our_team or not opponent_team:
            return "Unknown Team", "Unknown Opponent"
        
        our_team_name = our_team.get('team', 'Unknown Team')
        opponent_name = opponent_team.get('team', 'Unknown Opponent')
        
        return our_team_name, opponent_name
        
    except Exception:
        return "Unknown Team", "Unknown Opponent"


def find_player_team_in_cfb_game(game_data: Dict, player_id: str) -> Optional[str]:
    """
    Find which team a player belongs to in CFB game data.
    
    Args:
        game_data: Game data from College Football API
        player_id: Player ID to search for
        
    Returns:
        Team school name or None if not found
    """
    try:
        teams = safe_get_list(game_data, 'teams', [])
        
        for team in teams:
            categories = safe_get_list(team, 'categories', [])
            
            for category in categories:
                types = safe_get_list(category, 'types', [])
                
                for stat_type in types:
                    athletes = safe_get_list(stat_type, 'athletes', [])
                    
                    for athlete in athletes:
                        if athlete.get('id') == str(player_id):
                            return team.get('school')
        
        return None
        
    except Exception:
        return None


# ============================================================================
# DATETIME PARSING UTILITIES (Task 1.3)
# ============================================================================

def parse_datetime_flexible(date_string: str) -> Optional[datetime]:
    """
    Parse datetime from various string formats commonly used in football APIs.
    
    Args:
        date_string: Date/time string in various formats
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_string or date_string in ['null', 'None', '']:
        return None
    
    # Handle unexpected list input (defensive programming)
    if isinstance(date_string, list):
        if len(date_string) > 0:
            return parse_datetime_flexible(date_string[0])
        return None
    
    # Clean the input string
    clean_string = str(date_string).strip()
    
    # Common datetime formats found in football APIs
    formats_to_try = [
        # ISO formats
        '%Y-%m-%dT%H:%M:%S.%fZ',      # 2023-09-10T20:20:00.000Z
        '%Y-%m-%dT%H:%M:%SZ',         # 2023-09-10T20:20:00Z
        '%Y-%m-%dT%H:%M:%S.%f',       # 2023-09-10T20:20:00.000
        '%Y-%m-%dT%H:%M:%S',          # 2023-09-10T20:20:00
        '%Y-%m-%dT%H:%M',             # 2023-09-10T20:20
        
        # Date only formats
        '%Y-%m-%d',                   # 2023-09-10
        '%m/%d/%Y',                   # 09/10/2023
        '%m-%d-%Y',                   # 09-10-2023
        '%d/%m/%Y',                   # 10/09/2023 (European)
        '%d-%m-%Y',                   # 10-09-2023 (European)
        
        # US formats with time
        '%m/%d/%Y %H:%M:%S',          # 09/10/2023 20:20:00
        '%m/%d/%Y %I:%M:%S %p',       # 09/10/2023 8:20:00 PM
        
        # Other common formats
        '%Y%m%d',                     # 20230910
        '%B %d, %Y',                  # September 10, 2023
        '%b %d, %Y',                  # Sep 10, 2023
    ]
    
    # Try parsing with each format
    for fmt in formats_to_try:
        try:
            return datetime.strptime(clean_string, fmt)
        except ValueError:
            continue
    
    # Try handling timezone info manually
    if '+' in clean_string or 'T' in clean_string:
        try:
            # Remove timezone info and try again
            base_string = clean_string.split('+')[0].split('Z')[0]
            for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(base_string, fmt)
                except ValueError:
                    continue
        except:
            pass
    
    return None


def extract_season_year_robust(date_input: Union[str, datetime, int], default_year: int = 2023) -> int:
    """
    Robustly extract season year from various input types and formats.
    
    Args:
        date_input: Date as string, datetime object, or integer year
        default_year: Default year if extraction fails
        
    Returns:
        Integer year for the season
    """
    # Handle None or empty inputs
    if date_input is None or date_input == '' or date_input == 'null':
        return default_year
    
    # Handle unexpected list input (fix for bug)
    if isinstance(date_input, list):
        if len(date_input) > 0:
            return extract_season_year_robust(date_input[0], default_year)
        return default_year
    
    # Handle integer year input
    if isinstance(date_input, int):
        if 2000 <= date_input <= 2030:
            return date_input
        return default_year
    
    # Handle datetime object
    if isinstance(date_input, datetime):
        return date_input.year
    
    # Handle string input
    if isinstance(date_input, str):
        # Try direct year extraction for simple cases
        if date_input.isdigit() and len(date_input) == 4:
            year = int(date_input)
            if 2000 <= year <= 2030:
                return year
        
        # Parse datetime and extract year
        parsed_dt = parse_datetime_flexible(date_input)
        if parsed_dt:
            return parsed_dt.year
    
    return default_year


def get_football_season_from_date(game_date: Union[str, datetime], 
                                 league: str = "nfl") -> int:
    """
    Get the football season year based on game date and league.
    
    Football seasons span calendar years (e.g., 2023 season includes games 
    from late 2023 and early 2024). This function correctly maps dates to seasons.
    
    Args:
        game_date: Game date as string or datetime
        league: League type ("nfl" or "college") 
        
    Returns:
        Integer season year
    """
    parsed_date = None
    
    if isinstance(game_date, datetime):
        parsed_date = game_date
    elif isinstance(game_date, str):
        parsed_date = parse_datetime_flexible(game_date)
    
    if not parsed_date:
        return 2023  # Default season
    
    year = parsed_date.year
    month = parsed_date.month
    
    if league.lower() == "nfl":
        # NFL season typically runs September-February
        # Games in January-February belong to previous season
        if month <= 2:  # January, February
            return year - 1
        else:
            return year
    
    elif league.lower() in ["college", "cfb"]:
        # College season typically runs August-January
        # Games in January belong to previous season
        if month <= 1:  # January
            return year - 1
        else:
            return year
    
    # Default: use calendar year
    return year


def normalize_date_for_comparison(date_string: str) -> str:
    """
    Normalize date string to a standard format for comparison purposes.
    
    Args:
        date_string: Input date string
        
    Returns:
        Normalized date string in YYYY-MM-DD format or original if parsing fails
    """
    parsed_date = parse_datetime_flexible(date_string)
    if parsed_date:
        return parsed_date.strftime('%Y-%m-%d')
    return date_string


def is_valid_season_year(year: Any) -> bool:
    """
    Validate if a year value is reasonable for football season data.
    
    Args:
        year: Year value to validate
        
    Returns:
        True if year is valid for football data
    """
    try:
        year_int = int(year)
        return 2000 <= year_int <= 2030
    except (ValueError, TypeError):
        return False


# ============================================================================
# ENHANCED ERROR HANDLING PATTERNS (Task 1.4)
# ============================================================================

def safe_lookup_with_fallback(lookup_dict: Dict, key: Any, fallback_keys: List[Any] = None, 
                             default: Any = None, context: str = "") -> Any:
    """
    Safely lookup values with multiple fallback keys and graceful degradation.
    
    Args:
        lookup_dict: Dictionary to search
        key: Primary key to lookup
        fallback_keys: List of alternative keys to try if primary fails
        default: Default value if all lookups fail
        context: Context string for logging
        
    Returns:
        Found value or default
    """
    if not lookup_dict:
        return default
    
    # Try primary key
    if key in lookup_dict:
        return lookup_dict[key]
    
    # Try fallback keys
    if fallback_keys:
        for fallback_key in fallback_keys:
            if fallback_key in lookup_dict:
                return lookup_dict[fallback_key]
    
    # Log missing lookup for debugging (optional)
    if context:
        print(f"🔍 Lookup failed for {context}: key='{key}', fallbacks={fallback_keys}")
    
    return default


def safe_relationship_lookup(data: Dict, relationship_path: List[str], 
                           included_data: List[Dict], lookup_type: str,
                           attr_keys: List[str], fallback_value: str = "Unknown") -> str:
    """
    Safely lookup relationship data with graceful degradation for missing references.
    
    Args:
        data: Source data containing relationship references
        relationship_path: Path to relationship ID (e.g., ['relationships', 'team', 'data', 'id'])
        included_data: Array of included reference data
        lookup_type: Type to match in included data
        attr_keys: List of attribute keys to try for the final value
        fallback_value: Value to return if lookup fails
        
    Returns:
        Found attribute value or fallback_value
    """
    try:
        # Get relationship ID
        ref_id = safe_get_nested(data, relationship_path)
        if not ref_id:
            return fallback_value
        
        # Find matching item in included data
        matching_item = find_included_item_by_type_and_id(included_data, lookup_type, ref_id)
        if not matching_item:
            return fallback_value
        
        # Try to get value from attributes
        attributes = matching_item.get('attributes', {})
        for attr_key in attr_keys:
            value = attributes.get(attr_key)
            if value:
                return str(value)
        
        return fallback_value
        
    except Exception as e:
        # Log error for debugging but continue gracefully
        print(f"🔍 Relationship lookup failed: {e}")
        return fallback_value


def handle_missing_data_gracefully(record: Dict, required_fields: List[str], 
                                  optional_fields: List[str] = None) -> Dict:
    """
    Handle missing data by providing sensible defaults and warnings.
    
    Args:
        record: Record to validate and fill
        required_fields: Fields that must be present
        optional_fields: Fields that can have defaults
        
    Returns:
        Updated record with defaults for missing fields
    """
    if optional_fields is None:
        optional_fields = []
    
    updated_record = record.copy()
    
    # Default values for common fields
    default_values = {
        'team': 'Unknown Team',
        'opponent': 'Unknown Opponent', 
        'player': 'Unknown Player',
        'player_name': 'Unknown Player',
        'position': 'Unknown Position',
        'game_time': None,
        'season': 2023,
        'week': None,
        'league': 'unknown',
        'source': 'unknown'
    }
    
    # Handle required fields
    missing_required = []
    for field in required_fields:
        if field not in updated_record or updated_record[field] is None:
            if field in default_values:
                updated_record[field] = default_values[field]
                print(f"⚠️ Missing required field '{field}' filled with default: '{default_values[field]}'")
            else:
                missing_required.append(field)
    
    if missing_required:
        print(f"❌ Cannot provide defaults for required fields: {missing_required}")
    
    # Handle optional fields
    for field in optional_fields:
        if field not in updated_record or updated_record[field] is None:
            if field in default_values:
                updated_record[field] = default_values[field]
    
    return updated_record


def validate_lookup_data_quality(included_data: List[Dict], expected_types: List[str] = None) -> Dict:
    """
    Validate the quality of lookup/included data and report potential issues.
    
    Args:
        included_data: List of included items from API response
        expected_types: List of expected item types
        
    Returns:
        Dictionary with validation results and statistics
    """
    if expected_types is None:
        expected_types = ['team', 'market', 'new_player', 'player']
    
    validation_results = {
        'total_items': len(included_data) if included_data else 0,
        'items_by_type': {},
        'missing_types': [],
        'items_missing_attributes': [],
        'quality_score': 1.0
    }
    
    if not included_data:
        validation_results['quality_score'] = 0.0
        validation_results['missing_types'] = expected_types
        return validation_results
    
    # Count items by type
    for item in included_data:
        item_type = item.get('type', 'unknown')
        if item_type not in validation_results['items_by_type']:
            validation_results['items_by_type'][item_type] = 0
        validation_results['items_by_type'][item_type] += 1
        
        # Check for missing attributes
        if not item.get('attributes'):
            validation_results['items_missing_attributes'].append({
                'type': item_type,
                'id': item.get('id', 'unknown')
            })
    
    # Check for missing expected types
    found_types = set(validation_results['items_by_type'].keys())
    for expected_type in expected_types:
        if expected_type not in found_types:
            validation_results['missing_types'].append(expected_type)
    
    # Calculate quality score
    quality_factors = []
    quality_factors.append(1.0 if validation_results['total_items'] > 0 else 0.0)
    quality_factors.append(1.0 - (len(validation_results['missing_types']) / len(expected_types)))
    quality_factors.append(1.0 - (len(validation_results['items_missing_attributes']) / max(1, validation_results['total_items'])))
    
    validation_results['quality_score'] = sum(quality_factors) / len(quality_factors)
    
    return validation_results


def log_data_quality_issues(validation_results: Dict, parser_name: str = "Unknown") -> None:
    """
    Log data quality issues for debugging and monitoring.
    
    Args:
        validation_results: Results from validate_lookup_data_quality
        parser_name: Name of the parser for context
    """
    print(f"\n📊 Data Quality Report - {parser_name}")
    print(f"  Total Items: {validation_results['total_items']}")
    print(f"  Quality Score: {validation_results['quality_score']:.2f}/1.00")
    
    if validation_results['items_by_type']:
        print("  Items by Type:")
        for item_type, count in validation_results['items_by_type'].items():
            print(f"    {item_type}: {count}")
    
    if validation_results['missing_types']:
        print(f"  ⚠️ Missing Types: {validation_results['missing_types']}")
    
    if validation_results['items_missing_attributes']:
        print(f"  ⚠️ Items Missing Attributes: {len(validation_results['items_missing_attributes'])}")
        for item in validation_results['items_missing_attributes'][:3]:  # Show first 3
            print(f"    {item['type']} (ID: {item['id']})")
    
    print()


class GracefulParser:
    """
    Base class for parsers with enhanced error handling and graceful degradation.
    """
    
    def __init__(self, parser_name: str):
        self.parser_name = parser_name
        self.error_count = 0
        self.warning_count = 0
        self.errors = []
        self.warnings = []
    
    def log_error(self, message: str, context: str = "") -> None:
        """Log an error with context."""
        self.error_count += 1
        full_message = f"[{self.parser_name}] {message}"
        if context:
            full_message += f" (Context: {context})"
        self.errors.append(full_message)
        print(f"❌ {full_message}")
    
    def log_warning(self, message: str, context: str = "") -> None:
        """Log a warning with context."""
        self.warning_count += 1
        full_message = f"[{self.parser_name}] {message}"
        if context:
            full_message += f" (Context: {context})"
        self.warnings.append(full_message)
        print(f"⚠️ {full_message}")
    
    def safe_parse_with_fallback(self, parse_func, data: Any, fallback_value: Any = None):
        """
        Execute a parsing function with error handling and fallback.
        
        Args:
            parse_func: Function to execute
            data: Data to parse
            fallback_value: Value to return if parsing fails
            
        Returns:
            Parsed result or fallback_value
        """
        try:
            return parse_func(data)
        except Exception as e:
            self.log_error(f"Parse function failed: {e}", str(data)[:100])
            return fallback_value
    
    def get_summary(self) -> Dict:
        """Get summary of parsing results."""
        return {
            'parser_name': self.parser_name,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'errors': self.errors,
            'warnings': self.warnings
        }


# ============================================================================
# VALIDATION DECORATOR AND PLACEHOLDER DETECTION (Task 1.5)
# ============================================================================

def validate_no_placeholders(critical_fields: List[str] = None, 
                            allow_none_fields: List[str] = None):
    """
    Decorator to validate that parser output contains no placeholder values.
    
    Args:
        critical_fields: List of fields that cannot contain placeholder values
        allow_none_fields: List of fields that can be None (won't trigger placeholder validation)
        
    Returns:
        Decorated function that validates output
    """
    if critical_fields is None:
        critical_fields = ['team', 'opponent', 'player', 'player_name']
    
    if allow_none_fields is None:
        allow_none_fields = ['game_time', 'week', 'game_id']
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute the original function
            result = func(*args, **kwargs)
            
            # If result is a list, validate each item
            if isinstance(result, list):
                validated_result = []
                for i, item in enumerate(result):
                    if isinstance(item, dict):
                        try:
                            validate_record_no_placeholders(item, critical_fields, allow_none_fields)
                            validated_result.append(item)
                        except PlaceholderValueError as e:
                            print(f"⚠️ Record {i} excluded due to placeholder values: {e}")
                    else:
                        validated_result.append(item)
                return validated_result
            
            # If result is a single record, validate it
            elif isinstance(result, dict):
                validate_record_no_placeholders(result, critical_fields, allow_none_fields)
                return result
            
            # Return non-dict results as-is
            return result
        
        return wrapper
    return decorator


def validate_record_no_placeholders(record: Dict[str, Any], 
                                   critical_fields: List[str],
                                   allow_none_fields: List[str]) -> None:
    """
    Validate that a single record contains no placeholder values in critical fields.
    
    Args:
        record: Record to validate
        critical_fields: Fields that cannot contain placeholders
        allow_none_fields: Fields that can be None
        
    Raises:
        PlaceholderValueError: If placeholder values are found
    """
    placeholder_patterns = [
        'unknown', 'unk', 'unknown team', 'unknown opponent', 
        'unknown player', 'unknown position', 'n/a', 'na', 
        'null', 'none', 'missing', 'error', 'failed', 'invalid'
    ]
    
    for field in critical_fields:
        if field in record:
            value = record[field]
            
            # Allow None for specified fields
            if value is None and field in allow_none_fields:
                continue
            
            # Check for placeholder patterns
            if value is not None:
                value_str = str(value).lower().strip()
                if value_str in placeholder_patterns or value_str == '':
                    raise PlaceholderValueError(f"Placeholder value '{value}' found in critical field '{field}'")


def detect_placeholder_values(data: Union[Dict, List[Dict]], 
                             return_summary: bool = False) -> Union[bool, Dict]:
    """
    Detect placeholder values in parsed data.
    
    Args:
        data: Single record or list of records to check
        return_summary: If True, return detailed summary instead of boolean
        
    Returns:
        Boolean indicating if placeholders found, or summary dict if requested
    """
    placeholder_patterns = [
        'unknown', 'unk', 'unknown team', 'unknown opponent', 
        'unknown player', 'unknown position', 'n/a', 'na', 
        'null', 'none', 'missing', 'error', 'failed', 'invalid'
    ]
    
    critical_fields = ['team', 'opponent', 'player', 'player_name', 'position']
    
    issues = []
    total_records = 0
    records_with_issues = 0
    
    # Normalize input to list
    records = data if isinstance(data, list) else [data]
    
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            continue
            
        total_records += 1
        record_issues = []
        
        for field in critical_fields:
            if field in record and record[field] is not None:
                value_str = str(record[field]).lower().strip()
                if value_str in placeholder_patterns or value_str == '':
                    record_issues.append({
                        'field': field,
                        'value': record[field],
                        'record_index': i
                    })
        
        if record_issues:
            records_with_issues += 1
            issues.extend(record_issues)
    
    if return_summary:
        return {
            'has_placeholders': len(issues) > 0,
            'total_records': total_records,
            'records_with_issues': records_with_issues,
            'total_issues': len(issues),
            'issues': issues,
            'issue_rate': records_with_issues / max(1, total_records)
        }
    
    return len(issues) > 0


def clean_placeholder_values(record: Dict[str, Any], 
                           field_replacements: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Clean placeholder values from a record by replacing them with better alternatives.
    
    Args:
        record: Record to clean
        field_replacements: Custom replacement values for specific fields
        
    Returns:
        Cleaned record with placeholder values replaced
    """
    if field_replacements is None:
        field_replacements = {}
    
    placeholder_patterns = [
        'unknown', 'unk', 'unknown team', 'unknown opponent', 
        'unknown player', 'unknown position', 'n/a', 'na', 
        'null', 'none', 'missing', 'error', 'failed', 'invalid'
    ]
    
    default_replacements = {
        'team': 'TBD',
        'opponent': 'TBD', 
        'player': 'TBD',
        'player_name': 'TBD',
        'position': 'TBD'
    }
    
    cleaned_record = record.copy()
    
    for field, value in cleaned_record.items():
        if value is not None:
            value_str = str(value).lower().strip()
            if value_str in placeholder_patterns or value_str == '':
                # Use custom replacement if available
                if field in field_replacements:
                    cleaned_record[field] = field_replacements[field]
                # Use default replacement if available
                elif field in default_replacements:
                    cleaned_record[field] = default_replacements[field]
                # Otherwise set to None
                else:
                    cleaned_record[field] = None
    
    return cleaned_record


def require_valid_data(required_fields: List[str] = None):
    """
    Decorator to ensure parser output meets minimum data quality requirements.
    
    Args:
        required_fields: List of fields that must be present and non-placeholder
        
    Returns:
        Decorated function that validates minimum data requirements
    """
    if required_fields is None:
        required_fields = ['team', 'player']
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute the original function
            result = func(*args, **kwargs)
            
            # If result is a list, filter valid items
            if isinstance(result, list):
                valid_result = []
                for i, item in enumerate(result):
                    if isinstance(item, dict):
                        if meets_minimum_requirements(item, required_fields):
                            valid_result.append(item)
                        else:
                            print(f"⚠️ Record {i} excluded due to insufficient data quality")
                    else:
                        valid_result.append(item)
                return valid_result
            
            # If result is a single record, validate it
            elif isinstance(result, dict):
                if not meets_minimum_requirements(result, required_fields):
                    raise DataStructureError(f"Record does not meet minimum requirements: {required_fields}")
                return result
            
            # Return non-dict results as-is
            return result
        
        return wrapper
    return decorator


def meets_minimum_requirements(record: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Check if a record meets minimum data quality requirements.
    
    Args:
        record: Record to validate
        required_fields: Fields that must be present and valid
        
    Returns:
        True if record meets requirements
    """
    placeholder_patterns = [
        'unknown', 'unk', 'unknown team', 'unknown opponent', 
        'unknown player', 'unknown position', 'n/a', 'na', 
        'null', 'none', 'missing', 'error', 'failed', 'invalid', 'tbd'
    ]
    
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
        
        value_str = str(record[field]).lower().strip()
        if value_str in placeholder_patterns or value_str == '':
            return False
    
    return True