# Standard Imports
import logging
from datetime import datetime as dt
from typing import Tuple, Dict, List
from werkzeug.utils import secure_filename

# Third-Party Imports
from sqlalchemy import select, insert, update, desc
from flask import Blueprint, request, jsonify

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import User, Group, Receipt, Item, UserItems, UserSpending
from src.receipt_reader.SainsburysReceipt import SainsburysReceipt
from src.utils.app_logger import logger
from src.routes.group_routes import groups_blueprint

receipt_blueprint = Blueprint('receipts', __name__)

# Module-level logging inherited from 'main'
logger = logging.getLogger('main.receipt_routes')

# Nest group-related operations under 'groups/<group_id>/receipts'
@groups_blueprint.route('<int:group_id>/receipts', methods=['GET'])
def get_receipts_in_group(group_id: int):
    
    logger.info(f"Attempting to fetch receipts of group with ID {group_id}.")
    
    try:
        with SessionLocal() as session:
            logger.debug(f"Fetching receipt in group ID: {group_id}")
            receipts = session.query(Receipt).join(Group)\
                .filter(Group.group_id == group_id)\
                    .order_by(desc(Receipt.slot_time)).all()

            results = {
                "receipts": [
                    {
                        "receipt_id": receipt.receipt_id,
                        "order_id": receipt.order_id,
                        "slot_time": receipt.slot_time,
                        "total_price": receipt.total_price,
                        "payment_card": receipt.payment_card,
                    } 
                    for receipt in receipts
                ]
            }
            logger.debug(f"Sending receipt JSON...")
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    
    finally:
        session.close()


@groups_blueprint.route('/<int:group_id>/receipts', methods=['POST'])
def add_receipt_to_group(group_id: int):
    
    logger.info(f"Attempting to add receipt to group with ID {group_id}.")
    
    try:
        
        # Validate that group exists
        with SessionLocal() as session:
            group = session.scalar(select(Group)\
                .where(Group.group_id == group_id))
            
            # Return 404 Not Found error if group with this ID does not exist
            if not group:
                return jsonify({"error": "Not Found",
                               "message": "No group with this ID found"}), 404
        
        # Extract file object
        file = request.files.get("file")
        
        # File Validation - if invalid file type, raise 400 Bad Request
        if not file or file.filename == '':
            logger.error("Invalid file.")
            return jsonify({"error": "Bad Request",
                            "message": "No file provided"}), 400
        
        # Additional verification to ensure it is a .pdf file
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "Bad Request",
                            "message": "Expected PDF file"}), 400
                            
        # Secure filename to remove dangerous characters
        filename = secure_filename(file.filename)
        logger.debug(f"Received valid receipt with name: {filename}")
        
        # Not to be confused - receipt is the SainsburysReceipt object defined
        # in receipt_reader folder, whereas receipt_for_db is a database entry
        receipt = SainsburysReceipt(file)
        
        # Ensure the receipt is new - return Resource Already Exists error when
        # a receipt with the same order ID is found in the specified group
        with SessionLocal() as session:
            
            receipt_exists_in_group = session.query(Receipt)\
                .filter(Receipt.order_id==receipt.order_id,
                        Receipt.group_id==group_id)\
                .one_or_none()
                
            if receipt_exists_in_group:
                return jsonify({"message": 
                    f"Receipt with order ID {receipt.order_id} already\
                        exists in group with ID: {group_id}"}), 409
        
        # Add receipt to database
        receipt_for_db = Receipt(order_id=receipt.order_id,
                              slot_time=receipt.order_date,
                              total_price=receipt.total_price,
                              group_id=group_id,
                              payment_card=receipt.payment_card,
                              # Not locked by user yet so set as 0
                              locked_by=0,
                              # Set lock_timestamp arbitrarily to now
                              lock_timestamp=dt.now())
        
        with SessionLocal() as session:
            
            # Add the receipt and flush it to generate receipt id for the 
            # uploaded receipt to be referenced by items
            session.add(receipt_for_db)
            session.flush()
            added_receipt = session.query(Receipt)\
                .filter(Receipt.order_id==receipt.order_id, 
                        Receipt.group_id==group_id).first()
            
            # Add items in receipt to database
            for item in receipt.item_list:
                item_for_db = Item(item_name=item["item_name"],
                                   receipt_id=added_receipt.receipt_id,
                                   quantity=item["quantity"],
                                   weight=item["weight"],
                                   price=item["price"])
            
                session.add(item_for_db)
            session.commit()
        
        logger.debug("Receipt successfully added to group.")
        return jsonify({"message": "Receipt successfully added to group"}), 201
        
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": "Internal Server Error",
                        "message": str(e)}), 500


