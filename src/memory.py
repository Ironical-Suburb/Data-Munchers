import json
import os

# Create a central directory for user memory storage
PREFERENCE_DIR = os.getenv("PREFERENCE_DIR", "data")
os.makedirs(PREFERENCE_DIR, exist_ok=True)

def get_user_file(user_id):
    """Returns the full path to the user's preference file."""
    return os.path.join(PREFERENCE_DIR, f"{user_id}.json")

def load_preferences(user_id):
    """Load user preferences from JSON file. Returns empty dict if not found or corrupt."""
    file_path = get_user_file(user_id)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[Warning] Corrupt memory file for {user_id}. Returning empty.")
        return {}

def save_preferences(user_id, preferences):
    """Save the full user preferences dictionary to disk."""
    file_path = get_user_file(user_id)
    with open(file_path, 'w') as f:
        json.dump(preferences, f, indent=2)

def update_preference(user_id, key, value):
    """Update a specific key in the user's preferences."""
    prefs = load_preferences(user_id)
    prefs[key] = value
    save_preferences(user_id, prefs)

def get_preference(user_id, key, default=None):
    """Get a single preference value with an optional fallback."""
    prefs = load_preferences(user_id)
    return prefs.get(key, default)

def clean_preferences(user_id, allowed_keys):
    """Remove any preferences not in the allowed list (e.g., if structure changed)."""
    prefs = load_preferences(user_id)
    cleaned = {k: v for k, v in prefs.items() if k in allowed_keys}
    save_preferences(user_id, cleaned)

def format_preferences_for_prompt(user_id):
    """Convert user preferences into natural language text for Gemini prompt."""
    prefs = load_preferences(user_id)
    return f"""
    User's Past Preferences:
    - Destination: {prefs.get('destination', 'Not specified')}
    - Interests: {prefs.get('interests', 'Not specified')}
    - Budget: {prefs.get('budget', 'Not specified')}
    - Style: {prefs.get('style', 'Not specified')}
    """
