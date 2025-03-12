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

# Basic HTML wrapper for content
def html_wrapper(title, body_content):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
</head>
<body>
    {body_content}
</body>
</html>"""

# Handle both GET and HEAD methods for all routes
@app.api_route("/{full_path:path}", methods=["HEAD"])
async def head_route(full_path: str):
    # Return a 200 OK response with proper headers for HEAD requests
    return Response(
        status_code=200,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS"
        }
    )

# Simple test endpoint
@app.get("/test")
async def test_endpoint():
    html_content = html_wrapper(
        "Test Page",
        "<h1>Test Page</h1><p>This is a simple test page.</p>"
    )
    return HTMLResponse(
        content=html_content,
        headers={"Content-Type": "text/html; charset=utf-8"}
    )

# Root route
@app.get("/")
async def root():
    body_content = """
    <h1>Island Content API</h1>
    <p>The API is running successfully. Use the following endpoints:</p>
    <ul>
        <li>/api/islands - List all islands</li>
        <li>/api/islands/{island_id} - View island content</li>
    </ul>
    """
    html_content = html_wrapper("Island Content API", body_content)
    return HTMLResponse(
        content=html_content,
        headers={"Content-Type": "text/html; charset=utf-8"}
    )

# List all islands
@app.get("/api/islands")
async def list_islands():
    islands = load_islands()

    # Build the HTML body content
    body_content = "<h1>Available Islands</h1>"

    if not islands:
        body_content += "<p>No islands found.</p>"
    else:
        for island_id, island in islands.items():
            body_content += f"""
            <div>
                <h2>{island['name']}</h2>
                <p><strong>ID:</strong> {island_id}</p>
                <p><a href="/api/islands/{island_id}">View island content</a></p>
            </div>
            """

    html_content = html_wrapper("Islands List", body_content)
    return HTMLResponse(
        content=html_content,
        headers={"Content-Type": "text/html; charset=utf-8"}
    )

# Get island content
@app.get("/api/islands/{island_id}")
async def get_island_content(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        not_found_content = html_wrapper(
            "Island Not Found",
            "<h1>Island Not Found</h1><p>The requested island does not exist.</p>"
        )
        return HTMLResponse(
            content=not_found_content,
            status_code=404,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

    island = islands[island_id]
    content = island.get("content", "")

    # Convert line breaks to <br> tags for proper HTML display
    formatted_content = content.replace('\n', '<br>\n')

    body_content = f"""
    <h1>Island: {island["name"]}</h1>
    <div>{formatted_content}</div>
    """

    html_content = html_wrapper(f"Island: {island['name']}", body_content)
    return HTMLResponse(
        content=html_content,
        headers={"Content-Type": "text/html; charset=utf-8"}
    )

# Plain text version of island content
@app.get("/api/islands/{island_id}/text")
async def get_island_content_text(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        return PlainTextResponse(
            content="Island not found",
            status_code=404,
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )

    island = islands[island_id]
    content = island.get("content", "")

    return PlainTextResponse(
        content=f"Island: {island['name']}\n\n{content}",
        headers={"Content-Type": "text/plain; charset=utf-8"}
    )

# Get island content in JSON format
@app.get("/api/json/islands/{island_id}")
async def get_island_content_json(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    return JSONResponse(
        content={
            "island_name": island["name"],
            "content": island.get("content", "")
        },
        headers={"Content-Type": "application/json"}
    )

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

    return JSONResponse(
        content={
            "success": True,
            "id": island_id,
            "name": island.name
        }
    )

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

    return JSONResponse(
        content={
            "success": True,
            "id": island_id,
            "updated": {
                "name": update_data.name is not None,
                "content": update_data.content is not None
            }
        }
    )

# Delete an island
@app.delete("/api/islands/{island_id}/delete")
async def delete_island(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    # Delete the island
    del islands[island_id]

    save_islands(islands)

    return JSONResponse(
        content={
            "success": True,
            "id": island_id
        }
    )

# Sync all islands data
@app.post("/api/islands/sync")
async def sync_islands(data: IslandData):
    # Replace all islands with the provided data
    save_islands(data.islands)

    return JSONResponse(
        content={
            "success": True,
            "message": "Islands data synchronized successfully"
        }
    )

# Run the FastAPI server when this file is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
