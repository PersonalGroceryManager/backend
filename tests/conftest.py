import pytest
from src import create_app
from src.utils.database import engine, Base


@pytest.fixture
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

    with app.test_client() as client:
        
        # Ensure tables are dropped afterwards for independence
        try:
            yield client  # Tests run with this client
        except Exception as e:
            pass

    # Drop tables after each test
    with app.app_context():
        Base.metadata.drop_all(bind=engine)
