from src.memory import load_preferences, update_preference
from src.planner import plan_travel  
from src.executor import run_tasks   

def main():
    print("Welcome to your AI Travel Assistant!\n")
    user_id = input("Enter your user ID: ").strip()

    # Load saved preferences
    prefs = load_preferences(user_id)
    if prefs:
        print("\nLoaded your travel preferences:")
        for key, val in prefs.items():
            print(f"- {key}: {val}")
    else:
        print("\nNo preferences found. Let's set them up!")

    # Get user input
    destination = input("\nWhere do you want to travel? ")
    days = input("How many days is your trip? ")
    interests = input("What are your interests (e.g., history, food, art)? ")

    # Save new input as preferences
    update_preference(user_id, "destination", destination)
    update_preference(user_id, "days", days)
    update_preference(user_id, "interests", interests)

    # Plan the trip and get results
    tasks = plan_travel(destination, days, interests)
    result = run_tasks(tasks, destination, days, interests, prefs)

    print("\n====== Your Personalized Itinerary ======\n")
    print(result)
    print("\n=========================================")

if _name_ == "_main_":
    main()
