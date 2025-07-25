def plan_itinerary(location, days, interests, budget):
    return [
        f"You are a professional travel planner. List the most popular cities or attractions in {location} for a traveler interested in {interests}. Keep it to 3–5 destinations. No vague suggestions.",
        f"Plan a detailed {days}-day itinerary for a trip to {location} focused on {interests}. Show 1–2 main activities per day. Include estimated cost per activity. Format as: Day X: Activity - Cost.",
        f"List 2–3 budget-friendly hotels or guesthouses in {location}. Include estimated nightly cost and one-line description. Stay under {budget} total if possible.",
        f"List 5 must-try local dishes or street foods in {location}. Describe each briefly.",
        f"Give 3 travel safety tips or cultural dos/don’ts for visiting {location}. Be specific and up-to-date."
    ]

''' Test block to see if the function prints correctly

if __name__ == "__main__":
    tasks = plan_itinerary("Rome", 3, "history", 1000)
    for t in tasks:
        print("-", t)

'''