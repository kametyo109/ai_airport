# fastapi_server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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

# Run the FastAPI server when this file is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
