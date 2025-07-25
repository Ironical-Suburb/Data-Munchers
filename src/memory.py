import json
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_user_file(user_id):
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_preferences(user_id):
    """
    Load user preferences from JSON file.
    """
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_preferences(user_id, preferences):
    """
    Save user preferences to JSON file.
    """
    file_path = get_user_file(user_id)
    with open(file_path, 'w') as f:
        json.dump(preferences, f, indent=2)

def update_preference(user_id, key, value):
    """
    Update a specific preference.
    """
    prefs = load_preferences(user_id)
    prefs[key] = value
    save_preferences(user_id, prefs)
