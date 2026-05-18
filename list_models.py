from google import genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please add it to your .env file.")

client = genai.Client(api_key=api_key)
for model in client.models.list():
    print(model.name)
