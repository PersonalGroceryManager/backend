"""
Define the database metadata.
"""
# Standard Imports
from __future__ import annotations
from datetime import datetime
from typing import List, Tuple, Optional

# Third Party Imports
from sqlalchemy import Table, ForeignKey, Column, Integer, Float, DECIMAL, \
                       VARCHAR, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase): pass


# Association Tables (for many-to-many relationships) ------------------------- 
# A user can be in multiple groups, and a group consists of multiple users.
UserGroups = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.group_id', ondelete='CASCADE'), primary_key=True)
)

# Link each user to the quantity of items he/she bought. An item can be shared
# among users
UserItems = Table(
    'user_items',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.item_id', ondelete='CASCADE'), primary_key=True),
    # Units can refer to quantity or weight, depending on the item
    Column('unit', Integer, nullable=True)
)

class UserSpending(Base):
    __tablename__ = "user_spending"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.receipt_id", ondelete="CASCADE"), primary_key=True)
    cost: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships to User and Receipt
    user: Mapped["User"] = relationship("User", back_populates="spending")
    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="spending")

# Data Tables -----------------------------------------------------------------
class Group(Base):
    """
    SQLALchemy Database entry object.

    Args:
        id (int): Group ID as the primary key, Autoincremented
        group_name (VARCHAR(20)): Name of the group
        description(VARCHAR(50)): Description of the group, such as rules
    """
    
    __tablename__ = "groups"
    
    # ----- Columns ----- 
    group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Use string as it is more flexible to database types
    group_name: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    description: Mapped[str] = mapped_column(VARCHAR(100))
    
    
    # ----- Relationships -----
    # A group can have multiple users
    users: Mapped[List["User"]] = relationship("User", secondary=UserGroups, back_populates="groups")
    # A group can have multiple receipts
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="group")
    
    # ----- Methods -----
    def __repr__(self) -> str:
        return f"Group(id={self.group_id!r}, name = {self.name!r}, description = {self.description!r})"
    

class User(Base):
    """
    SQLAlchemy Database entry object.
    
    Args:
        user_id (int): User ID as the primary key, autoincremented
        username (String(10)): Username
        hashed_password (VARCHAR(100)): Hashed password of the user
        email (VARCHAR(100)): User Email, for forgotten password
    """
    
    __tablename__ = "users"
    
    # ----- Columns -----
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(VARCHAR(20))
    hashed_password: Mapped[str] = mapped_column(VARCHAR(100))
    email: Mapped[str] = mapped_column(VARCHAR(50))  # Needed for password reset
    
    # ----- Relationships -----
    # A user can join multiple groups
    groups: Mapped[List[Group]] = relationship("Group", secondary=UserGroups, back_populates="users")
    # A user can have multiple items
    items: Mapped[List[Item]] = relationship("Item", secondary=UserItems, back_populates="users")
    # A user can have multiple spendings across receipts
    spending: Mapped[List["UserSpending"]] = relationship("UserSpending", cascade="all, delete-orphan", back_populates="user")
    
    # ----- Methods -----
    def __repr__(self) -> str:
        return f"User"


class Receipt(Base):
    """
    SQLAlchemy Database entry object.
    
    Args:
        receipt_id (int): Primary key, autoincremented
        receipt_id (int): Assigned order ID
        slot_time (float): Time in UNIX epoch
        total_price (Decimal): Price of the receipt
        group_id (int): Group which the receipt belongs to.
        payment_card (int): Last four digit of a payment card
        locked_by (int): User ID of whoever is opening the receipt
        lock_timestamp (Decimal): The timestamp since the last user locked it
    """
    
    __tablename__ = "receipts"
    
    # ----- Columns -----
    receipt_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    slot_time: Mapped[datetime] = mapped_column(DateTime)
    total_price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.group_id', ondelete='CASCADE'))
    payment_card: Mapped[int]  # Last four digits of the payment card
    locked_by: Mapped[int] = mapped_column(Integer)          # User ID of whoever is opening the receipt
    lock_timestamp: Mapped[datetime] = mapped_column(DateTime)  # Timestamp of locks
    
    # ----- Relationships -----
    # Bi-directional relationship - plural 'items' as a receipt can contain multiple items
    items: Mapped[List[Item]] = relationship("Item", back_populates="receipt", cascade="all, delete-orphan")
    group: Mapped[Group] = relationship("Group", back_populates="receipts")
    # Each receipt is linked to the a list of spendings in UserSpending
    spending: Mapped[List["UserSpending"]] = relationship("UserSpending", cascade="all, delete-orphan", back_populates="receipt")

    # ----- Methods -----
    def __repr__(self):
        return f"Receipt ID: {self.receipt_id!r}, delivered at {self.slot_time!r}, paid GBP{self.price!r} with card no. {self.payment_card!r}"
    

class Item(Base):
    """
    SQLAlchemy Database entry object.
    
    Args:
        item_id (int): Primary key for an item, autoincremented
        name (string): Full item name
        receipt_id (int): Receipt ID
        quantity (int): Quantity of the item, if applicable.
        weight (float): Weight of the item, if applicable.
        price (Decimal): Price of the item.
    """
    
    __tablename__ = "items"
    
    # ----- Columns -----
    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(VARCHAR(255))
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.receipt_id'))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    price: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2))
    
    # ----- Relationships -----
    # One-to-many - an item only belong to one receipt
    receipt: Mapped[Receipt] = relationship("Receipt", back_populates="items")
    # Many-to-many - An item can belong to multiple users
    users: Mapped[User] = relationship("User", secondary=UserItems, back_populates="items")
