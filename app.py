import streamlit as st
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

def main():
    st.title("Island Content Manager")

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
                        help="Enter the content for this island. Each line will be displayed as written."
                    )
                    st.button("Save Changes", key=f"save_btn_{island_id}",
                              on_click=update_island_content, args=(island_id,))

                    # Ensure updated_at exists (for backwards compatibility)
                    if 'updated_at' not in island:
                        island['updated_at'] = island.get('created_at', datetime.now().isoformat())

                    updated_time = datetime.fromisoformat(island["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"Last updated: {updated_time}")

    with tab2:
        st.header("Create a New Island")
        st.text_input("Island Name", key="new_island_name")
        st.button("Create Island", on_click=create_island)

    with tab3:
        st.header("API Access")
        st.markdown("""
        ### How to Access Islands

        Each island has a unique API endpoint that can be accessed to view its content.

        **Usage Instructions:**
        1. Enter content in your island
        2. When visiting the API endpoint, you will see the exact content as written

        **Important:** Make sure to enter your API URL below (not your Streamlit URL)
        """)

        # Get the API base URL - this needs to point to your Render deployment
        api_base_url = st.text_input(
            "Your API base URL (e.g., https://ai-airport.onrender.com)",
            placeholder="Enter your deployed API base URL (no trailing slash)",
            help="This should be your Render API URL, not your Streamlit URL"
        )

        if api_base_url:
            # Remove trailing slash if present
            if api_base_url.endswith('/'):
                api_base_url = api_base_url[:-1]

            st.markdown("### Your Island API Links")

            # Display a table with island names and their API endpoints
            data = []
            for island_id, island in st.session_state.islands.items():
                api_url = f"{api_base_url}/api/islands/{island_id}/html"
                data.append({
                    "Island Name": island['name'],
                    "Content URL": api_url
                })

            # If there are islands, display them in a dataframe
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, hide_index=True, use_container_width=True)

                # Also provide individual sections for easy copy-paste
                st.markdown("### Individual Islands")
                for island_id, island in st.session_state.islands.items():
                    with st.expander(f"🏝️ {island['name']}"):
                        api_url = f"{api_base_url}/api/islands/{island_id}/html"
                        st.markdown("**Content URL:**")
                        st.code(api_url)

                        st.markdown("**Instructions:**")
                        st.markdown(f"""
                        ```
                        Please visit {api_url} to view the content of this island.
                        ```
                        """)
            else:
                st.info("You don't have any islands yet. Create one in the 'Create Island' tab!")
        else:
            st.warning("Please enter your API base URL (from Render) to see the API endpoints.")

        # Info about data sharing between platforms
        st.markdown("""
        ### Important Note About Data Storage

        Your islands data is stored locally in each platform:

        - Data created in Streamlit Cloud stays in Streamlit Cloud
        - Data created in your API server on Render stays on Render

        To use content created here, you need to:

        1. Create and edit your islands in this Streamlit app
        2. Copy the content manually to your API server on Render or vice versa

        For a production setup, consider using a shared database like MongoDB Atlas.
        """)

if __name__ == "__main__":
    main()
