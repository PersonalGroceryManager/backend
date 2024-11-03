import pytest
from src.run import create_app
from src.utils.database import create_engine, Base


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True

    # Create the necessary tables
    with app.test_client() as client:
        yield client
