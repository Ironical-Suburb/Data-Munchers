# Technical Explanation

## 1. Agent Workflow

Describe step-by-step how your agent processes an input:
1. Receive user input
  Via React, user provides: 
    departure city, destination, travel dates, interests, budget

2. (Optional) Retrieve relevant memory  
  memory.py checks if past trips or preferences exists and loads additional information to give Gemini

3. Plan sub-tasks (e.g., using ReAct / BabyAGI pattern)  
  planner.py constructs a master prompt incorporating all user inputs. Missing information is requested.
  The prompt is sent to Gemini to break down trip into tasks e.g. itinerary, accomodations, flights.

4. Call tools or APIs as needed  
  executor.py handles each tool call
    It uses Gemini for task execution
    Makes real-time calls to RapidAPI (Booking.com) to fetch:
      hotel listings via fetch_hotels()
      flight details via fetch_flights()

5. Summarize and return final output  
    Gemini composes a complete itinerary and merges it with real-time data.


## 2. Key Modules

- **Planner** (`planner.py`): Handles goal decomposition and prompt engineering. Calls run_tasks() from executor.py with a structured prompt for Gemini.
- **Executor** (`executor.py`): Executes tasks step-by-step using Gemini Flash. Integrates hotel/flight APIs, processes results, and combines them with LLM output.
- **Memory Store** (`memory.py`): Implements persistent storage for user history. Remembers previous destinations and preferences for personalization.
- **Main** (`main.py`): Collects user input, loads memory, calls planner and executor modules, and displays the final itinerary. Acts as the entry point for CLI usage.

## 3. Tool Integration

List each external tool or API and how you call it:
- Booking.com RapidAPI (v1)
    get_destination_id(location): get destination ID
    get_airport_code(city_name): get airport code
    fetch_hotels(location, checkin, checkout): real-time hotels listing
    fetch_flights(origin_city, dest_city): real-time flight details

## 4. Observability & Testing

Explain your logging and how judges can trace decisions:
- Logging: Each execution logs tool calls, API responses, and Gemini input/output into a local file for traceability. 
- Testing: A manual test block (if __name__ == "__main__") tests get_destination_id(), get_airport_code(), etc.

## 5. Known Limitations

Be honest about edge cases or performance bottlenecks:
- Booking.com API rate limits can block hotel/flight search, requiring retries or mocking fallback.
- If user submits an invalid or ambiguous city name, destination ID lookup may fail.
- Although Gemini is guided with structured prompts, occasional overconfident or off-topic answers can appear.

