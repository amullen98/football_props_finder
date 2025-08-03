#!/usr/bin/env python3
"""
2024 Season Player Performance Data Loader

This script fetches and loads comprehensive 2024 season PLAYER PERFORMANCE data 
for both NFL and College Football (excludes betting lines - only actual stats).
It handles API rate limiting, error recovery, and database population.
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

from src.database.parser_integration import bulk_load_parsed_directory
from src.database.connection import cursor_context


class Season2024Loader:
    """Comprehensive loader for 2024 NFL and CFB season data."""
    
    def __init__(self):
        self.progress_file = 'data_loading_progress.json'
        self.delay_between_calls = 2  # seconds between API calls
        self.delay_between_weeks = 5  # seconds between weeks
        self.max_retries = 3
        
        # 2024 season parameters
        self.nfl_weeks = list(range(1, 19))  # Weeks 1-18
        self.cfb_weeks = list(range(1, 16))  # Weeks 1-15
        self.year = 2024
        
        self.load_progress()
    
    def load_progress(self):
        """Load existing progress from file."""
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                'nfl_completed': [],
                'cfb_completed': [],
                'last_updated': None,
                'total_api_calls': 0,
                'total_records_loaded': 0
            }
    
    def save_progress(self):
        """Save current progress to file."""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def run_shell_command(self, command: str, description: str) -> bool:
        """Run a shell command with error handling."""
        print(f"\n🔄 {description}")
        print(f"📋 Command: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {description} - SUCCESS")
                return True
            else:
                print(f"❌ {description} - FAILED")
                print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - TIMEOUT (5 minutes)")
            return False
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            return False
    
    def fetch_nfl_week_data(self, week: int) -> bool:
        """Fetch NFL data for a specific week."""
        if week in self.progress['nfl_completed']:
            print(f"⏭️  NFL Week {week} already completed, skipping...")
            return True
        
        # Fetch NFL game IDs
        game_ids_cmd = f"./generate_api_data.sh nfl-stats {self.year} {week} 2"
        if not self.run_shell_command(game_ids_cmd, f"NFL Week {week} Game IDs"):
            return False
        
        time.sleep(self.delay_between_calls)
        
        # Fetch NFL boxscores for the week
        boxscores_cmd = f"./generate_api_data.sh nfl-week-boxscores {self.year} {week} 2"
        if not self.run_shell_command(boxscores_cmd, f"NFL Week {week} Boxscores"):
            return False
        
        self.progress['nfl_completed'].append(week)
        self.progress['total_api_calls'] += 1  # This actually makes ~16 API calls
        return True
    
    def fetch_cfb_week_data(self, week: int) -> bool:
        """Fetch CFB data for a specific week."""
        if week in self.progress['cfb_completed']:
            print(f"⏭️  CFB Week {week} already completed, skipping...")
            return True
        
        # Fetch CFB stats
        cfb_cmd = f"./generate_api_data.sh cfb-stats {self.year} {week} regular"
        if not self.run_shell_command(cfb_cmd, f"CFB Week {week} Stats"):
            return False
        
        self.progress['cfb_completed'].append(week)
        self.progress['total_api_calls'] += 1
        return True
    
    def load_data_to_database(self) -> Dict[str, Any]:
        """Load only NFL and CFB player performance data into the database."""
        print(f"\n📊 Loading NFL/CFB player data into database...")
        
        try:
            # Clear any existing test data
            with cursor_context() as cursor:
                cursor.execute("DELETE FROM player_stats WHERE source = 'test'")
                cursor.execute("DELETE FROM games_processed WHERE source = 'test'")
            
            # Use the existing bulk_load_parsed_directory function but filter for only NFL/CFB data
            results = bulk_load_parsed_directory('parsed_data', use_upsert=True, batch_size=1000)
            
            # Filter out PrizePicks results and keep only NFL/CFB data
            filtered_results = {
                'nfl_boxscore': results.get('nfl_boxscore', []),
                'cfb_stats': results.get('cfb_stats', []), 
                'nfl_game_ids': results.get('nfl_game_ids', [])
            }
            results = filtered_results
            
            # Calculate totals
            total_inserted = 0
            total_errors = 0
            
            for data_type, result_list in results.items():
                if result_list:
                    # Handle both BatchInsertResult objects and lists
                    type_inserted = 0
                    type_errors = 0
                    for r in result_list:
                        if hasattr(r, 'inserted'):
                            type_inserted += r.inserted
                        if hasattr(r, 'errors'):
                            type_errors += r.errors
                    total_inserted += type_inserted
                    total_errors += type_errors
                    print(f"  {data_type}: {type_inserted} inserted, {type_errors} errors")
                else:
                    print(f"  {data_type}: No files found")
            
            self.progress['total_records_loaded'] = total_inserted
            
            return {
                'success': True,
                'total_inserted': total_inserted,
                'total_errors': total_errors,
                'details': results
            }
            
        except Exception as e:
            print(f"❌ Database loading error: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_inserted': 0,
                'total_errors': 0
            }
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database record counts for player performance data."""
        try:
            with cursor_context() as cursor:
                stats = {}
                # Focus on player performance tables only
                tables = ['player_stats', 'games_processed', 'players', 'teams']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}
    
    def run_full_season_load(self):
        """Run the complete 2024 season player performance data loading process."""
        print("🏈 Starting 2024 Season Player Performance Data Loading")
        print("=" * 60)
        print(f"📅 NFL Weeks: {len(self.nfl_weeks)} weeks (1-18) - Player boxscore stats")
        print(f"📅 CFB Weeks: {len(self.cfb_weeks)} weeks (1-15) - Player game stats")
        print(f"🚫 PrizePicks: EXCLUDED (betting lines not needed for historical analysis)")
        print(f"⏱️  Estimated time: ~45-60 minutes")
        print()
        
        # Get initial database stats
        initial_stats = self.get_database_stats()
        print("📊 Initial Database Stats (Player Performance Data):")
        for table, count in initial_stats.items():
            print(f"  {table}: {count:,} records")
        print()
        
        start_time = time.time()
        total_weeks = len(self.nfl_weeks) + len(self.cfb_weeks)
        completed_weeks = len(self.progress['nfl_completed']) + len(self.progress['cfb_completed'])
        
        try:
            # Process NFL weeks
            print("🏈 Processing NFL weeks...")
            for week in self.nfl_weeks:
                print(f"\n📅 NFL Week {week}/{max(self.nfl_weeks)} ({completed_weeks + 1}/{total_weeks} total)")
                
                retry_count = 0
                while retry_count < self.max_retries:
                    if self.fetch_nfl_week_data(week):
                        completed_weeks += 1
                        break
                    else:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            print(f"🔄 Retrying NFL Week {week} (attempt {retry_count + 1}/{self.max_retries})")
                            time.sleep(self.delay_between_calls * 2)
                        else:
                            print(f"❌ Failed to fetch NFL Week {week} after {self.max_retries} attempts")
                
                self.save_progress()
                time.sleep(self.delay_between_weeks)
            
            # Process CFB weeks
            print(f"\n🎓 Processing CFB weeks...")
            for week in self.cfb_weeks:
                print(f"\n📅 CFB Week {week}/{max(self.cfb_weeks)} ({completed_weeks + 1}/{total_weeks} total)")
                
                retry_count = 0
                while retry_count < self.max_retries:
                    if self.fetch_cfb_week_data(week):
                        completed_weeks += 1
                        break
                    else:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            print(f"🔄 Retrying CFB Week {week} (attempt {retry_count + 1}/{self.max_retries})")
                            time.sleep(self.delay_between_calls * 2)
                        else:
                            print(f"❌ Failed to fetch CFB Week {week} after {self.max_retries} attempts")
                
                self.save_progress()
                time.sleep(self.delay_between_weeks)
            
            # Load all data into database
            print(f"\n" + "=" * 60)
            db_result = self.load_data_to_database()
            
            # Get final database stats
            final_stats = self.get_database_stats()
            
            # Print final summary
            elapsed_time = time.time() - start_time
            print(f"\n🎉 2024 Season Loading Complete!")
            print("=" * 60)
            print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
            print(f"📊 Total API calls: {self.progress['total_api_calls']}")
            print(f"📈 NFL weeks completed: {len(self.progress['nfl_completed'])}/{len(self.nfl_weeks)}")
            print(f"📈 CFB weeks completed: {len(self.progress['cfb_completed'])}/{len(self.cfb_weeks)}")
            
            if db_result['success']:
                print(f"✅ Database loading: {db_result['total_inserted']:,} records inserted")
            else:
                print(f"❌ Database loading failed: {db_result.get('error', 'Unknown error')}")
            
            print(f"\n📊 Final Database Stats:")
            for table, count in final_stats.items():
                initial_count = initial_stats.get(table, 0)
                added = count - initial_count
                print(f"  {table}: {count:,} records (+{added:,})")
            
            self.save_progress()
            
        except KeyboardInterrupt:
            print(f"\n\n⏸️  Process interrupted by user")
            print(f"📊 Progress saved. Resume by running this script again.")
            self.save_progress()
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            self.save_progress()
            raise


def main():
    """Main entry point."""
    loader = Season2024Loader()
    
    # Check if we should resume or start fresh
    completed_weeks = len(loader.progress['nfl_completed']) + len(loader.progress['cfb_completed'])
    total_weeks = len(loader.nfl_weeks) + len(loader.cfb_weeks)
    
    if completed_weeks > 0:
        print(f"📋 Found existing progress: {completed_weeks}/{total_weeks} weeks completed")
        response = input("Continue from where you left off? (y/n): ").lower().strip()
        if response != 'y':
            print("Starting fresh...")
            loader.progress = {
                'nfl_completed': [],
                'cfb_completed': [],
                'last_updated': None,
                'total_api_calls': 0,
                'total_records_loaded': 0
            }
    
    loader.run_full_season_load()


if __name__ == "__main__":
    main()