from src.memory import load_preferences, update_preference
from src.executor import fetch_hotels, fetch_flights, execute_task
from src.planner import plan_travel
from datetime import datetime

def needs_more_info(prefs):
    required = ["departure_city", "destination", "departure_date", "return_date", "interests", "budget"]
    return not all(prefs.get(k) for k in required)

def build_prompt(prefs):
    return plan_travel(
        prefs["destination"],
        prefs["days"] if "days" in prefs else "a few",
        prefs["interests"],
        prefs["budget"]
    )

def main():
    print("🌍 Welcome to your AI Travel Assistant!\n")
    user_id = input("Enter your user ID: ").strip()

    # Load previous preferences
    prefs = load_preferences(user_id)
    if prefs:
        print("🧠 Loaded previous preferences:")
        for k, v in prefs.items():
            print(f"- {k}: {v}")
    else:
        prefs = {}

    # Prompt user for missing inputs
    fields = {
        "departure_city": "Departure city",
        "destination": "Destination",
        "departure_date": "Departure date (YYYY-MM-DD)",
        "return_date": "Return date (YYYY-MM-DD)",
        "interests": "Travel interests",
        "budget": "Estimated travel budget in USD"
    }

    for key, label in fields.items():
        if not prefs.get(key):
            prefs[key] = input(f"{label}: ").strip()
            update_preference(user_id, key, prefs[key])

    # Auto-calculate days
    try:
        d1 = datetime.strptime(prefs["departure_date"], "%Y-%m-%d")
        d2 = datetime.strptime(prefs["return_date"], "%Y-%m-%d")
        prefs["days"] = (d2 - d1).days
    except Exception:
        prefs["days"] = "a few"

    # Generate base prompt
    full_prompt = build_prompt(prefs)

    # Fetch hotel options
    hotels = fetch_hotels(
        location=prefs["destination"],
        checkin=prefs["departure_date"],
        checkout=prefs["return_date"]
    )

    if hotels:
        hotel_info = "\n".join([
            f"- {h['name']}, ${h['price']} per night, {h['address']}, Score: {h['review_score']}"
            for h in hotels
        ])
        full_prompt += f"\n\n📍 Hotel Options:\n{hotel_info}"

    # Fetch flight options
    flights = fetch_flights(
        origin=prefs["departure_city"],
        destination=prefs["destination"],
        departure_date=prefs["departure_date"]
    )

    if flights:
        flight_info = "\n".join([
            f"- {f['airline']}: {f['from']} ➜ {f['to']} | Departure: {f['departure']} | Price: ${f['price']}"
            for f in flights
        ])
        full_prompt += f"\n\n✈️ Flight Options:\n{flight_info}"

    # Execute Gemini task
    print("\n🧠 Generating itinerary...\n")
    itinerary = execute_task(full_prompt)

    print("\n🗺️ Your Personalized Itinerary:\n")
    print(itinerary)

if __name__ == "__main__":
    main()
