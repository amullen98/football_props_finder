"""
Parser Integration Module

This module provides integration between the existing parsers and the database
insertion functions. It routes parsed JSON data to appropriate database tables
with intelligent data mapping and error handling.

Features:
- Automatic routing of parsed data to correct tables
- Data transformation and mapping
- Batch processing integration
- Error handling and reporting
- Support for all existing parsers
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

from .insert import (
    insert_prop_line, insert_player_stats, insert_game_processed,
    insert_player, insert_team, upsert_prop_line, upsert_player_stats,
    upsert_game_processed, upsert_player, upsert_team, InsertError
)
from .batch import (
    batch_insert_prop_lines, batch_insert_player_stats,
    batch_insert_games_processed, batch_insert_mixed_data,
    BatchInsertResult, BatchInsertError
)
from .connection import get_connection_manager, PSYCOPG2_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParserIntegrationError(Exception):
    """Custom exception for parser integration errors."""
    pass


class DataRouter:
    """Routes parsed data to appropriate database tables."""
    
    def __init__(self, use_upsert: bool = True, batch_size: int = 1000):
        """
        Initialize data router.
        
        Args:
            use_upsert: Whether to use upsert functions (handles duplicates)
            batch_size: Batch size for bulk operations
        """
        self.use_upsert = use_upsert
        self.batch_size = batch_size
        self.connection_manager = get_connection_manager()
    
    def route_prizepicks_data(self, parsed_data: List[Dict[str, Any]], 
                             connection=None) -> BatchInsertResult:
        """
        Route PrizePicks parsed data to prop_lines table.
        
        Args:
            parsed_data: List of parsed PrizePicks projections
            connection: Optional database connection
            
        Returns:
            BatchInsertResult with operation details
        """
        logger.info(f"Routing {len(parsed_data)} PrizePicks records to prop_lines table")
        
        try:
            # Transform data for prop_lines table if needed
            transformed_data = []
            for record in parsed_data:
                # PrizePicks data should already match prop_lines schema
                transformed_record = {
                    'player_id': record.get('player_id'),
                    'player_name': record.get('player'),  # Note: 'player' field maps to 'player_name'
                    'team': record.get('team'),
                    'opponent': record.get('opponent'),
                    'position': record.get('position'),
                    'stat_type': record.get('stat_type'),
                    'line_score': record.get('line_score'),
                    'game_time': record.get('game_time'),
                    'league': record.get('league'),
                    'source': record.get('source', 'PrizePicks'),
                    'odds_type': record.get('odds_type', 'standard'),
                    'season': record.get('season'),
                    'projection_id': record.get('projection_id')
                }
                
                # Only add records with required fields
                if all(transformed_record.get(field) for field in 
                      ['player_id', 'player_name', 'team', 'position', 'stat_type', 'league', 'season']):
                    transformed_data.append(transformed_record)
                else:
                    logger.warning(f"Skipping incomplete PrizePicks record: {record}")
            
            # Batch insert
            return batch_insert_prop_lines(
                transformed_data, 
                connection=connection, 
                chunk_size=self.batch_size
            )
            
        except Exception as e:
            logger.error(f"Failed to route PrizePicks data: {e}")
            raise ParserIntegrationError(f"PrizePicks routing failed: {e}") from e
    
    def route_nfl_boxscore_data(self, parsed_data: List[Dict[str, Any]], 
                               connection=None) -> BatchInsertResult:
        """
        Route NFL boxscore parsed data to player_stats table.
        
        Args:
            parsed_data: List of parsed NFL boxscore player stats
            connection: Optional database connection
            
        Returns:
            BatchInsertResult with operation details
        """
        logger.info(f"Routing {len(parsed_data)} NFL boxscore records to player_stats table")
        
        try:
            # Transform data for player_stats table
            transformed_data = []
            for record in parsed_data:
                # NFL boxscore data should already match player_stats schema
                transformed_record = {
                    'player_id': record.get('player_id'),
                    'player_name': record.get('player'),
                    'team': record.get('team'),
                    'opponent': record.get('opponent'),
                    'position': record.get('position'),
                    'stat_type': record.get('stat_type'),
                    'game_id': record.get('game_id'),
                    'week': record.get('week'),
                    'game_date': record.get('game_date'),
                    'season': record.get('season'),
                    'league': record.get('league', 'nfl'),
                    'source': record.get('source', 'RapidAPI'),
                    
                    # Position-specific stats
                    'passing_yards': record.get('passing_yards'),
                    'completions': record.get('completions'),
                    'attempts': record.get('attempts'),
                    'passing_touchdowns': record.get('passing_touchdowns'),
                    'interceptions': record.get('interceptions'),
                    'sacks': record.get('sacks'),
                    'sack_yards_lost': record.get('sack_yards_lost'),
                    'receiving_yards': record.get('receiving_yards'),
                    'receptions': record.get('receptions'),
                    'targets': record.get('targets'),
                    'receiving_touchdowns': record.get('receiving_touchdowns'),
                    'rushing_yards': record.get('rushing_yards'),
                    'rushing_attempts': record.get('rushing_attempts'),
                    'rushing_touchdowns': record.get('rushing_touchdowns')
                }
                
                # Only add records with required fields
                if all(transformed_record.get(field) for field in 
                      ['player_id', 'player_name', 'team', 'position', 'stat_type', 'game_id', 'season']):
                    transformed_data.append(transformed_record)
                else:
                    logger.warning(f"Skipping incomplete NFL boxscore record: {record}")
            
            # Batch insert
            return batch_insert_player_stats(
                transformed_data,
                connection=connection,
                chunk_size=self.batch_size
            )
            
        except Exception as e:
            logger.error(f"Failed to route NFL boxscore data: {e}")
            raise ParserIntegrationError(f"NFL boxscore routing failed: {e}") from e
    
    def route_cfb_stats_data(self, parsed_data: List[Dict[str, Any]], 
                            connection=None) -> BatchInsertResult:
        """
        Route College Football parsed data to player_stats table.
        
        Args:
            parsed_data: List of parsed CFB player stats
            connection: Optional database connection
            
        Returns:
            BatchInsertResult with operation details
        """
        logger.info(f"Routing {len(parsed_data)} CFB stats records to player_stats table")
        
        try:
            # Transform data for player_stats table
            transformed_data = []
            for record in parsed_data:
                # CFB data should already match player_stats schema
                transformed_record = {
                    'player_id': record.get('player_id'),
                    'player_name': record.get('player'),
                    'team': record.get('team'),
                    'opponent': record.get('opponent'),
                    'position': record.get('position'),
                    'stat_type': record.get('stat_type'),
                    'game_id': record.get('game_id', f"cfb_{record.get('season', 2023)}_w{record.get('week', 1)}_{record.get('team', 'unk').lower()}"),
                    'week': record.get('week'),
                    'game_date': record.get('start_time'),  # CFB uses 'start_time'
                    'season': record.get('season'),
                    'league': record.get('league', 'college'),
                    'source': record.get('source', 'CollegeFootballData'),
                    
                    # Position-specific stats
                    'passing_yards': record.get('passing_yards'),
                    'completions': record.get('completions'),
                    'attempts': record.get('attempts'),
                    'passing_touchdowns': record.get('passing_touchdowns'),
                    'interceptions': record.get('interceptions'),
                    'receiving_yards': record.get('receiving_yards'),
                    'receptions': record.get('receptions'),
                    'receiving_touchdowns': record.get('receiving_touchdowns'),
                    'rushing_yards': record.get('rushing_yards'),
                    'rushing_attempts': record.get('rushing_attempts'),
                    'rushing_touchdowns': record.get('rushing_touchdowns')
                }
                
                # Only add records with required fields
                if all(transformed_record.get(field) for field in 
                      ['player_id', 'player_name', 'team', 'position', 'stat_type', 'season']):
                    transformed_data.append(transformed_record)
                else:
                    logger.warning(f"Skipping incomplete CFB record: {record}")
            
            # Batch insert
            return batch_insert_player_stats(
                transformed_data,
                connection=connection,
                chunk_size=self.batch_size
            )
            
        except Exception as e:
            logger.error(f"Failed to route CFB stats data: {e}")
            raise ParserIntegrationError(f"CFB stats routing failed: {e}") from e
    
    def route_nfl_game_ids_data(self, parsed_data: Dict[str, Any], 
                               connection=None) -> BatchInsertResult:
        """
        Route NFL game IDs parsed data to games_processed table.
        
        Args:
            parsed_data: Dictionary with game IDs, week, and year
            connection: Optional database connection
            
        Returns:
            BatchInsertResult with operation details
        """
        logger.info(f"Routing NFL game IDs data to games_processed table")
        
        try:
            # Transform game IDs data into games_processed records
            game_records = []
            week = parsed_data.get('week')
            year = parsed_data.get('year')
            game_ids = parsed_data.get('game_ids', [])
            
            for game_id in game_ids:
                game_record = {
                    'game_id': game_id,
                    'week': week,
                    'year': year,
                    'league': 'nfl',
                    'source': 'RapidAPI',
                    'game_type': 2  # Regular season
                }
                game_records.append(game_record)
            
            # Batch insert
            return batch_insert_games_processed(
                game_records,
                connection=connection,
                chunk_size=self.batch_size
            )
            
        except Exception as e:
            logger.error(f"Failed to route NFL game IDs data: {e}")
            raise ParserIntegrationError(f"NFL game IDs routing failed: {e}") from e


def load_and_route_parsed_file(file_path: Union[str, Path], 
                              data_type: str,
                              use_upsert: bool = True,
                              batch_size: int = 1000,
                              connection=None) -> BatchInsertResult:
    """
    Load a parsed JSON file and route to appropriate database table.
    
    Args:
        file_path: Path to parsed JSON file
        data_type: Type of data ('prizepicks', 'nfl_boxscore', 'cfb_stats', 'nfl_game_ids')
        use_upsert: Whether to use upsert functions
        batch_size: Batch size for bulk operations
        connection: Optional database connection
        
    Returns:
        BatchInsertResult with operation details
        
    Raises:
        ParserIntegrationError: If file loading or routing fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ParserIntegrationError(f"Parsed file not found: {file_path}")
    
    try:
        # Load parsed data
        with open(file_path, 'r') as f:
            parsed_data = json.load(f)
        
        logger.info(f"Loaded {file_path} with {len(parsed_data) if isinstance(parsed_data, list) else 1} records")
        
        # Route to appropriate table
        router = DataRouter(use_upsert=use_upsert, batch_size=batch_size)
        
        if data_type == 'prizepicks':
            return router.route_prizepicks_data(parsed_data, connection)
        elif data_type == 'nfl_boxscore':
            return router.route_nfl_boxscore_data(parsed_data, connection)
        elif data_type == 'cfb_stats':
            return router.route_cfb_stats_data(parsed_data, connection)
        elif data_type == 'nfl_game_ids':
            return router.route_nfl_game_ids_data(parsed_data, connection)
        else:
            raise ParserIntegrationError(f"Unknown data type: {data_type}")
        
    except json.JSONDecodeError as e:
        raise ParserIntegrationError(f"Invalid JSON in file {file_path}: {e}") from e
    except Exception as e:
        if isinstance(e, ParserIntegrationError):
            raise
        raise ParserIntegrationError(f"Failed to load and route file {file_path}: {e}") from e


