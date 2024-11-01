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

user_blueprint = Blueprint('user', __name__)

# Authentication Context
auth = Authentication()


@user_blueprint.route("/get-all", methods=['GET'])
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
        
        
@user_blueprint.route("/get/user-info/<int:user_id>", methods=['GET'])
def get_user_info(user_id:int):
    """
    Get user information of a user given user ID, in the form:
        {
            "user_id": 1,
            "username": "Arthur",
            "email": "arthur@gmail.com"
        }
    """
    pass


@user_blueprint.route("/get/username/<int:user_id>", methods=['GET'])
def get_username(user_id:int):
    """Get username of a user given user_id"""
    try:
        with SessionLocal() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            return jsonify({"username": user.username}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    
        
@user_blueprint.route("/get/user-id/<username>", methods=['GET'])
def get_user_id(username: str):
    """Get user ID of a given username"""
    try:
        with SessionLocal() as session:
            user = session.query(User).filter_by(username=username).one_or_none()
            return jsonify({"user_id": user.user_id}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 600
    

@user_blueprint.route("/get/email/<int:user_id>", methods=['GET'])
def get_user_email(user_id:int):
    """Get email of a user given user_id"""
    try:
        with SessionLocal() as session:
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            return jsonify({"email": user.email}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    

@user_blueprint.route("/get/groups/<int:user_id>", methods=['GET'])
def get_groups_jonined_by_user(user_id: int):
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
        return jsonify({"status": "failed", "message": str(e)}), 400


@user_blueprint.route("/create", methods=['POST'])
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
        
        with SessionLocal() as session:
            # Checks if the username exists - fail if exists
            user_exists = session.query(exists().where(User.username == username)).scalar()
            if user_exists:
                return jsonify({"status": "failed", "message": "User already exists!"}), 400
            
            # Hash the password before storing in database
            hashed_password = auth.hash_password(password)
            
            # Create a new_user
            new_user = User(username=username, hashed_password=hashed_password, email=email)
            session.add(new_user)

        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    

@user_blueprint.route("/delete", methods=['POST'])
def delete_user():
    """
    Delete a user from the database.
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        
        with SessionLocal() as db_session:
        
        # Checks if user exists - fail if not
            user = db_session.query(User).filter_by(user_id=user_id).one_or_none()
            if not user:
                return jsonify({"status": "failed", "message": "User does not exists!"}), 400
            db_session.delete(user)

        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    

@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    
    # If authentication successful, flask session cookies will be set.
    user_id = auth.authenticate(username, password)
    
    # Send the user_id to the frontend to user
    if user_id:
        return jsonify({"message": "Login successful!", "user_id": user_id}), 200
    else:
        return jsonify({"message": "Invalid username or password", "user_id": None}), 401


@user_blueprint.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for(login))
