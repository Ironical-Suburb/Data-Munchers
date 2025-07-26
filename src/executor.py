#executor.py
from dotenv import load_dotenv # Loads variable from .env or shell
import os # Access environment variables
import google.generativeai as genai # Gemini SDK

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

# Read the key from the environment
API_KEY = os.getenv("GEMINI_API_KEY")

# Create a Gemini client using your API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash") # or "gemini-pro" if needed

def execute_task(task):
    '''Send a task prompt to Gemini and return the AI-generated response'''
    response = model.generate_content(task)
    return response.text

#Text block (optional)
'''
if __name__ == "__main__":
    sample_task = "List 3 budget-friendly guesthouse in Kyoto with nightly prices under $50."
    answer = execute_task(sample_task)
    print("Gemini Response:\n", answer)
'''
