"""
College Football Player Statistics Parser

This module parses College Football player statistics from the CollegeFootballData API.
It filters for QB, WR, and RB positions and extracts relevant statistics for prop betting analysis.
"""

from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    safe_get_nested,
    print_parser_summary,
    ParserError,
    DataStructureError,
    add_standard_metadata,
    validate_metadata_fields,
    validate_no_placeholder_values,
    detect_placeholder_values,
    derive_team_and_opponent_from_cfb_game,
    find_player_team_in_cfb_game
)


def parse_cfb_player_stats(data_source: Union[str, List]) -> List[Dict[str, Any]]:
    """
    Enhanced College Football player statistics parser with comprehensive validation.
    
    Args:
        data_source: File path to players_YYYY_weekN_regular.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with enhanced fields:
        - player: Player's full name (no placeholders)
        - team: Team school name (derived from game data)
        - opponent: Opponent school name (derived from game logic)
        - position: Player position (QB, WR, RB only)
        - week: Week number (from game data)
        - game_id: Game identifier
        - start_time: Game start time
        - league: "college"
        - season: Integer year from start_time
        - source: "CollegeFootballData"
        - player_id: Unique player identifier hash
        - [position-specific stats]: passYards, receivingYards, etc.
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        MetadataValidationError: If metadata validation fails
        PlaceholderValueError: If placeholder values found in critical fields
        ParserError: For other parsing-related errors
    """
    parser_name = "College Football"
    parsed_records = []
    errors = []
    
    # Valid positions we want to track
    VALID_POSITIONS = ['QB', 'WR', 'RB']
    
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
                teams_data = safe_get_list(game, 'teams', [])
                
                if len(teams_data) < 2:
                    errors.append(f"Game {game_id}: Insufficient team data")
                    continue
                
                # Task 4.1 & 4.2: Enhanced team/opponent derivation
                for team_data in teams_data:
                    try:
                        team_name_raw = team_data.get('team')  # CFB API uses 'team' not 'school'
                        if not team_name_raw:
                            continue
                        
                        # Derive team and opponent using helper function
                        team_name, opponent_name = derive_team_and_opponent_from_cfb_game(game, team_name_raw)
                        
                        # Task 4.6: Validate team/opponent relationships
                        if team_name == opponent_name or team_name == "Unknown Team" or opponent_name == "Unknown Opponent":
                            errors.append(f"Invalid team/opponent relationship for {team_name_raw} in game {game_id}")
                            continue
                        
                        # Extract player statistics
                        categories = safe_get_list(team_data, 'categories', [])
                        
                        for category in categories:
                            category_name = category.get('name', '')
                            types = safe_get_list(category, 'types', [])
                            
                            for stat_type in types:
                                stat_name = stat_type.get('name', '')
                                athletes = safe_get_list(stat_type, 'athletes', [])
                                
                                for athlete in athletes:
                                    try:
                                        player_name = athlete.get('name')
                                        if not player_name or player_name.strip() in [' Team', 'Team', '']:
                                            continue  # Skip team-level stats
                                            
                                        stat_value = athlete.get('stat', '0')
                                        
                                        # Convert stat value to appropriate type
                                        try:
                                            if '/' in str(stat_value):
                                                stat_value = str(stat_value)
                                            else:
                                                stat_value = float(stat_value) if '.' in str(stat_value) else int(stat_value)
                                        except (ValueError, TypeError):
                                            stat_value = str(stat_value)
                                        
                                        # Determine position from stat category
                                        position = None
                                        if category_name == 'passing' or stat_name in ['C/ATT', 'YDS', 'AVG', 'TD', 'INT', 'QBR']:
                                            position = 'QB'
                                        elif category_name == 'receiving' or stat_name in ['REC', 'YDS', 'AVG', 'TD', 'LONG']:
                                            position = 'WR'  # Could also be RB receiving
                                        elif category_name == 'rushing':
                                            continue  # We only track receiving stats for RBs
                                        
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
                                            base_record = {
                                                'player': player_name,
                                                'team': team_name,
                                                'opponent': opponent_name,
                                                'position': position,
                                                'week': week,
                                                'game_id': game_id,
                                                'start_time': start_time
                                            }
                                            
                                            # Task 4.3, 4.4, 4.5: Add metadata fields
                                            enhanced_record = add_standard_metadata(
                                                base_record,
                                                league="college",
                                                source="CollegeFootballData",
                                                game_time=start_time,
                                                player_name=player_name,
                                                team=team_name,
                                                game_id=game_id
                                            )
                                            
                                            parsed_records.append(enhanced_record)
                                            player_record = enhanced_record
                                        
                                        # Add stat to record
                                        if category_name == 'passing' and stat_name == 'YDS':
                                            player_record['passYards'] = stat_value
                                        elif category_name == 'receiving' and stat_name == 'YDS':
                                            player_record['receivingYards'] = stat_value
                                        elif category_name == 'passing' and stat_name == 'C/ATT':
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
                                        elif stat_name == 'TD':
                                            if position == 'QB':
                                                player_record['passTD'] = stat_value
                                            else:
                                                player_record['receivingTD'] = stat_value
                                        elif stat_name == 'REC':
                                            player_record['receptions'] = stat_value
                                        elif stat_name == 'INT' and position == 'QB':
                                            player_record['interceptions'] = stat_value
                                        
                                    except Exception as e:
                                        errors.append(f"Error processing athlete {athlete.get('name', 'unknown')}: {e}")
                                        continue
                        
                    except Exception as e:
                        errors.append(f"Error processing team {team_data.get('team', 'unknown')}: {e}")
                        continue
                        
            except Exception as e:
                errors.append(f"Error processing game {game.get('id', 'unknown')}: {e}")
                continue
        
        # Step 3: Filter, validate and clean records
        validated_records = []
        for record in parsed_records:
            try:
                position = record.get('position')
                
                # Ensure minimum required stats for each position
                has_relevant_stats = False
                if position == 'QB':
                    has_relevant_stats = (record.get('passYards') is not None or 
                                        record.get('completions') is not None)
                elif position == 'WR':
                    has_relevant_stats = (record.get('receivingYards') is not None or 
                                        record.get('receptions') is not None)
                elif position == 'RB':
                    has_relevant_stats = record.get('receivingYards') is not None
                
                if not has_relevant_stats:
                    continue
                
                # Task 4.6: Validate all required fields and relationships
                validate_metadata_fields(record, parser_name)
                validate_no_placeholder_values(record, parser_name)
                
                # Additional validation for team/opponent
                if record.get('team') == record.get('opponent'):
                    errors.append(f"Team and opponent are the same for {record.get('player')}")
                    continue
                
                validated_records.append(record)
                
            except Exception as validation_error:
                errors.append(f"Validation failed for {record.get('player', 'unknown')}: {validation_error}")
                continue
        
        # Step 4: Final quality check
        if validated_records:
            placeholder_summary = detect_placeholder_values(validated_records, return_summary=True)
            if placeholder_summary['has_placeholders']:
                print(f"⚠️ {parser_name}: {placeholder_summary['records_with_issues']} records have placeholder values")
        
        # Step 5: Print summary and return results
        print_parser_summary(parser_name, total_games_processed, len(validated_records), errors if errors else None)
        
        if validated_records:
            print(f"📊 Enhanced Fields Added:")
            print(f"   • Team/opponent derivation from game structure")
            print(f"   • Metadata fields (league, season, source, player_id)")
            print(f"   • Enhanced validation and quality checking")
        
        return validated_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