def bulk_load_parsed_directory(parsed_data_dir: Union[str, Path],
                              use_upsert: bool = True,
                              batch_size: int = 1000) -> Dict[str, List[BatchInsertResult]]:
    """
    Load all parsed files from parsed_data directory and route to database.
    
    Args:
        parsed_data_dir: Path to parsed_data directory
        use_upsert: Whether to use upsert functions
        batch_size: Batch size for bulk operations
        
    Returns:
        Dictionary mapping data types to list of BatchInsertResult objects
        
    Raises:
        ParserIntegrationError: If directory access or bulk loading fails
    """
    parsed_data_dir = Path(parsed_data_dir)
    
    if not parsed_data_dir.exists():
        raise ParserIntegrationError(f"Parsed data directory not found: {parsed_data_dir}")
    
    results = {
        'prizepicks': [],
        'nfl_boxscore': [],
        'cfb_stats': [],
        'nfl_game_ids': []
    }
    
    try:
        logger.info(f"Bulk loading parsed data from: {parsed_data_dir}")
        
        # Process PrizePicks data
        prizepicks_dir = parsed_data_dir / 'prizepicks'
        if prizepicks_dir.exists():
            for file in prizepicks_dir.glob('*_parsed.json'):
                try:
                    result = load_and_route_parsed_file(file, 'prizepicks', use_upsert, batch_size)
                    results['prizepicks'].append(result)
                    logger.info(f"✅ {file.name}: {result}")
                except Exception as e:
                    logger.error(f"❌ {file.name}: {e}")
        
        # Process NFL boxscore data
        nfl_boxscore_dir = parsed_data_dir / 'nfl_boxscore'
        if nfl_boxscore_dir.exists():
            for file in nfl_boxscore_dir.glob('*_parsed.json'):
                try:
                    result = load_and_route_parsed_file(file, 'nfl_boxscore', use_upsert, batch_size)
                    results['nfl_boxscore'].append(result)
                    logger.info(f"✅ {file.name}: {result}")
                except Exception as e:
                    logger.error(f"❌ {file.name}: {e}")
        
        # Process CFB stats data
        cfb_stats_dir = parsed_data_dir / 'cfb_stats'
        if cfb_stats_dir.exists():
            for file in cfb_stats_dir.glob('*_parsed.json'):
                try:
                    result = load_and_route_parsed_file(file, 'cfb_stats', use_upsert, batch_size)
                    results['cfb_stats'].append(result)
                    logger.info(f"✅ {file.name}: {result}")
                except Exception as e:
                    logger.error(f"❌ {file.name}: {e}")
        
        # Process NFL game IDs data
        nfl_stats_dir = parsed_data_dir / 'nfl_stats'
        if nfl_stats_dir.exists():
            for file in nfl_stats_dir.glob('*_parsed.json'):
                try:
                    result = load_and_route_parsed_file(file, 'nfl_game_ids', use_upsert, batch_size)
                    results['nfl_game_ids'].append(result)
                    logger.info(f"✅ {file.name}: {result}")
                except Exception as e:
                    logger.error(f"❌ {file.name}: {e}")
        
        # Summary
        total_files = sum(len(file_results) for file_results in results.values())
        total_records = sum(
            sum(result.successful_records for result in file_results) 
            for file_results in results.values()
        )
        
        logger.info(f"Bulk load completed: {total_files} files, {total_records} records inserted")
        
        return results
        
    except Exception as e:
        logger.error(f"Bulk load failed: {e}")
        raise ParserIntegrationError(f"Bulk load failed: {e}") from e


