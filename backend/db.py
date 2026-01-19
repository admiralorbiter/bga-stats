"""
Database initialization and session management for BGA Stats application.
Provides engine setup, session factories, and database initialization functions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.config import SQLALCHEMY_DATABASE_URI
from backend.models import Base

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    echo=False,  # Set to True for SQL debugging
    connect_args={'check_same_thread': False}  # Required for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread-safety
Session = scoped_session(SessionLocal)


def init_db():
    """
    Initialize the database by creating all tables.
    Safe to call multiple times - won't recreate existing tables.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {SQLALCHEMY_DATABASE_URI}")


def get_session():
    """
    Get a new database session.
    
    Usage:
        session = get_session()
        try:
            # Use session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    Returns:
        Session: A new SQLAlchemy session
    """
    return Session()


def close_session():
    """
    Remove the current session.
    Useful for cleanup in Flask teardown.
    """
    Session.remove()
