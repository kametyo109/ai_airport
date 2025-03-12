# fastapi_server.py
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
import uvicorn
import json
import os
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Island Content API")

# Add CORS middleware with settings allowing ALL origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Path to the shared data file
ISLANDS_FILE = 'islands.json'

# Models for API requests
class IslandCreate(BaseModel):
    name: str

class IslandUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

class IslandData(BaseModel):
    islands: Dict[str, Any]

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

# Function to save islands to file
def save_islands(islands):
    with open(ISLANDS_FILE, 'w') as f:
        json.dump(islands, f)

# Root route
@app.get("/")
async def root():
    return {
        "message": "Island Content API is running",
        "usage": "Use /api/islands/{island_id} to view an island's content"
    }

# Root route with HTML response
@app.get("/html", response_class=HTMLResponse)
async def root_html():
    return """
    <html>
        <head>
            <title>Island Content API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                p { line-height: 1.6; }
                .endpoint { background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>Island Content API</h1>
            <p>The API is running successfully. Use the following endpoints:</p>
            <ul>
                <li class="endpoint">/api/islands - List all islands</li>
                <li class="endpoint">/api/islands/{island_id} - View island content</li>
                <li class="endpoint">/api/islands/{island_id}/update - Update island content</li>
                <li class="endpoint">/api/islands/sync - Sync all islands data</li>
            </ul>
        </body>
    </html>
    """

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

# HTML version of islands list
@app.get("/api/islands/html", response_class=HTMLResponse)
async def list_islands_html():
    islands = load_islands()

    html = """
    <html>
        <head>
            <title>Islands List</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                .island { margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Available Islands</h1>
    """

    if not islands:
        html += "<p>No islands found.</p>"
    else:
        for island_id, island in islands.items():
            html += f"""
            <div class="island">
                <h2>{island['name']}</h2>
                <p>ID: {island_id}</p>
                <p>Content URL: <a href="/api/islands/{island_id}">/api/islands/{island_id}</a></p>
            </div>
            """

    html += """
        </body>
    </html>
    """

    return html

# Get island content (JSON)
@app.get("/api/islands/{island_id}")
async def get_island_content(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    return {
        "island_name": island["name"],
        "content": island.get("content", "")
    }

# Get island content (HTML)
@app.get("/api/islands/{island_id}/html", response_class=HTMLResponse)
async def get_island_content_html(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        return """
        <html>
            <head>
                <title>Island Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    h1 { color: #d9534f; }
                </style>
            </head>
            <body>
                <h1>Island Not Found</h1>
                <p>The requested island does not exist.</p>
            </body>
        </html>
        """

    island = islands[island_id]
    content = island.get("content", "")

    html = f"""
    <html>
        <head>
            <title>Island: {island["name"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; margin-bottom: 20px; }}
                .content {{ white-space: pre-wrap; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <h1>Island: {island["name"]}</h1>
            <div class="content">{content}</div>
        </body>
    </html>
    """

    return html

# Create a new island
@app.post("/api/islands/create")
async def create_island(island: IslandCreate):
    islands = load_islands()

    # Generate a unique ID (simple UUID implementation)
    import uuid
    island_id = str(uuid.uuid4())

    # Create the island
    islands[island_id] = {
        "name": island.name,
        "content": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    save_islands(islands)

    return {
        "success": True,
        "id": island_id,
        "name": island.name
    }

# Update island content
@app.post("/api/islands/{island_id}/update")
async def update_island(island_id: str, update_data: IslandUpdate):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    # Update fields if provided
    if update_data.name is not None:
        islands[island_id]["name"] = update_data.name

    if update_data.content is not None:
        islands[island_id]["content"] = update_data.content

    # Update the timestamp
    islands[island_id]["updated_at"] = datetime.now().isoformat()

    save_islands(islands)

    return {
        "success": True,
        "id": island_id,
        "updated": {
            "name": update_data.name is not None,
            "content": update_data.content is not None
        }
    }

# Delete an island
@app.delete("/api/islands/{island_id}/delete")
async def delete_island(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    # Delete the island
    del islands[island_id]

    save_islands(islands)

    return {
        "success": True,
        "id": island_id
    }

# Sync all islands data
@app.post("/api/islands/sync")
async def sync_islands(data: IslandData):
    # Replace all islands with the provided data
    save_islands(data.islands)

    return {
        "success": True,
        "message": "Islands data synchronized successfully"
    }

# Run the FastAPI server when this file is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