@receipt_blueprint.route('/<int:receipt_id>/items', methods=['GET'])
def get_receipt_items(receipt_id: int):
    
    logger.info(f"Attempting to fetch receipt items with receipt ID {receipt_id}.")
        
    try:
        
        with SessionLocal() as session:
            
            # Query for all items pertaining to the receipt ID
            items: List[Item] = session.query(Item)\
                .filter(Item.receipt_id==receipt_id).all()
                
            # Raise 404 Not Found error if no items are found
            if not items:
                return jsonify({
                    "error": "Not Found",
                    "message": "No items found associated with this receipt"
                }), 404
            
            results = [{"item_id": item.item_id,
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "weight": item.weight,
                        "price": item.price}
                       for item in items]

            logger.info(f"Successfully gathered receipt item data to send.")

        return jsonify(results), 200

    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": "Internal Server Error", 
                        "message": str(e)}), 500
    

@receipt_blueprint.route('<int:receipt_id>/users/<int:user_id>', 
                         methods=['POST'])
def create_user_item_associations(receipt_id: int, user_id: int):
    """
    Create new entry in the user quantity table given the user and receipt ID.
    """
    logger.info(f"Attempting to create new association between user \
        (user ID = {user_id}) and receipt (receipt ID = {receipt_id})")
    
    try:
        # Data type validation
        if not isinstance(receipt_id, int):
            msg = f"Receipt ID is not of type {int} with \
                its content being {receipt_id}"
            logger.error(msg)
            return jsonify({"error": "Internal Server Error", 
                            "message": msg}), 500
        if not isinstance(user_id, int):
            msg = f"User ID is not of type {int} with \
                its content being {user_id}"
            return jsonify({"error": "Internal Server Error", 
                            "message": msg}), 500
            
        # Verify that user exists
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.user_id == user_id))
            if not user:
                return jsonify({"error": "Not Found",
                                "message": "No user with this ID exists"}),\
                                    404
        
        # Verify that receipt exists
        with SessionLocal() as session:
            receipt = session.execute(select(Receipt.receipt_id)
                                      .where(Receipt.receipt_id == receipt_id))
            if not receipt:
                return jsonify({"error": "Not Found",
                                "message": "No receipt with this ID exists"}),\
                                    404
        
        with SessionLocal() as session:
            
            # Create new entries to link the new user to all items in receipt
            items: List[Item] = session.query(Item)\
                .filter(Item.receipt_id==receipt_id).all()
            
            for item in items:
                stmt = insert(UserItems).values(
                    user_id=user_id,
                    item_id=item.item_id,
                    unit=0,
                )
                session.execute(stmt)
            session.commit()
            logger.info(f"Added user ID {user_id} to receipt ID {receipt_id}")

        return jsonify({"message": "User added to this receipt"}), 201
    
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error", "message": e}), 500


