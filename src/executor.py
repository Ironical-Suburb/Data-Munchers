from dotenv import load_dotenv
import os
import time
import requests
import google.generativeai as genai
from datetime import datetime

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
    params = {"query": location}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    print("Location API response:", data)

    for item in data.get("data", []):
        if "dest_id" in item:
            return item["dest_id"]

    raise ValueError(f"No destination ID found in response for location: {location}")


def get_airport_code(city_name):
    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }
    params = {"query": city_name}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print("Flight location API response:", data)

    for item in data.get("data", []):
        if item.get("id", "").endswith(".AIRPORT") or item.get("id", "").endswith(".CITY"):
            return item["id"]

    raise ValueError(f"No airport/city code found for: {city_name}")


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
    hotels_raw = data.get("data", {}).get("hotels", [])

    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_date - checkin_date).days

    hotels = []
    for hotel in hotels_raw[:3]:
        price_per_night = hotel.get("priceBreakdown", {}).get("grossPrice", {}).get("value", 0)
        total_price = round(price_per_night * nights, 2)

        hotels.append({
            "name": hotel.get("accessibilityLabel", "N/A"),
            "price_per_night": price_per_night,
            "total_price": total_price,
            "photo": hotel.get("photoUrls", [""])[0],
            "score": hotel.get("property", {}).get("reviewScoreWord", "N/A"),
            "address": hotel.get("property", {}).get("address", {}).get("addressLine", "N/A"),
            "link": hotel.get("property", {}).get("url", "")
        })

    return hotels


def fetch_flights(origin_city, dest_city):
    origin_code = get_airport_code(origin_city)
    dest_code = get_airport_code(dest_city)

    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }
    params = {
        "fromId": origin_code,
        "toId": dest_code,
        "stops": "none",
        "pageNo": "1",
        "adults": "1",
        "sort": "BEST",
        "cabinClass": "ECONOMY",
        "currency_code": "USD"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print("Flight search API response:", data)

    flights = []
    for item in data.get("data", [])[:3]:
        flights.append({
            "airline": item.get("airline", "N/A"),
            "from": item.get("origin", "N/A"),
            "to": item.get("destination", "N/A"),
            "departure": item.get("departureDate", "N/A"),
            "price": item.get("price", 0),
            "deeplink": item.get("deeplink", "")
        })
    return flights
