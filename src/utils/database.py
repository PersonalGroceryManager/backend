"""
Defines database connection configuration and a session object used for
database transaction. Also creates the defined tables in `models.py` upon
connection.

Dependencies: models.py
"""
# Standard Imports
import os
from contextlib import contextmanager
from pathlib import Path

# Third-Party Imports
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Project-Specific Imports
from src.utils.models import Base

load_dotenv()

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
engine = create_engine(DATABASE_URL)

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
    session = session_blueprint()
    
    try:
        yield session
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise e 
    
    finally:
        session.close()

# Create tables (IF NOT EXISTS)
Base.metadata.create_all(bind=engine)