if __name__ == "__main__":
    """Test the parser integration functionality."""
    
    print("🔌 Football Props Finder - Parser Integration")
    print("=" * 55)
    
    # Test data routing
    print("\n1. Testing data router...")
    router = DataRouter(use_upsert=True, batch_size=2)
    
    # Test PrizePicks data
    test_prizepicks = [
        {
            'player_id': 'test_pp_1',
            'player': 'Test Player 1',
            'team': 'KC',
            'opponent': 'DET',
            'position': 'QB',
            'stat_type': 'Pass Yards',
            'line_score': 285.5,
            'league': 'nfl',
            'season': 2023,
            'source': 'PrizePicks',
            'projection_id': 'pp_test_1'
        }
    ]
    
    try:
        result = router.route_prizepicks_data(test_prizepicks)
        print(f"✅ PrizePicks routing: {result}")
    except Exception as e:
        print(f"❌ PrizePicks routing failed: {e}")
    
    # Test NFL boxscore data
    test_nfl_boxscore = [
        {
            'player_id': 'test_nfl_1',
            'player': 'Test Player 1',
            'team': 'KC',
            'opponent': 'DET',
            'position': 'QB',
            'stat_type': 'passing',
            'passing_yards': 295,
            'completions': 24,
            'attempts': 35,
            'game_id': 'test_game_1',
            'week': 1,
            'season': 2023,
            'league': 'nfl',
            'source': 'RapidAPI'
        }
    ]
    
    try:
        result = router.route_nfl_boxscore_data(test_nfl_boxscore)
        print(f"✅ NFL boxscore routing: {result}")
    except Exception as e:
        print(f"❌ NFL boxscore routing failed: {e}")
    
    # Test NFL game IDs data
    test_game_ids = {
        'week': 1,
        'year': 2023,
        'game_ids': ['test_game_1', 'test_game_2']
    }
    
    try:
        result = router.route_nfl_game_ids_data(test_game_ids)
        print(f"✅ NFL game IDs routing: {result}")
    except Exception as e:
        print(f"❌ NFL game IDs routing failed: {e}")
    
    print("\n2. Testing file loading...")
    # Test would require actual parsed files
    print("✅ File loading functions available (requires actual parsed files to test)")
    
    print("\n3. Testing bulk directory loading...")
    print("✅ Bulk loading functions available (requires parsed_data directory to test)")
    
    print("\n🎉 Parser integration testing complete!")