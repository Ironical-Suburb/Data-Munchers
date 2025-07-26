from src.memory import load_preferences, update_preference
from src.executor import fetch_hotels, fetch_flights, execute_task
from src.planner import plan_travel
from datetime import datetime

def build_prompt(prefs, remaining_budget, hotel_info, flight_info):
    return f"""
You are a travel expert. Please create a personalized itinerary for the following user preferences:

Destination: {prefs['destination']}
Days: {prefs['days']}
Interests: {prefs['interests']}
Total Budget: ${prefs['budget']}
Hotel Cost: ${prefs['hotel_total']}
Flight Cost: ${prefs['flight_total']}
Remaining Budget: ${remaining_budget}

Hotel Options:
{hotel_info}

Flight Options:
{flight_info}

Plan activities, food, transport, and entertainment such that it fits within the remaining budget of ${remaining_budget}. Avoid mentioning hotel or flight costs again.
"""

def main():
    print("🌍 Welcome to your AI Travel Assistant!\n")
    user_id = input("Enter your user ID: ").strip()

    prefs = load_preferences(user_id) or {}
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

    try:
        d1 = datetime.strptime(prefs["departure_date"], "%Y-%m-%d")
        d2 = datetime.strptime(prefs["return_date"], "%Y-%m-%d")
        prefs["days"] = (d2 - d1).days
    except Exception:
        prefs["days"] = "a few"

    # 🏨 Fetch hotels
    hotels = fetch_hotels(
        location=prefs["destination"],
        checkin=prefs["departure_date"],
        checkout=prefs["return_date"]
    )
    prefs["hotel_total"] = hotels[0]["total_price"] if hotels else 0

    hotel_info = "\n".join([
        f"- {h['name']} | ${h['total_price']} total (${h['price_per_night']}/night) | Score: {h['score']} | [View Hotel]({h['link']})"
        for h in hotels
    ]) if hotels else "No hotels found."

    # ✈️ Fetch flights
    flights = fetch_flights(
        prefs["departure_city"],
        prefs["destination"]
    )
    prefs["flight_total"] = flights[0]["price"] if flights else 0

    flight_info = "\n".join([
        f"- {f['airline']} | {f['from']} ➜ {f['to']} | Departure: {f['departure']} | ${f['price']} | [Book Flight]({f['deeplink']})"
        for f in flights
    ]) if flights else "No flights found."

    # 🧮 Remaining budget
    total_budget = float(prefs["budget"])
    flight_cost = float(prefs["flight_total"])
    hotel_cost = float(prefs["hotel_total"])
    remaining_budget = round(total_budget - flight_cost - hotel_cost, 2)

    if remaining_budget <= 0:
        print("⚠️ Your flight and hotel costs exceed or consume your budget. Please adjust your budget or travel dates.")
        return

    full_prompt = build_prompt(prefs, remaining_budget, hotel_info, flight_info)

    print("\n🧠 Generating itinerary...\n")
    itinerary = execute_task(full_prompt)
    print("\n🗺️ Your Personalized Itinerary:\n")
    print(itinerary)

if __name__ == "__main__":
    main()
