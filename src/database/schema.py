"""
Database Schema Management Module

This module handles database schema creation, modification, and management
for the Football Props Finder project.

NOTE: psycopg2-binary installation may fail on Python 3.13 due to compatibility issues.
If installation fails, the database schema has been verified to work correctly with
direct SQL commands. The module will be fully functional once psycopg3 or compatible
version is available.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default connection parameters
DEFAULT_CONNECTION_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'football_props',
    'user': 'andrew'
}

class SchemaManager:
    """Manages database schema creation, updates, and verification."""
    
    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize schema manager with database connection parameters.
        
        Args:
            connection_params: Database connection parameters. Uses defaults if None.
        """
        self.connection_params = connection_params or DEFAULT_CONNECTION_PARAMS
        self.project_root = Path(__file__).parent.parent.parent
        self.ddl_script_path = self.project_root / "setup_database.sql"
        
    def get_connection(self, database: Optional[str] = None):
        """
        Get database connection.
        
        Args:
            database: Database name override (useful for connecting to postgres db)
            
        Returns:
            psycopg2 connection object
        """
        params = self.connection_params.copy()
        if database:
            params['database'] = database
            
        try:
            conn = psycopg2.connect(**params)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_database_if_not_exists(self) -> bool:
        """
        Create the football_props database if it doesn't exist.
        
        Returns:
            True if database was created or already exists, False on error
        """
        try:
            # Connect to postgres database to create our target database
            conn = self.get_connection(database='postgres')
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.connection_params['database'],)
                )
                
                if cursor.fetchone():
                    logger.info(f"Database '{self.connection_params['database']}' already exists")
                    return True
                
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.connection_params['database'])
                    )
                )
                logger.info(f"Created database '{self.connection_params['database']}'")
                return True
                
        except psycopg2.Error as e:
            logger.error(f"Failed to create database: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def execute_ddl_script(self, script_path: Optional[Path] = None) -> bool:
        """
        Execute DDL script to create tables and schema.
        
        Args:
            script_path: Path to SQL script file. Uses default if None.
            
        Returns:
            True if successful, False on error
        """
        script_path = script_path or self.ddl_script_path
        
        if not script_path.exists():
            logger.error(f"DDL script not found: {script_path}")
            return False
        
        try:
            conn = self.get_connection()
            
            with conn:
                with conn.cursor() as cursor:
                    # Read and execute the SQL script
                    with open(script_path, 'r') as f:
                        sql_script = f.read()
                    
                    # Split script into individual statements (simple approach)
                    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                    
                    for statement in statements:
                        # Skip comments and psql commands
                        if (statement.startswith('--') or 
                            statement.startswith('\\') or 
                            'pg_stats' in statement.lower()):
                            continue
                            
                        try:
                            cursor.execute(statement)
                        except psycopg2.Error as e:
                            # Log but continue for statements that might fail (like CREATE IF NOT EXISTS)
                            if "already exists" not in str(e):
                                logger.warning(f"Statement failed: {e}")
            
            logger.info("DDL script executed successfully")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to execute DDL script: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def verify_tables_exist(self) -> Dict[str, bool]:
        """
        Verify that all required tables exist in the database.
        
        Returns:
            Dictionary mapping table names to existence status
        """
        required_tables = ['prop_lines', 'player_stats', 'games_processed', 'players', 'teams']
        table_status = {}
        
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    
                    table_status[table] = cursor.fetchone()[0]
            
            return table_status
            
        except psycopg2.Error as e:
            logger.error(f"Failed to verify tables: {e}")
            return {table: False for table in required_tables}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_table_info(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get detailed information about a table's structure.
        
        Args:
            table_name: Name of the table to inspect
            
        Returns:
            List of column information dictionaries, or None on error
        """
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                return [
                    {
                        'column_name': col[0],
                        'data_type': col[1],
                        'is_nullable': col[2],
                        'column_default': col[3],
                        'character_maximum_length': col[4]
                    }
                    for col in columns
                ]
            
        except psycopg2.Error as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def drop_all_tables(self, confirm: bool = False) -> bool:
        """
        Drop all tables in the database. USE WITH CAUTION!
        
        Args:
            confirm: Must be True to actually drop tables
            
        Returns:
            True if successful, False on error
        """
        if not confirm:
            logger.warning("drop_all_tables called without confirmation - no action taken")
            return False
        
        try:
            conn = self.get_connection()
            
            with conn:
                with conn.cursor() as cursor:
                    # Get all table names
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                    """)
                    
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Drop tables in reverse dependency order
                    for table in tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                        logger.info(f"Dropped table: {table}")
            
            logger.info("All tables dropped successfully")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()


def create_all_tables() -> bool:
    """
    Convenience function to create all database tables.
    
    Returns:
        True if successful, False on error
    """
    schema_manager = SchemaManager()
    
    # Create database if needed
    if not schema_manager.create_database_if_not_exists():
        return False
    
    # Execute DDL script
    if not schema_manager.execute_ddl_script():
        return False
    
    # Verify tables were created
    table_status = schema_manager.verify_tables_exist()
    all_created = all(table_status.values())
    
    if all_created:
        logger.info("All tables created successfully")
        logger.info(f"Table status: {table_status}")
    else:
        logger.error(f"Some tables failed to create: {table_status}")
    
    return all_created


def drop_all_tables(confirm: bool = False) -> bool:
    """
    Convenience function to drop all database tables.
    
    Args:
        confirm: Must be True to actually drop tables
        
    Returns:
        True if successful, False on error
    """
    schema_manager = SchemaManager()
    return schema_manager.drop_all_tables(confirm=confirm)


def verify_schema() -> bool:
    """
    Verify that the database schema is properly set up.
    
    Returns:
        True if schema is valid, False otherwise
    """
    schema_manager = SchemaManager()
    table_status = schema_manager.verify_tables_exist()
    
    required_tables = ['prop_lines', 'player_stats', 'games_processed', 'players', 'teams']
    missing_tables = [table for table in required_tables if not table_status.get(table, False)]
    
    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False
    
    logger.info("Database schema verification successful")
    return True


if __name__ == "__main__":
    """Test the schema management functionality."""
    
    print("🗃️ Football Props Finder - Database Schema Manager")
    print("=" * 55)
    
    # Test schema creation
    print("\n1. Testing database and table creation...")
    if create_all_tables():
        print("✅ Tables created successfully")
    else:
        print("❌ Table creation failed")
        exit(1)
    
    # Test schema verification
    print("\n2. Verifying schema...")
    if verify_schema():
        print("✅ Schema verification passed")
    else:
        print("❌ Schema verification failed")
    
    # Show table information
    print("\n3. Table information:")
    schema_manager = SchemaManager()
    
    for table in ['prop_lines', 'player_stats', 'games_processed']:
        print(f"\n📋 Table: {table}")
        table_info = schema_manager.get_table_info(table)
        if table_info:
            for col in table_info[:5]:  # Show first 5 columns
                print(f"  - {col['column_name']}: {col['data_type']}")
            if len(table_info) > 5:
                print(f"  ... and {len(table_info) - 5} more columns")
    
    print("\n🎉 Schema management testing complete!")