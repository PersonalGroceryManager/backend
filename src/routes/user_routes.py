# Standard Imports
import logging
from typing import Tuple, Dict
from passlib.context import CryptContext

# Third party imports
from sqlalchemy import select, update, insert
from sqlalchemy.sql import exists
from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import Group, User, Receipt, UserGroups, UserSpending
from src.utils.Authentication import Authentication

users_blueprint = Blueprint('users', __name__)

# Authentication Context
auth = Authentication()

# Module-level logging inherited from 'main'
logger = logging.getLogger('main.user_routes')


@users_blueprint.route("", methods=['POST'])
def register_user():
    """
    Registers a new user. The expected JSON request should contain:
    {
        "username": "Example username",
        "password": "Example password",
        "email": "example@gmail.com"
    }
    """
    logger.info(f"Attempting to register new user with username {username}")
    
    try:

        data = request.json

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        # Raise bad request error for imcomplete fields
        if (not username) or (not password) or (not email):
            return jsonify({
                "error": "Bad Request",
                "message": "Please provide all required information: \
                    username, password and email",
            }), 400

        with SessionLocal() as session:
            
            # Checks if the username already exists. If so, return Resource
            # Conflict Error
            user_exists = session.query(exists().\
                where(User.username == username)).scalar()
            if user_exists:
                logger.warning(f"User with username '{username}' already exists.")
                return jsonify({"error": "Resource Conflict", 
                                "message": "User already exists"}), 409

            # Hash the password before storing in database
            hashed_password = auth.hash_password(password)

            # Create a new_user
            new_user = User(username=username, 
                            hashed_password=hashed_password, 
                            email=email)
            session.add(new_user)

        logger.info("User created successfully.")
        return jsonify({
            "message": "User created successfully"}), 201

    except Exception as e:
        logger.error(f"User Registration Failed - {str(e)}")
        return jsonify({"error": "Internal Server Error", 
                        "message": str(e)}), 500


@users_blueprint.route('', methods=['DELETE'])
@jwt_required()
def delete_user():
    """
    Delete the current user from the database, given the user ID in JWT
    """
    logger.info(f"Attempting to delete a user.")
    
    try:
        user_id = get_jwt_identity()
        logger.info(f"Attempting to delete a user with ID {user_id}.")
        
        with SessionLocal() as db_session:

            # Prioritize the user of user_id as an identifier. If not, resort
            # to username
            if user_id:
                user = db_session.query(User)\
                    .filter_by(user_id=user_id).one_or_none() 

            # Return 404 Not found is user does not exist            
            if not user:
                logger.error(f"User cannot be deleted since a user with ID \
                    {user_id} cannot be found")
                return jsonify({"Error": "Not Found", 
                                "message": "User does not exists!"}), 404
            
            # Delete the user
            db_session.delete(user)

        # Return 204 No Content upon successful deletion
        logger.info(f"User with ID {user_id} deleted successfully.")
        return '', 204
        
    except Exception as e:
        logger.error(f"User deletion failed - {str(e)}")
        return jsonify({"status": "failed", "message": str(e)}), 500
    

@users_blueprint.route('/login', methods=['POST'])
def login():
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    
    logger.info(f"Attempt to login by {username}.")
    
    if (not username) or (not password):
        logger.warning(f"Login failed as username or password is not given.")
        return jsonify({
            "error": "Bad Request",
            "message": "Username or password not provided"
        })
    
    # If authentication successful, flask session cookies will be set.
    user_id = auth.authenticate(username, password)
    
    # Send the user_id to the frontend to user
    if user_id:
        
        logger.info(f"User ID {user_id} authenticated for login.\
                    Generating JWT token...")
        
        # Generate JWT and pass as access token
        access_token = create_access_token(identity=user_id)
        return jsonify({"message": "Login successful!", 
                        "access_token": access_token,
                        "user_id": user_id}), 200
    else:
        logger.warning(f"Login failed as user is unauthorized.")
        return jsonify({"error": "Unauthorized",
                        "message": "Invalid username or password", 
                        "user_id": None}), 401

@users_blueprint.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for(login))

        
@users_blueprint.route("", methods=['GET'])
@jwt_required()
def get_user_info():
    """
    Get user information of a user given user ID, in the form:
        {
            "user_id": 1,
            "username": "Arthur",
            "email": "arthur@gmail.com"
        }
    """
    logger.debug("Attempt to get user information.")
    
    try:
        # Returns error 401 if not authorized
        user_id = get_jwt_identity()
        
        with SessionLocal() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            logger.info(f"User '{user.username}' found.")
            return jsonify({
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email
                }), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch user information - {str(e)}")
        return jsonify({"status": "failed", "message": str(e)}), 400
    
        
