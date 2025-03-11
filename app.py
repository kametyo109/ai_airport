import streamlit as st
import random
import uuid
from datetime import datetime
import json
import os
import pandas as pd

# Initialize session state for islands if not exists
if 'islands' not in st.session_state:
    st.session_state.islands = {}

# Function to load islands from file
def load_islands():
    if os.path.exists('islands.json'):
        with open('islands.json', 'r') as f:
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
    with open('islands.json', 'w') as f:
        json.dump(islands, f)

# Load islands at startup
if not st.session_state.islands:
    st.session_state.islands = load_islands()

def create_island():
    """Create a new island with a unique ID"""
    island_id = str(uuid.uuid4())
    island_name = st.session_state.new_island_name

    if not island_name:
        st.error("Please enter an island name.")
        return

    st.session_state.islands[island_id] = {
        "name": island_name,
        "content": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    save_islands(st.session_state.islands)
    st.session_state.new_island_name = ""
    st.success(f"Island '{island_name}' created successfully!")

def update_island_content(island_id):
    """Update an island's content"""
    content = st.session_state.get(f"island_content_{island_id}", "")

    st.session_state.islands[island_id]["content"] = content
    st.session_state.islands[island_id]["updated_at"] = datetime.now().isoformat()
    save_islands(st.session_state.islands)
    st.success("Content updated successfully!")

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

def display_static_html_view(island_id):
    """Display an extremely simple HTML view of random ideas for ChatGPT"""
    if island_id not in st.session_state.islands:
        html = """
        <html>
        <body>
            <h1>Error: Island not found</h1>
        </body>
        </html>
        """
        st.markdown(html, unsafe_allow_html=True)
        return

    island = st.session_state.islands[island_id]

    # Get random lines
    random_lines = get_random_lines(island.get("content", ""), 3)

    # Create extremely simple HTML with no JavaScript dependencies
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1>Island: {island['name']}</h1>
        <p>Here are 3 random ideas from this island:</p>
    """

    if not random_lines:
        html += "<p>No ideas available on this island yet.</p>"
    else:
        for i, line in enumerate(random_lines):
            html += f"<p><strong>Idea {i+1}:</strong> {line}</p>"

    html += """
    </body>
    </html>
    """

    # Render raw HTML and disable all Streamlit elements
    st.markdown(html, unsafe_allow_html=True)

    # Hide all Streamlit elements
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .block-container {padding-top: 0 !important; padding-bottom: 0 !important;}
    section.main {padding: 0 !important;}
    div.stApp {
        margin: 0;
        padding: 0;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("Idea Islands")

    tab1, tab2, tab3 = st.tabs(["Islands Dashboard", "Create Island", "API Access"])

    with tab1:
        st.header("Your Islands")

        if not st.session_state.islands:
            st.info("You don't have any islands yet. Create one in the 'Create Island' tab!")
        else:
            for island_id, island in st.session_state.islands.items():
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

        Each island has a unique URL that ChatGPT can access. Use ChatGPT's task feature to fetch random ideas from your islands.

        **Usage Instructions:**
        1. Enter each idea on a separate line in your island's content
        2. When ChatGPT visits the island URL, it will see 3 randomly selected ideas

        **Island URLs:**
        """)

        base_url = st.text_input("Your Streamlit app URL (e.g., https://your-app-domain.streamlit.app)",
                             placeholder="Enter your deployed app URL")

        if base_url:
            st.markdown("### Your Island Links")

            # Display a table with island names and their URLs
            data = []
            for island_id, island in st.session_state.islands.items():
                # Use the static HTML view format which works better with ChatGPT
                island_url = f"{base_url}?view=static&island_id={island_id}"
                data.append({
                    "Island Name": island['name'],
                    "URL": island_url,
                    "ChatGPT Instruction": f"Please visit {island_url} and return the 3 random ideas from this island."
                })

            # If there are islands, display them in a dataframe
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, hide_index=True, use_container_width=True)

                # Also provide individual sections for easy copy-paste
                st.markdown("### Individual Islands")
                for island_id, island in st.session_state.islands.items():
                    with st.expander(f"🏝️ {island['name']}"):
                        # Use the static HTML view format
                        island_url = f"{base_url}?view=static&island_id={island_id}"
                        st.code(island_url)
                        st.markdown("**ChatGPT Instruction:**")
                        st.markdown(f"""
                        ```
                        Please visit {island_url} and return the 3 random ideas from this island named "{island['name']}".
                        ```
                        """)
            else:
                st.info("You don't have any islands yet. Create one in the 'Create Island' tab!")
        else:
            st.info("Enter your deployed Streamlit app URL to see the links ChatGPT can access.")

def handle_app_view():
    """Handle different app views based on query params"""
    # Check if we're in static view mode (for ChatGPT access)
    view = st.query_params.get("view", "")

    if view == "static":
        island_id = st.query_params.get("island_id", "")

        if island_id:
            # Display the static HTML view
            display_static_html_view(island_id)
            return True

    # Default to main app
    return False

if __name__ == "__main__":
    # First check if we should display a special view
    if not handle_app_view():
        # If not, show the main app
        main()
