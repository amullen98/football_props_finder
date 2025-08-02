"""
NFL Boxscore Player Statistics Parser

This module parses NFL boxscore data to extract detailed player statistics.
It navigates the complex nested structure to find QB, WR, and RB statistics
for prop betting analysis.
"""

import re
import os
from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    safe_get_nested,
    validate_required_fields,
    print_parser_summary,
    ParserError,
    DataStructureError
)


def parse_nfl_boxscore(data_source: Union[str, Dict], game_id: str = None) -> List[Dict[str, Any]]:
    """
    Parse NFL boxscore player statistics.
    
    Args:
        data_source: File path to boxscore_<eventid>.json or pre-loaded JSON data
        game_id: Game ID (optional, can be parsed from filename)
        
    Returns:
        List of dictionaries with keys: player, team, position, game_id, stat_type,
        and position-specific stats (yards, completions, touchdowns, etc.)
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        ParserError: For other parsing-related errors
    """
    parser_name = "NFL Boxscore"
    parsed_records = []
    errors = []
    
    # Valid positions we want to track
    VALID_POSITIONS = ['QB', 'WR', 'RB']
    
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # Step 2: Extract game_id from filename if not provided
        parsed_game_id = game_id
        
        if isinstance(data_source, str) and parsed_game_id is None:
            # Try to parse filename: boxscore_401547353.json
            filename = os.path.basename(data_source)
            
            # Pattern: boxscore_<eventid>.json
            pattern = r'boxscore_(\w+)\.json'
            match = re.search(pattern, filename)
            
            if match:
                parsed_game_id = match.group(1)
            else:
                # Fallback: look for any numeric ID in filename
                id_match = re.search(r'(\d+)', filename)
                if id_match:
                    parsed_game_id = id_match.group(1)
        
        # Set default if still not found
        if parsed_game_id is None:
            parsed_game_id = "unknown_game"
            errors.append("Game ID not found in filename, using 'unknown_game'")
        
        # Step 3: Validate required top-level structure
        validate_required_fields(data, ['boxscore'], f"{parser_name} JSON structure")
        
        boxscore = data['boxscore']
        validate_required_fields(boxscore, ['players'], f"{parser_name} boxscore structure")
        
        # Step 4: Navigate the nested boxscore.players data structure
        players_data = safe_get_list(boxscore, 'players', [])
        
        if not players_data:
            errors.append("No players data found in boxscore")
            print_parser_summary(parser_name, 0, 0, errors)
            return []
        
        total_players_processed = 0
        
        # Step 5: Process each team's players
        for team_index, team_data in enumerate(players_data):
            try:
                # Extract team information
                team_info = team_data.get('team', {})
                team_name = team_info.get('name', team_info.get('abbreviation', f'Team_{team_index}'))
                team_abbreviation = team_info.get('abbreviation', team_name)
                
                # Process team statistics
                statistics = safe_get_list(team_data, 'statistics', [])
                
                for stat_category in statistics:
                    try:
                        category_name = stat_category.get('name', '').lower()
                        athletes = safe_get_list(stat_category, 'athletes', [])
                        
                        # Map stat category to position (with some inference)
                        category_positions = {
                            'passing': 'QB',
                            'receiving': 'WR',  # Could also be RB, but we'll check stats
                            'rushing': 'RB',
                            'defense': None,    # Skip defensive stats
                            'kicking': None,    # Skip kicking stats
                            'punting': None,    # Skip punting stats
                            'kickreturns': None,  # Skip return stats for now
                            'puntreturns': None,  # Skip return stats for now
                            'interceptions': None  # Skip defensive stats
                        }
                        
                        inferred_position = category_positions.get(category_name)
                        
                        # Skip categories we don't care about
                        if inferred_position is None:
                            continue
                        
                        # Get stat labels and keys for this category
                        stat_labels = safe_get_list(stat_category, 'labels', [])
                        stat_keys = safe_get_list(stat_category, 'keys', [])
                        
                        # Process each athlete in this category
                        for athlete_data in athletes:
                            try:
                                total_players_processed += 1
                                
                                # Extract athlete information
                                athlete_info = athlete_data.get('athlete', {})
                                player_name = athlete_info.get('displayName', athlete_info.get('name', 'Unknown Player'))
                                player_id = athlete_info.get('id')
                                
                                # Extract stats array
                                stats_array = safe_get_list(athlete_data, 'stats', [])
                                
                                if not stats_array:
                                    errors.append(f"No stats found for player {player_name}")
                                    continue
                                
                                # Determine actual position based on stats and category
                                actual_position = inferred_position
                                
                                # For receiving category, check if it's actually an RB
                                if category_name == 'receiving':
                                    # We'll assume WR unless we have other info
                                    # In a real implementation, you might cross-reference with roster data
                                    actual_position = 'WR'  # Default, could be RB
                                
                                # Skip if not in our target positions
                                if actual_position not in VALID_POSITIONS:
                                    continue
                                
                                # Create base player record
                                player_record = {
                                    'player': player_name,
                                    'team': team_abbreviation,
                                    'position': actual_position,
                                    'game_id': parsed_game_id,
                                    'stat_type': category_name
                                }
                                
                                # Extract position-specific statistics
                                if actual_position == 'QB' and category_name == 'passing':
                                    # Extract QB passing statistics
                                    qb_stats = extract_qb_passing_stats(stats_array, stat_labels, stat_keys)
                                    player_record.update(qb_stats)
                                    
                                elif actual_position in ['WR', 'RB'] and category_name == 'receiving':
                                    # Extract receiving statistics
                                    receiving_stats = extract_receiving_stats(stats_array, stat_labels, stat_keys)
                                    player_record.update(receiving_stats)
                                    
                                    # For RB, we only keep receiving stats (as per requirements)
                                    if actual_position == 'RB':
                                        # Filter to only receiving yards
                                        rb_record = {
                                            'player': player_record['player'],
                                            'team': player_record['team'],
                                            'position': 'RB',
                                            'game_id': player_record['game_id'],
                                            'stat_type': 'receiving',
                                            'receiving_yards': receiving_stats.get('receiving_yards')
                                        }
                                        player_record = rb_record
                                
                                # Only add records with meaningful stats
                                if has_meaningful_stats(player_record, actual_position):
                                    parsed_records.append(player_record)
                                
                            except Exception as e:
                                errors.append(f"Error processing athlete {athlete_data.get('athlete', {}).get('displayName', 'unknown')}: {e}")
                                continue
                        
                    except Exception as e:
                        errors.append(f"Error processing stat category {stat_category.get('name', 'unknown')}: {e}")
                        continue
                
            except Exception as e:
                errors.append(f"Error processing team {team_index}: {e}")
                continue
        
        # Step 6: Print summary and return results
        print_parser_summary(parser_name, total_players_processed, len(parsed_records), errors if errors else None)
        
        # Print position breakdown
        if parsed_records:
            positions = {}
            for record in parsed_records:
                pos = record.get('position', 'Unknown')
                positions[pos] = positions.get(pos, 0) + 1
            
            print("📋 Position breakdown:")
            for pos, count in positions.items():
                print(f"  {pos}: {count} players")
        
        return parsed_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


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
            else:
                qb_stats[field_name] = convert_stat_value(stat_value)
    
    return qb_stats


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


