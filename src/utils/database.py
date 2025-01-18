"""
Defines database connection configuration and a session object used for
database transaction. Also creates the defined tables in `models.py` upon
connection.

Dependencies: models.py
"""
# Standard Imports
import os
import logging
import time
from contextlib import contextmanager
from pathlib import Path

# Third-Party Imports
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Project-Specific Imports
from src.utils.models import Base


# Load environmental variables
load_dotenv()

# Number of retries and delay in seconds between retries
RETRY_LIMIT = 3
RETRY_DELAY = 2

# Initialize module-level logger
logger = logging.getLogger('main.db')

# Set database URL based on MODE environmental variable
mode = os.getenv('MODE', 'development')  # default to 'development'
if mode == 'development':
    DATABASE_URL = os.getenv('DATABASE_URL_DEV')
elif mode == 'testing':
    DATABASE_URL = os.getenv('DATABASE_URL_TEST')
elif mode == 'production':
    DATABASE_URL = os.getenv('DATABASE_URL_PROD')
else:
    raise ValueError(f"Invalid MODE: {mode}")

print(f"Running in {mode} mode!")

# Create Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session object for database transaction sessions
@contextmanager
def SessionLocal():
    """
    Context manager to make transactions around database.
    
    Example Usage:
        with SessionLocal() as session:
            user = session.query(User).filter_by(User.user_id=user_id).first()
    """
    session_blueprint = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    attempt = 0
    
    while attempt < RETRY_LIMIT:
        session = session_blueprint()
        
        try:
            # Yield session to the calling code
            yield session
            
            # Commit the transaction
            session.commit()
            break
        
        # Catch database connection errors. This must be raised by children
        # try/catch statements
        except Exception as e:
            session.rollback()
            attempt += 1
            if attempt >= RETRY_LIMIT:
                msg = f"""Database operation faiiled after 
                      {RETRY_LIMIT} retries: {e}"""
                logger.critical(msg)
                raise Exception(msg)
            
            logger.critical((f"Retrying session operation due to "
                             f"disconnection..." 
                             f"(Attempt {attempt}/{RETRY_LIMIT})"))
            time.sleep(RETRY_DELAY)
        
        finally:
            session.close()

# Create tables (IF NOT EXISTS)
Base.metadata.create_all(bind=engine)
