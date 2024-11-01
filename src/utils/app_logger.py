# Standard Imports
import os
import logging

# Third-Party Imports
from dotenv import load_dotenv

# Load environmental variable to check if logger is configured
load_dotenv()
LOG = os.getenv('LOG')


if LOG:    # TODO: This does not seem to work - it LOGS nevertheless
    # Configure the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Configure handlers
    file_handler = logging.FileHandler('flask.log')

    # Define a custom formatter that logs the parent folder and filename
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            # Get the full pathname of the module where the log message was generated
            full_path = record.pathname
            
            # Extract the filename
            filename = os.path.basename(full_path)
            
            # Extract the parent folder name
            parent_folder = os.path.basename(os.path.dirname(full_path))
            
            # Modify the log message format
            record.custom_filepath = f"{parent_folder}/{filename}"
            
            # Now use this in the log message format
            return super().format(record)

    # Create a log format with the custom filepath
    formatter = CustomFormatter('%(asctime)s - %(custom_filepath)s:%(lineno)d - %(levelname)s - %(message)s')

    # Apply formatter to handlers
    # console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    # logger.addHandler(console_handler)
    logger.addHandler(file_handler)

else:
    # Disable logging if LOG is set to False
    logging.disable(logging.CRITICAL)  # Disable all logging
