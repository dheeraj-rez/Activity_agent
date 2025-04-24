import os
from dotenv import load_dotenv

def load_api_key() -> str:
    """
    Load API keys from environment variables.
    """
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
    
    return openai_api_key