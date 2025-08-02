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
    safe_get_nested,
    validate_required_fields,
    print_parser_summary,
    ParserError,
    DataStructureError,
    derive_team_from_prizepicks,
    derive_opponent_from_prizepicks,
    derive_position_from_prizepicks,
    derive_game_time_from_prizepicks,
    add_standard_metadata,
    validate_metadata_fields,
    validate_no_placeholder_values,
    detect_placeholder_values
)


def parse_prizepicks_data(data_source: Union[str, Dict]) -> List[Dict[str, Any]]:
    """
    Enhanced PrizePicks NFL projection data parser with comprehensive validation.
    
    Args:
        data_source: File path to nfl_projections.json or pre-loaded JSON data
        
    Returns:
        List of dictionaries with enhanced fields:
        - player_name: Player's full name (no placeholders)
        - team: Team name/abbreviation (derived from relationships)
        - opponent: Opponent team name (derived from market data)
        - stat_type: Type of statistic (e.g., "Pass Yds", "Rec Yds")
        - line_score: Betting line value (float)
        - game_time: Game start time (derived from projection/market)
        - projection_id: Unique projection identifier
        - position: Player position (derived from player data)
        - league: "nfl" or "college"
        - season: Integer year (derived from game_time)
        - source: "PrizePicks"
        - player_id: Unique player identifier hash
        - odds_type: Odds type from projection or "standard"
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        MetadataValidationError: If metadata validation fails
        PlaceholderValueError: If placeholder values found in critical fields
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
        
        # Step 3: Get included data for relationship lookups
        included_data = safe_get_list(data, 'included', [])
        
        # Step 4: Parse data[] array to extract projection records
        projections = safe_get_list(data, 'data', [])
        
        for projection in projections:
            try:
                # Extract basic projection data
                projection_id = projection.get('id', '')
                attributes = projection.get('attributes', {})
                
                # Extract stat type and line score
                stat_type = attributes.get('stat_type', 'unknown')
                line_score = attributes.get('line_score')
                
                # Convert line_score to float if possible
                if line_score is not None:
                    try:
                        line_score = float(line_score)
                    except (ValueError, TypeError):
                        line_score = None
                
                # Task 2.1: Enhanced team derivation using helper function
                team = derive_team_from_prizepicks(projection, included_data)
                
                # Task 2.2: Enhanced opponent derivation using helper function  
                opponent = derive_opponent_from_prizepicks(projection, included_data)
                
                # Task 2.3: Position field extraction using helper function
                position = derive_position_from_prizepicks(projection, included_data)
                
                # Task 2.4: Fix game_time field using helper function
                game_time = derive_game_time_from_prizepicks(projection, included_data)
                
                # Task 2.6: Add odds_type field with fallback
                odds_type = attributes.get('odds_type', 'standard')
                
                # Extract player name from relationships
                player_name = "Unknown Player"
                player_id_raw = None
                relationships = projection.get('relationships', {})
                
                if 'new_player' in relationships:
                    player_data = relationships['new_player'].get('data', {})
                    player_id_raw = player_data.get('id')
                    
                    # Find player in included data
                    for item in included_data:
                        if (item.get('type') == 'new_player' and 
                            item.get('id') == player_id_raw):
                            attributes_player = item.get('attributes', {})
                            player_name = (attributes_player.get('display_name') or 
                                         attributes_player.get('name') or 'Unknown Player')
                            break
                
                # Build the base parsed record
                parsed_record = {
                    'player_name': player_name,
                    'team': team,
                    'opponent': opponent,
                    'stat_type': stat_type,
                    'line_score': line_score,
                    'game_time': game_time,
                    'projection_id': projection_id,
                    'position': position,
                    'odds_type': odds_type
                }
                
                # Determine league based on league ID in relationships
                league_id = safe_get_nested(projection, ['relationships', 'league', 'data', 'id'])
                league = "college" if league_id == "15" else "nfl"  # 15=CFB, 9=NFL
                
                # Task 2.5: Add metadata fields using helper function
                enhanced_record = add_standard_metadata(
                    parsed_record,
                    league=league,
                    source="PrizePicks",
                    game_time=game_time,
                    player_name=player_name,
                    team=team,
                    game_id=projection_id
                )
                
                # Task 2.7: Validate all required fields are populated
                try:
                    validate_metadata_fields(enhanced_record, parser_name)
                    validate_no_placeholder_values(enhanced_record, parser_name)
                    
                    # Only add records with valid essential data
                    if (enhanced_record['player_name'] not in ['Unknown Player', 'Unknown', ''] and 
                        enhanced_record['stat_type'] not in ['unknown', 'Unknown', ''] and 
                        enhanced_record['line_score'] is not None):
                        parsed_records.append(enhanced_record)
                    else:
                        errors.append(f"Essential data missing for projection {projection_id}")
                        
                except Exception as validation_error:
                    errors.append(f"Validation failed for projection {projection_id}: {validation_error}")
                    
            except Exception as e:
                errors.append(f"Error parsing projection {projection.get('id', 'unknown')}: {e}")
                continue
        
        # Step 5: Final quality check and reporting
        if parsed_records:
            placeholder_summary = detect_placeholder_values(parsed_records, return_summary=True)
            if placeholder_summary['has_placeholders']:
                print(f"⚠️ {parser_name}: {placeholder_summary['records_with_issues']} records have placeholder values")
                print(f"   Issue rate: {placeholder_summary['issue_rate']:.2%}")
        
        # Step 6: Print summary and return results
        print_parser_summary(parser_name, len(projections), len(parsed_records), errors if errors else None)
        
        # Additional quality reporting
        if parsed_records:
            print(f"📊 Enhanced Fields Added:")
            print(f"   • Team derivation using relationship lookups")
            print(f"   • Opponent derivation from market data")
            print(f"   • Position extraction from player data")
            print(f"   • Metadata fields (league, season, source, player_id)")
            print(f"   • Quality validation and placeholder detection")
        
        return parsed_records
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


if __name__ == "__main__":
    """
    Enhanced test suite for the PrizePicks parser (Task 2.8).
    Tests with multiple NFL projection data samples and validates output quality.
    """
    import os
    
    # Test with actual API data if available
    test_files = [
        "api_data/prizepicks/nfl_projections.json",
        "api_data/prizepicks/cfb_projections.json"
    ]
    
    print("🏈 ENHANCED PRIZEPICKS PARSER - COMPREHENSIVE TEST SUITE")
    print("=========================================================")
    
    total_tests = 0
    successful_tests = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            total_tests += 1
            print(f"\n🧪 Testing with {test_file}")
            
            try:
                results = parse_prizepicks_data(test_file)
                print(f"📊 Successfully parsed {len(results)} projections")
                
                if results:
                    successful_tests += 1
                    
                    # Quality validation
                    placeholder_summary = detect_placeholder_values(results, return_summary=True)
                    print(f"📈 Quality Metrics:")
                    print(f"   • Records parsed: {len(results)}")
                    print(f"   • Placeholder rate: {placeholder_summary['issue_rate']:.2%}")
                    print(f"   • Records with issues: {placeholder_summary['records_with_issues']}")
                    
                    # Sample record validation
                    print("\n📋 Sample enhanced record:")
                    sample = results[0]
                    for key, value in sample.items():
                        print(f"   {key}: {value}")
                    
                    # Field validation
                    required_fields = ['player_name', 'team', 'opponent', 'stat_type', 
                                     'line_score', 'position', 'league', 'season', 
                                     'source', 'player_id']
                    
                    missing_fields = [field for field in required_fields 
                                    if field not in sample]
                    
                    if missing_fields:
                        print(f"⚠️ Missing required fields: {missing_fields}")
                    else:
                        print("✅ All required fields present")
                    
                    # Validate no "Unknown" values in critical fields
                    critical_fields = ['team', 'opponent', 'player_name']
                    unknown_issues = []
                    for field in critical_fields:
                        if field in sample and str(sample[field]).lower() in ['unknown', 'unknown team', 'unknown opponent', 'unknown player']:
                            unknown_issues.append(field)
                    
                    if unknown_issues:
                        print(f"⚠️ Placeholder values found in: {unknown_issues}")
                    else:
                        print("✅ No placeholder values in critical fields")
                        
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
        print("🎉 All tests passed! Enhanced parser working correctly.")
    else:
        print("⚠️ Some tests failed. Review the output above.")