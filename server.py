from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import google.generativeai as genai
from datetime import datetime

from src.memory import (
    load_preferences,
    update_preference,
    query_memory,
    add_memory,
    format_preferences_for_prompt
)
from src.planner import plan_travel
from src.executor import run_tasks

# ===== Gemini Config =====
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# ===== User Credentials (Basic Demo Login) =====
USER_CREDENTIALS = {
    "priyanshu": "secret123",
    "guest": "letmein"
}

# ===== App Config =====
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_streamed_response(websocket: WebSocket, text: str, delay: float = 0.03):
    """Send response word-by-word with typing effect."""
    for token in text.split():
        await websocket.send_text(token + " ")
        await asyncio.sleep(delay)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Step 1: Login
    await websocket.send_text("👋 Hi there! I'm your AI Travel Assistant.")
    await websocket.send_text("👤 Please enter your username:")
    username = await websocket.receive_text()

    await websocket.send_text("🔒 Please enter your password:")
    password = await websocket.receive_text()

    if username not in USER_CREDENTIALS or USER_CREDENTIALS[username] != password:
        await websocket.send_text("❌ Invalid credentials. Connection closing.")
        await websocket.close()
        return

    user_id = username

    # Step 2: Load Preferences
    prefs = load_preferences(user_id)
    if prefs:
        message = "🧠 Loaded your preferences:\n" + "\n".join([f"- {k.capitalize()}: {v}" for k, v in prefs.items()])
    else:
        message = "No preferences found. Let's create them."
    await websocket.send_text(message)

    # Step 3: Collect Preferences
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

    # Save preferences
    update_preference(user_id, "destination", destination)
    update_preference(user_id, "days", days)
    update_preference(user_id, "interests", interests)
    update_preference(user_id, "budget", budget)
    update_preference(user_id, "style", style)

    # Step 4: Query Memory
    context_snippets = query_memory(destination)
    if context_snippets:
        await websocket.send_text("📚 I found some related past memories:")
        for ctx in context_snippets:
            await websocket.send_text(f"• {ctx}")

    await websocket.send_text("🛠 Planning your trip now...")

    # Step 5: Generate Itinerary
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
    await websocket.send_text("💬 You can now ask me anything else!")

    # Step 6: Open-ended Gemini Chat
    while True:
        try:
            user_msg = await websocket.receive_text()
            if not user_msg.strip():
                continue

            await websocket.send_text("🤖 Thinking...")

            # Inject memory into prompt
            memory_context = "\n".join(f"• {m}" for m in query_memory(user_msg))
            gemini_prompt = f"""
You're a helpful travel assistant. Use the following memory if relevant:

{memory_context if memory_context else 'No previous memory available.'}

User message: {user_msg}
"""

            # Retry-safe Gemini call
            reply = ""
            for attempt in range(3):
                try:
                    gemini_response = model.generate_content(gemini_prompt)
                    reply = gemini_response.text.strip()
                    break
                except Exception as e:
                    if attempt == 2:
                        reply = f"⚠️ Gemini failed after 3 attempts: {e}"
                    else:
                        await asyncio.sleep(1)

            await send_streamed_response(websocket, reply)
            add_memory(user_id, f"User asked: {user_msg}\nReply: {reply}")

        except Exception as e:
            await websocket.send_text(f"⚠️ Error: {str(e)}")
            break
