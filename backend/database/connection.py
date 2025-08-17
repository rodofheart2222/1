"""
Database Connection Manager

Provides database connection management and session handling for the MT5 Dashboard
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database URL, defaults to SQLite file
        """
        if database_url is None:
            db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine and session factory"""
        try:
            # SQLite specific configuration
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=False,  # Set to True for SQL debugging
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600  # Recycle connections every hour
                )
            else:
                # PostgreSQL or other databases
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=10,
                    max_overflow=20,
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database engine initialized: {self.database_url}")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing database engine: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup
        
        Usage:
            with db_manager.get_session() as session:
                # Use session here
                session.query(Model).all()
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected database session error: {e}")
            raise
        finally:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Failed to close database session: {e}")
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        return self.engine
    
    def create_tables(self):
        """Create all database tables"""
        try:
            from models.base import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            from models.base import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error dropping database tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:

                from sqlalchemy import text

                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing database connection: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error(f"Failed to close database connections: {e}")


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


def initialize_database_manager(database_url: str = None) -> DatabaseManager:
    """Initialize global database manager with custom URL"""
    global _database_manager
    if _database_manager:
        _database_manager.close()
    _database_manager = DatabaseManager(database_url)
    return _database_manager


def get_db_session():
    """Get database session for FastAPI dependency injection"""
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session


def test_database_connection() -> bool:
    """Test database connection"""
    try:
        db_manager = get_database_manager()
        return db_manager.test_connection()
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False