# Third-Party Imports
from flask import session, jsonify
from passlib.context import CryptContext

# Project-Specific Imports
from src.utils.database import SessionLocal
from src.utils.models import User


class Authentication():
    
    def __init__(self):
        
        # Encryption context for password hashing
        self._pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        
    def hash_password(self, plain_password: str) -> str:
        return self._pwd_context.hash(plain_password)

    def _verify_password(self, plain_password: str, hashed_password: str):
        """
        Hash a plain password and verify if it is equal to the input hashed
        password (usually obtained from database entry).
        
        Inputs
        ------
        plain_password: str
        hashed_password: str

        Returns
        -------
        bool
            0: The passwords are not equal
            1: The passwords are equal
        """
        return self._pwd_context.verify(plain_password, hashed_password)
    
    def authenticate(self, username: str, password: str) -> int:
        """
        Authenticate the user given the username and password, setting the 
        required session cookies.
        
        Inputs
        ------
        username (str)
            Username
        password (str)
            Password to authenticate with the given username
        Returns
        -------
        int | bool: 
            int: user_id of the user with the given username and password
            None: User does not exist
        """
        try:
            with SessionLocal() as db_session:
                
                # Find the user with selected username. Not filtered by
                # username and password combination to prevent injection attack
                user = db_session.query(User).filter_by(username=username).first()
                
                # Match the provided password with the stored password
                if user and self._verify_password(password, user.hashed_password):
                    
                    # Setting flask session cookies
                    session['authenticated'] = True
                    session['user_id'] = user.user_id

                    return user.user_id

                # Return none for invalid credentials
                return None

        except Exception as e:
            print(str(e))
            return None

    
    def logout(self):
        """
        Logout function by removing the 'user_id' key from the backend session
        NOT USED
        """
        
        session.pop('user_id', None)
        return jsonify({'message': 'Logged out successfully'}), 200
