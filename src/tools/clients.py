from openai import OpenAI
from mistralai import Mistral
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not openai_client:
    print("🚨 OpenAI client not initialized. Check your API key.")
    raise ValueError("OpenAI client not initialized. Check your API key.")  

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
if not mistral_client:
    print("🚨 Mistral client not initialized. Check your API key.")
    raise ValueError("Mistral client not initialized. Check your API key.")