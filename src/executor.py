from dotenv import load_dotenv  # Loads variable from .env or shell
import os  # Access environment variables
import time  # For retry delays
import google.generativeai as genai  # Gemini SDK

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

# Read the key from the environment
API_KEY = os.getenv("GEMINI_API_KEY")

# Create a Gemini client using your API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-pro" if needed

def execute_task(task, max_retries=3, delay=2):
    """Send a task prompt to Gemini with retry logic for errors."""
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(task)
            return response.text
        except Exception as e:
            print(f"[Attempt {attempt}] Gemini failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                return f"⚠️ Gemini failed after {max_retries} attempts: {e}"

def run_tasks(tasks, destination, days, interests, budget, memory_text):
    full_prompt = f"""
You are an expert travel planner. Use the following preferences and history to answer the tasks below.

User Preferences:
Destination: {destination}
Days: {days}
Interests: {interests}
Budget: {budget}
Other Info: {memory_text}

Tasks:
"""

    results = []
    for i, task in enumerate(tasks, 1):
        combined_task = full_prompt + f"\nTask {i}:\n{task}"
        answer = execute_task(combined_task)
        results.append(f"### Task {i} Result:\n{answer.strip()}\n")

    return "\n".join(results)
