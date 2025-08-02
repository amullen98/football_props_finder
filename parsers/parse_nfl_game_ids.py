"""
NFL Game IDs Parser

This module parses NFL game ID lists from weekly game data.
It extracts event IDs and provides structured output for downstream processing.
"""

import re
import os
from typing import Dict, List, Any, Union
from .common import (
    safe_load_json,
    safe_get_list,
    validate_required_fields,
    print_parser_summary,
    ParserError,
    DataStructureError
)


def parse_nfl_game_ids(data_source: Union[str, Dict], week: int = None, year: int = None) -> Dict[str, Any]:
    """
    Parse NFL game IDs from weekly game data.
    
    Args:
        data_source: File path to games_YYYY_weekN_typeT.json or pre-loaded JSON data
        week: Week number (optional, can be parsed from filename)
        year: Year (optional, can be parsed from filename)
        
    Returns:
        Dictionary with keys: week, year, game_ids (list of event IDs)
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
        DataStructureError: If expected data structure is missing
        ParserError: For other parsing-related errors
    """
    parser_name = "NFL Game IDs"
    errors = []
    
    try:
        # Step 1: Load and validate input data
        data = safe_load_json(data_source)
        
        # Step 2: Extract week and year from filename if not provided
        parsed_week = week
        parsed_year = year
        
        if isinstance(data_source, str) and (parsed_week is None or parsed_year is None):
            # Try to parse filename: games_YYYY_weekN_typeT.json
            filename = os.path.basename(data_source)
            
            # Pattern: games_2023_week1_type2.json
            pattern = r'games_(\d{4})_week(\d+)_type(\d+)\.json'
            match = re.search(pattern, filename)
            
            if match:
                if parsed_year is None:
                    parsed_year = int(match.group(1))
                if parsed_week is None:
                    parsed_week = int(match.group(2))
                # Note: type is match.group(3) but we don't need it for output
            else:
                # Fallback: try simpler patterns
                year_match = re.search(r'(\d{4})', filename)
                week_match = re.search(r'week(\d+)', filename, re.IGNORECASE)
                
                if year_match and parsed_year is None:
                    parsed_year = int(year_match.group(1))
                if week_match and parsed_week is None:
                    parsed_week = int(week_match.group(1))
        
        # Set defaults if still not found
        if parsed_year is None:
            parsed_year = 2023  # Default year
            errors.append("Year not found in filename, defaulting to 2023")
        
        if parsed_week is None:
            parsed_week = 1  # Default week
            errors.append("Week not found in filename, defaulting to 1")
        
        # Step 3: Validate required fields
        validate_required_fields(data, ['items'], f"{parser_name} JSON structure")
        
        # Step 4: Extract eventid values from items[] array
        items = safe_get_list(data, 'items', [])
        
        if not items:
            errors.append("No items found in data - empty game list")
            game_ids = []
        else:
            game_ids = []
            
            for i, item in enumerate(items):
                try:
                    event_id = item.get('eventid')
                    
                    if event_id:
                        # Ensure it's a string and clean it
                        event_id = str(event_id).strip()
                        if event_id:  # Make sure it's not empty after stripping
                            game_ids.append(event_id)
                        else:
                            errors.append(f"Empty eventid found in item {i}")
                    else:
                        errors.append(f"Missing eventid in item {i}: {item}")
                        
                except Exception as e:
                    errors.append(f"Error processing item {i}: {e}")
                    continue
        
        # Step 5: Create structured output
        result = {
            'week': parsed_week,
            'year': parsed_year,
            'game_ids': game_ids
        }
        
        # Step 6: Print summary and return results
        total_items = len(items)
        successful_extractions = len(game_ids)
        
        print_parser_summary(parser_name, total_items, successful_extractions, errors if errors else None)
        
        # Print additional context
        print(f"📅 Parsed: {parsed_year} Season, Week {parsed_week}")
        print(f"🎯 Extracted {successful_extractions} game IDs")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to parse {parser_name} data: {e}"
        print_parser_summary(parser_name, 0, 0, [error_msg])
        raise ParserError(error_msg) from e


def extract_game_ids_only(data_source: Union[str, Dict]) -> List[str]:
    """
    Convenience function to extract just the list of game IDs.
    
    Args:
        data_source: File path or pre-loaded JSON data
        
    Returns:
        List of game ID strings
    """
    result = parse_nfl_game_ids(data_source)
    return result.get('game_ids', [])


def get_game_count(data_source: Union[str, Dict]) -> int:
    """
    Convenience function to get the count of games.
    
    Args:
        data_source: File path or pre-loaded JSON data
        
    Returns:
        Number of games found
    """
    result = parse_nfl_game_ids(data_source)
    return len(result.get('game_ids', []))


if __name__ == "__main__":
    """
    Test the NFL Game IDs parser with sample data files.
    """
    import os
    
    # Test with actual API data if available
    test_files = [
        "api_data/nfl_stats/games_2023_week1_type2.json",
        "api_data/nfl_stats/games_2023_week2_type2.json"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Testing with {test_file}")
            try:
                result = parse_nfl_game_ids(test_file)
                
                print(f"📊 Parsing Results:")
                print(f"  Year: {result['year']}")
                print(f"  Week: {result['week']}")
                print(f"  Game IDs Count: {len(result['game_ids'])}")
                
                if result['game_ids']:
                    print(f"\n📋 Game IDs:")
                    for i, game_id in enumerate(result['game_ids'][:5], 1):  # Show first 5
                        print(f"  {i}. {game_id}")
                    
                    if len(result['game_ids']) > 5:
                        print(f"  ... and {len(result['game_ids']) - 5} more")
                
                # Test convenience functions
                print(f"\n🔧 Convenience Functions:")
                ids_only = extract_game_ids_only(test_file)
                count = get_game_count(test_file)
                print(f"  extract_game_ids_only(): {len(ids_only)} IDs")
                print(f"  get_game_count(): {count} games")
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    # Test with sample data structure
    print(f"\n🧪 Testing with sample data structure:")
    sample_data = {
        "items": [
            {"eventid": "401547353"},
            {"eventid": "401547403"},
            {"eventid": "401547397"}
        ],
        "count": 3
    }
    
    try:
        result = parse_nfl_game_ids(sample_data, week=1, year=2023)
        print(f"📊 Sample Data Results:")
        print(f"  Week: {result['week']}, Year: {result['year']}")
        print(f"  Game IDs: {result['game_ids']}")
    except Exception as e:
        print(f"❌ Sample test failed: {e}")