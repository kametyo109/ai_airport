# app.py
import streamlit as st
import random
import uuid
from datetime import datetime
import json
import os
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import threading
import nest_asyncio

# Apply nest_asyncio to allow running asyncio code in Streamlit
nest_asyncio.apply()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared data file
ISLANDS_FILE = 'islands.json'

# Function to load islands from file
def load_islands():
    if os.path.exists(ISLANDS_FILE):
        with open(ISLANDS_FILE, 'r') as f:
            islands_data = json.load(f)
            # Migrate old format to new format if needed
            for island_id, island in islands_data.items():
                # Check if using old format (with 'notes' instead of 'content')
                if 'content' not in island:
                    # Convert old format to new format
                    if 'notes' in island:
                        notes_content = "\n".join([note.get('content', '') for note in island.get('notes', [])])
                        island['content'] = notes_content
                    else:
                        island['content'] = ""

                    # Make sure we have updated_at field
                    if 'updated_at' not in island:
                        island['updated_at'] = island.get('created_at', datetime.now().isoformat())

            return islands_data
    return {}

# Function to save islands to file
def save_islands(islands):
    with open(ISLANDS_FILE, 'w') as f:
        json.dump(islands, f)

# Function to get random lines from text
def get_random_lines(text, count=3):
    """Get random lines from a text blob"""
    if not text or not isinstance(text, str) or not text.strip():
        return []

    # Split text into lines, filtering out empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return []

    # Get random lines
    return random.sample(lines, min(count, len(lines)))

# FastAPI routes
@app.get("/")
async def root():
    return {"message": "Idea Islands API is running. Use /api/islands/{island_id}/random to get random ideas."}

@app.get("/api/islands/{island_id}/random")
async def get_random_ideas(island_id: str, count: int = 3):
    # Load islands data
    islands = load_islands()

    if island_id not in islands:
        raise HTTPException(status_code=404, detail="Island not found")

    island = islands[island_id]

    # Get random lines
    random_lines = get_random_lines(island.get("content", ""), count)

    # Return formatted response
    return {
        "island_name": island["name"],
        "ideas": [f"Idea {i+1}: {line}" for i, line in enumerate(random_lines)]
    }

# Streamlit app functions
def create_island():
    """Create a new island with a unique ID"""
    island_id = str(uuid.uuid4())
    island_name = st.session_state.new_island_name

    if not island_name:
        st.error("Please enter an island name.")
        return

    # Load islands, update, save
    islands = load_islands()
    islands[island_id] = {
        "name": island_name,
        "content": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    save_islands(islands)

    st.session_state.new_island_name = ""
    st.success(f"Island '{island_name}' created successfully!")

def update_island_content(island_id):
    """Update an island's content"""
    content = st.session_state.get(f"island_content_{island_id}", "")

    # Load islands, update, save
    islands = load_islands()
    if island_id in islands:
        islands[island_id]["content"] = content
        islands[island_id]["updated_at"] = datetime.now().isoformat()
        save_islands(islands)
        st.success("Content updated successfully!")
    else:
        st.error("Island not found!")

def streamlit_app():
    st.title("Idea Islands")

    # Always reload islands from file to ensure sync with FastAPI
    islands = load_islands()

    tab1, tab2, tab3 = st.tabs(["Islands Dashboard", "Create Island", "API Access"])

    with tab1:
        st.header("Your Islands")

        if not islands:
            st.info("You don't have any islands yet. Create one in the 'Create Island' tab!")
        else:
            for island_id, island in islands.items():
                with st.expander(f"🏝️ {island['name']} (ID: {island_id})"):
                    # Ensure content key exists (for backwards compatibility)
                    if 'content' not in island:
                        island['content'] = ""

                    st.text_area(
                        "Island Content",
                        value=island["content"],
                        height=300,
                        key=f"island_content_{island_id}",
                        help="Enter your ideas, one per line. Each line will be treated as a separate idea."
                    )
                    st.button("Save Changes", key=f"save_btn_{island_id}",
                              on_click=update_island_content, args=(island_id,))

                    # Ensure updated_at exists (for backwards compatibility)
                    if 'updated_at' not in island:
                        island['updated_at'] = island.get('created_at', datetime.now().isoformat())

                    updated_time = datetime.fromisoformat(island["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"Last updated: {updated_time}")

                    # Preview random lines
                    if st.button("Preview 3 Random Ideas", key=f"random_{island_id}"):
                        random_lines = get_random_lines(island["content"])
                        if random_lines:
                            st.write("Random Ideas (as would be seen by ChatGPT):")
                            for i, line in enumerate(random_lines):
                                st.info(f"Idea {i+1}: {line}")
                        else:
                            st.warning("No ideas found! Add some content (one idea per line).")

    with tab2:
        st.header("Create a New Island")
        st.text_input("Island Name", key="new_island_name")
        st.button("Create Island", on_click=create_island)

    with tab3:
        st.header("API Access for ChatGPT")
        st.markdown("""
        ### How to Access Islands with ChatGPT

        Each island has a unique API endpoint that ChatGPT can access. Use ChatGPT's task feature to fetch random ideas from your islands.

        **Usage Instructions:**
        1. Enter each idea on a separate line in your island's content
        2. When ChatGPT visits the API endpoint, it will receive 3 randomly selected ideas in JSON format

        **API Endpoints:**
        """)

        # Get the hostname from Streamlit's config
        fastapi_port = 8000  # The port FastAPI will run on
        api_base_url = st.text_input("Your FastAPI base URL (e.g., https://your-app-domain.com:8000 or http://localhost:8000)",
                             placeholder="Enter your deployed FastAPI base URL")

        if api_base_url:
            st.markdown("### Your Island API Links")

            # Display a table with island names and their API endpoints
            data = []
            for island_id, island in islands.items():
                api_url = f"{api_base_url}/api/islands/{island_id}/random"
                data.append({
                    "Island Name": island['name'],
                    "API URL": api_url,
                    "ChatGPT Instruction": f"Please visit {api_url} and return the random ideas from this island named \"{island['name']}\"."
                })

            # If there are islands, display them in a dataframe
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, hide_index=True, use_container_width=True)

                # Also provide individual sections for easy copy-paste
                st.markdown("### Individual Islands")
                for island_id, island in islands.items():
                    with st.expander(f"🏝️ {island['name']}"):
                        api_url = f"{api_base_url}/api/islands/{island_id}/random"
                        st.code(api_url)
                        st.markdown("**ChatGPT Instruction:**")
                        st.markdown(f"""
                        ```
                        Please visit {api_url} and return the random ideas from this island named "{island['name']}".
                        ```
                        """)
            else:
                st.info("You don't have any islands yet. Create one in the 'Create Island' tab!")
        else:
            st.info("Enter your FastAPI base URL to see the API endpoints ChatGPT can access.")

        # Information on how to run the FastAPI server
        st.markdown("""
        ### Running the FastAPI Server

        To make the API endpoints available, you need to run the FastAPI server:

        ```bash
        # In one terminal, run Streamlit
        streamlit run app.py

        # In another terminal, run the FastAPI server
        python fastapi_server.py
        ```

        If you're deploying to a hosting service, you'll need to ensure both Streamlit and FastAPI are running.
        """)

# Start FastAPI in a separate thread when running locally
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Main entry point
if __name__ == "__main__":
    # Start the Streamlit app
    streamlit_app()
