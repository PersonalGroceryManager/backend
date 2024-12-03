# Standard Imports
import os
import logging

# Third-Party Imports
from dotenv import load_dotenv

# Load environmental variable to check if logger is configured
load_dotenv()
LOG = os.getenv('LOG', False)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')


# Configure the main logger with the name 'main'
logger = logging.getLogger('main')

# Set the logging level to the environment variable
numeric_level = getattr(logging, LOG_LEVEL, logging.DEBUG)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {LOG_LEVEL}")
logger.setLevel(numeric_level)


# Define a custom formatter that logs the parent folder and filename
class CustomFormatter(logging.Formatter):
    
    def format(self, record):
        """Overide"""
        
        # Get the full pathname of the module where the log message was generated
        full_path = record.pathname
        
        # Extract the filename
        filename = os.path.basename(full_path)
        
        # Modify the log message format to show the filename
        record.custom_filepath = filename
        
        # Now use this in the log message format
        return super().format(record)

# Create a log format with the custom filepath
formatter = CustomFormatter('%(asctime)s - %(levelname)s - %(custom_filepath)s:%(lineno)d - %(message)s')

# Configure handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('flask.log')
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
