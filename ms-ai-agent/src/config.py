"""
Configuration loader for the application.
"""
import os
from dotenv import load_dotenv

GITHUB_TOKEN = ""

def load_environment():
    """
    Loads environment variables from a .env file and ensures critical
    variables are set.
    """
    load_dotenv()
    
    required_variables = ["AZURE_OPENAI_KEY", "OPENAI_API_KEY"]
    for var in required_variables:
        if not os.environ.get(var):
            raise AssertionError(f"{var} environment variable not set.")

# Load environment variables on import
load_environment()

# You can also define other configurations here
# For example:
# LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

def set_github_token(token: str) -> None:
    global GITHUB_TOKEN
    if not isinstance(token, str):
        raise TypeError("token must be a string")
    GITHUB_TOKEN = token
    

def get_github_token() -> str:
    return GITHUB_TOKEN