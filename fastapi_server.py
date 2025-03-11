# fastapi_server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
import random
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Idea Islands API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the shared data file
ISLANDS_FILE = 'islands.json'

# Function to load islands from file
def load_islands():
    if os.path.exists(ISLANDS_FILE):
        with open(ISLANDS_FILE, 'r') as f:
            islands_data = json.load(f)
            # Check for old format and migrate if needed
            for island_id, island in islands_data.items():
                if 'content' not in island and 'notes' in island:
                    notes_content = "\n".join([note.get('content', '') for note in island.get('notes', [])])
                    island['content'] = notes_content

                if 'content' not in island:
                    island['content'] = ""

                if 'updated_at' not in island:
                    island['updated_at'] = island.get('created_at', datetime.now().isoformat())

            return islands_data
    return {}

# Function to get random lines from text content
def get_random_lines(text, count=3):
    if not text or not isinstance(text, str) or not text.strip():
        return []

    # Split text into lines, filtering out empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return []

    # Get random lines
    return random.sample(lines, min(count, len(lines)))

# Root route
@app.get("/")
async def root():
    return {
        "message": "Idea Islands API is running",
        "usage": "Use /api/islands/{island_id}/random to get random ideas from an island"
    }

# List all islands
@app.get("/api/islands")
async def list_islands():
    islands = load_islands()
    result = []

    for island_id, island in islands.items():
        result.append({
            "id": island_id,
            "name": island["name"]
        })

    return result

# Get random ideas from a specific island
@app.get("/api/islands/{island_id}/random")
async def get_random_ideas(island_id: str, count: int = 3):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    # Get random lines
    random_lines = get_random_lines(island.get("content", ""), count)

    # Format the response
    formatted_ideas = [f"Idea {i+1}: {line}" for i, line in enumerate(random_lines)]

    return {
        "island_name": island["name"],
        "ideas": formatted_ideas
    }

# Run the FastAPI server when this file is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