@receipt_blueprint.route('/user-items', methods=['PUT'])
def update_user_item_associations():
    """
    Update a set of existing rows corresponding to the combination of user
    IDs and item IDs, usually after some modification.
        [
            {'user_id': 1, 'item_id': 1, 'unit': 0.1},
            {'user_id': 1, 'item_id': 2, 'unit': 1.0},
        ]
    """
    logger.info(f"Attempting to create new association between user and items.")

    try:
        
        data = request.json
        
        # Ensure received data is a list
        if not isinstance(data, list):
            msg = f"Data is not of type list, but of type {type(data)}, with the content being {data}"
            logger.error(msg)
            return jsonify({"error": "Internal Server Error", 
                            "message": msg}), 500
        
        # Validate each entry in the dictionary
        for obj in data:
        
            # Ensure each content is a dictionary
            if not isinstance(obj, dict):
                msg = f"Content within data is not of type dict, but of type {type(data)}, with the content being {data}"
                logger.error(msg)
                return jsonify({"error": "Internal Server Error", 
                                "message": msg}), 500
            
            # Ensure neccessary fields are present
            required_fields = ['user_id', 'item_id', 'unit']
            for field in required_fields:
                if field not in obj:
                    msg = f"Missing required field: {field}"
                    logger.error(msg)
                    return jsonify({"error": "Internal Server Error", 
                                    "message": msg}), 500   
             
            # Ensure field types are correct
            if not isinstance(obj["user_id"], int):
                msg = f"user_id must be an integer. Received {obj['user_id']}"
                logger.error(msg)
                return jsonify({"error": "Internal Server Error", 
                                "message": msg}), 500
                
            if not isinstance(obj["item_id"], int):
                msg = f"receipt_id must be an integer. Received {obj['receipt_id']}"
                logger.error(msg)
                return jsonify({"error": "Internal Server Error", 
                                "message": msg}), 500
                
            if not isinstance(obj["unit"], (float, int)) or obj["unit"] < 0:
                msg = f"cost must be a positive number. Received {obj['unit']}"
                logger.error(msg)
                return jsonify({"error": "Internal Server Error", 
                                "message": msg}), 500
            
        # Create a new entry in the database
        with SessionLocal() as session:
                
            for entry in data:
                
                user_id, item_id = entry["user_id"], entry["item_id"]
                
                # Ensure user with this user ID exists
                user = session.execute(select(User)\
                    .where(User.user_id == user_id))
                if not user:
                    return jsonify({
                        "error": "Not Found",
                        "message": "No user with this user_id found"
                    }), 404
                    
                # Ensure item with this item ID exists
                item = session.execute(select(UserItems)\
                    .where(UserItems.c.item_id == item_id))
                if not item:
                    return jsonify({
                        "error": "Not Found",
                        "message": "No user with this item_id found"
                    }), 404
                
                stmt = update(UserItems).where(
                    (UserItems.c.user_id==entry["user_id"]) &
                    (UserItems.c.item_id==entry["item_id"])
                ).values(unit=entry["unit"])
                
                session.execute(stmt)
            session.commit()

        return jsonify({"message": "Updated successfully"}), 200

    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": "Internal Server Error", 
                        "message": str(e)}), 500
    

@receipt_blueprint.route('/user-items/<int:receipt_id>', methods=['GET'])
def get_user_item_associations(receipt_id: int):
    
    logger.info(f"Attempting to fetch user-item associations from receipt ID \
        {receipt_id}")
    
    try:
        with SessionLocal() as session:
            
            # Verify that the receipt with the provided ID exists
            receipt = session.execute(select(Receipt).\
                where(Receipt.receipt_id == receipt_id)).one_or_none()
            if not receipt:
                return jsonify({
                    "error": "Not Found",
                    "message": "Receipt with this ID does not exist"
                }), 404
            
            # Execute the results
            results = session.query(UserItems).\
                join(Item, Item.item_id==UserItems.c.item_id).\
                filter(Item.receipt_id==receipt_id).all()
        
        user_item_association = [{
            'user_id': user_item_comb.user_id,
            'item_id': user_item_comb.item_id,
            'unit': user_item_comb.unit,
            } for user_item_comb in results]

        return jsonify(user_item_association), 200
    
    # Raise internal server error
    except Exception as e:
        logger.info(str(e))
        return jsonify({"error": "Internal Server Error",
                        "message": "Failed to get user and item mappings"}),\
                            500
