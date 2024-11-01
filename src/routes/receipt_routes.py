# Standard Imports
from datetime import datetime as dt
from typing import Tuple, Dict, List

# Third-Party Imports
from sqlalchemy import insert, update, desc
from flask import Blueprint, request, jsonify

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import Group, Receipt, Item, UserItems, UserSpending
from src.receipt_reader.SainsburysReceipt import SainsburysReceipt
from src.utils.app_logger import logger

receipt_blueprint = Blueprint('receipt', __name__)

@receipt_blueprint.route('/get-receipt-list/<int:group_id>', methods=['GET'])
def get_receipts_in_group(group_id: int):
    
    try:
        with SessionLocal() as session:
            logger.debug(f"Fetching receipt in group ID: {group_id}")
            receipts = session.query(Receipt).join(Group).filter(Group.group_id == group_id).order_by(desc(Receipt.slot_time)).all()

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


@receipt_blueprint.route('/add', methods=['POST'])
def add_receipt_to_group():
    
    try:
        group_id = request.form.get('group_id')
        file = request.files["file"]
        
        # File Validation
        if file.filename == '':
            logger.error("Invalid file.")
            return jsonify({"error": "No selected file"})

        # Not to be confused - receipt is the SainsburysReceipt object defined
        # in receipt_reader folder, whereas receipt_for_db is a database entry
        receipt = SainsburysReceipt(file)
        logger.debug("Received valid receipt.")
        
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
            added_receipt = session.query(Receipt).filter(Receipt.order_id==receipt.order_id, 
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
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 400


@receipt_blueprint.route('/get/<int:receipt_id>', methods=['GET'])
def get_receipt_items(receipt_id: int):
        
    try:
        logger.debug(f"Fetching item data for receipt ID: {receipt_id}")
        with SessionLocal() as session:
            items: List[Item] = session.query(Item).filter(Item.receipt_id==receipt_id).all()
            
            results = {
                "items":
                    [
                        {"item_id": item.item_id,
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "weight": item.weight,
                        "price": item.price}
                    for item in items]
            }
            logger.debug(f"Gathered receipt data to send.")
        return jsonify(results), 200

    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 400
    

@receipt_blueprint.route('<int:receipt_id>/add-user/<int:user_id>', methods=['POST'])    
def create_user_item_associations(receipt_id: int, user_id: int):
    """
    Create new entry in the user quantity table given the user and receipt ID.
    """
    try:
        # Data validation
        if not isinstance(receipt_id, int):
            msg = f"Receipt ID is not of type {int} with its content being {receipt_id}"
            logger.error(msg)
            return jsonify({"status": "failed", "message": msg})
        if not isinstance(user_id, int):
            msg = f"User ID is not of type {int} with its content being {user_id}"
            return jsonify({"status": "failed", "message": msg})
        
        # Create a new entry in the database
        with SessionLocal() as session:
            items: List[Item] = session.query(Item).filter(Item.receipt_id==receipt_id).all()
            for item in items:
                stmt = insert(UserItems).values(
                    user_id=user_id,
                    item_id=item.item_id,
                    unit=0,  # Default to zero
                )
                session.execute(stmt)
            session.commit()
            logger.info(f"Added user ID {user_id} to receipt ID {receipt_id}")
            
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        logger.error(e)
        return jsonify({"status": "failed", "message": e}), 400


@receipt_blueprint.route('/update/user-items', methods=['PUT'])
def update_user_item_associations():
    """
    Update a set of existing rows corresponding to the combination of user
    IDs and item IDs, usually after some modification.
        [
            {'user_id': 1, 'item_id': 1, 'unit': 0.1},
            {'user_id': 1, 'item_id': 2, 'unit': 1.0},
        ]
    """
    try:
        
        data = request.json
        
        # Ensure received data is a list
        if not isinstance(data, list):
            msg = f"Data is not of type list, but of type {type(data)}, with the content being {data}"
            logger.error(msg)
            return jsonify({"status": "failed", "message": msg})
        
        # Validate each entry in the dictionary
        for obj in data:
        
            # Ensure each content is a dictionary
            if not isinstance(obj, dict):
                msg = f"Content within data is not of type dict, but of type {type(data)}, with the content being {data}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg})
            
            # Ensure neccessary fields are present
            required_fields = ['user_id', 'item_id', 'unit']
            for field in required_fields:
                if field not in obj:
                    msg = f"Missing required field: {field}"
                    logger.error(msg)
                    return jsonify({"status": "failed", "message": msg}), 400
                
            # Ensure field types are correct
            if not isinstance(obj["user_id"], int):
                msg = f"user_id must be an integer. Received {obj['user_id']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["item_id"], int):
                msg = f"receipt_id must be an integer. Received {obj['receipt_id']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["unit"], (float, int)) or obj["unit"] < 0:
                msg = f"cost must be a positive number. Received {obj['unit']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400
            
        # Create a new entry in the database
        with SessionLocal() as session:
                
            for entry in data:
                stmt = update(UserItems).where(
                    (UserItems.c.user_id==entry["user_id"]) &
                    (UserItems.c.item_id==entry["item_id"])
                ).values(unit=entry["unit"])
                
                session.execute(stmt)
            session.commit()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 400
    

@receipt_blueprint.route('/get/user-items/<int:receipt_id>', methods=['GET'])
def get_user_item_associations(receipt_id: int):
    
    try:
        with SessionLocal() as session:
            results = session.query(UserItems).\
                join(Item, Item.item_id==UserItems.c.item_id).\
                filter(Item.receipt_id==receipt_id).all()
        
        user_item_association = {
            "user_item_association": [{
                'user_id': user_item_comb.user_id,
                'item_id': user_item_comb.item_id,
                'unit': user_item_comb.unit,
            } for user_item_comb in results]
        }

        return jsonify(user_item_association), 200
        
    except Exception as e:
        logger.info(str(e))
        

@receipt_blueprint.route('/add/user-cost/', methods=['POST'])
def add_user_costs():
    """
    Add a new entry of user spending given the user ID and receipt ID. 
    Expects a object structure JSON in the format of:    
        {"user_id": 1, "receipt_id": 2}
    """
    try:
        data: Dict = request.json
        logger.debug(f"Received user-cost data: {data}")
        
        # Check that data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Data is not a dict, but of type {type(data)}.")
            return jsonify({"status": "failed"}), 400

        # Ensure necessary fields are present
        required_fields = ["user_id", "receipt_id"]
        for field in required_fields:
            if field not in data:
                msg = f"Missing required field: {field}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400
                
        # Ensure field types are correct
        if not isinstance(data["user_id"], int):
            msg = f"user_id must be an integer. Received {data['user_id']} of type {type(data['user_id'])}"
            logger.error(msg)
            return jsonify({"status": "failed", "message": msg}), 400

        if not isinstance(data["receipt_id"], int):
            msg = f"receipt_id must be an integer. Received {data['receipt_id']} of type {type(data['receipt_id'])}"
            logger.error(msg)
            return jsonify({"status": "failed", "message": msg}), 400

        # Add new entries to the database
        with SessionLocal() as session:

            user_id = data.get("user_id")
            receipt_id = data.get("receipt_id")

            logger.debug(f"Preparing to add spending entry for user ID {user_id} on receipt ID ")
            stmt = insert(UserSpending).values(
                    user_id=user_id,
                    receipt_id=receipt_id,
                    cost=0)
            session.execute(stmt)
            session.commit()

        return jsonify({"status": "success"}), 200
                    
    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 400
    
    
@receipt_blueprint.route('/get/user-cost/<int:user_id>', methods=['GET'])
def get_user_costs(user_id: int):
    """
    Given a user ID, gets an array of the time (of the receipt) and cost spent
    on that receipt.
        [
            {"receipt_id" 1, "slot_time":  14-Jun-24, "cost": 12.78},
            {"receipt_id" 2, "slot_time":  15-Jun-24, "cost":  9.10}
        ]
    """
    try:
        
        # Validate that user_id is an integer
        if not isinstance(user_id, int):
            msg = f"User ID is not an int, but is of type {user_id}, with content user_id={user_id}"
            logger.error(msg)
            return jsonify({"status": "failed", "message": msg}), 400

        
        with SessionLocal() as session:
            # Performing an inner join where receipt ID matches and filter
            # by user ID
            # Perform an inner join and select the required fields
            results = session.query(
                Receipt.receipt_id,
                Receipt.slot_time,
                UserSpending.c.cost
            )\
            .join(UserSpending, UserSpending.c.receipt_id == Receipt.receipt_id)\
            .filter(UserSpending.c.user_id == user_id)\
            .all()  # Get all results
                
            # Return error 404 if results are no results are returned
            if not results:
                msg = f"No records found for the given user_id"
                logger.info(msg)
                return jsonify({"status": "failed", "message": msg}), 404
            
            # Initialize an empty list to store the dictionary
            data_list = []
            
            for row in results:
                data_dict = {"receipt_id": row.receipt_id,
                             "slot_time":  row.slot_time,
                             "cost":       row.cost}
                data_list.append(data_dict)
                
        return jsonify(data_list), 200

    except Exception as e:
        logger.critical(str(e))
        return jsonify({"status": "failed", "message": str(e)}), 400
    

@receipt_blueprint.route('/update/user-cost/', methods=['PUT'])
def update_user_costs():
    """
    Expects an array-based JSON structure containing the user ID, receipt ID
    and the user's spending in the receipt.
        [
            {"user_id": 1, "receipt_id": 2, "cost": 12.78},
            {"user_id:: 2, "receipt_id": 2, "cost":  9.10}
        ]
    """
    try:
        data: List[Dict] = request.json
        logger.debug(f"Received user-cost data: {data}")
        
        # Check that data is a list
        if not isinstance(data, list):
            logger.error(f"Data is not a list, but of type {type(data)}.")
            return jsonify({"status": "failed"}), 400

        # Validate each entry in the list
        for obj in data:

            # Ensure list content are dictionaries
            if not isinstance(obj, dict):
                msg = f"Expected dict, but received {type(obj)}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400
            
            # Ensure necessary fields are present
            required_fields = ["user_id", "receipt_id", "cost"]
            for field in required_fields:
                if field not in obj:
                    msg = f"Missing required field: {field}"
                    logger.error(msg)
                    return jsonify({"status": "failed", "message": msg}), 400
                
            # Ensure field types are correct
            if not isinstance(obj["user_id"], int):
                msg = f"user_id must be an integer. Received {obj['user_id']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["receipt_id"], int):
                msg = f"receipt_id must be an integer. Received {obj['receipt_id']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400

            if not isinstance(obj["cost"], (float, int)) or obj["cost"] < 0:
                msg = f"cost must be a positive number. Received {obj['cost']}"
                logger.error(msg)
                return jsonify({"status": "failed", "message": msg}), 400

        # Update old user spending entries
        with SessionLocal() as session:
            for entry in data:
                
                # Extract data from dictionary
                user_id = entry.get("user_id")
                receipt_id = entry.get("receipt_id")
                cost = entry.get("cost")
                
                stmt = update(UserSpending).where(
                        (UserSpending.c.user_id==user_id) &
                        (UserSpending.c.receipt_id==receipt_id))\
                            .values(cost=cost)
                session.execute(stmt)
            session.commit()

        return jsonify({"status": "success"}), 200
                    
    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "failed", "message": str(e)})
