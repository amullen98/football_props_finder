#!/usr/bin/env python3
"""
Simple test script for manual validation of all football data parsers.

This script provides an easy way to test all parsers with actual API data
and validate their functionality independently.

Usage:
    python3 parsers/test_all_parsers.py
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from parsers import (
    parse_prizepicks_data,
    parse_cfb_player_stats,
    parse_nfl_game_ids,
    parse_nfl_boxscore
)


def test_prizepicks_parser():
    """Test PrizePicks parser with available data files."""
    print("🎯 TESTING PRIZEPICKS PARSER")
    print("=" * 40)
    
    test_files = [
        "api_data/prizepicks/nfl_projections.json",
        "api_data/prizepicks/cfb_projections.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Testing with: {file_path}")
            try:
                results = parse_prizepicks_data(file_path)
                print(f"✅ Successfully parsed {len(results)} projections")
                
                if results:
                    sample = results[0]
                    print(f"📋 Sample projection:")
                    print(f"  Player: {sample.get('player_name')}")
                    print(f"  Team: {sample.get('team')}")
                    print(f"  Stat: {sample.get('stat_type')}")
                    print(f"  Line: {sample.get('line_score')}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")


def test_cfb_parser():
    """Test College Football parser with available data files."""
    print("\n\n🏈 TESTING COLLEGE FOOTBALL PARSER")
    print("=" * 40)
    
    test_files = [
        "api_data/cfb_stats/players_2023_week1_regular.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Testing with: {file_path}")
            try:
                results = parse_cfb_player_stats(file_path)
                print(f"✅ Successfully parsed {len(results)} player records")
                
                # Show position breakdown
                positions = {}
                for record in results:
                    pos = record.get('position', 'Unknown')
                    positions[pos] = positions.get(pos, 0) + 1
                
                print(f"📊 Position breakdown:")
                for pos, count in positions.items():
                    print(f"  {pos}: {count} players")
                
                # Show sample records
                if results:
                    for pos in ['QB', 'WR']:
                        samples = [r for r in results if r.get('position') == pos]
                        if samples:
                            sample = samples[0]
                            print(f"📋 Sample {pos}:")
                            print(f"  Player: {sample.get('player')}")
                            print(f"  Team: {sample.get('team')}")
                            if pos == 'QB':
                                print(f"  Pass Yards: {sample.get('passYards', 'N/A')}")
                            else:
                                print(f"  Receiving Yards: {sample.get('receivingYards', 'N/A')}")
                            break
                            
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")


def test_nfl_game_ids_parser():
    """Test NFL Game IDs parser with available data files."""
    print("\n\n🏟️ TESTING NFL GAME IDS PARSER")
    print("=" * 40)
    
    test_files = [
        "api_data/nfl_stats/games_2023_week1_type2.json",
        "api_data/nfl_stats/games_2023_week2_type2.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Testing with: {file_path}")
            try:
                result = parse_nfl_game_ids(file_path)
                print(f"✅ Successfully parsed game data")
                print(f"📊 Year: {result['year']}, Week: {result['week']}")
                print(f"🎯 Game IDs: {len(result['game_ids'])} games")
                
                if result['game_ids']:
                    print(f"📋 Sample game IDs: {result['game_ids'][:3]}...")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")


def test_nfl_boxscore_parser():
    """Test NFL Boxscore parser with available data files."""
    print("\n\n📊 TESTING NFL BOXSCORE PARSER")
    print("=" * 40)
    
    # Find available boxscore files
    boxscore_dir = "api_data/nfl_boxscore/"
    if os.path.exists(boxscore_dir):
        boxscore_files = [f for f in os.listdir(boxscore_dir) 
                         if f.startswith('boxscore_') and f.endswith('.json')]
        
        test_files = [os.path.join(boxscore_dir, f) for f in sorted(boxscore_files)[:2]]  # Test first 2
    else:
        test_files = [
            "api_data/nfl_boxscore/boxscore_401547353.json",
            "api_data/nfl_boxscore/boxscore_401220225.json"
        ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Testing with: {os.path.basename(file_path)}")
            try:
                results = parse_nfl_boxscore(file_path)
                print(f"✅ Successfully parsed {len(results)} player records")
                
                # Show position breakdown
                positions = {}
                for record in results:
                    pos = record.get('position', 'Unknown')
                    positions[pos] = positions.get(pos, 0) + 1
                
                print(f"📊 Position breakdown:")
                for pos, count in positions.items():
                    print(f"  {pos}: {count} players")
                
                # Show sample records
                if results:
                    for pos in ['QB', 'WR']:
                        samples = [r for r in results if r.get('position') == pos]
                        if samples:
                            sample = samples[0]
                            print(f"📋 Sample {pos}:")
                            print(f"  Player: {sample.get('player')}")
                            print(f"  Team: {sample.get('team')}")
                            if pos == 'QB':
                                print(f"  Pass Yards: {sample.get('passing_yards', 'N/A')}")
                            else:
                                print(f"  Receiving Yards: {sample.get('receiving_yards', 'N/A')}")
                            break
                            
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")


def run_all_tests():
    """Run all parser tests."""
    print("🏈 FOOTBALL PROP INSIGHTS - PARSER VALIDATION SUITE")
    print("=" * 60)
    print("Testing all parsers with actual API data files...")
    
    # Test each parser
    test_prizepicks_parser()
    test_cfb_parser()
    test_nfl_game_ids_parser()
    test_nfl_boxscore_parser()
    
    print("\n\n🎉 VALIDATION SUITE COMPLETE")
    print("=" * 60)
    print("All parsers have been tested with available data files.")
    print("Check the output above for any errors or issues.")


if __name__ == "__main__":
    run_all_tests()