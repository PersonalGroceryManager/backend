# Third-Party Imports
from flask import Blueprint, request, jsonify
from sqlalchemy import select

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import Group, User, UserGroups
from src.utils.Authentication import Authentication

groups_blueprint = Blueprint('groups', __name__)
auth = Authentication()


@groups_blueprint.route('', methods=['GET', 'POST', 'OUT', 'DELETE'])
def manage_groups():
    """
    General route for group management.
    
    GET: Get all available groups
    POST: Create a group given group name and description
    PUT: Update an existing group given a new group name and description
    DELETE: Delete a group.
    """
    # GET: Get all available groups
    if request.method == 'GET':
        try:
            with SessionLocal() as session:

                groups = session.query(Group).all()
                
                # Raise no content error if no groups found
                if not groups:
                    return jsonify({"error": "No Content",
                                    "message": "No groups available"}), 404
                
                # Successful code
                return jsonify([{
                    "group_id": group.group_id,
                    "group_name": group.group_name,
                    "description": group.description
                } for group in groups]), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # POST: Create a group
    elif request.method == 'POST':
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No group name provided!"}), 400

        group_name = data.get('group_name')
        group_desc = data.get('description')
        
        # Verify group name is provided
        if not group_name:
            return jsonify({"error": "Group name is required!"}), 400

        try:
            with SessionLocal() as session:
                
                if session.query(Group).filter_by(group_name=group_name)\
                                       .first():
                    return jsonify({"message": "Group with this name \
                        already exists!"}), 409

                new_group = Group(group_name=group_name, 
                                  description=group_desc)
                session.add(new_group)
                session.commit()
                
                # Fetch the newly created group, including the auto-incremented
                # group_id
                session.refresh(new_group)
                
                return jsonify({"message": "Group created successfully!",
                                "group": {
                                    "group_id": new_group.group_id,
                                    "group_name": new_group.group_name,
                                    "description": new_group.description
                                    }
                                }), 201

        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500

    # PUT: Update a group given a new group name (required) and description 
    # (optional)
    elif request.method == 'PUT':
        
        data = request.json
    
        try: 
            old_name = data.get('old_name')
            new_name = data.get('new_name')
            new_description = data.get('description')
        
            if not new_name:
                return jsonify({
                    "error": "Bad Request",
                    "message": "Name must be provided"}), 400

            with SessionLocal() as session:
                group = session.query(Group).\
                    filter_by(group_name=old_name).one_or_none()

                # Check if the group to-be-updated exists
                if not group:
                    return jsonify({"error": "Group not found!"}), 404
                
                # Check if there is a group with the new name
                existing_group = session.query(Group)\
                    .filter_by(group_name=new_name)\
                        .first()
                if existing_group:
                    return jsonify({"Error": "A group with this name already \
                        exists!"}), 400
                
                # Change the group name and description        
                if new_name:
                    group.group_name = new_name
                if new_description:
                    group.description = new_description

            return jsonify({"status": "success", "message": "Group updated successfully!"}), 200
        
        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500

    # DELETE: Delete a group based on a group name
    elif request.method == 'DELETE':
        
        data = request.json
        group_name = data.get('group_name', False)
        
        if not group_name:
            return jsonify({"error": "No group name provided!"}), 400

        try:
            
            with SessionLocal() as session:
                group = session.query(Group).\
                    filter_by(group_name=group_name).one_or_none()
                if not group:
                    return jsonify({"error": "Group not found!"}), 404
                session.delete(group)

            # Upon successful deletion, return 204 - no content
            return '', 204
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

@groups_blueprint.route('/<int:group_id>', methods=['GET'])
def get_group_info(group_id: int):
    """
    Get the name and description of a group
    """
    try:
        with SessionLocal() as session:
            
            group = session.execute(select(Group)\
                .where(Group.group_id == group_id)).one_or_none()
            
            # Raise 404 Not Found error if no group with this ID is found
            if not group:
                return jsonify({
                    "error": "Not Found",
                    "message": "Group with given ID not found"
                }), 404
            
            # Return group ID, name and description if successful
            return jsonify({
                "message": "Group found",
                "group_id": group_id,
                "group_name": group.group_name,
                "description": group.description
            }), 200

    except Exception as e:
        return jsonify({"error": "Internat Server Error"}), 500


@groups_blueprint.route('/resolve/<string:group_name>', methods=['GET'])
def resolve_group_name(group_name: str):
    
    with SessionLocal() as session:
        group_id = session.scalar(
            select(Group.group_id).where(Group.group_name == group_name))
        
        if not group_id:
            return jsonify({
                "error": "Not Found",
                "message": f"No group with name '{group_name}' is found"
            }), 400
        
    return jsonify({
        "message": "Group resolved successfully", "group_id": group_id}), 200
   
     
@groups_blueprint.route('/<int:group_id>/users', methods=['GET'])
def get_all_users_in_group(group_id: int):
    """
    Get the user information within a group of group_id, including user_id and username.
    """
    with SessionLocal() as session:
        users_in_group = session.query(User).join(
            UserGroups, User.user_id==UserGroups.c.user_id
        ).filter(UserGroups.c.group_id==group_id)
        
        if not users_in_group:
            return jsonify({"error": "No user found in this group!"}), 404
    
    return jsonify([{
        "user_id": user.user_id,
        "username": user.username
    } for user in users_in_group])


@groups_blueprint.route('/<int:group_id>/users/<int:user_id>', 
                        methods=['POST', 'DELETE'])
def manage_users_in_group(group_id: int, user_id: int):
    """
    Create or delete a user from a group given user_id and group_id
    
    From the perspective of the frontend, this is usually accessed after
    resolving a group name using alternative routes.
    """
    
    if request.method == 'POST':
        
        try: 
            
            with SessionLocal() as session:
                
                # Checks if user and group exists
                group = session.query(Group)\
                    .filter_by(group_id=group_id).one_or_none()
                user = session.query(User)\
                    .filter_by(user_id=user_id).one_or_none()
                if not group and not user:
                    return jsonify({"error": "Group or user does not exist"}), 404
                
                # Checks if user is already in the group
                if user in group.users:
                    return jsonify({"error": "User is already in the group"}), 409
                
                # Let the user join the group
                group.users.append(user)
            
                return jsonify({"message": "User added to group"}), 200
        
        except Exception as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500

        finally:
            session.close()
            
    elif request.method == 'DELETE':
        
        try:
            with SessionLocal() as session:
                user = session.query(User)\
                    .filter_by(user_id=user_id).one_or_none()
                group = session.query(Group)\
                    .filter_by(group_id=group_id).one_or_none()
                
                # Check if the user and group exist
                if not user or not group:
                    return jsonify(
                        {"error": "Not Found", 
                         "message": "User or group does not exist"
                         }), 404
                
                # Check if the user is in the group
                if group not in user.groups:
                    return jsonify({"error": "Not Found", 
                                    "message": "User not in the group"}), 404
                
                # Remove the user from the group
                user.groups.remove(group)
            
            return jsonify({"message": "User removed from the group!"}), 200
    
        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500
    