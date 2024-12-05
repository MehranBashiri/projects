import json
import logging
import re
from functools import wraps
from logging_config import setup_logging  # Import the setup_logging function

# Set up logging configuration
setup_logging()

# Custom exception for invalid user input
class InvalidInputError(Exception):
    def __init__(self, message):
        super().__init__(message)

# Custom exception for invalid relatives data
class InvalidRelativesDataError(Exception):
    def __init__(self, message):
        super().__init__(message)

# Decorator for logging function calls
def log_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"{func.__name__} returned successfully: {result}")
            return result
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

@log_function_call
def get_user_preferences():
    """
    Collect user preferences for route optimization: least time, least cost, or balanced.
    Validates the user input using regular expressions and raises an error for invalid input.
    """
    preferences = {}
    print("Select your route preference:")
    print("1. Least Time")
    print("2. Least Cost")
    print("3. Balanced Time and Cost")
    
    while True:
        choice = input("Enter your choice (1/2/3): ").strip()
        
        # Validate input using regex for numeric values (1, 2, or 3)
        if not re.match(r"^[1-3]$", choice):
            logging.error(f"Invalid choice: {choice}")
            raise InvalidInputError("Invalid choice. Please select 1, 2, or 3.")
        
        if choice == "1":
            preferences["preference"] = "least_time"
            break
        elif choice == "2":
            preferences["preference"] = "least_cost"
            break
        elif choice == "3":
            preferences["preference"] = "balanced"
            break

    logging.info(f"User preference: {preferences['preference']}")
    return preferences

@log_function_call
def validate_relatives_data(data):
    """
    Validate that each relative has the required fields: name, latitude, and longitude.
    """
    required_fields = ["name", "latitude", "longitude"]
    for relative in data:
        if not all(field in relative for field in required_fields):
            logging.error(f"Missing required field in relative data: {relative}")
            raise InvalidRelativesDataError("Missing required field in relative data.")
    logging.info("Relatives data validated successfully.")

@log_function_call
def load_relatives(file_path="data/relatives.json"):
    """
    Load relatives' data from the specified JSON file.
    Handles missing file, malformed JSON, file permission, and malformed data errors.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        validate_relatives_data(data)
        logging.info(f"Successfully loaded relatives data from {file_path}")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError("Relatives data file not found. Please check the file path.")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        raise ValueError(f"Error decoding JSON in {file_path}: {e}")
    except PermissionError:
        logging.error(f"Permission denied when accessing the file: {file_path}")
        raise PermissionError(f"Permission denied when accessing the file: {file_path}")
    except InvalidRelativesDataError as e:
        logging.error(f"Invalid relatives data: {e}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error loading file {file_path}: {e}")
        raise Exception(f"Unexpected error: {e}")
