import pytest
from sqlalchemy import text
from src import create_app
from src.utils.database import engine, Base


def seed_database():
    """
    Seed the database with data from a raw SQL file.
    """
    with engine.connect() as conn:
        with open("tests/seed_data.sql", "r") as sql_file:
            sql_statements = sql_file.read()
            # For multi-line files, split by semi-colon
            for statement in sql_statements.split(";"):
                statement = statement.strip()  # Remove extra whitespace
                conn.execute(text(statement))
            conn.commit()

# Runs once before all tests
@pytest.fixture(scope="session")
def client():
    """
    Yield a client object to assess the routes.
    
    Construct a new database before each test and destoy it upon completion.
    TODO: Find a more efficient way to establish independence. 
    """
    
    app = create_app()
    app.config['TESTING'] = True

    # Create tables before each test
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        seed_database()

    yield app.test_client()
