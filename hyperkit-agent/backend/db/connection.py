"""
Database connection and session management for HyperKit AI Agent.

This module handles database connections, session management, and connection pooling
for the production PostgreSQL database.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager for production system."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection with proper configuration."""
        try:
            # Get database URL from environment
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://hyperkit:password@localhost:5432/hyperkit_production"
            )
            
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=20,  # Number of connections to maintain
                max_overflow=30,  # Additional connections beyond pool_size
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connection setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup database connection: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables."""
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.get_db_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


def get_database_session() -> Session:
    """Get a database session for dependency injection."""
    return db_manager.get_session()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database sessions."""
    with db_manager.get_db_session() as session:
        yield session


def init_database():
    """Initialize database with tables."""
    db_manager.create_tables()


def check_database_health() -> dict:
    """Check database health and return status."""
    is_healthy = db_manager.health_check()
    
    return {
        "database": {
            "status": "healthy" if is_healthy else "unhealthy",
            "connection_pool": {
                "size": db_manager.engine.pool.size(),
                "checked_in": db_manager.engine.pool.checkedin(),
                "checked_out": db_manager.engine.pool.checkedout(),
                "overflow": db_manager.engine.pool.overflow(),
            }
        }
    }
