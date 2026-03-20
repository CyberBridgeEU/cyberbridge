# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection
# Automatically detect environment: production (Docker) vs development (local)
def get_database_url():
    container_env = os.getenv("CONTAINER_ENV")
    db_host = os.getenv("DB_HOST")

    # Check if we're running in a container (common environment variable)
    if container_env == "docker" or db_host:
        # Production: Running in Docker container - ignore .env DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        # Only use DATABASE_URL if it points to cyberbridge_db (Docker environment)
        if database_url and "cyberbridge_db" in database_url:
            return database_url
        else:
            return "postgresql://postgres:postgres@cyberbridge_db:5432/postgres"
    else:
        # Development: Running locally - use .env DATABASE_URL or default
        database_url = os.getenv("DATABASE_URL")
        return database_url or "postgresql://postgres:postgres@localhost:5433/postgres"

DATABASE_URL = get_database_url()

logger.info(f"Connecting to database with URL: {DATABASE_URL}")

try:
    # DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "compliance_assessments")
    DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "public")
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"options": f"-c search_path={DATABASE_SCHEMA}"},
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    # Test the connection
    with engine.connect() as connection:
        logger.info("Successfully connected to the database!")
except Exception as e:
    logger.error(f"Database connection failed: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Context manager for database operations
class DBContextManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type is not None:
                # An exception occurred, rollback the transaction
                self.db.rollback()
            self.db.close()

# Helper function to execute database operations with a context manager
def with_db_context(operation_func):
    """
    Executes a database operation within a context manager to ensure proper connection handling.

    Args:
        operation_func: A function that takes a database session as its first argument
                       and performs database operations.

    Returns:
        The result of the operation_func.
    """
    with DBContextManager() as db:
        return operation_func(db)

def db_operation(func):
    """
    Decorator for repository functions to ensure proper error handling and connection management.

    Args:
        func: The repository function to wrap.

    Returns:
        A wrapped function that handles database errors and ensures connections are properly closed.
    """
    def wrapper(*args, **kwargs):
        # Extract the database session from args or kwargs
        db = None
        if args and isinstance(args[0], Session):
            db = args[0]
        elif 'db' in kwargs and isinstance(kwargs['db'], Session):
            db = kwargs['db']

        if not db:
            raise ValueError("No database session provided to repository function")

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Database operation error in {func.__name__}: {str(e)}")
            raise
    return wrapper

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