if __name__ == "__main__":
    """
    Test the NFL Boxscore parser with sample data files.
    """
    import os
    
    # Test with actual API data if available
    test_files = [
        "api_data/nfl_boxscore/boxscore_401220225.json",
        "api_data/nfl_boxscore/boxscore_401547353.json"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Testing with {test_file}")
            try:
                results = parse_nfl_boxscore(test_file)
                print(f"📊 Successfully parsed {len(results)} player records")
                
                # Show breakdown by position
                positions = {}
                for record in results:
                    pos = record.get('position', 'Unknown')
                    positions[pos] = positions.get(pos, 0) + 1
                
                print("📋 Position breakdown:")
                for pos, count in positions.items():
                    print(f"  {pos}: {count} players")
                
                if results:
                    print("\n📋 Sample parsed records by position:")
                    for pos in ['QB', 'WR', 'RB']:
                        samples = [r for r in results if r.get('position') == pos]
                        if samples:
                            sample = samples[0]
                            print(f"\n  {pos} Example ({sample.get('player')}):")
                            for key, value in sample.items():
                                if value is not None:
                                    print(f"    {key}: {value}")
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    # Test with any available boxscore files
    boxscore_dir = "api_data/nfl_boxscore/"
    if os.path.exists(boxscore_dir):
        boxscore_files = [f for f in os.listdir(boxscore_dir) if f.startswith('boxscore_') and f.endswith('.json')]
        if boxscore_files:
            test_file = os.path.join(boxscore_dir, boxscore_files[0])
            print(f"\n🧪 Testing with available file: {test_file}")
            try:
                results = parse_nfl_boxscore(test_file)
                print(f"📊 Found {len(results)} player records in {boxscore_files[0]}")
            except Exception as e:
                print(f"❌ Test failed: {e}")
    else:
        print(f"\n⚠️ No boxscore directory found at {boxscore_dir}")