@users_blueprint.route("/resolve/<string:username>", methods=['GET'])
def resolve_username(username: str):
    """Get user ID of a given username"""
    try:
        with SessionLocal() as session:
            user_id = session.scalar(select(User.user_id)\
                .where(User.username == username))
            
            # Not Found Error: If no user ID found for this name
            if not user_id:
                return jsonify({
                    "message": "No users found with this name"
                }), 404
            
            # Success: return status code 200 (default)
            return jsonify({"message": "User ID found", "user_id": user_id})
        
    except Exception as e:
        print(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 500


@users_blueprint.route("/resolve/<int:user_id>", methods=['GET'])
def resolve_user_id(user_id: int):
    """Get username of a given user ID"""
    try:
        with SessionLocal() as session:
            username = session.scalar(select(User.username)\
                .where(User.user_id == user_id))
            
            # Not Found Error: If no user ID found for this name
            if not username:
                return jsonify({
                    "message": "No users found with this ID"
                }), 404
            
            # Success: return status code 200 (default)
            return jsonify({"message": "Username found", "username": username})
        
    except Exception as e:
        print(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 500
    

@users_blueprint.route("/groups", methods=['GET'])
@jwt_required()
def get_groups_joined_by_user():
    """
    Get the groups joined by the user.
    """
    logger.info("Attempting to fetch groups joined by user.")
    
    try:
        
        user_id = get_jwt_identity()
        logger.info(f"Attempting to fetch groups joined by authorized user with ID {user_id}.")
        
        with SessionLocal() as session:
            groups_joined_by_user = session.query(Group).join(
                UserGroups, Group.group_id == UserGroups.c.group_id
            ).filter_by(user_id=user_id)

            return jsonify(
                [
                    {
                        "group_id": group.group_id,
                        "group_name": group.group_name,
                        "description": group.description
                    }
                    for group in groups_joined_by_user 
                ]
            ), 200
        
    except Exception as e:
        logger.error(f"Failed to get groups joined by user - {str(e)}")
        return jsonify({"status": "failed", "message": str(e)}), 500


@users_blueprint.route("/costs", methods=['GET'])
@jwt_required()
def get_user_costs():
    """
    Given a user ID, gets an array of the time (of the receipt) and cost spent
    on that receipt.
        [
            {"receipt_id" 1, "slot_time":  14-Jun-24, "cost": 12.78},
            {"receipt_id" 2, "slot_time":  15-Jun-24, "cost":  9.10}
        ]
    """
    logger.info("Fetching user costs...")
    
    try:
        
        # Return 401 unauthorized error if no JWT
        user_id = get_jwt_identity()
        
        # Validate that user_id is an integer
        if not isinstance(user_id, int):
            msg = f"User ID is not an int, but is of type {user_id}, \
                with content user_id={user_id}"
            return jsonify({"Error": "Not Found", "message": msg}), 400
        
        with SessionLocal() as session:
            # Performing an inner join where receipt ID matches and filter
            # by user ID
            # Perform an inner join and select the required fields
            results = session.query(Receipt.receipt_id,
                                    Receipt.slot_time,
                                    UserSpending.c.cost)\
            .join(UserSpending, 
                  UserSpending.c.receipt_id == Receipt.receipt_id)\
            .filter(UserSpending.c.user_id == user_id)\
            .all()
                
            # Return error 404 if results are no results are returned
            if not results:
                msg = f"No records found for the given user_id"
                logger.info(msg)
                return jsonify({"error": "Not Found", "message": msg}), 404
            
            # Initialize an empty list to store the dictionary
            data_list = []
            
            for row in results:
                data_dict = {"receipt_id": row.receipt_id,
                             "slot_time":  row.slot_time,
                             "cost":       row.cost}
                data_list.append(data_dict)
                
        return jsonify(data_list), 200

    except Exception as e:
        logger.error(f"Failed to get user spending - {str(e)}")
        return jsonify({"error": "Internal Server Error", 
                        "message": str(e)}), 500


@users_blueprint.route('/costs', methods=['PUT'])
def update_user_costs():
    """
    Expects an array-based JSON structure containing the user ID, receipt ID
    and the user's spending in the receipt.
        [
            {"user_id": 1, "receipt_id": 2, "cost": 12.78},
            {"user_id:: 2, "receipt_id": 2, "cost":  9.10}
        ]
    """
    logger.info("Updating user costs...")
    
    try:
        data = request.json
        
        # Check that data is a list
        if not isinstance(data, list):
            return jsonify({"status": "failed"}), 400

        # Validate each entry in the list
        for obj in data:

            # Ensure list content are dictionaries
            if not isinstance(obj, dict):
                msg = f"Expected dict, but received {type(obj)}"
                return jsonify({"status": "failed", "message": msg}), 400
            
            # Ensure necessary fields are present
            required_fields = ["user_id", "receipt_id", "cost"]
            for field in required_fields:
                if field not in obj:
                    msg = f"Missing required field: {field}"
                    logger.info(msg)
                    return jsonify({"status": "failed", "message": msg}), 400
                
            # Ensure field types are correct
            if not isinstance(obj["user_id"], int):
                msg = f"user_id must be an integer. Received {obj['user_id']}"
                logger.info(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["receipt_id"], int):
                msg = f"receipt_id must be an integer. Received {obj['receipt_id']}"
                logger.info(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["cost"], (float, int)) or obj["cost"] < 0:
                msg = f"cost must be a positive number. Received {obj['cost']}"
                logger.info(msg)
                return jsonify({"status": "failed", "message": msg}), 400

        with SessionLocal() as session:
            for entry in data:
                
                # Extract data from dictionary
                user_id = entry.get("user_id")
                receipt_id = entry.get("receipt_id")
                cost = entry.get("cost")
                
                # Check if entry exists
                existing_entry = session.query(UserSpending).filter_by(
                    user_id=user_id,
                    receipt_id=receipt_id
                ).one_or_none()
                
                # If user has no association with the receipt ID, 
                # create a new entry
                if not existing_entry:
                    # This table is not an ORM table so must use traditional
                    # query-based syntax
                    stmt = UserSpending.insert().values(user_id=user_id, receipt_id=receipt_id, cost=cost)
                
                # If an entry exists, just update the values
                else:
                    stmt = update(UserSpending).where(
                            (UserSpending.c.user_id==user_id) &
                            (UserSpending.c.receipt_id==receipt_id))\
                                .values(cost=cost)
                    print(stmt)
                session.execute(stmt)
            session.commit()

        # Must have empty content
        return '', 204
                    
    except Exception as e:
        logger.error(f"Failed to update user spending - {str(e)}")
        return jsonify({"status": "failed", "message": str(e)}), 500
