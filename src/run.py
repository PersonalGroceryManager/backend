"""
run.py

This script is to be used when running locally. It is the same copy as `app.py`
which is intended as the backend entrypoint.
"""
import os
from dotenv import load_dotenv
from src import create_app

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    app = create_app()
    
    mode = os.getenv('MODE', 'development')

    # Run in debug mode for non-production environment
    if mode != 'production':
        app.run(debug=True)
