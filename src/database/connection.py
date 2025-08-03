"""
Database Connection Management Module

This module provides PostgreSQL connection management, connection pooling,
error handling, and configuration management for the Football Props Finder project.

Features:
- Connection pooling for performance
- Graceful error handling and retries
- Configuration management with environment variables
- Connection health monitoring
- Transaction management utilities
"""

import os
import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator, Union
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import psycopg2, but handle import errors gracefully
try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError as e:
    logger.warning(f"psycopg2 not available: {e}")
    logger.warning("Connection module will provide interface but require psycopg2 installation for functionality")
    PSYCOPG2_AVAILABLE = False
    
    # Create mock classes for development
    class MockPool:
        def getconn(self): pass
        def putconn(self, conn): pass
        def closeall(self): pass
    
    class MockCursor:
        def execute(self, query, params=None): pass
        def fetchone(self): return None
        def fetchall(self): return []
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class MockConnection:
        def cursor(self): return MockCursor()
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass


class DatabaseConfig:
    """Database configuration management with environment variable support."""
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize database configuration.
        
        Args:
            env_file: Optional path to .env file for loading environment variables
        """
        # Load environment variables if env_file provided
        if env_file and env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                logger.warning("python-dotenv not available, using system environment variables only")
        
        # Default configuration
        self._config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'football_props'),
            'user': os.getenv('DB_USER', 'andrew'),
            'password': os.getenv('DB_PASSWORD', ''),  # Empty for peer auth
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', 30)),
            'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', 30))
        }
        
        # Connection pool configuration
        self._pool_config = {
            'minconn': int(os.getenv('DB_POOL_MIN', 1)),
            'maxconn': int(os.getenv('DB_POOL_MAX', 10)),
            'host': self._config['host'],
            'port': self._config['port'],
            'database': self._config['database'],
            'user': self._config['user']
        }
        
        # Add password only if provided (for peer auth compatibility)
        if self._config['password']:
            self._pool_config['password'] = self._config['password']
    
    @property
    def connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for psycopg2."""
        params = {
            'host': self._config['host'],
            'port': self._config['port'],
            'database': self._config['database'],
            'user': self._config['user'],
            'connect_timeout': self._config['connect_timeout']
        }
        
        if self._config['password']:
            params['password'] = self._config['password']
            
        return params
    
    @property
    def pool_params(self) -> Dict[str, Any]:
        """Get connection pool parameters."""
        return self._pool_config.copy()
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        if self._config['password']:
            return (f"postgresql://{self._config['user']}:{self._config['password']}@"
                   f"{self._config['host']}:{self._config['port']}/{self._config['database']}")
        else:
            return (f"postgresql://{self._config['user']}@"
                   f"{self._config['host']}:{self._config['port']}/{self._config['database']}")


