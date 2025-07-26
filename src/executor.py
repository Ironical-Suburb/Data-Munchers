from dotenv import load_dotenv
import os
import time
import requests
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def execute_task(task, max_retries=3, delay=2):
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


def get_destination_id(location):
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }
    params = {
        "query": location
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    print("Location API response:", data)

    # Find first valid destination with dest_id
    for item in data.get("data", []):
        if "dest_id" in item:
            return item["dest_id"]

    raise ValueError(f"No destination ID found in response for location: {location}")


def fetch_hotels(location, checkin, checkout):
    dest_id = get_destination_id(location)

    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }

    params = {
        "dest_id": dest_id,
        "search_type": "CITY",
        "adults": "1",
        "room_qty": "1",
        "units": "metric",
        "temperature_unit": "c",
        "languagecode": "en-us",
        "currency_code": "USD",
        "checkin_date": checkin,
        "checkout_date": checkout
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    hotels = []
    for hotel in data.get("data", {}).get("hotels", [])[:3]:
        hotels.append({
            "name": hotel.get("accessibilityLabel", "N/A"),
            "price": hotel.get("priceBreakdown", {}).get("grossPrice", {}).get("value", "N/A"),
            "photo": hotel.get("photoUrls", ["N/A"])[0],
            "score": hotel.get("property", {}).get("reviewScoreWord", "N/A")
        })

    return hotels


def fetch_flights(origin, destination, departure_date):
    url = "https://skyscanner44.p.rapidapi.com/search-extended"

    querystring = {
        "origin": origin,
        "destination": destination,
        "departureDate": departure_date,
        "currency": "USD",
        "adults": "1",
        "stops": "0"
    }

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "skyscanner44.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    flights = []
    for f in data.get("itineraries", [])[:3]:
        flight_info = f["legs"][0]
        flights.append({
            "airline": flight_info.get("carriers", [{}])[0].get("name", "N/A"),
            "from": flight_info.get("origin", {}).get("name"),
            "to": flight_info.get("destination", {}).get("name"),
            "departure": flight_info.get("departure"),
            "arrival": flight_info.get("arrival"),
            "duration": flight_info.get("duration"),
            "price": f.get("price", {}).get("raw")
        })

    return flights
