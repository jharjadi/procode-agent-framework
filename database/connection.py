"""
Database Connection Management

Handles database connections for both SQLite (development) and PostgreSQL (production).
Uses environment variables to configure the database URL.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

# Base class for all models
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Defaults to SQLite for development if no DATABASE_URL is set.
    
    Returns:
        Database URL string
    """
    # Check for explicit DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Default to SQLite for development
    db_path = os.getenv("SQLITE_DB_PATH", "data/procode.db")
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    return f"sqlite:///{db_path}"


def create_db_engine():
    """
    Create database engine based on configuration.
    
    Returns:
        SQLAlchemy engine
    """
    database_url = get_database_url()
    
    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    # PostgreSQL configuration
    else:
        engine = create_engine(
            database_url,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=True,  # Verify connections before using
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
    
    return engine


def init_db():
    """
    Initialize database connection and create tables.
    
    This should be called once at application startup.
    """
    global _engine, _SessionLocal
    
    if _engine is None:
        _engine = create_db_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )
        
        # Import all models to ensure they're registered
        from database import models  # noqa: F401
        
        # Create all tables
        Base.metadata.create_all(bind=_engine)
        
        print(f"✓ Database initialized: {get_database_url()}")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Use as a dependency injection or context manager:
    
    ```python
    # As dependency
    def my_function(db: Session = Depends(get_db)):
        ...
    
    # As context manager
    with next(get_db()) as db:
        ...
    ```
    
    Yields:
        Database session
    """
    if _SessionLocal is None:
        init_db()
    
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def close_db():
    """
    Close database connection.
    
    This should be called at application shutdown.
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        print("✓ Database connection closed")


def get_session() -> Session:
    """
    Get a new database session (for manual management).
    
    Remember to close the session when done:
    ```python
    session = get_session()
    try:
        # Use session
        ...
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
    ```
    
    Returns:
        Database session
    """
    if _SessionLocal is None:
        init_db()
    
    return _SessionLocal()
