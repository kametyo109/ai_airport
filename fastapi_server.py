# fastapi_server.py
from fastapi import FastAPI, HTTPException, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any, List
import uvicorn
import json
import os
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Island Content API", docs_url=None, redoc_url=None)

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

# Function to generate HTML for an island
def generate_island_html(island_name, content):
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Island: {island_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }}
                h1 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }}
                .content {{ white-space: pre-wrap; line-height: 1.5; }}
                footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Island: {island_name}</h1>
            <div class="content">{content}</div>
            <footer>Content retrieved from Island Content API</footer>
        </body>
    </html>
    """

# Handle both GET and HEAD methods for all routes
@app.api_route("/{full_path:path}", methods=["HEAD"])
async def head_route(full_path: str):
    # Simply return a 200 OK response for HEAD requests
    return Response(status_code=200)

# Root route
@app.get("/", response_class=HTMLResponse)
async def root(user_agent: Optional[str] = Header(None)):
    # Return HTML by default
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Island Content API</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }
                h1 { color: #333; }
                p { line-height: 1.6; }
                .endpoint { background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; margin-bottom: 10px; }
                footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.8em; color: #666; }
            </style>
        </head>
        <body>
            <h1>Island Content API</h1>
            <p>The API is running successfully. Use the following endpoints:</p>
            <ul>
                <li class="endpoint">/api/islands - List all islands</li>
                <li class="endpoint">/api/islands/{island_id} - View island content</li>
            </ul>
            <footer>Island Content API - Web scraper friendly</footer>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# List all islands
@app.get("/api/islands", response_class=HTMLResponse)
async def list_islands(user_agent: Optional[str] = Header(None)):
    islands = load_islands()

    # Return HTML by default
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Islands List</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }
                h1 { color: #333; }
                .island { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
                .island h2 { margin-top: 0; }
                a { color: #0366d6; text-decoration: none; }
                a:hover { text-decoration: underline; }
                footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.8em; color: #666; }
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
                <p><strong>ID:</strong> {island_id}</p>
                <p><a href="/api/islands/{island_id}">View island content</a></p>
            </div>
            """

    html += """
            <footer>Island Content API - Web scraper friendly</footer>
        </body>
    </html>
    """

    return HTMLResponse(content=html)

# Get island content
@app.get("/api/islands/{island_id}", response_class=HTMLResponse)
async def get_island_content(island_id: str, user_agent: Optional[str] = Header(None)):
    islands = load_islands()

    if island_id not in islands:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Island Not Found</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }
                        h1 { color: #d9534f; }
                        footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.8em; color: #666; }
                    </style>
                </head>
                <body>
                    <h1>Island Not Found</h1>
                    <p>The requested island does not exist.</p>
                    <p><a href="/api/islands">Back to island list</a></p>
                    <footer>Island Content API - Web scraper friendly</footer>
                </body>
            </html>
            """,
            status_code=404
        )

    island = islands[island_id]
    content = island.get("content", "")

    html_content = generate_island_html(island["name"], content)
    return HTMLResponse(content=html_content)

# JSON API endpoints (for programmatic access)

# Get island content in JSON
@app.get("/api/json/islands/{island_id}")
async def get_island_content_json(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    return {
        "island_name": island["name"],
        "content": island.get("content", "")
    }

# Create a new island
@app.post("/api/islands/create")
async def create_island(island: IslandCreate):
    islands = load_islands()

    # Generate a unique ID
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
