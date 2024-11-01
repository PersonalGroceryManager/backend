# Third-Party Imports
from flask import Blueprint, request, jsonify

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import Group, User, UserGroups
from src.utils.Authentication import Authentication

groups_blueprint = Blueprint('groups', __name__)
auth = Authentication()

@groups_blueprint.route('/get-all', methods=['GET'])
def get_groups():
    """
    Get all available groups.
    """
    try:
        with SessionLocal() as session:

            groups = session.query(Group).all()
            return jsonify([{
                "group_id": group.group_id,
                "group_name": group.group_name,
                "description": group.description
            } for group in groups]), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500


@groups_blueprint.route('/get/<int:group_id>', methods=['GET'])
def get_group(group_id: int):
    """
    Get group information based on group ID.
    """
    try:
        with SessionLocal() as session:
        
            group = session.query(Group).filter_by(group_id=group_id).one_or_none()
            
            if not group:
                return jsonify({"status": "failed", "message": "Group not found!"}), 404
            
            group_info = {
                "id": group.group_id,
                "name": group.group_name,
                "description": group.description
            } 
            return jsonify(group_info), 200
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500


@groups_blueprint.route('/create', methods=['POST'])
def create_new_group():
    """
    Create a new group
    """
    data = request.json
    
    if not data:
        return jsonify({"status": "failed", "message": "No data provided!"}), \
               400
               
    group_name = data.get('group_name')
    group_desc = data.get('description')
    
    # Verify group name is provided
    if not group_name:
        return jsonify({"status": "failed", "message": "Group name is required!"}), 400

    try:
        with SessionLocal() as session:
            if session.query(Group).filter_by(group_name=group_name).first():
                return jsonify({"status": "failed", "message": "Group already exists!"}), 400

            new_group = Group(group_name=group_name, description=group_desc)
            session.add(new_group)
            session.commit()

        return jsonify({"status": "success", "message": "Group created successfully!"}), 201

    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500


@groups_blueprint.route('/delete', methods=['DELETE'])
def delete_group():
    """
    Delete a group based on group name.
    """

    data = request.json
    group_name = data.get('group_name')
    
    try:
        
        with SessionLocal() as session:
            group = session.query(Group).filter_by(group_name=group_name).one_or_none()
            if not group:
                return jsonify({"status": "failed", "message": "Group not found!"}), 404
            session.delete(group)
            
        return jsonify({"status": "success", "message": "Group deleted successfully!"}), 204
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)})
    
        
@groups_blueprint.route('/update', methods=['PUT'])
def update_group():
    
    data = request.json
    
    try: 
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        new_description = data.get('description')
    
        if not new_name and not new_description:
            return jsonify({"status": "failed", "message": "At least one field (name or description) is required!"}), 400

        with SessionLocal() as session:
            group = session.query(Group).filter_by(group_name=old_name).one_or_none()

            # Check if the group to-be-updated exists
            if not group:
                return jsonify({"status": "failed", "message": "Group not found!"}), 404
            
            # Check if there is a group with the new name
            existing_group = session.query(Group).filter_by(group_name=new_name).first()
            if existing_group:
                return jsonify({"status": "failed", "message": "Group name already exists!"}), 400
            
            # Change the group name and description        
            if new_name:
                group.group_name = new_name
            if new_description:
                group.description = new_description

        return jsonify({"status": "success", "message": "Group updated successfully!"}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500


@groups_blueprint.route('/in/<group_id>', methods=['GET'])
def get_users_in_group(group_id: int):
    """
    Get the user information within a group of group_id, including user_id and username.
    """
    with SessionLocal() as session:
        users_in_group = session.query(User).join(
            UserGroups, User.user_id==UserGroups.c.user_id
        ).filter(UserGroups.c.group_id==group_id)
    
    return jsonify([{
        "user_id": user.user_id,
        "username": user.username
    } for user in users_in_group])


@groups_blueprint.route('/add-user-to-group/', methods=['POST'])
def add_user_to_group():
    """
    Request format:
        {
            "user_id": 4,
            "group_name": "Example Group"
        }
    """
    try: 
        
        with SessionLocal() as session:
        
            # Extracts data
            data = request.json
            user_id = data.get('user_id')
            group_name = data.get('group_name')
            
            # Checks if user and group exists
            group = session.query(Group).filter_by(group_name=group_name).one_or_none()
            user = session.query(User).filter_by(user_id=user_id).one_or_none()
            if not group and not user:
                return jsonify({"status": "failed", "message": "Group or user does not exist"}), 404
            
            # Checks if user is already in the group
            if user in group.users:
                return jsonify({"status": "failed", "message": "User is already in the group"}), 404
            
            # Let the user join the group
            group.users.append(user)
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500

    finally:
        session.close()
        

@groups_blueprint.route('/del-user-from-group/', methods=['DELETE'])
def del_user_from_group():
    """
    Delete a user from a group, given its user_id and group_id.
    Expects a JSON request:
        {
            "username": "Example Username",
            "group_name": "Example Group Name"
        }
    """
    
    try:
        data = request.json
        username = data.get("username")
        group_name = data.get("group_name")
        
        with SessionLocal() as session:
            user = session.query(User).filter_by(username=username).one_or_none()
            group = session.query(Group).filter_by(group_name=group_name).one_or_none()
            
            # Check if the user and group exist
            if not user or not group:
                return jsonify({"status": "failed", "message": "User or group does not exist, hence cannot be deleted."}), 404
            
            # Check if the user is in the group
            if group not in user.groups:
                return jsonify({"status": "failed", "message": "User not in the group!"}), 404
            
            # Remove the user from the group
            user.groups.remove(group)
        
        return jsonify({"status": "success", "message": "User removed from the group!"}), 200
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    