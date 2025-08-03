"""
Sample Data and Testing Module for Football Props Finder Database

This module provides functionality for loading and testing database operations
with real data from parsed files. It includes sample data insertion, validation
testing, and comprehensive verification of database functionality.

Features:
- Load sample data from existing parsed JSON files
- Test all database insertion functions (direct, batch, upsert)
- Validate data integrity and quality
- Performance testing for batch operations
- Comprehensive error handling and logging
"""

import json
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import database modules - handle gracefully if not available
try:
    from .insert import (
        insert_prop_line, insert_player_stats, insert_game_processed,
        insert_player, insert_team, upsert_prop_line, upsert_player_stats
    )
    from .batch import (
        batch_insert_prop_lines, batch_insert_player_stats,
        batch_insert_games_processed, batch_transaction
    )
    from .validation import DataValidator
    from .connection import get_connection_manager, cursor_context
    from .parser_integration import (
        route_prizepicks_data, route_nfl_boxscore_data,
        route_cfb_stats_data, route_nfl_game_ids_data
    )
    DATABASE_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database modules not fully available: {e}")
    DATABASE_MODULES_AVAILABLE = False


class SampleDataLoader:
    """Loads and manages sample data for testing database operations."""
    
    def __init__(self, base_path: str = "parsed_data"):
        """
        Initialize the sample data loader.
        
        Args:
            base_path: Path to parsed data directory
        """
        self.base_path = Path(base_path)
        self.validator = DataValidator(strict_mode=False) if DATABASE_MODULES_AVAILABLE else None
        self.connection_manager = get_connection_manager() if DATABASE_MODULES_AVAILABLE else None
        
    def get_available_data_files(self) -> Dict[str, List[str]]:
        """
        Scan for available parsed data files.
        
        Returns:
            Dictionary mapping data types to available file paths
        """
        available_files = {
            'prizepicks': [],
            'nfl_stats': [],
            'nfl_boxscore': [],
            'cfb_stats': []
        }
        
        if not self.base_path.exists():
            logger.warning(f"Parsed data directory not found: {self.base_path}")
            return available_files
        
        # Scan for PrizePicks files
        prizepicks_dir = self.base_path / "prizepicks"
        if prizepicks_dir.exists():
            available_files['prizepicks'] = [
                str(f) for f in prizepicks_dir.glob("*_parsed.json")
            ]
        
        # Scan for NFL stats files
        nfl_stats_dir = self.base_path / "nfl_stats"
        if nfl_stats_dir.exists():
            available_files['nfl_stats'] = [
                str(f) for f in nfl_stats_dir.glob("games_*_parsed.json")
            ]
        
        # Scan for NFL boxscore files
        nfl_boxscore_dir = self.base_path / "nfl_boxscore"
        if nfl_boxscore_dir.exists():
            available_files['nfl_boxscore'] = [
                str(f) for f in nfl_boxscore_dir.glob("*_parsed.json")
            ][:5]  # Limit to 5 files for testing
        
        # Scan for CFB stats files
        cfb_stats_dir = self.base_path / "cfb_stats"
        if cfb_stats_dir.exists():
            available_files['cfb_stats'] = [
                str(f) for f in cfb_stats_dir.glob("*_parsed.json")
            ]
        
        return available_files
    
    def load_sample_data(self, data_type: str, max_records: int = 50) -> List[Dict[str, Any]]:
        """
        Load sample data from parsed files.
        
        Args:
            data_type: Type of data to load (prizepicks, nfl_boxscore, etc.)
            max_records: Maximum number of records to return
            
        Returns:
            List of sample records
        """
        available_files = self.get_available_data_files()
        
        if data_type not in available_files or not available_files[data_type]:
            logger.warning(f"No {data_type} files available for testing")
            return []
        
        # Load from the first available file
        file_path = available_files[data_type][0]
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, list):
                sample_data = data[:max_records]
            elif isinstance(data, dict) and 'data' in data:
                sample_data = data['data'][:max_records]
            else:
                logger.warning(f"Unexpected data structure in {file_path}")
                return []
            
            logger.info(f"Loaded {len(sample_data)} {data_type} records from {file_path}")
            return sample_data
            
        except Exception as e:
            logger.error(f"Error loading {data_type} data from {file_path}: {e}")
            return []
    
    def create_sample_prop_lines(self, count: int = 10) -> List[Dict[str, Any]]:
        """Create sample prop line data for testing."""
        sample_data = []
        
        players = [
            ('Patrick Mahomes', 'KC', 'QB'),
            ('Josh Allen', 'BUF', 'QB'),
            ('Tyreek Hill', 'MIA', 'WR'),
            ('Travis Kelce', 'KC', 'TE'),
            ('Derrick Henry', 'TEN', 'RB')
        ]
        
        stat_types = ['Pass Yards', 'Rush Yards', 'Receptions', 'Receiving Yards']
        
        for i in range(count):
            player_name, team, position = random.choice(players)
            stat_type = random.choice(stat_types)
            
            # Adjust stat_type based on position
            if position == 'QB':
                stat_type = random.choice(['Pass Yards', 'Passing TDs', 'Rush Yards'])
                line_score = random.uniform(200, 350) if 'Yards' in stat_type else random.uniform(0.5, 3.5)
            elif position in ['WR', 'TE']:
                stat_type = random.choice(['Receptions', 'Receiving Yards', 'Receiving TDs'])
                line_score = random.uniform(3, 12) if stat_type == 'Receptions' else random.uniform(40, 120)
            else:  # RB
                stat_type = random.choice(['Rush Yards', 'Rushing TDs', 'Receptions'])
                line_score = random.uniform(60, 150) if 'Yards' in stat_type else random.uniform(0.5, 2.5)
            
            sample_data.append({
                'player_id': f"{position.lower()}_{player_name.lower().replace(' ', '_')}_{team.lower()}_2023",
                'player_name': player_name,
                'team': team,
                'opponent': random.choice(['DET', 'GB', 'CHI', 'MIN', 'LAR', 'SF']),
                'position': position,
                'stat_type': stat_type,
                'line_score': round(line_score, 1),
                'game_time': datetime.now() + timedelta(days=random.randint(1, 7)),
                'league': 'nfl',
                'source': 'PrizePicks',
                'season': 2023,
                'odds_type': 'over_under',
                'projection_id': f"test_proj_{i+1}"
            })
        
        return sample_data
    
    def create_sample_player_stats(self, count: int = 10) -> List[Dict[str, Any]]:
        """Create sample player statistics for testing."""
        sample_data = []
        
        players = [
            ('Patrick Mahomes', 'KC', 'QB'),
            ('Josh Allen', 'BUF', 'QB'),
            ('Tyreek Hill', 'MIA', 'WR'),
            ('Travis Kelce', 'KC', 'TE'),
            ('Derrick Henry', 'TEN', 'RB')
        ]
        
        for i in range(count):
            player_name, team, position = random.choice(players)
            
            base_stats = {
                'player_id': f"{position.lower()}_{player_name.lower().replace(' ', '_')}_{team.lower()}_2023",
                'player_name': player_name,
                'team': team,
                'opponent': random.choice(['DET', 'GB', 'CHI', 'MIN', 'LAR', 'SF']),
                'position': position,
                'game_id': f"nfl_2023_w{random.randint(1, 17)}_{team.lower()}_test",
                'week': random.randint(1, 17),
                'game_date': datetime.now().date() - timedelta(days=random.randint(1, 30)),
                'season': 2023,
                'league': 'nfl',
                'source': 'RapidAPI'
            }
            
            # Add position-specific stats
            if position == 'QB':
                base_stats.update({
                    'stat_type': 'passing',
                    'passing_yards': random.randint(200, 400),
                    'completions': random.randint(15, 35),
                    'attempts': random.randint(25, 45),
                    'passing_touchdowns': random.randint(0, 4),
                    'interceptions': random.randint(0, 2),
                    'sacks': random.randint(0, 5),
                    'sack_yards_lost': random.randint(0, 25)
                })
                # Ensure completions <= attempts
                if base_stats['completions'] > base_stats['attempts']:
                    base_stats['completions'] = base_stats['attempts']
            
            elif position in ['WR', 'TE']:
                base_stats.update({
                    'stat_type': 'receiving',
                    'receiving_yards': random.randint(30, 150),
                    'receptions': random.randint(2, 12),
                    'targets': random.randint(3, 15),
                    'receiving_touchdowns': random.randint(0, 2)
                })
                # Ensure receptions <= targets
                if base_stats['receptions'] > base_stats['targets']:
                    base_stats['targets'] = base_stats['receptions']
            
            else:  # RB
                stat_type = random.choice(['rushing', 'receiving'])
                base_stats['stat_type'] = stat_type
                
                if stat_type == 'rushing':
                    base_stats.update({
                        'rushing_yards': random.randint(40, 200),
                        'rushing_attempts': random.randint(10, 30),
                        'rushing_touchdowns': random.randint(0, 3)
                    })
                else:
                    base_stats.update({
                        'receiving_yards': random.randint(20, 80),
                        'receptions': random.randint(2, 8),
                        'targets': random.randint(3, 10),
                        'receiving_touchdowns': random.randint(0, 1)
                    })
                    # Ensure receptions <= targets
                    if base_stats['receptions'] > base_stats['targets']:
                        base_stats['targets'] = base_stats['receptions']
            
            sample_data.append(base_stats)
        
        return sample_data


