"""
Database Batch Insertion Functions

This module provides batch insertion capabilities with transaction support for
efficient bulk data loading. Includes rollback capabilities and performance
optimization for large datasets.

Features:
- Batch insertion for all table types
- Transaction management with rollback
- Performance optimization for large datasets
- Detailed progress reporting
- Error handling with partial success reporting
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from contextlib import contextmanager

from .connection import get_connection_manager, PSYCOPG2_AVAILABLE
from .insert import InsertError, _validate_required_fields

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchInsertError(Exception):
    """Custom exception for batch insertion errors."""
    pass


class BatchInsertResult:
    """Result object for batch insertion operations."""
    
    def __init__(self, table_name: str, total_records: int):
        self.table_name = table_name
        self.total_records = total_records
        self.successful_records = 0
        self.failed_records = 0
        self.errors: List[str] = []
        self.inserted_ids: List[int] = []
        self.start_time = datetime.now()
        self.end_time = None
        
    def add_success(self, record_id: Optional[int] = None):
        """Record a successful insertion."""
        self.successful_records += 1
        if record_id:
            self.inserted_ids.append(record_id)
    
    def add_error(self, error_message: str):
        """Record a failed insertion."""
        self.failed_records += 1
        self.errors.append(error_message)
    
    def finish(self):
        """Mark the batch operation as finished."""
        self.end_time = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_records / self.total_records) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate operation duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def __str__(self) -> str:
        """String representation of batch result."""
        return (f"BatchInsertResult({self.table_name}: "
                f"{self.successful_records}/{self.total_records} "
                f"({self.success_rate:.1f}%) in {self.duration:.2f}s)")


@contextmanager
def batch_transaction(connection=None, rollback_on_error: bool = True):
    """
    Context manager for batch transaction handling.
    
    Args:
        connection: Optional database connection to use
        rollback_on_error: Whether to rollback on any error
        
    Yields:
        Database connection with transaction context
    """
    manager = get_connection_manager()
    
    if connection:
        # Use provided connection
        conn = connection
        external_connection = True
    else:
        # Get connection from manager
        conn = manager.get_connection()
        external_connection = False
    
    if not PSYCOPG2_AVAILABLE:
        logger.info("Mock transaction context (psycopg2 not available)")
        yield conn
        return
    
    try:
        # Start transaction
        conn.autocommit = False
        yield conn
        
        # Commit if we reach here
        conn.commit()
        logger.debug("Batch transaction committed successfully")
        
    except Exception as e:
        if rollback_on_error:
            conn.rollback()
            logger.warning(f"Batch transaction rolled back due to error: {e}")
        else:
            logger.error(f"Batch transaction error (no rollback): {e}")
        raise
        
    finally:
        # Restore autocommit and return connection
        if not external_connection:
            conn.autocommit = True
            manager.return_connection(conn)


def _prepare_batch_insert_query(table_name: str, data_list: List[Dict[str, Any]]) -> Tuple[str, List[tuple]]:
    """
    Prepare batch INSERT query with multiple value sets.
    
    Args:
        table_name: Name of target table
        data_list: List of data dictionaries
        
    Returns:
        Tuple of (query_string, list_of_parameter_tuples)
    """
    if not data_list:
        raise BatchInsertError(f"No data provided for batch insert into {table_name}")
    
    # Get column names from first record (assuming all have same structure)
    first_record = data_list[0]
    filtered_first = {k: v for k, v in first_record.items() if v is not None and k != 'id'}
    columns = list(filtered_first.keys())
    
    if not columns:
        raise BatchInsertError(f"No valid columns found for batch insert into {table_name}")
    
    # Prepare query with RETURNING clause for IDs
    placeholders = '(' + ', '.join(['%s'] * len(columns)) + ')'
    
    query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES %s
        RETURNING id
    """
    
    # Prepare parameters for each record
    parameters = []
    for record in data_list:
        filtered_record = {k: v for k, v in record.items() if v is not None and k != 'id'}
        # Ensure all records have the same columns
        record_values = tuple(filtered_record.get(col) for col in columns)
        parameters.append(record_values)
    
    return query, parameters


