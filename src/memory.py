import os
import json
import uuid
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ===== File-based Preferences =====
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_user_file(user_id):
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_preferences(user_id):
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_preferences(user_id, preferences):
    file_path = get_user_file(user_id)
    with open(file_path, 'w') as f:
        json.dump(preferences, f, indent=2)

def update_preference(user_id, key, value):
    prefs = load_preferences(user_id)
    prefs[key] = value
    save_preferences(user_id, prefs)

def format_preferences_for_prompt(user_id):
    prefs = load_preferences(user_id)
    if not prefs:
        return "No preferences saved."
    return "\n".join(f"{k.capitalize()}: {v}" for k, v in prefs.items())

# ===== Vector-Based Memory (Semantic) =====
client = chromadb.PersistentClient(path="./vector_store")
collection = client.get_or_create_collection("memory")
model = SentenceTransformer("all-MiniLM-L6-v2")

def add_memory(user_id: str, text: str):
    """Add a memory entry (text) with timestamp for a user."""
    timestamp = datetime.now().isoformat()
    embedding = model.encode(text).tolist()
    memory_id = f"{user_id}_{uuid.uuid4()}"
    metadata = {"user_id": user_id, "timestamp": timestamp}
    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[memory_id]
    )

def query_memory(query: str, top_k=3, after_date: str = None):
    """
    Query vector memory for top-k similar documents.
    Optionally filter by timestamp (ISO format 'YYYY-MM-DDTHH:MM:SS').
    """
    embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=top_k)
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results.get("metadatas") else []

    if after_date:
        after_dt = datetime.fromisoformat(after_date)
        docs = [
            doc for doc, meta in zip(docs, metas)
            if datetime.fromisoformat(meta["timestamp"]) > after_dt
        ]

    return docs

def format_memory_snippets_for_prompt(query: str, top_k=3, after_date: str = None):
    snippets = query_memory(query, top_k=top_k, after_date=after_date)
    if not snippets:
        return "No related memory found."
    return "\n".join(f"• {s}" for s in snippets)

def reset_user_memory(user_id: str):
    """Remove all vector memory entries related to a specific user."""
    all_ids = collection.peek()["ids"]
    user_ids = [id for id in all_ids if id.startswith(f"{user_id}_")]
    if user_ids:
        collection.delete(ids=user_ids)

# ===== Export / Import Memory =====
def export_memory_to_json(filepath="memory_export.json"):
    """Export entire memory collection to a JSON file."""
    data = collection.peek()
    records = [
        {"id": id, "text": doc, "metadata": meta}
        for id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
    ]
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)
    return filepath

def import_memory_from_json(filepath="memory_export.json"):
    """Import memory entries from a JSON file into the collection."""
    with open(filepath, "r") as f:
        records = json.load(f)
    for r in records:
        embedding = model.encode(r["text"]).tolist()
        collection.add(
            documents=[r["text"]],
            embeddings=[embedding],
            ids=[r["id"]],
            metadatas=[r["metadata"]]
        )
