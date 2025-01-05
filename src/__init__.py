# Standard Imports
import os

# Third-Party Imports
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Routes
from src.routes.group_routes import groups_blueprint
from src.routes.user_routes import users_blueprint
from src.routes.receipt_routes import receipt_blueprint

def create_app():
    app = Flask(__name__)
    
    # Enable Cross-Origin Resource Sharing for all routes
    # To-do: Change this to frontend domain only
    CORS(app)
    
    app.register_blueprint(groups_blueprint,  url_prefix='/groups')
    app.register_blueprint(users_blueprint,   url_prefix='/users')
    app.register_blueprint(receipt_blueprint, url_prefix='/receipts')

    # Generate a 24-byte random key
    # TODO: Use a fix key in env variable for persistance across redeployments
    # This also causes issue in initial sign in
    app.secret_key = os.urandom(24)
    app.config["JWT_SECRET_KEY"] = os.urandom(24)
    app.secret_key = "random"
    app.config["JWT_SECRET_KEY"] = "random"

    # Change token expiry date to an hour (3600s)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    
    jwt = JWTManager(app)
    

    return app
