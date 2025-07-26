from src.planner import plan_travel
from src.executor import run_tasks
from src.memory import format_preferences_for_prompt, update_preference

def main():
    print("🧪 Travel Planner CLI Test Mode\n")

    user_id = input("👤 Enter test user ID: ").strip()

    # Collect preferences
    destination = input("📍 Destination: ").strip()
    days = input("📅 How many days? ").strip()
    interests = input("🎯 Interests (comma-separated): ").strip()
    budget = input("💰 Budget (low, medium, high): ").strip()
    style = input("🧳 Travel style (relaxed, adventure, cultural): ").strip()

    # Save preferences just like the chat backend
    update_preference(user_id, "destination", destination)
    update_preference(user_id, "days", days)
    update_preference(user_id, "interests", interests)
    update_preference(user_id, "budget", budget)
    update_preference(user_id, "style", style)

    # Plan the trip
    tasks = plan_travel(destination, days, interests)

    # Load memory context
    memory_text = format_preferences_for_prompt(user_id)

    # Run task execution
    result = run_tasks(
        tasks=tasks,
        destination=destination,
        days=days,
        interests=interests,
        budget=budget,
        memory_text=memory_text
    )

    print("\n🗺️ Final Itinerary:\n")
    print(result)

if __name__ == "__main__":
    main()
