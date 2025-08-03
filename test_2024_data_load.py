#!/usr/bin/env python3
"""
Test 2024 Player Performance Data Loading

This script tests the player performance data loading process with just a few weeks 
to ensure everything works before running the full season load.
(Excludes PrizePicks betting lines - only NFL/CFB player stats)
"""

import sys
sys.path.append('.')

from load_2024_season_data import Season2024Loader


def test_load():
    """Test loading with just a few weeks."""
    loader = Season2024Loader()
    
    # Override with just a few weeks for testing
    loader.nfl_weeks = [1, 2]  # Just weeks 1-2
    loader.cfb_weeks = [1, 2]  # Just weeks 1-2
    
    print("🧪 TESTING MODE: Loading only weeks 1-2 for each league")
    print("📊 Data Types: NFL player boxscores + CFB player stats (NO PrizePicks)")
    print("=" * 60)
    
    loader.run_full_season_load()


if __name__ == "__main__":
    test_load()