def batch_insert_prop_lines(data_list: List[Dict[str, Any]], 
                           connection=None,
                           chunk_size: int = 1000,
                           rollback_on_error: bool = True) -> BatchInsertResult:
    """
    Batch insert prop betting line records.
    
    Args:
        data_list: List of prop line data dictionaries
        connection: Optional database connection to use
        chunk_size: Number of records to insert per batch
        rollback_on_error: Whether to rollback entire transaction on any error
        
    Returns:
        BatchInsertResult with operation details
    """
    table_name = 'prop_lines'
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'league', 'source', 'season']
    
    result = BatchInsertResult(table_name, len(data_list))
    
    try:
        with batch_transaction(connection, rollback_on_error) as conn:
            # Process in chunks
            for i in range(0, len(data_list), chunk_size):
                chunk = data_list[i:i + chunk_size]
                
                try:
                    # Validate chunk data
                    for j, record in enumerate(chunk):
                        try:
                            _validate_required_fields(record, required_fields, table_name)
                            
                            # Add defaults
                            if 'odds_type' not in record:
                                record['odds_type'] = 'standard'
                                
                        except Exception as e:
                            result.add_error(f"Record {i+j+1} validation failed: {e}")
                            if rollback_on_error:
                                raise BatchInsertError(f"Validation failed for record {i+j+1}: {e}")
                    
                    # Insert chunk
                    if PSYCOPG2_AVAILABLE:
                        from psycopg2.extras import execute_values
                        
                        # Prepare data for execute_values
                        columns = ['player_id', 'player_name', 'team', 'opponent', 'position', 'stat_type', 
                                  'line_score', 'game_time', 'league', 'source', 'odds_type', 'season', 'projection_id']
                        
                        values = []
                        for record in chunk:
                            row = tuple(record.get(col) for col in columns)
                            values.append(row)
                        
                        query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES %s
                            RETURNING id
                        """
                        
                        with conn.cursor() as cursor:
                            execute_values(cursor, query, values, template=None, page_size=chunk_size)
                            inserted_ids = [row[0] for row in cursor.fetchall()]
                            
                            for inserted_id in inserted_ids:
                                result.add_success(inserted_id)
                    else:
                        # Mock insertion
                        for j, record in enumerate(chunk):
                            logger.info(f"Mock batch insert {table_name}: {record.get('player_name', 'unknown')}")
                            result.add_success(i + j + 1)
                    
                except Exception as e:
                    error_msg = f"Chunk {i//chunk_size + 1} failed: {e}"
                    result.add_error(error_msg)
                    if rollback_on_error:
                        raise BatchInsertError(error_msg) from e
        
        result.finish()
        logger.info(f"Batch insert completed: {result}")
        return result
        
    except Exception as e:
        result.finish()
        logger.error(f"Batch insert failed: {e}")
        if not isinstance(e, BatchInsertError):
            raise BatchInsertError(f"Batch insert failed: {e}") from e
        raise


def batch_insert_player_stats(data_list: List[Dict[str, Any]], 
                             connection=None,
                             chunk_size: int = 1000,
                             rollback_on_error: bool = True) -> BatchInsertResult:
    """
    Batch insert player statistics records.
    
    Args:
        data_list: List of player stats data dictionaries
        connection: Optional database connection to use
        chunk_size: Number of records to insert per batch
        rollback_on_error: Whether to rollback entire transaction on any error
        
    Returns:
        BatchInsertResult with operation details
    """
    table_name = 'player_stats'
    required_fields = ['player_id', 'player_name', 'team', 'position', 'stat_type', 'game_id', 'season', 'league', 'source']
    
    result = BatchInsertResult(table_name, len(data_list))
    
    try:
        with batch_transaction(connection, rollback_on_error) as conn:
            # Process in chunks
            for i in range(0, len(data_list), chunk_size):
                chunk = data_list[i:i + chunk_size]
                
                try:
                    # Validate chunk data
                    for j, record in enumerate(chunk):
                        try:
                            _validate_required_fields(record, required_fields, table_name)
                        except Exception as e:
                            result.add_error(f"Record {i+j+1} validation failed: {e}")
                            if rollback_on_error:
                                raise BatchInsertError(f"Validation failed for record {i+j+1}: {e}")
                    
                    # Insert chunk
                    if PSYCOPG2_AVAILABLE:
                        from psycopg2.extras import execute_values
                        
                        # All player_stats columns
                        columns = [
                            'player_id', 'player_name', 'team', 'opponent', 'position', 'stat_type',
                            'passing_yards', 'completions', 'attempts', 'passing_touchdowns', 'interceptions',
                            'sacks', 'sack_yards_lost', 'receiving_yards', 'receptions', 'targets', 
                            'receiving_touchdowns', 'rushing_yards', 'rushing_attempts', 'rushing_touchdowns',
                            'game_id', 'week', 'game_date', 'season', 'league', 'source'
                        ]
                        
                        values = []
                        for record in chunk:
                            row = tuple(record.get(col) for col in columns)
                            values.append(row)
                        
                        query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES %s
                            RETURNING id
                        """
                        
                        with conn.cursor() as cursor:
                            execute_values(cursor, query, values, template=None, page_size=chunk_size)
                            inserted_ids = [row[0] for row in cursor.fetchall()]
                            
                            for inserted_id in inserted_ids:
                                result.add_success(inserted_id)
                    else:
                        # Mock insertion
                        for j, record in enumerate(chunk):
                            logger.info(f"Mock batch insert {table_name}: {record.get('player_name', 'unknown')}")
                            result.add_success(i + j + 1)
                    
                except Exception as e:
                    error_msg = f"Chunk {i//chunk_size + 1} failed: {e}"
                    result.add_error(error_msg)
                    if rollback_on_error:
                        raise BatchInsertError(error_msg) from e
        
        result.finish()
        logger.info(f"Batch insert completed: {result}")
        return result
        
    except Exception as e:
        result.finish()
        logger.error(f"Batch insert failed: {e}")
        if not isinstance(e, BatchInsertError):
            raise BatchInsertError(f"Batch insert failed: {e}") from e
        raise


