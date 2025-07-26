from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import google.generativeai as genai
import os

from src.memory import (
    load_preferences,
    update_preference,
    query_memory,
    add_memory,
    format_preferences_for_prompt
)
from src.planner import plan_travel
from src.executor import run_tasks

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set your API key in env or replace directly
model = genai.GenerativeModel("gemini-pro")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_streamed_response(websocket: WebSocket, text: str, delay: float = 0.03):
    for token in text.split():
        await websocket.send_text(token + " ")
        await asyncio.sleep(delay)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("👋 Hi there! I'm your AI Travel Assistant. What's your user ID?")
    user_id = await websocket.receive_text()

    prefs = load_preferences(user_id)
    if prefs:
        message = "🧠 Loaded your preferences:\n" + "\n".join([f"- {k.capitalize()}: {v}" for k, v in prefs.items()])
    else:
        message = "No preferences found. Let's create them."
    await websocket.send_text(message)

    # Step-by-step preference collection
    await websocket.send_text("📍 Where do you want to go?")
    destination = await websocket.receive_text()

    await websocket.send_text("📅 How many days is your trip?")
    days = await websocket.receive_text()

    await websocket.send_text("🎯 What are your interests?")
    interests = await websocket.receive_text()

    await websocket.send_text("💰 What is your travel budget (low, medium, high)?")
    budget = await websocket.receive_text()

    await websocket.send_text("🧳 What's your travel style (relaxed, adventure, cultural)?")
    style = await websocket.receive_text()

    # Save to memory
    update_preference(user_id, "destination", destination)
    update_preference(user_id, "days", days)
    update_preference(user_id, "interests", interests)
    update_preference(user_id, "budget", budget)
    update_preference(user_id, "style", style)

    context_snippets = query_memory(destination)
    if context_snippets:
        await websocket.send_text("📚 I found some related past memories:")
        for ctx in context_snippets:
            await websocket.send_text(f"• {ctx}")

    await websocket.send_text("🛠 Planning your trip now...")

    memory_text = format_preferences_for_prompt(user_id)
    tasks = plan_travel(destination, days, interests)

    result = run_tasks(
        tasks=tasks,
        destination=destination,
        days=days,
        interests=interests,
        budget=budget,
        memory_text=memory_text
    )

    await send_streamed_response(websocket, f"🗺️ Here’s your personalized itinerary:\n\n{result}")
    add_memory(user_id, f"Planned trip to {destination} for {days} days: {interests}, {style}, {budget}")
    await websocket.send_text("\n✅ Trip plan complete!")
    await websocket.send_text("💬 You can now ask me any other questions or get more info!")

    # Fallback chat loop
    while True:
        try:
            user_msg = await websocket.receive_text()
            if not user_msg.strip():
                continue

            await websocket.send_text("🤖 Thinking...")

            gemini_response = model.generate_content(user_msg)
            reply = gemini_response.text.strip()

            add_memory(user_id, user_msg, reply)  # Optional
            await send_streamed_response(websocket, reply)

        except Exception as e:
            await websocket.send_text(f"⚠️ Error: {str(e)}")
            break