class DatabaseTester:
    """Comprehensive testing suite for database operations."""
    
    def __init__(self):
        """Initialize the database tester."""
        self.loader = SampleDataLoader()
        self.validator = DataValidator(strict_mode=False) if DATABASE_MODULES_AVAILABLE else None
        self.test_results = {
            'direct_insertion': {'passed': 0, 'failed': 0, 'errors': []},
            'batch_insertion': {'passed': 0, 'failed': 0, 'errors': []},
            'upsert_operations': {'passed': 0, 'failed': 0, 'errors': []},
            'validation': {'passed': 0, 'failed': 0, 'errors': []},
            'data_integrity': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def test_direct_insertion(self) -> bool:
        """Test direct insertion functions."""
        if not DATABASE_MODULES_AVAILABLE:
            logger.warning("Database modules not available - skipping direct insertion tests")
            return False
        
        logger.info("🔬 Testing direct insertion functions...")
        
        try:
            # Test prop line insertion
            sample_props = self.loader.create_sample_prop_lines(5)
            
            with cursor_context() as cursor:
                for prop_data in sample_props:
                    try:
                        result = insert_prop_line(cursor, prop_data)
                        if result and result.get('success'):
                            self.test_results['direct_insertion']['passed'] += 1
                            logger.info(f"✅ Inserted prop line for {prop_data['player_name']}")
                        else:
                            self.test_results['direct_insertion']['failed'] += 1
                            error_msg = f"Failed to insert prop line for {prop_data['player_name']}"
                            self.test_results['direct_insertion']['errors'].append(error_msg)
                            logger.error(f"❌ {error_msg}")
                    except Exception as e:
                        self.test_results['direct_insertion']['failed'] += 1
                        error_msg = f"Exception inserting prop line: {e}"
                        self.test_results['direct_insertion']['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
            
            # Test player stats insertion
            sample_stats = self.loader.create_sample_player_stats(5)
            
            with cursor_context() as cursor:
                for stats_data in sample_stats:
                    try:
                        result = insert_player_stats(cursor, stats_data)
                        if result and result.get('success'):
                            self.test_results['direct_insertion']['passed'] += 1
                            logger.info(f"✅ Inserted player stats for {stats_data['player_name']}")
                        else:
                            self.test_results['direct_insertion']['failed'] += 1
                            error_msg = f"Failed to insert player stats for {stats_data['player_name']}"
                            self.test_results['direct_insertion']['errors'].append(error_msg)
                            logger.error(f"❌ {error_msg}")
                    except Exception as e:
                        self.test_results['direct_insertion']['failed'] += 1
                        error_msg = f"Exception inserting player stats: {e}"
                        self.test_results['direct_insertion']['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Direct insertion test failed: {e}")
            self.test_results['direct_insertion']['errors'].append(str(e))
            return False
    
    def test_batch_insertion(self) -> bool:
        """Test batch insertion functions."""
        if not DATABASE_MODULES_AVAILABLE:
            logger.warning("Database modules not available - skipping batch insertion tests")
            return False
        
        logger.info("🔬 Testing batch insertion functions...")
        
        try:
            # Test batch prop line insertion
            sample_props = self.loader.create_sample_prop_lines(20)
            
            with batch_transaction() as transaction:
                result = batch_insert_prop_lines(transaction, sample_props)
                if result.success:
                    self.test_results['batch_insertion']['passed'] += result.inserted_count
                    logger.info(f"✅ Batch inserted {result.inserted_count} prop lines")
                else:
                    self.test_results['batch_insertion']['failed'] += len(sample_props)
                    error_msg = f"Batch prop line insertion failed: {result.errors}"
                    self.test_results['batch_insertion']['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            # Test batch player stats insertion
            sample_stats = self.loader.create_sample_player_stats(20)
            
            with batch_transaction() as transaction:
                result = batch_insert_player_stats(transaction, sample_stats)
                if result.success:
                    self.test_results['batch_insertion']['passed'] += result.inserted_count
                    logger.info(f"✅ Batch inserted {result.inserted_count} player stats")
                else:
                    self.test_results['batch_insertion']['failed'] += len(sample_stats)
                    error_msg = f"Batch player stats insertion failed: {result.errors}"
                    self.test_results['batch_insertion']['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Batch insertion test failed: {e}")
            self.test_results['batch_insertion']['errors'].append(str(e))
            return False
    
    def test_validation_functions(self) -> bool:
        """Test validation functions with various data quality scenarios."""
        if not self.validator:
            logger.warning("Validator not available - skipping validation tests")
            return False
        
        logger.info("🔬 Testing validation functions...")
        
        # Test valid data
        valid_prop = {
            'player_id': 'test_valid_player',
            'player_name': 'Test Player',
            'team': 'KC',
            'opponent': 'DET',
            'position': 'QB',
            'stat_type': 'Pass Yards',
            'line_score': 285.5,
            'league': 'nfl',
            'source': 'PrizePicks',
            'season': 2023
        }
        
        try:
            report = self.validator.validate_prop_line(valid_prop)
            if report.is_valid:
                self.test_results['validation']['passed'] += 1
                logger.info("✅ Valid data passed validation")
            else:
                self.test_results['validation']['failed'] += 1
                error_msg = f"Valid data failed validation: {report.get_errors()}"
                self.test_results['validation']['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        except Exception as e:
            self.test_results['validation']['failed'] += 1
            error_msg = f"Validation test exception: {e}"
            self.test_results['validation']['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        # Test invalid data
        invalid_prop = {
            'player_id': '',  # Empty
            'player_name': 'Unknown',  # Placeholder
            'team': 'X',  # Too short
            'position': 'INVALID',  # Invalid position
            'stat_type': '',  # Empty
            'line_score': -10,  # Negative
            'league': 'xyz',  # Invalid league
            'season': 1999  # Too old
        }
        
        try:
            report = self.validator.validate_prop_line(invalid_prop)
            if not report.is_valid and len(report.get_errors()) > 0:
                self.test_results['validation']['passed'] += 1
                logger.info(f"✅ Invalid data correctly rejected ({len(report.get_errors())} errors)")
            else:
                self.test_results['validation']['failed'] += 1
                error_msg = "Invalid data incorrectly passed validation"
                self.test_results['validation']['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        except Exception as e:
            self.test_results['validation']['failed'] += 1
            error_msg = f"Invalid data validation exception: {e}"
            self.test_results['validation']['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return True
    
    def test_real_data_loading(self) -> bool:
        """Test loading and processing real parsed data files."""
        logger.info("🔬 Testing real data file loading...")
        
        available_files = self.loader.get_available_data_files()
        
        for data_type, files in available_files.items():
            if not files:
                logger.warning(f"No {data_type} files available for testing")
                continue
            
            try:
                sample_data = self.loader.load_sample_data(data_type, max_records=10)
                if sample_data:
                    self.test_results['data_integrity']['passed'] += len(sample_data)
                    logger.info(f"✅ Successfully loaded {len(sample_data)} {data_type} records")
                    
                    # Validate a few sample records if validator is available
                    if self.validator and len(sample_data) > 0:
                        sample_record = sample_data[0]
                        
                        if data_type == 'prizepicks':
                            report = self.validator.validate_prop_line(sample_record)
                        elif 'nfl_boxscore' in data_type:
                            report = self.validator.validate_player_stats(sample_record)
                        else:
                            continue  # Skip validation for other types for now
                        
                        if report.is_valid:
                            logger.info(f"✅ {data_type} data passed validation")
                        else:
                            logger.warning(f"⚠️ {data_type} data validation issues: {len(report.get_errors())} errors, {len(report.get_warnings())} warnings")
                else:
                    self.test_results['data_integrity']['failed'] += 1
                    error_msg = f"Failed to load {data_type} data"
                    self.test_results['data_integrity']['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    
            except Exception as e:
                self.test_results['data_integrity']['failed'] += 1
                error_msg = f"Exception loading {data_type} data: {e}"
                self.test_results['data_integrity']['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        return True
    
    def test_query_validation(self) -> bool:
        """Test query validation functions to verify data integrity."""
        if not DATABASE_MODULES_AVAILABLE:
            logger.warning("Database modules not available - skipping query validation tests")
            return False
        
        logger.info("🔬 Testing query validation functions...")
        
        try:
            with cursor_context() as cursor:
                # Test basic table existence
                table_queries = {
                    'prop_lines': "SELECT COUNT(*) FROM prop_lines",
                    'player_stats': "SELECT COUNT(*) FROM player_stats", 
                    'games_processed': "SELECT COUNT(*) FROM games_processed",
                    'players': "SELECT COUNT(*) FROM players",
                    'teams': "SELECT COUNT(*) FROM teams"
                }
                
                for table_name, query in table_queries.items():
                    try:
                        cursor.execute(query)
                        count = cursor.fetchone()[0]
                        self.test_results['data_integrity']['passed'] += 1
                        logger.info(f"✅ Table {table_name} accessible, {count} records")
                    except Exception as e:
                        self.test_results['data_integrity']['failed'] += 1
                        error_msg = f"Failed to query {table_name}: {e}"
                        self.test_results['data_integrity']['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
                
                # Test data quality queries
                quality_queries = {
                    'duplicate_player_ids': """
                        SELECT player_id, COUNT(*) as cnt 
                        FROM prop_lines 
                        GROUP BY player_id, stat_type, season, source 
                        HAVING COUNT(*) > 1
                    """,
                    'missing_required_fields': """
                        SELECT COUNT(*) 
                        FROM prop_lines 
                        WHERE player_name IS NULL OR team IS NULL OR stat_type IS NULL
                    """,
                    'invalid_seasons': """
                        SELECT COUNT(*) 
                        FROM prop_lines 
                        WHERE season < 2000 OR season > 2030
                    """,
                    'statistical_consistency': """
                        SELECT COUNT(*) 
                        FROM player_stats 
                        WHERE (completions > attempts AND completions IS NOT NULL AND attempts IS NOT NULL)
                           OR (receptions > targets AND receptions IS NOT NULL AND targets IS NOT NULL)
                    """
                }
                
                for check_name, query in quality_queries.items():
                    try:
                        cursor.execute(query)
                        result = cursor.fetchall()
                        
                        if check_name in ['duplicate_player_ids', 'missing_required_fields', 'invalid_seasons', 'statistical_consistency']:
                            # These should return 0 or empty results for good data quality
                            if not result or (len(result) == 1 and result[0][0] == 0):
                                self.test_results['data_integrity']['passed'] += 1
                                logger.info(f"✅ Data quality check '{check_name}': PASSED")
                            else:
                                self.test_results['data_integrity']['failed'] += 1
                                error_msg = f"Data quality issue in '{check_name}': {result}"
                                self.test_results['data_integrity']['errors'].append(error_msg)
                                logger.warning(f"⚠️ {error_msg}")
                        
                    except Exception as e:
                        self.test_results['data_integrity']['failed'] += 1
                        error_msg = f"Query validation failed for {check_name}: {e}"
                        self.test_results['data_integrity']['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Query validation test failed: {e}")
            self.test_results['data_integrity']['errors'].append(str(e))
            return False
    
    def test_data_consistency(self) -> bool:
        """Test data consistency between related tables."""
        if not DATABASE_MODULES_AVAILABLE:
            logger.warning("Database modules not available - skipping data consistency tests")
            return False
        
        logger.info("🔬 Testing data consistency between tables...")
        
        try:
            with cursor_context() as cursor:
                # Test referential integrity (without foreign keys enforced)
                consistency_queries = {
                    'player_refs_in_stats': """
                        SELECT COUNT(DISTINCT ps.player_id) as stats_players,
                               COUNT(DISTINCT p.player_id) as ref_players
                        FROM player_stats ps
                        LEFT JOIN players p ON ps.player_id = p.player_id
                    """,
                    'team_consistency': """
                        SELECT COUNT(*) 
                        FROM prop_lines pl
                        WHERE pl.team != pl.opponent 
                        AND pl.team IS NOT NULL 
                        AND pl.opponent IS NOT NULL
                    """,
                    'season_alignment': """
                        SELECT COUNT(*) 
                        FROM player_stats ps
                        JOIN prop_lines pl ON ps.player_id = pl.player_id
                        WHERE ps.season = pl.season
                    """
                }
                
                for check_name, query in consistency_queries.items():
                    try:
                        cursor.execute(query)
                        result = cursor.fetchall()
                        self.test_results['data_integrity']['passed'] += 1
                        logger.info(f"✅ Consistency check '{check_name}': {result}")
                    except Exception as e:
                        self.test_results['data_integrity']['failed'] += 1
                        error_msg = f"Consistency check failed for {check_name}: {e}"
                        self.test_results['data_integrity']['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data consistency test failed: {e}")
            self.test_results['data_integrity']['errors'].append(str(e))
            return False
    
    def test_performance_baseline(self) -> bool:
        """Test performance baseline for batch insertions."""
        if not DATABASE_MODULES_AVAILABLE:
            logger.warning("Database modules not available - skipping performance tests")
            return False
        
        logger.info("🔬 Testing performance baseline (1000+ records)...")
        
        try:
            # Generate large dataset
            large_prop_dataset = self.loader.create_sample_prop_lines(1000)
            large_stats_dataset = self.loader.create_sample_player_stats(1000)
            
            # Test prop lines insertion performance
            start_time = datetime.now()
            
            with batch_transaction() as transaction:
                result = batch_insert_prop_lines(transaction, large_prop_dataset)
                
            prop_duration = (datetime.now() - start_time).total_seconds()
            
            if result.success and prop_duration < 10.0:
                self.test_results['batch_insertion']['passed'] += 1
                logger.info(f"✅ Prop lines performance: {result.inserted_count} records in {prop_duration:.2f}s")
            else:
                self.test_results['batch_insertion']['failed'] += 1
                error_msg = f"Prop lines performance failed: {prop_duration:.2f}s for {result.inserted_count if result.success else 0} records"
                self.test_results['batch_insertion']['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
            
            # Test player stats insertion performance
            start_time = datetime.now()
            
            with batch_transaction() as transaction:
                result = batch_insert_player_stats(transaction, large_stats_dataset)
                
            stats_duration = (datetime.now() - start_time).total_seconds()
            
            if result.success and stats_duration < 10.0:
                self.test_results['batch_insertion']['passed'] += 1
                logger.info(f"✅ Player stats performance: {result.inserted_count} records in {stats_duration:.2f}s")
            else:
                self.test_results['batch_insertion']['failed'] += 1
                error_msg = f"Player stats performance failed: {stats_duration:.2f}s for {result.inserted_count if result.success else 0} records"
                self.test_results['batch_insertion']['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance baseline test failed: {e}")
            self.test_results['batch_insertion']['errors'].append(str(e))
            return False
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all available tests and return comprehensive results."""
        logger.info("🧪 Starting comprehensive database testing suite...")
        logger.info("=" * 60)
        
        # Run all test categories
        self.test_validation_functions()
        self.test_real_data_loading()
        
        if DATABASE_MODULES_AVAILABLE:
            self.test_direct_insertion()
            self.test_batch_insertion()
            self.test_query_validation()
            self.test_data_consistency()
            self.test_performance_baseline()
        else:
            logger.warning("⚠️ Skipping database insertion tests (psycopg2 not available)")
        
        # Generate summary
        total_passed = sum(result['passed'] for result in self.test_results.values())
        total_failed = sum(result['failed'] for result in self.test_results.values())
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'success_rate': success_rate,
            'details': self.test_results,
            'database_available': DATABASE_MODULES_AVAILABLE
        }
        
        # Print summary
        logger.info("\n📊 TEST SUMMARY")
        logger.info("-" * 30)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {total_passed}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Database Modules Available: {DATABASE_MODULES_AVAILABLE}")
        
        if total_failed > 0:
            logger.info("\n❌ FAILED TEST DETAILS:")
            for test_type, results in self.test_results.items():
                if results['failed'] > 0:
                    logger.info(f"  {test_type}: {results['failed']} failures")
                    for error in results['errors'][:3]:  # Show first 3 errors
                        logger.info(f"    • {error}")
        
        logger.info("\n🎉 Comprehensive testing complete!")
        
        return summary


def test_all_insertions():
    """Main function to run all database tests."""
    tester = DatabaseTester()
    return tester.run_comprehensive_tests()


def load_sample_prizepicks_data(max_records: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to load sample PrizePicks data."""
    loader = SampleDataLoader()
    return loader.load_sample_data('prizepicks', max_records)


def load_sample_nfl_boxscore_data(max_records: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to load sample NFL boxscore data."""
    loader = SampleDataLoader()
    return loader.load_sample_data('nfl_boxscore', max_records)


if __name__ == "__main__":
    """Run comprehensive database testing when module is executed directly."""
    results = test_all_insertions()
    
    if results['success_rate'] >= 80:
        print("\n🎉 Database testing PASSED!")
        exit(0)
    else:
        print(f"\n❌ Database testing FAILED (success rate: {results['success_rate']:.1f}%)")
        exit(1)