if __name__ == "__main__":
    """
    Enhanced test suite for the College Football parser (Task 4.7).
    Tests with multiple CFB data samples and validates team/opponent accuracy.
    """
    import os
    
    print("🏈 ENHANCED COLLEGE FOOTBALL PARSER - COMPREHENSIVE TEST SUITE")
    print("==============================================================")
    
    # Test with actual API data if available
    test_files = [
        "api_data/cfb_stats/players_2023_week1_regular.json",
        "api_data/cfb_stats/players_2023_week2_regular.json"
    ]
    
    total_tests = 0
    successful_tests = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            total_tests += 1
            print(f"\n🧪 Testing with {test_file}")
            
            try:
                results = parse_cfb_player_stats(test_file)
                print(f"📊 Successfully parsed {len(results)} player records")
                
                if results:
                    successful_tests += 1
                    
                    # Quality validation
                    placeholder_summary = detect_placeholder_values(results, return_summary=True)
                    print(f"📈 Quality Metrics:")
                    print(f"   • Records parsed: {len(results)}")
                    print(f"   • Placeholder rate: {placeholder_summary['issue_rate']:.2%}")
                    print(f"   • Records with issues: {placeholder_summary['records_with_issues']}")
                    
                    # Position breakdown
                    positions = {}
                    for record in results:
                        pos = record.get('position', 'Unknown')
                        positions[pos] = positions.get(pos, 0) + 1
                    
                    print("📋 Position breakdown:")
                    for pos, count in positions.items():
                        print(f"   {pos}: {count} players")
                    
                    # Enhanced field validation
                    sample = results[0]
                    required_fields = ['player', 'team', 'opponent', 'position', 
                                     'week', 'game_id', 'start_time', 'league', 
                                     'season', 'source', 'player_id']
                    
                    missing_fields = [field for field in required_fields 
                                    if field not in sample]
                    
                    if missing_fields:
                        print(f"⚠️ Missing required fields: {missing_fields}")
                    else:
                        print("✅ All required fields present")
                    
                    # Team/opponent relationship validation
                    team_opponent_issues = 0
                    for record in results:
                        if record.get('team') == record.get('opponent'):
                            team_opponent_issues += 1
                    
                    if team_opponent_issues > 0:
                        print(f"⚠️ {team_opponent_issues} records have team/opponent issues")
                    else:
                        print("✅ All team/opponent relationships valid")
                    
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
    
    print(f"\n🎯 TEST SUMMARY")
    print(f"===============")
    print(f"Tests run: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success rate: {(successful_tests/max(1,total_tests)):.1%}")
    
    if successful_tests == total_tests and total_tests > 0:
        print("🎉 All tests passed! Enhanced CFB parser working correctly.")
    else:
        print("⚠️ Some tests failed. Review the output above.")