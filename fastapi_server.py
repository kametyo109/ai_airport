# fastapi_server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import json
import os
import random
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Idea Islands API")

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

# Root route with HTML response
@app.get("/html", response_class=HTMLResponse)
async def root_html():
    return """
    <html>
        <head>
            <title>Idea Islands API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                p { line-height: 1.6; }
                .endpoint { background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>Idea Islands API</h1>
            <p>The API is running successfully. Use the following endpoints:</p>
            <ul>
                <li class="endpoint">/api/islands - List all islands</li>
                <li class="endpoint">/api/islands/{island_id}/random - Get random ideas from an island</li>
                <li class="endpoint">/api/islands/{island_id}/html - Get random ideas in HTML format</li>
                <li class="endpoint">/api/islands/{island_id}/all - Get all ideas from an island</li>
                <li class="endpoint">/api/islands/{island_id}/all/html - Get all ideas in HTML format</li>
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
                <p>Random ideas URL: <a href="/api/islands/{island_id}/html">/api/islands/{island_id}/html</a></p>
                <p>All ideas URL: <a href="/api/islands/{island_id}/all/html">/api/islands/{island_id}/all/html</a></p>
            </div>
            """

    html += """
        </body>
    </html>
    """

    return html

# Get random ideas from a specific island (JSON)
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

# Get random ideas from a specific island (HTML)
@app.get("/api/islands/{island_id}/html", response_class=HTMLResponse)
async def get_random_ideas_html(island_id: str, count: int = 3):
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

    # Get random lines
    random_lines = get_random_lines(island.get("content", ""), count)

    html = f"""
    <html>
        <head>
            <title>Random Ideas from {island["name"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .idea {{ padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>Random Ideas from Island: {island["name"]}</h1>
    """

    if not random_lines:
        html += "<p>No ideas available on this island.</p>"
    else:
        for i, line in enumerate(random_lines):
            html += f"""
            <div class="idea">
                <strong>Idea {i+1}:</strong> {line}
            </div>
            """

    html += """
        </body>
    </html>
    """

    return html

# Plain text version for maximum compatibility
@app.get("/api/islands/{island_id}/text")
async def get_random_ideas_text(island_id: str, count: int = 3):
    islands = load_islands()

    if island_id not in islands:
        return {"error": "Island not found"}

    island = islands[island_id]

    # Get random lines
    random_lines = get_random_lines(island.get("content", ""), count)

    # Build a plain text response
    response_text = f"Random Ideas from Island: {island['name']}\n\n"

    if not random_lines:
        response_text += "No ideas available on this island."
    else:
        for i, line in enumerate(random_lines):
            response_text += f"Idea {i+1}: {line}\n"

    return {"text": response_text}

# Get all ideas from a specific island (JSON)
@app.get("/api/islands/{island_id}/all")
async def get_all_ideas(island_id: str):
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    # Get all lines
    lines = [line.strip() for line in island.get("content", "").splitlines() if line.strip()]

    # Format the response
    formatted_ideas = [f"Idea {i+1}: {line}" for i, line in enumerate(lines)]

    return {
        "island_name": island["name"],
        "ideas": formatted_ideas
    }

# Get all ideas from a specific island (HTML)
@app.get("/api/islands/{island_id}/all/html", response_class=HTMLResponse)
async def get_all_ideas_html(island_id: str):
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

    # Get all lines
    lines = [line.strip() for line in island.get("content", "").splitlines() if line.strip()]

    html = f"""
    <html>
        <head>
            <title>All Ideas from {island["name"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .idea {{ padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>All Ideas from Island: {island["name"]}</h1>
    """

    if not lines:
        html += "<p>No ideas available on this island.</p>"
    else:
        for i, line in enumerate(lines):
            html += f"""
            <div class="idea">
                <strong>Idea {i+1}:</strong> {line}
            </div>
            """

    html += """
        </body>
    </html>
    """

    return html

# Run the FastAPI server when this file is executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
