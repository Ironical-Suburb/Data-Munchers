import os
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ===== File-Based Preferences =====
DATA_DIR = "data"
MEMORY_EXPORT = "memory_export.json"
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
    with open(get_user_file(user_id), 'w') as f:
        json.dump(preferences, f, indent=2)

def update_preference(user_id, key, value):
    prefs = load_preferences(user_id)
    prefs[key] = value
    save_preferences(user_id, prefs)

def format_preferences_for_prompt(user_id):
    prefs = load_preferences(user_id)
    if not prefs:
        return "No preferences found."
    return "\n".join(f"{k.capitalize()}: {v}" for k, v in prefs.items())

# ===== Vector-Based Memory (ChromaDB Persistent Client) =====
client = chromadb.PersistentClient(path="./vector_store")
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("memory", embedding_function=embedding_fn)

def add_memory(user_id: str, text: str, reply: str = None):
    now = datetime.utcnow().isoformat()
    combined = f"{text}\n{reply}" if reply else text
    doc_id = f"{user_id}_{len(collection.peek())}"
    collection.add(
        documents=[combined],
        metadatas=[{"user_id": user_id, "timestamp": now}],
        ids=[doc_id]
    )

def query_memory(query: str, top_k=3, since=None):
    """
    Search memory using semantic similarity and optional time filtering.
    `since`: ISO timestamp string for filtering entries.
    """
    results = collection.query(query_texts=[query], n_results=top_k)
    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if since:
        try:
            cutoff = datetime.fromisoformat(since)
            filtered = [
                doc for doc, meta in zip(documents, metadatas)
                if "timestamp" in meta and datetime.fromisoformat(meta["timestamp"]) >= cutoff
            ]
            return filtered
        except Exception:
            return documents  # fallback
    return documents

def export_memory():
    """Export entire memory collection to a JSON file."""
    all_data = collection.get()
    with open(MEMORY_EXPORT, "w") as f:
        json.dump({
            "documents": all_data["documents"],
            "metadatas": all_data["metadatas"],
            "ids": all_data["ids"]
        }, f, indent=2)

def import_memory():
    """Import memory from a previously exported JSON file."""
    if not os.path.exists(MEMORY_EXPORT):
        return
    with open(MEMORY_EXPORT, "r") as f:
        data = json.load(f)
        for doc, meta, doc_id in zip(data["documents"], data["metadatas"], data["ids"]):
            collection.add(
                documents=[doc],
                metadatas=[meta],
                ids=[doc_id]
            )
