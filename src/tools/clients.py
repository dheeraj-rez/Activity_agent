from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not openai_client:
    print("🚨 OpenAI client not initialized. Check your API key.")
    raise ValueError("OpenAI client not initialized. Check your API key.")  

