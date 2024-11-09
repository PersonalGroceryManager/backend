# Standard Imports
from typing import Tuple, Dict
from passlib.context import CryptContext
from sqlalchemy import select, insert
from sqlalchemy.sql import exists
from flask import Blueprint, request, jsonify, session, redirect, url_for

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import Group, User, UserGroups
from src.utils.Authentication import Authentication

users_blueprint = Blueprint('users', __name__)

# Authentication Context
auth = Authentication()


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
                return jsonify({"error": "Resource Conflict", 
                                "message": "User already exists"}), 409

            # Hash the password before storing in database
            hashed_password = auth.hash_password(password)

            # Create a new_user
            new_user = User(username=username, 
                            hashed_password=hashed_password, 
                            email=email)
            session.add(new_user)

        return jsonify({
            "message": "User created successfully"}), 201

    except Exception as e:
        return jsonify({"error": "Internal Server Error", 
                        "message": str(e)}), 500


@users_blueprint.route('', methods=['DELETE'])
def delete_user():
    """
    Delete a user from the database, given the user ID or username.
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        
        # Raise bad request error if both user ID and username are not given
        if (not user_id) and (not username):
            return jsonify({
                "error": "Bad Request",
                "message": "User ID not given"
            }), 400
        
        
        with SessionLocal() as db_session:

            # Prioritize the user of user_id as an identifier. If not, resort
            # to username
            if user_id:
                user = db_session.query(User)\
                    .filter_by(user_id=user_id).one_or_none()
            elif username:
                user = db_session.query(User)\
                    .filter_by(username=username).one_or_none()    

            # Return 404 Not found is user does not exist            
            if not user:
                return jsonify({"Error": "Not Found", 
                                "message": "User does not exists!"}), 404
            
            # Delete the user
            db_session.delete(user)

        # Return 204 No Content upon successful deletion
        return '', 204
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    

@users_blueprint.route('/login', methods=['POST'])
def login():
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    
    if (not username) or (not password):
        return jsonify({
            "error": "Bad Request",
            "message": "Username or password not provided"
        })
    
    # If authentication successful, flask session cookies will be set.
    user_id = auth.authenticate(username, password)
    
    # Send the user_id to the frontend to user
    if user_id:
        return jsonify({"message": "Login successful!", 
                        "user_id": user_id}), 200
    else:
        return jsonify({"error": "Unauthorized",
                        "message": "Invalid username or password", 
                        "user_id": None}), 401

@users_blueprint.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for(login))


@users_blueprint.route("/get-all", methods=['GET'])
def get_all_users():
    """
    Get all user information.
    """
    try:
        with SessionLocal() as session:
            users = session.query(User).all()
        
            return jsonify([{
                "user_id": user.user_id,
                "username": user.username
            } for user in users]), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
        
        
@users_blueprint.route("/<int:user_id>", methods=['GET'])
def get_user_info_by_id(user_id:int):
    """
    Get user information of a user given user ID, in the form:
        {
            "user_id": 1,
            "username": "Arthur",
            "email": "arthur@gmail.com"
        }
    """
    try:
        with SessionLocal() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            return jsonify({
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email
                }), 200
        
    except Exception as e:
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
    

@users_blueprint.route("/<int:user_id>/groups", methods=['GET'])
def get_groups_joined_by_user(user_id: int):
    """
    Get the groups joined by the user.
    """
    try:
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
        return jsonify({"status": "failed", "message": str(e)}), 500
