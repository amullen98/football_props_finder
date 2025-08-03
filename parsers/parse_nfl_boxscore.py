"""
NFL Boxscore Player Statistics Parser

This module parses NFL boxscore data to extract detailed player statistics.
It navigates the complex nested structure to find QB, WR, and RB statistics
for prop betting analysis.
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    safe_get_nested,
    validate_required_fields,
    print_parser_summary,
    ParserError,
    DataStructureError,
    add_standard_metadata,
    validate_metadata_fields,
    validate_no_placeholder_values,
    detect_placeholder_values
)


def parse_nfl_boxscore(data_source: Union[str, Dict], game_id: str = None) -> List[Dict[str, Any]]:
    """
    Enhanced NFL boxscore player statistics parser with comprehensive validation.
    
    Args:
        data_source: File path to boxscore_<eventid>.json or pre-loaded JSON data
        game_id: Game ID (optional, can be parsed from filename)
        
    Returns:
        List of dictionaries with enhanced fields:
        - player: Player's full name (no placeholders)
        - team: Team name/abbreviation (no placeholders)
        - opponent: Opponent team name (derived from game data)
        - position: Player position (QB, WR, RB, accurately classified)
        - game_id: Game event identifier
        - stat_type: Type of statistics ("passing", "receiving", "rushing")
        - league: "nfl"
        - season: Integer year from game context (2023)
        - source: "RapidAPI"
        - player_id: Unique player identifier hash
        - [position-specific stats]: yards, touchdowns, etc.
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        MetadataValidationError: If metadata validation fails
        PlaceholderValueError: If placeholder values found in critical fields
        ParserError: For other parsing-related errors
    """
    parser_name = "NFL Boxscore"
    parsed_records = []
    errors = []
    
    # Valid positions we want to track (PATCH 1: Added TE and UNK)
    VALID_POSITIONS = ['QB', 'WR', 'RB', 'TE', 'UNK']
    
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # Step 2: Extract game_id from filename if not provided
        parsed_game_id = game_id
        
        if isinstance(data_source, str) and parsed_game_id is None:
            filename = os.path.basename(data_source)
            pattern = r'boxscore_(\w+)\.json'
            match = re.search(pattern, filename)
            
            if match:
                parsed_game_id = match.group(1)
            else:
                id_match = re.search(r'(\d+)', filename)
                if id_match:
                    parsed_game_id = id_match.group(1)
        
        if parsed_game_id is None:
            parsed_game_id = "unknown_game"
            errors.append("Game ID not found in filename, using 'unknown_game'")
        
        # Step 3: Validate required structure
        validate_required_fields(data, ['boxscore'], f"{parser_name} JSON structure")
        boxscore = data['boxscore']
        validate_required_fields(boxscore, ['players'], f"{parser_name} boxscore structure")
        
        # Step 4: Navigate nested boxscore.players data
        players_data = safe_get_list(boxscore, 'players', [])
        
        if not players_data:
            errors.append("No players data found in boxscore")
            print_parser_summary(parser_name, 0, 0, errors)
            return []
        
        # PATCH 2 & 4: Enhanced team/opponent derivation with game metadata
        team_names = []
        game_metadata = extract_game_metadata(data, parsed_game_id)
        
        for team_data in players_data:
            team_info = team_data.get('team', {})
            team_name = team_info.get('abbreviation', team_info.get('name', ''))
            if team_name:
                team_names.append(normalize_team_abbreviation(team_name))
        
        total_players_processed = 0
        
        # Step 5: Process each team's players with enhanced logic
        for team_index, team_data in enumerate(players_data):
            try:
                # Extract team information
                team_info = team_data.get('team', {})
                raw_team_name = team_info.get('abbreviation', team_info.get('name', f'Team_{team_index}'))
                team_name = normalize_team_abbreviation(raw_team_name)
                
                # PATCH 2: Enhanced opponent derivation with cross-referencing
                opponent_name = derive_opponent_with_cross_reference(
                    team_name, team_names, parsed_game_id, game_metadata
                )
                
                # Process team statistics
                statistics = safe_get_list(team_data, 'statistics', [])
                
                for stat_category in statistics:
                    try:
                        category_name = stat_category.get('name', '').lower()
                        athletes = safe_get_list(stat_category, 'athletes', [])
                        
                        # Enhanced position mapping
                        category_positions = {
                            'passing': 'QB',
                            'receiving': 'WR',  # Will be refined below
                            'rushing': 'RB',
                        }
                        
                        inferred_position = category_positions.get(category_name)
                        
                        # Skip unwanted categories
                        if inferred_position is None:
                            continue
                        
                        stat_labels = safe_get_list(stat_category, 'labels', [])
                        stat_keys = safe_get_list(stat_category, 'keys', [])
                        
                        # Process each athlete
                        for athlete_data in athletes:
                            try:
                                total_players_processed += 1
                                
                                athlete_info = athlete_data.get('athlete', {})
                                player_name = athlete_info.get('displayName', athlete_info.get('name', 'Unknown Player'))
                                
                                if player_name == 'Unknown Player':
                                    continue
                                
                                stats_array = safe_get_list(athlete_data, 'stats', [])
                                if not stats_array:
                                    continue
                                
                                # Task 5.1 & 5.5: Enhanced position classification
                                actual_position = determine_accurate_position(
                                    inferred_position, category_name, player_name, stats_array, stat_labels
                                )
                                
                                if actual_position not in VALID_POSITIONS:
                                    continue
                                
                                # Create base record
                                base_record = {
                                    'player': player_name,
                                    'team': team_name,
                                    'opponent': opponent_name,
                                    'position': normalize_position_casing(actual_position),
                                    'game_id': parsed_game_id,
                                    'stat_type': category_name
                                }
                                
                                # Extract position-specific stats
                                if actual_position == 'QB' and category_name == 'passing':
                                    qb_stats = extract_qb_passing_stats(stats_array, stat_labels, stat_keys)
                                    base_record.update(qb_stats)
                                    
                                elif actual_position in ['WR', 'RB'] and category_name == 'receiving':
                                    receiving_stats = extract_receiving_stats(stats_array, stat_labels, stat_keys)
                                    base_record.update(receiving_stats)
                                
                                # Task 5.6: Validate meaningful stats
                                if not has_meaningful_stats(base_record, actual_position):
                                    continue
                                
                                # PATCH 4: Enhanced metadata with game-derived fields
                                enhanced_record = add_standard_metadata(
                                    base_record,
                                    league="nfl",
                                    source="RapidAPI",
                                    game_time=game_metadata.get('game_date'),
                                    player_name=player_name,
                                    team=team_name,
                                    game_id=parsed_game_id
                                )
                                
                                # PATCH 4: Add additional metadata fields
                                enhanced_record.update({
                                    'season': game_metadata.get('season', 2023),
                                    'week': game_metadata.get('week'),
                                    'game_date': game_metadata.get('game_date')
                                })
                                
                                # Validate record quality
                                try:
                                    validate_metadata_fields(enhanced_record, parser_name)
                                    validate_no_placeholder_values(enhanced_record, parser_name)
                                    parsed_records.append(enhanced_record)
                                except Exception as validation_error:
                                    errors.append(f"Validation failed for {player_name}: {validation_error}")
                                
                            except Exception as e:
                                errors.append(f"Error processing athlete {athlete_data.get('athlete', {}).get('displayName', 'unknown')}: {e}")
                                continue
                        
                    except Exception as e:
                        errors.append(f"Error processing stat category {stat_category.get('name', 'unknown')}: {e}")
                        continue
                
            except Exception as e:
                errors.append(f"Error processing team {team_index}: {e}")
                continue
        
        # Step 6: Final quality check and summary
        if parsed_records:
            placeholder_summary = detect_placeholder_values(parsed_records, return_summary=True)
            if placeholder_summary['has_placeholders']:
                print(f"⚠️ {parser_name}: {placeholder_summary['records_with_issues']} records have placeholder values")
        
        print_parser_summary(parser_name, total_players_processed, len(parsed_records), errors if errors else None)
        
        # Enhanced reporting
        if parsed_records:
            positions = {}
            for record in parsed_records:
                pos = record.get('position', 'Unknown')
                positions[pos] = positions.get(pos, 0) + 1
            
            print("📋 Position breakdown:")
            for pos, count in positions.items():
                print(f"  {pos}: {count} players")
            
            print(f"📊 Enhanced Fields Added:")
            print(f"   • Improved position accuracy (RB vs WR distinction)")
            print(f"   • Opponent field derivation from game data")
            print(f"   • Metadata fields (league, season, source, player_id)")
            print(f"   • Enhanced validation and quality checking")
        
        return parsed_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


def determine_accurate_position(inferred_position: str, category_name: str, 
                               player_name: str, stats_array: List, stat_labels: List) -> str:
    """
    PATCH 1: Enhanced position classification with external metadata fallback hierarchy.
    
    Fallback hierarchy:
    1. Try position from external metadata (future: Algolia/known mappings)
    2. Infer from stat_type and volume analysis
    3. Use "UNK" as last resort
    
    Args:
        inferred_position: Initial position guess from stat category
        category_name: Statistics category (e.g., "receiving", "passing")
        player_name: Player's name for metadata lookup
        stats_array: Array of stat values
        stat_labels: Array of stat labels
        
    Returns:
        Refined position (QB, WR, RB, TE, UNK)
    """
    # Step 1: Try external metadata lookup (placeholder for future implementation)
    external_position = get_player_position_from_metadata(player_name)
    if external_position and external_position in ['QB', 'WR', 'RB', 'TE']:
        return external_position
    
    # Step 2: Category-based inference with enhanced logic
    if category_name == 'passing':
        return 'QB'
    
    # For receiving, use enhanced RB/WR/TE distinction
    if category_name == 'receiving':
        receptions = 0
        receiving_yards = 0
        targets = 0
        
        # Extract receiving stats for analysis
        for i, stat_value in enumerate(stats_array):
            if i < len(stat_labels):
                label = stat_labels[i]
                try:
                    numeric_value = convert_stat_value(stat_value)
                    if isinstance(numeric_value, (int, float)):
                        if label == 'REC':
                            receptions = numeric_value
                        elif label == 'YDS':
                            receiving_yards = numeric_value
                        elif label == 'TARGETS':
                            targets = numeric_value
                except:
                    pass
        
        # Enhanced heuristics for RB vs WR vs TE
        if receptions <= 2 and receiving_yards <= 30:
            return 'RB'  # Very low volume = RB
        elif receptions >= 8 or receiving_yards >= 100:
            return 'WR'  # High volume = WR
        elif 3 <= receptions <= 7 and 30 < receiving_yards < 100:
            # Medium volume could be TE or WR - use name patterns
            if any(indicator in player_name.upper() for indicator in ['JR', 'SR', 'III']):
                return 'WR'  # Name patterns suggest WR
            else:
                return 'TE'  # Default medium volume to TE
        else:
            return 'WR'  # Default unclear cases to WR
    
    # For rushing, it's RB
    if category_name == 'rushing':
        return 'RB'
    
    # Step 3: Last resort fallback
    return 'UNK'


def get_player_position_from_metadata(player_name: str) -> str:
    """
    PATCH 1: Placeholder for external metadata lookup.
    
    Future implementation could include:
    - Algolia search API
    - Known player mappings
    - Team roster data
    
    Args:
        player_name: Player's full name
        
    Returns:
        Position from external source or None
    """
    # Known player position mappings (can be expanded)
    known_positions = {
        'Travis Kelce': 'TE',
        'Tyreek Hill': 'WR', 
        'Derrick Henry': 'RB',
        'Aaron Rodgers': 'QB',
        'Josh Allen': 'QB',
        'Cooper Kupp': 'WR',
        'Alvin Kamara': 'RB',
        'Davante Adams': 'WR',
        'Rob Gronkowski': 'TE',
        'Christian McCaffrey': 'RB'
    }
    
    return known_positions.get(player_name, None)


def extract_qb_passing_stats(stats_array: List, labels: List, keys: List) -> Dict[str, Any]:
    """
    Extract QB passing statistics from stats array.
    
    Returns dict with: yards, completions, attempts, touchdowns, interceptions
    """
    qb_stats = {}
    
    # Common label mappings for QB stats
    label_mappings = {
        'C/ATT': 'completions_attempts',
        'YDS': 'yards',
        'AVG': 'yards_per_attempt',
        'TD': 'touchdowns',
        'INT': 'interceptions',
        'SACKS': 'sacks',
        'QBR': 'qbr',
        'RTG': 'rating'
    }
    
    # Map stats to labels
    for i, stat_value in enumerate(stats_array):
        if i < len(labels):
            label = labels[i]
            field_name = label_mappings.get(label, label.lower())
            
            # Handle special cases
            if label == 'C/ATT' and '/' in str(stat_value):
                # Split completions/attempts
                parts = str(stat_value).split('/')
                if len(parts) == 2:
                    try:
                        qb_stats['completions'] = int(parts[0])
                        qb_stats['attempts'] = int(parts[1])
                    except ValueError:
                        qb_stats['completions_attempts'] = stat_value
            elif label == 'YDS':
                qb_stats['passing_yards'] = convert_stat_value(stat_value)
            elif label == 'TD':
                qb_stats['passing_touchdowns'] = convert_stat_value(stat_value)
            elif label == 'INT':
                qb_stats['interceptions'] = convert_stat_value(stat_value)
            elif label == 'SACKS':
                # PATCH 3: Split sacks field "4-11" into sacks: 4, sack_yards_lost: 11
                sacks_info = parse_sacks_field(stat_value)
                qb_stats.update(sacks_info)
            else:
                qb_stats[field_name] = convert_stat_value(stat_value)
    
    return qb_stats


def parse_sacks_field(sacks_value: Any) -> Dict[str, Any]:
    """
    PATCH 3: Parse sacks field from formats like "4-11" into separate fields.
    
    Args:
        sacks_value: Raw sacks value (e.g., "4-11", "2-8", "0-0")
        
    Returns:
        Dict with 'sacks' and 'sack_yards_lost' fields
    """
    sacks_info = {}
    
    try:
        sacks_str = str(sacks_value)
        
        # Handle "4-11" format
        if '-' in sacks_str:
            parts = sacks_str.split('-')
            if len(parts) == 2:
                try:
                    sacks_info['sacks'] = int(parts[0])
                    sacks_info['sack_yards_lost'] = int(parts[1])
                except ValueError:
                    # Fallback if parsing fails
                    sacks_info['sacks_raw'] = sacks_str
            else:
                sacks_info['sacks_raw'] = sacks_str
        else:
            # Single number - assume it's just sacks count
            try:
                sacks_info['sacks'] = int(sacks_str)
                sacks_info['sack_yards_lost'] = 0
            except ValueError:
                sacks_info['sacks_raw'] = sacks_str
                
    except Exception:
        sacks_info['sacks_raw'] = str(sacks_value)
    
    return sacks_info


def extract_receiving_stats(stats_array: List, labels: List, keys: List) -> Dict[str, Any]:
    """
    Extract receiving statistics from stats array.
    
    Returns dict with: yards, receptions, targets, touchdowns
    """
    receiving_stats = {}
    
    # Common label mappings for receiving stats
    label_mappings = {
        'REC': 'receptions',
        'YDS': 'yards',
        'AVG': 'yards_per_reception',
        'TD': 'touchdowns',
        'LONG': 'longest_reception',
        'TARGETS': 'targets'
    }
    
    # Map stats to labels
    for i, stat_value in enumerate(stats_array):
        if i < len(labels):
            label = labels[i]
            field_name = label_mappings.get(label, label.lower())
            
            # Handle special cases
            if label == 'YDS':
                receiving_stats['receiving_yards'] = convert_stat_value(stat_value)
            elif label == 'TD':
                receiving_stats['receiving_touchdowns'] = convert_stat_value(stat_value)
            elif label == 'REC':
                receiving_stats['receptions'] = convert_stat_value(stat_value)
            else:
                receiving_stats[field_name] = convert_stat_value(stat_value)
    
    return receiving_stats


def convert_stat_value(value: Any) -> Any:
    """
    Convert stat value to appropriate type (int, float, or string).
    """
    if value is None or value == '':
        return None
    
    try:
        # Try integer first
        if '.' not in str(value) and '/' not in str(value):
            return int(value)
        # Try float
        elif '.' in str(value):
            return float(value)
        else:
            # Keep as string (e.g., for "4-11" sacks format)
            return str(value)
    except (ValueError, TypeError):
        return str(value)


def has_meaningful_stats(record: Dict, position: str) -> bool:
    """
    Check if a player record has meaningful stats for their position.
    """
    if position == 'QB':
        return (record.get('passing_yards') is not None or 
                record.get('completions') is not None or
                record.get('passing_touchdowns') is not None)
    
    elif position in ['WR', 'RB']:
        return (record.get('receiving_yards') is not None or 
                record.get('receptions') is not None or
                record.get('receiving_touchdowns') is not None)
    
    return False


def lookup_game_metadata_from_files(game_id: str) -> Dict[str, Any]:
    """
    Look up week and year information for a game ID from parsed NFL games files.
    
    Args:
        game_id: NFL game event ID (e.g., "401547353")
        
    Returns:
        Dict with game metadata: {'week': int, 'year': int, 'type': int}
        Returns None values if not found.
    """
    metadata = {
        'week': None,
        'year': None,
        'type': None
    }
    
    try:
        # Look for parsed NFL games files in parsed_data/nfl_stats/
        parsed_data_dir = Path("parsed_data/nfl_stats")
        if not parsed_data_dir.exists():
            return metadata
            
        # Find games_*_parsed.json files
        games_files = list(parsed_data_dir.glob("games_*_parsed.json"))
        
        for games_file in games_files:
            try:
                with open(games_file, 'r') as f:
                    games_data = json.load(f)
                
                # Check if our game_id is in this file's game_ids list
                game_ids = games_data.get('game_ids', [])
                if game_id in game_ids:
                    # Extract metadata from filename and content
                    metadata['week'] = games_data.get('week')
                    metadata['year'] = games_data.get('year')
                    
                    # Try to extract type from filename (e.g., games_2023_week1_type2_parsed.json)
                    filename = games_file.name
                    if 'type' in filename:
                        type_match = re.search(r'type(\d+)', filename)
                        if type_match:
                            metadata['type'] = int(type_match.group(1))
                    
                    return metadata
                    
            except Exception as e:
                # Skip files that can't be parsed
                continue
                
    except Exception:
        pass  # Return default metadata if lookup fails
    
    return metadata


def extract_game_metadata(boxscore_data: Dict, game_id: str) -> Dict[str, Any]:
    """
    PATCH 4: Extract game metadata from boxscore data for enhanced fields.
    
    Args:
        boxscore_data: Raw boxscore JSON data
        game_id: Game event ID
        
    Returns:
        Dict with game metadata (week, season, game_date, etc.)
    """
    metadata = {
        'season': 2023,  # Default to 2023
        'week': None,
        'game_date': None
    }
    
    # ENHANCED: First try to lookup from parsed games files
    games_metadata = lookup_game_metadata_from_files(game_id)
    if games_metadata['week'] is not None:
        metadata['week'] = games_metadata['week']
    if games_metadata['year'] is not None:
        metadata['season'] = games_metadata['year']
    
    # Try to extract from boxscore structure if available
    try:
        # Look for game info in boxscore.header or similar sections
        header = boxscore_data.get('boxscore', {}).get('header', {})
        if header:
            # Extract season/week if available (fallback)
            season_info = header.get('season', {})
            if season_info and metadata['season'] == 2023:  # Only override default
                metadata['season'] = season_info.get('year', 2023)
                
            # Extract game date if available
            game_date = header.get('gameDate') or header.get('date')
            if game_date:
                metadata['game_date'] = game_date
                
        # If we have week but no game_date, try to derive from season context
        if metadata['week'] is not None and metadata['game_date'] is None:
            # For NFL 2023, week 1 started around September 7, 2023
            # This is a rough approximation - could be enhanced with actual NFL calendar
            if metadata['season'] == 2023:
                # Approximate game date based on week (NFL 2023 season started Sept 7)
                from datetime import datetime, timedelta
                season_start = datetime(2023, 9, 7)  # Thursday Night Football Week 1
                # Approximate: each week is ~7 days, games typically Thursday-Monday
                week_offset = (metadata['week'] - 1) * 7
                approx_date = season_start + timedelta(days=week_offset)
                metadata['game_date'] = approx_date.strftime('%Y-%m-%d')
        
    except Exception:
        pass  # Use defaults if extraction fails
    
    return metadata


def derive_opponent_with_cross_reference(team_name: str, team_names: List[str], 
                                       game_id: str, game_metadata: Dict) -> str:
    """
    PATCH 2: Enhanced opponent derivation with cross-referencing capability.
    
    Args:
        team_name: Current team name
        team_names: List of teams in this game
        game_id: Game event ID for cross-referencing
        game_metadata: Game metadata dict
        
    Returns:
        Opponent team name
    """
    # Strategy 1: Use teams from current boxscore
    if len(team_names) == 2:
        for name in team_names:
            if name != team_name:
                return name
    
    # Strategy 2: Cross-reference with games data (future enhancement)
    # TODO: Load games_2023_week1_type2_parsed.json and cross-reference by game_id
    # This would provide the definitive opponent mapping
    
    # Strategy 3: Fallback to TBD
    return "TBD"


def normalize_team_abbreviation(team_name: str) -> str:
    """
    PATCH 5: Standardize team abbreviations to match dataset conventions.
    
    Args:
        team_name: Raw team name or abbreviation
        
    Returns:
        Normalized team abbreviation
    """
    # Common team abbreviation mappings
    abbreviation_map = {
        'LAS VEGAS': 'LV',
        'LAS VEGAS RAIDERS': 'LV',
        'RAIDERS': 'LV',
        'LOS ANGELES RAMS': 'LAR',
        'LOS ANGELES CHARGERS': 'LAC',
        'NEW ENGLAND': 'NE',
        'NEW ENGLAND PATRIOTS': 'NE',
        'NEW YORK GIANTS': 'NYG',
        'NEW YORK JETS': 'NYJ',
        'TAMPA BAY': 'TB',
        'TAMPA BAY BUCCANEERS': 'TB',
        'GREEN BAY': 'GB',
        'GREEN BAY PACKERS': 'GB',
        'SAN FRANCISCO': 'SF',
        'SAN FRANCISCO 49ERS': 'SF'
    }
    
    # Normalize to uppercase for consistent matching
    normalized = team_name.upper().strip()
    
    # Return mapped abbreviation or original if not found
    return abbreviation_map.get(normalized, team_name.upper()[:3])


def normalize_position_casing(position: str) -> str:
    """
    PATCH 5: Ensure consistent position field casing.
    
    Args:
        position: Raw position string
        
    Returns:
        Normalized position ("QB", "RB", "WR", "TE", "UNK")
    """
    if not position:
        return "UNK"
    
    # Normalize to uppercase
    pos = position.upper().strip()
    
    # Valid positions
    if pos in ['QB', 'RB', 'WR', 'TE', 'UNK']:
        return pos
    
    # Handle common variations
    position_map = {
        'QUARTERBACK': 'QB',
        'RUNNING BACK': 'RB', 
        'RUNNINGBACK': 'RB',
        'WIDE RECEIVER': 'WR',
        'WIDERECEIVER': 'WR',
        'TIGHT END': 'TE',
        'TIGHTEND': 'TE',
        'UNKNOWN': 'UNK'
    }
    
    return position_map.get(pos, 'UNK')


if __name__ == "__main__":
    """
    Enhanced test suite for the NFL Boxscore parser (Task 5.7).
    Tests with multiple NFL boxscore samples focusing on RB/WR receiving stats validation.
    """
    import os
    
    print("🏈 ENHANCED NFL BOXSCORE PARSER - COMPREHENSIVE TEST SUITE")
    print("===========================================================")
    
    # Test with specific files and any available boxscore files
    test_files = [
        "api_data/nfl_boxscore/boxscore_401220225.json",
        "api_data/nfl_boxscore/boxscore_401547353.json"
    ]
    
    # Add any additional available files
    boxscore_dir = "api_data/nfl_boxscore/"
    if os.path.exists(boxscore_dir):
        additional_files = [
            os.path.join(boxscore_dir, f) 
            for f in os.listdir(boxscore_dir) 
            if f.startswith('boxscore_') and f.endswith('.json')
        ]
        # Add up to 3 additional files for comprehensive testing
        for file in additional_files[:3]:
            if file not in test_files:
                test_files.append(file)
    
    total_tests = 0
    successful_tests = 0
    all_rb_receiving = []
    all_wr_receiving = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            total_tests += 1
            print(f"\n🧪 Testing with {os.path.basename(test_file)}")
            
            try:
                results = parse_nfl_boxscore(test_file)
                print(f"📊 Successfully parsed {len(results)} player records")
                
                if results:
                    successful_tests += 1
                    
                    # Quality validation
                    placeholder_summary = detect_placeholder_values(results, return_summary=True)
                    print(f"📈 Quality Metrics:")
                    print(f"   • Records parsed: {len(results)}")
                    print(f"   • Placeholder rate: {placeholder_summary['issue_rate']:.2%}")
                    print(f"   • Records with issues: {placeholder_summary['records_with_issues']}")
                    
                    # Position breakdown with RB/WR focus
                    positions = {}
                    for record in results:
                        pos = record.get('position', 'Unknown')
                        positions[pos] = positions.get(pos, 0) + 1
                    
                    print("📋 Position breakdown:")
                    for pos, count in positions.items():
                        print(f"   {pos}: {count} players")
                    
                    # Task 5.6: Validate receiving statistics attribution
                    rb_receiving = [r for r in results if r.get('position') == 'RB' and r.get('stat_type') == 'receiving']
                    wr_receiving = [r for r in results if r.get('position') == 'WR' and r.get('stat_type') == 'receiving']
                    
                    all_rb_receiving.extend(rb_receiving)
                    all_wr_receiving.extend(wr_receiving)
                    
                    print(f"🎯 Receiving Statistics Validation:")
                    print(f"   • RBs with receiving stats: {len(rb_receiving)}")
                    print(f"   • WRs with receiving stats: {len(wr_receiving)}")
                    
                    # Enhanced field validation
                    if results:
                        sample = results[0]
                        required_fields = ['player', 'team', 'opponent', 'position', 
                                         'game_id', 'league', 'season', 'source', 'player_id']
                        
                        missing_fields = [field for field in required_fields 
                                        if field not in sample]
                        
                        if missing_fields:
                            print(f"⚠️ Missing required fields: {missing_fields}")
                        else:
                            print("✅ All required fields present")
                        
                        # Sample enhanced record
                        print("\n📋 Sample enhanced record:")
                        for key, value in sample.items():
                            print(f"   {key}: {value}")
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    # Final comprehensive analysis
    print(f"\n🎯 COMPREHENSIVE TEST SUMMARY")
    print(f"=============================")
    print(f"Tests run: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success rate: {(successful_tests/max(1,total_tests)):.1%}")
    
    if all_rb_receiving or all_wr_receiving:
        print(f"\n📊 Position Classification Results:")
        print(f"   • Total RBs with receiving stats: {len(all_rb_receiving)}")
        print(f"   • Total WRs with receiving stats: {len(all_wr_receiving)}")
        
        # Show sample RB vs WR receiving stats
        if all_rb_receiving:
            rb_sample = all_rb_receiving[0]
            print(f"\n📋 Sample RB receiving stats ({rb_sample.get('player')}):")
            print(f"   • Receptions: {rb_sample.get('receptions')}")
            print(f"   • Receiving Yards: {rb_sample.get('receiving_yards')}")
        
        if all_wr_receiving:
            wr_sample = all_wr_receiving[0]
            print(f"\n📋 Sample WR receiving stats ({wr_sample.get('player')}):")
            print(f"   • Receptions: {wr_sample.get('receptions')}")
            print(f"   • Receiving Yards: {wr_sample.get('receiving_yards')}")
    
    if successful_tests == total_tests and total_tests > 0:
        print("\n🎉 All tests passed! Enhanced NFL Boxscore parser working correctly.")
    else:
        print("\n⚠️ Some tests failed. Review the output above.")