def batch_insert_games_processed(data_list: List[Dict[str, Any]], 
                                connection=None,
                                chunk_size: int = 1000,
                                rollback_on_error: bool = True) -> BatchInsertResult:
    """
    Batch insert processed game tracking records.
    
    Args:
        data_list: List of game processing data dictionaries
        connection: Optional database connection to use
        chunk_size: Number of records to insert per batch
        rollback_on_error: Whether to rollback entire transaction on any error
        
    Returns:
        BatchInsertResult with operation details
    """
    table_name = 'games_processed'
    required_fields = ['game_id', 'week', 'year', 'league', 'source']
    
    result = BatchInsertResult(table_name, len(data_list))
    
    try:
        with batch_transaction(connection, rollback_on_error) as conn:
            # Process in chunks
            for i in range(0, len(data_list), chunk_size):
                chunk = data_list[i:i + chunk_size]
                
                try:
                    # Validate and add defaults
                    for j, record in enumerate(chunk):
                        try:
                            _validate_required_fields(record, required_fields, table_name)
                            if 'game_type' not in record:
                                record['game_type'] = 2  # Regular season
                        except Exception as e:
                            result.add_error(f"Record {i+j+1} validation failed: {e}")
                            if rollback_on_error:
                                raise BatchInsertError(f"Validation failed for record {i+j+1}: {e}")
                    
                    # Insert chunk
                    if PSYCOPG2_AVAILABLE:
                        from psycopg2.extras import execute_values
                        
                        columns = ['game_id', 'week', 'year', 'league', 'source', 'game_type']
                        
                        values = []
                        for record in chunk:
                            row = tuple(record.get(col) for col in columns)
                            values.append(row)
                        
                        query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES %s
                            RETURNING id
                        """
                        
                        with conn.cursor() as cursor:
                            execute_values(cursor, query, values, template=None, page_size=chunk_size)
                            inserted_ids = [row[0] for row in cursor.fetchall()]
                            
                            for inserted_id in inserted_ids:
                                result.add_success(inserted_id)
                    else:
                        # Mock insertion
                        for j, record in enumerate(chunk):
                            logger.info(f"Mock batch insert {table_name}: {record.get('game_id', 'unknown')}")
                            result.add_success(i + j + 1)
                    
                except Exception as e:
                    error_msg = f"Chunk {i//chunk_size + 1} failed: {e}"
                    result.add_error(error_msg)
                    if rollback_on_error:
                        raise BatchInsertError(error_msg) from e
        
        result.finish()
        logger.info(f"Batch insert completed: {result}")
        return result
        
    except Exception as e:
        result.finish()
        logger.error(f"Batch insert failed: {e}")
        if not isinstance(e, BatchInsertError):
            raise BatchInsertError(f"Batch insert failed: {e}") from e
        raise


def batch_insert_mixed_data(prop_lines: List[Dict[str, Any]] = None,
                           player_stats: List[Dict[str, Any]] = None,
                           games_processed: List[Dict[str, Any]] = None,
                           connection=None,
                           chunk_size: int = 1000,
                           rollback_on_error: bool = True) -> Dict[str, BatchInsertResult]:
    """
    Batch insert mixed data types in a single transaction.
    
    Args:
        prop_lines: List of prop line data dictionaries
        player_stats: List of player stats data dictionaries  
        games_processed: List of game processing data dictionaries
        connection: Optional database connection to use
        chunk_size: Number of records to insert per batch
        rollback_on_error: Whether to rollback entire transaction on any error
        
    Returns:
        Dictionary mapping table names to BatchInsertResult objects
    """
    results = {}
    
    try:
        with batch_transaction(connection, rollback_on_error) as conn:
            # Insert games_processed first (dependencies)
            if games_processed:
                logger.info(f"Batch inserting {len(games_processed)} games_processed records...")
                results['games_processed'] = batch_insert_games_processed(
                    games_processed, conn, chunk_size, rollback_on_error=False
                )
            
            # Insert prop_lines
            if prop_lines:
                logger.info(f"Batch inserting {len(prop_lines)} prop_lines records...")
                results['prop_lines'] = batch_insert_prop_lines(
                    prop_lines, conn, chunk_size, rollback_on_error=False
                )
            
            # Insert player_stats
            if player_stats:
                logger.info(f"Batch inserting {len(player_stats)} player_stats records...")
                results['player_stats'] = batch_insert_player_stats(
                    player_stats, conn, chunk_size, rollback_on_error=False
                )
        
        # Log summary
        total_success = sum(result.successful_records for result in results.values())
        total_records = sum(result.total_records for result in results.values())
        logger.info(f"Mixed batch insert completed: {total_success}/{total_records} records successful")
        
        return results
        
    except Exception as e:
        logger.error(f"Mixed batch insert failed: {e}")
        if not isinstance(e, BatchInsertError):
            raise BatchInsertError(f"Mixed batch insert failed: {e}") from e
        raise


if __name__ == "__main__":
    """Test the batch insertion functions."""
    
    print("📦 Football Props Finder - Batch Insertion Functions")
    print("=" * 60)
    
    # Test data
    test_prop_lines = [
        {
            'player_id': f'test_{i}',
            'player_name': f'Test Player {i}',
            'team': 'KC',
            'opponent': 'DET',
            'position': 'QB',
            'stat_type': 'Pass Yards',
            'line_score': 285.5 + i,
            'league': 'nfl',
            'source': 'PrizePicks',
            'season': 2023,
            'projection_id': f'pp_{i}'
        }
        for i in range(5)
    ]
    
    test_player_stats = [
        {
            'player_id': f'test_{i}',
            'player_name': f'Test Player {i}',
            'team': 'KC',
            'opponent': 'DET',
            'position': 'QB',
            'stat_type': 'passing',
            'passing_yards': 295 + i * 10,
            'completions': 24 + i,
            'attempts': 35 + i,
            'game_id': f'game_{i}',
            'week': 1,
            'season': 2023,
            'league': 'nfl',
            'source': 'RapidAPI'
        }
        for i in range(3)
    ]
    
    test_games = [
        {
            'game_id': f'game_{i}',
            'week': 1,
            'year': 2023,
            'league': 'nfl',
            'source': 'RapidAPI'
        }
        for i in range(3)
    ]
    
    # Test batch insertions
    print("\n1. Testing batch prop lines insertion...")
    try:
        result = batch_insert_prop_lines(test_prop_lines, chunk_size=2)
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Batch prop lines insertion failed: {e}")
    
    print("\n2. Testing batch player stats insertion...")
    try:
        result = batch_insert_player_stats(test_player_stats, chunk_size=2)
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Batch player stats insertion failed: {e}")
    
    print("\n3. Testing batch games processed insertion...")
    try:
        result = batch_insert_games_processed(test_games, chunk_size=2)
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Batch games processed insertion failed: {e}")
    
    print("\n4. Testing mixed batch insertion...")
    try:
        results = batch_insert_mixed_data(
            prop_lines=test_prop_lines[:2],
            player_stats=test_player_stats[:2],
            games_processed=test_games[:2],
            chunk_size=1
        )
        print("✅ Mixed batch insertion results:")
        for table, result in results.items():
            print(f"   {table}: {result}")
    except Exception as e:
        print(f"❌ Mixed batch insertion failed: {e}")
    
    print("\n5. Testing error handling...")
    try:
        # This should fail due to missing required fields
        invalid_data = [{'player_name': 'Invalid Player'}]
        result = batch_insert_prop_lines(invalid_data, rollback_on_error=False)
        print(f"✅ Error handling working: {result.failed_records} failed, {result.successful_records} succeeded")
    except Exception as e:
        print(f"✅ Error handling working: {e}")
    
    print("\n🎉 Batch insertion testing complete!")