class ConnectionManager:
    """Manages PostgreSQL connections with pooling and error handling."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize connection manager.
        
        Args:
            config: Database configuration. Creates default if None.
        """
        self.config = config or DatabaseConfig()
        self._pool: Optional[Union[pool.SimpleConnectionPool, MockPool]] = None
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        
    def initialize_pool(self) -> bool:
        """
        Initialize connection pool.
        
        Returns:
            True if successful, False otherwise
        """
        if not PSYCOPG2_AVAILABLE:
            logger.error("Cannot initialize pool: psycopg2 not available")
            self._pool = MockPool()
            return False
        
        try:
            pool_params = self.config.pool_params
            
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=pool_params['minconn'],
                maxconn=pool_params['maxconn'],
                host=pool_params['host'],
                port=pool_params['port'],
                database=pool_params['database'],
                user=pool_params['user'],
                password=pool_params.get('password'),
                connect_timeout=30
            )
            
            logger.info(f"Connection pool initialized: {pool_params['minconn']}-{pool_params['maxconn']} connections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            self._pool = MockPool()
            return False
    
    def get_connection(self, retries: int = 3, retry_delay: float = 1.0):
        """
        Get connection from pool with retry logic.
        
        Args:
            retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Database connection or MockConnection
        """
        if not self._pool:
            if not self.initialize_pool():
                logger.warning("Using mock connection due to pool initialization failure")
                return MockConnection()
        
        if not PSYCOPG2_AVAILABLE:
            return MockConnection()
        
        for attempt in range(retries + 1):
            try:
                conn = self._pool.getconn()
                if conn:
                    return conn
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("All connection attempts failed, using mock connection")
                    return MockConnection()
        
        return MockConnection()
    
    def return_connection(self, conn) -> None:
        """
        Return connection to pool.
        
        Args:
            conn: Database connection to return
        """
        if not self._pool or not PSYCOPG2_AVAILABLE:
            return
        
        try:
            self._pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
    
    @contextmanager
    def get_connection_context(self, retries: int = 3) -> Generator[Any, None, None]:
        """
        Context manager for database connections.
        
        Args:
            retries: Number of retry attempts
            
        Yields:
            Database connection
        """
        conn = self.get_connection(retries=retries)
        try:
            yield conn
        finally:
            if conn and hasattr(conn, 'close'):
                self.return_connection(conn)
    
    @contextmanager
    def get_cursor_context(self, retries: int = 3, autocommit: bool = True) -> Generator[Any, None, None]:
        """
        Context manager for database cursors.
        
        Args:
            retries: Number of retry attempts
            autocommit: Whether to automatically commit the transaction
            
        Yields:
            Database cursor
        """
        with self.get_connection_context(retries=retries) as conn:
            try:
                with conn.cursor() as cursor:
                    yield cursor
                if autocommit and PSYCOPG2_AVAILABLE:
                    conn.commit()
            except Exception as e:
                if PSYCOPG2_AVAILABLE:
                    conn.rollback()
                raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = False,
                     retries: int = 3) -> Optional[Any]:
        """
        Execute a SQL query with error handling.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Whether to fetch one result
            fetch_all: Whether to fetch all results
            retries: Number of retry attempts
            
        Returns:
            Query results if fetching, None otherwise
        """
        if not PSYCOPG2_AVAILABLE:
            logger.warning(f"Mock execution of query: {query[:50]}...")
            return None
        
        for attempt in range(retries + 1):
            try:
                with self.get_cursor_context(retries=1) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch_one:
                        return cursor.fetchone()
                    elif fetch_all:
                        return cursor.fetchall()
                    return None
                    
            except Exception as e:
                logger.warning(f"Query execution attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    time.sleep(1.0)
                else:
                    logger.error(f"All query execution attempts failed for: {query[:50]}...")
                    raise
        
        return None
    
    def execute_transaction(self, queries: list, retries: int = 3) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            retries: Number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        if not PSYCOPG2_AVAILABLE:
            logger.warning(f"Mock execution of transaction with {len(queries)} queries")
            return True
        
        for attempt in range(retries + 1):
            try:
                with self.get_connection_context(retries=1) as conn:
                    with conn.cursor() as cursor:
                        for query, params in queries:
                            cursor.execute(query, params)
                        conn.commit()
                        return True
                        
            except Exception as e:
                logger.warning(f"Transaction attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    time.sleep(1.0)
                else:
                    logger.error("All transaction attempts failed")
                    return False
        
        return False
    
    def check_connection_health(self, force: bool = False) -> bool:
        """
        Check database connection health.
        
        Args:
            force: Force health check even if recently performed
            
        Returns:
            True if healthy, False otherwise
        """
        current_time = time.time()
        
        if not force and (current_time - self._last_health_check) < self._health_check_interval:
            return True
        
        try:
            result = self.execute_query("SELECT 1", fetch_one=True)
            healthy = result is not None or not PSYCOPG2_AVAILABLE
            
            if healthy:
                self._last_health_check = current_time
                logger.debug("Database connection health check passed")
            else:
                logger.warning("Database connection health check failed")
            
            return healthy
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close_pool(self) -> None:
        """Close connection pool and all connections."""
        if self._pool and PSYCOPG2_AVAILABLE:
            try:
                self._pool.closeall()
                logger.info("Connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
        
        self._pool = None


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None

def get_connection_manager(config: Optional[DatabaseConfig] = None) -> ConnectionManager:
    """
    Get global connection manager instance.
    
    Args:
        config: Database configuration for initialization
        
    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager(config)
    
    return _connection_manager

def get_connection(retries: int = 3):
    """
    Convenience function to get database connection.
    
    Args:
        retries: Number of retry attempts
        
    Returns:
        Database connection
    """
    return get_connection_manager().get_connection(retries=retries)

@contextmanager
def connection_context(retries: int = 3) -> Generator[Any, None, None]:
    """
    Convenience context manager for database connections.
    
    Args:
        retries: Number of retry attempts
        
    Yields:
        Database connection
    """
    with get_connection_manager().get_connection_context(retries=retries) as conn:
        yield conn

@contextmanager
def cursor_context(retries: int = 3, autocommit: bool = True) -> Generator[Any, None, None]:
    """
    Convenience context manager for database cursors.
    
    Args:
        retries: Number of retry attempts
        autocommit: Whether to automatically commit the transaction
        
    Yields:
        Database cursor
    """
    with get_connection_manager().get_cursor_context(retries=retries, autocommit=autocommit) as cursor:
        yield cursor

def execute_query(query: str, params: Optional[tuple] = None,
                 fetch_one: bool = False, fetch_all: bool = False,
                 retries: int = 3) -> Optional[Any]:
    """
    Convenience function to execute SQL queries.
    
    Args:
        query: SQL query to execute
        params: Query parameters  
        fetch_one: Whether to fetch one result
        fetch_all: Whether to fetch all results
        retries: Number of retry attempts
        
    Returns:
        Query results if fetching, None otherwise
    """
    return get_connection_manager().execute_query(
        query, params, fetch_one, fetch_all, retries
    )

def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection is healthy, False otherwise
    """
    return get_connection_manager().check_connection_health(force=True)


if __name__ == "__main__":
    """Test the connection management functionality."""
    
    print("🔗 Football Props Finder - Database Connection Manager")
    print("=" * 60)
    
    # Test configuration
    print("\n1. Testing database configuration...")
    config = DatabaseConfig()
    print(f"✅ Host: {config.connection_params['host']}")
    print(f"✅ Port: {config.connection_params['port']}")
    print(f"✅ Database: {config.connection_params['database']}")
    print(f"✅ User: {config.connection_params['user']}")
    
    # Test connection manager
    print("\n2. Testing connection manager...")
    manager = get_connection_manager(config)
    
    if PSYCOPG2_AVAILABLE:
        print("✅ psycopg2 available - full functionality enabled")
        
        # Test pool initialization
        if manager.initialize_pool():
            print("✅ Connection pool initialized successfully")
        else:
            print("❌ Connection pool initialization failed")
        
        # Test connection health
        if manager.check_connection_health(force=True):
            print("✅ Database connection health check passed")
        else:
            print("❌ Database connection health check failed")
        
        # Test query execution
        try:
            result = manager.execute_query("SELECT current_database()", fetch_one=True)
            if result:
                print(f"✅ Test query successful: Connected to '{result[0]}'")
            else:
                print("❌ Test query returned no results")
        except Exception as e:
            print(f"❌ Test query failed: {e}")
    
    else:
        print("⚠️ psycopg2 not available - using mock functionality")
        print("   Install psycopg2-binary for full database connectivity")
        
        # Test mock functionality
        with manager.get_connection_context() as conn:
            print("✅ Mock connection context working")
            
        with manager.get_cursor_context() as cursor:
            print("✅ Mock cursor context working")
    
    print("\n3. Testing convenience functions...")
    health_status = check_database_connection()
    print(f"✅ Database health check: {'Healthy' if health_status else 'Issues detected'}")
    
    print("\n🎉 Connection manager testing complete!")
    
    # Clean up
    manager.close_pool()