"""
PrizePicks NFL Projections Parser

This module parses PrizePicks NFL projection data from JSON files.
It handles the complex structure with data[] and included[] arrays,
creating lookup dictionaries for players, teams, and markets.
"""

from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    validate_required_fields,
    print_parser_summary,
    ParserError,
    DataStructureError
)


def parse_prizepicks_data(data_source: Union[str, Dict]) -> List[Dict[str, Any]]:
    """
    Parse PrizePicks NFL projection data.
    
    Args:
        data_source: File path to nfl_projections.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with keys: player_name, team, opponent, stat_type, 
        line_score, game_time, projection_id
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        ParserError: For other parsing-related errors
    """
    parser_name = "PrizePicks"
    parsed_records = []
    errors = []
    
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # Step 2: Validate required top-level fields
        validate_required_fields(data, ['data', 'included'], f"{parser_name} JSON structure")
        
        # Step 3: Create lookup dictionaries from included[] array
        players_lookup = {}
        teams_lookup = {}
        markets_lookup = {}
        
        included_items = safe_get_list(data, 'included', [])
        
        for item in included_items:
            item_type = item.get('type', '')
            item_id = item.get('id', '')
            
            if item_type == 'new_player' and item_id:
                attributes = item.get('attributes', {})
                players_lookup[item_id] = {
                    'name': attributes.get('name', 'Unknown Player'),
                    'display_name': attributes.get('display_name', attributes.get('name', 'Unknown Player'))
                }
            
            elif item_type == 'team' and item_id:
                attributes = item.get('attributes', {})
                teams_lookup[item_id] = {
                    'name': attributes.get('name', 'Unknown Team'),
                    'abbreviation': attributes.get('abbreviation', attributes.get('name', 'UNK'))
                }
            
            elif item_type == 'market' and item_id:
                attributes = item.get('attributes', {})
                markets_lookup[item_id] = {
                    'name': attributes.get('name', 'Unknown Market'),
                    'start_time': attributes.get('start_time', None),
                    'opponent': attributes.get('opponent', 'Unknown Opponent')
                }
        
        # Step 4: Parse data[] array to extract projection records
        projections = safe_get_list(data, 'data', [])
        
        for projection in projections:
            try:
                # Extract basic projection data
                projection_id = projection.get('id', '')
                attributes = projection.get('attributes', {})
                relationships = projection.get('relationships', {})
                
                # Extract stat type and line score
                stat_type = attributes.get('stat_type', 'unknown')
                line_score = attributes.get('line_score')
                
                # Convert line_score to float if possible
                if line_score is not None:
                    try:
                        line_score = float(line_score)
                    except (ValueError, TypeError):
                        line_score = None
                
                # Extract relationship IDs
                player_id = None
                team_id = None
                market_id = None
                
                if 'new_player' in relationships:
                    player_data = relationships['new_player'].get('data', {})
                    player_id = player_data.get('id')
                
                if 'team' in relationships:
                    team_data = relationships['team'].get('data', {})
                    team_id = team_data.get('id')
                
                if 'market' in relationships:
                    market_data = relationships['market'].get('data', {})
                    market_id = market_data.get('id')
                
                # Look up related data
                player_info = players_lookup.get(player_id, {})
                team_info = teams_lookup.get(team_id, {})
                market_info = markets_lookup.get(market_id, {})
                
                # Build the parsed record
                parsed_record = {
                    'player_name': player_info.get('display_name', player_info.get('name', 'Unknown Player')),
                    'team': team_info.get('abbreviation', 'UNK'),
                    'opponent': market_info.get('opponent', 'Unknown Opponent'),
                    'stat_type': stat_type,
                    'line_score': line_score,
                    'game_time': market_info.get('start_time'),
                    'projection_id': projection_id
                }
                
                # Only add records with valid essential data
                if (parsed_record['player_name'] != 'Unknown Player' and 
                    parsed_record['stat_type'] != 'unknown' and 
                    parsed_record['line_score'] is not None):
                    parsed_records.append(parsed_record)
                else:
                    errors.append(f"Incomplete data for projection {projection_id}")
                    
            except Exception as e:
                errors.append(f"Error parsing projection {projection.get('id', 'unknown')}: {e}")
                continue
        
        # Step 5: Print summary and return results
        print_parser_summary(parser_name, len(projections), len(parsed_records), errors if errors else None)
        return parsed_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


if __name__ == "__main__":
    """
    Test the PrizePicks parser with sample data files.
    """
    import os
    
    # Test with actual API data if available
    test_files = [
        "api_data/prizepicks/nfl_projections.json",
        "api_data/prizepicks/cfb_projections.json"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Testing with {test_file}")
            try:
                results = parse_prizepicks_data(test_file)
                print(f"📊 Successfully parsed {len(results)} projections")
                
                if results:
                    print("\n📋 Sample parsed record:")
                    sample = results[0]
                    for key, value in sample.items():
                        print(f"  {key}: {value}")
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
        else:
            print(f"⚠️ Test file not found: {test_file}")