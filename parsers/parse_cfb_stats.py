"""
College Football Player Statistics Parser

This module parses College Football player statistics from the CollegeFootballData API.
It filters for QB, WR, and RB positions and extracts relevant statistics for prop betting analysis.
"""

from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    print_parser_summary,
    ParserError,
    DataStructureError
)


def parse_cfb_player_stats(data_source: Union[str, List]) -> List[Dict[str, Any]]:
    """
    Parse College Football player statistics.
    
    Args:
        data_source: File path to players_YYYY_weekN_regular.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with keys: player, team, opponent, position, week,
        game_id, start_time, and position-specific stats (passYards, receivingYards, etc.)
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        ParserError: For other parsing-related errors
    """
    parser_name = "College Football"
    parsed_records = []
    errors = []
    
    # Valid positions we want to track
    VALID_POSITIONS = ['QB', 'WR', 'RB']
    
    # QB statistics to extract
    QB_STATS = ['passYards', 'completions', 'attempts', 'passTD']
    
    # WR statistics to extract
    WR_STATS = ['receivingYards', 'receptions', 'targets', 'receivingTD']
    
    # RB statistics to extract (receiving only)
    RB_RECEIVING_STATS = ['receivingYards']
    
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # CFB API returns a list of games
        if not isinstance(data, list):
            raise DataStructureError(f"{parser_name} data should be a list of games")
        
        total_games_processed = 0
        
        # Step 2: Process each game
        for game in data:
            try:
                total_games_processed += 1
                
                # Extract game-level information
                game_id = game.get('id')
                week = game.get('week')
                start_time = game.get('start_time')
                
                # Extract teams information
                teams = safe_get_list(game, 'teams', [])
                
                for team_data in teams:
                    try:
                        team_name = team_data.get('school', 'Unknown Team')
                        
                        # Find opponent (the other team in this game)
                        opponent = 'Unknown Opponent'
                        for other_team in teams:
                            if other_team.get('school') != team_name:
                                opponent = other_team.get('school', 'Unknown Opponent')
                                break
                        
                        # Extract player statistics
                        statistics = safe_get_list(team_data, 'statistics', [])
                        
                        for stat_category in statistics:
                            category_name = stat_category.get('name', '')
                            stat_types = safe_get_list(stat_category, 'types', [])
                            
                            # Process each stat type within the category
                            for stat_type in stat_types:
                                stat_name = stat_type.get('name', '')
                                athletes = safe_get_list(stat_type, 'athletes', [])
                                
                                # Process each athlete
                                for athlete in athletes:
                                    try:
                                        player_id = athlete.get('id')
                                        player_name = athlete.get('name', 'Unknown Player')
                                        stat_value = athlete.get('stat', '0')
                                        
                                        # Convert stat value to appropriate type
                                        try:
                                            if '/' in str(stat_value):
                                                # Handle fractional stats like "20/30"
                                                stat_value = str(stat_value)
                                            else:
                                                # Try to convert to integer/float
                                                stat_value = float(stat_value) if '.' in str(stat_value) else int(stat_value)
                                        except (ValueError, TypeError):
                                            stat_value = str(stat_value)
                                        
                                        # We need to determine the player's position
                                        # Since the CFB API doesn't always provide position directly,
                                        # we'll infer it from the stat categories they appear in
                                        position = None
                                        
                                        # Infer position from stat category and stat name
                                        if category_name == 'passing' or stat_name in ['C/ATT', 'YDS', 'AVG', 'TD', 'INT', 'QBR']:
                                            position = 'QB'
                                        elif category_name == 'receiving' or stat_name in ['REC', 'YDS', 'AVG', 'TD', 'LONG']:
                                            position = 'WR'  # Could also be RB, but we'll handle that below
                                        elif category_name == 'rushing':
                                            # For now, we'll consider rushing stats as potentially RB
                                            # but we're only interested in RB receiving stats
                                            continue
                                        
                                        # Skip if position not determined or not in our target positions
                                        if not position or position not in VALID_POSITIONS:
                                            continue
                                        
                                        # Create or find existing player record
                                        player_record = None
                                        for record in parsed_records:
                                            if (record.get('player') == player_name and 
                                                record.get('team') == team_name and 
                                                record.get('game_id') == game_id):
                                                player_record = record
                                                break
                                        
                                        # Create new record if not found
                                        if not player_record:
                                            player_record = {
                                                'player': player_name,
                                                'team': team_name,
                                                'opponent': opponent,
                                                'position': position,
                                                'week': week,
                                                'game_id': game_id,
                                                'start_time': start_time
                                            }
                                            parsed_records.append(player_record)
                                        
                                        # Map stat names to standardized field names
                                        field_mapping = {
                                            # Passing stats
                                            'YDS': 'passYards',
                                            'C/ATT': 'completions_attempts',
                                            'TD': 'passTD' if position == 'QB' else 'receivingTD',
                                            'INT': 'interceptions',
                                            
                                            # Receiving stats
                                            'REC': 'receptions',
                                            'LONG': 'receivingLong',
                                            'AVG': 'receivingAvg' if category_name == 'receiving' else 'passAvg'
                                        }
                                        
                                        # Handle special cases for stats
                                        if category_name == 'passing' and stat_name == 'YDS':
                                            player_record['passYards'] = stat_value
                                        elif category_name == 'receiving' and stat_name == 'YDS':
                                            player_record['receivingYards'] = stat_value
                                        elif category_name == 'passing' and stat_name == 'C/ATT':
                                            # Split completions/attempts
                                            if '/' in str(stat_value):
                                                parts = str(stat_value).split('/')
                                                if len(parts) == 2:
                                                    try:
                                                        player_record['completions'] = int(parts[0])
                                                        player_record['attempts'] = int(parts[1])
                                                    except ValueError:
                                                        player_record['completions_attempts'] = stat_value
                                            else:
                                                player_record['completions'] = stat_value
                                        elif stat_name in field_mapping:
                                            field_name = field_mapping[stat_name]
                                            player_record[field_name] = stat_value
                                        
                                    except Exception as e:
                                        errors.append(f"Error processing athlete {athlete.get('name', 'unknown')}: {e}")
                                        continue
                        
                    except Exception as e:
                        errors.append(f"Error processing team {team_data.get('school', 'unknown')}: {e}")
                        continue
                        
            except Exception as e:
                errors.append(f"Error processing game {game.get('id', 'unknown')}: {e}")
                continue
        
        # Step 3: Filter and clean records
        filtered_records = []
        for record in parsed_records:
            position = record.get('position')
            
            # Ensure we have the minimum required stats for each position
            if position == 'QB':
                # QB needs at least passing yards or completions
                if record.get('passYards') is not None or record.get('completions') is not None:
                    filtered_records.append(record)
            elif position == 'WR':
                # WR needs at least receiving yards or receptions
                if record.get('receivingYards') is not None or record.get('receptions') is not None:
                    filtered_records.append(record)
            elif position == 'RB':
                # RB needs receiving yards (we only track RB receiving stats)
                if record.get('receivingYards') is not None:
                    filtered_records.append(record)
        
        # Step 4: Print summary and return results
        print_parser_summary(parser_name, total_games_processed, len(filtered_records), errors if errors else None)
        return filtered_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


if __name__ == "__main__":
    """
    Test the College Football parser with sample data files.
    """
    import os
    
    # Test with actual API data if available
    test_files = [
        "api_data/cfb_stats/players_2023_week1_regular.json",
        "api_data/cfb_stats/players_2023_week2_regular.json"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Testing with {test_file}")
            try:
                results = parse_cfb_player_stats(test_file)
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
                    print("\n📋 Sample parsed records:")
                    for pos in ['QB', 'WR', 'RB']:
                        sample = next((r for r in results if r.get('position') == pos), None)
                        if sample:
                            print(f"\n  {pos} Example:")
                            for key, value in sample.items():
                                print(f"    {key}: {value}")
                            break
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
        else:
            print(f"⚠️ Test file not found: {test_file}")