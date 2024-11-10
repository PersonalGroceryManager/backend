"""
run.py

This script is to be used when running locally. It is the same copy as `app.py`
which is intended as the backend entrypoint.
"""
# Standard Imports
import os

# Third-Party Imports
from flask import Flask
from flask_jwt_extended import JWTManager

# Routes
from src.routes.group_routes import groups_blueprint
from src.routes.user_routes import users_blueprint
from src.routes.receipt_routes import receipt_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(groups_blueprint,  url_prefix='/groups')
    app.register_blueprint(users_blueprint,   url_prefix='/users')
    app.register_blueprint(receipt_blueprint, url_prefix='/receipts')

    # Generate a 24-byte random key
    # TODO: Use a fix key in env variable for persistance across redeployments
    app.secret_key = os.urandom(24)
    app.config["JWT_SECRET_KEY"] = os.urandom(24)
    jwt = JWTManager(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
