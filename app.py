import streamlit as st
import uuid
from datetime import datetime
import json
import os
import pandas as pd
import requests

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

# Function to sync with API server
def sync_with_api_server(api_base_url, island_id=None, operation="update"):
    """
    Sync island data with the API server

    Parameters:
    - api_base_url: Base URL of the API server
    - island_id: ID of the island to update (None for full sync)
    - operation: "update" for single island update, "full_sync" for complete sync
    """
    if not api_base_url:
        st.error("Please enter your API base URL in the API Access tab to enable syncing.")
        return False

    # Remove trailing slash if present
    if api_base_url.endswith('/'):
        api_base_url = api_base_url[:-1]

    try:
        if operation == "update" and island_id:
            # Update a single island
            island = st.session_state.islands[island_id]
            response = requests.post(
                f"{api_base_url}/api/islands/{island_id}/update",
                json={
                    "name": island["name"],
                    "content": island["content"]
                }
            )

            if response.status_code == 200:
                st.success(f"Island '{island['name']}' synced with API server.")
                return True
            else:
                st.error(f"Failed to sync island with API server: {response.text}")
                return False

        elif operation == "full_sync":
            # Full sync of all islands
            response = requests.post(
                f"{api_base_url}/api/islands/sync",
                json={"islands": st.session_state.islands}
            )

            if response.status_code == 200:
                st.success("All islands synced with API server.")
                return True
            else:
                st.error(f"Failed to sync islands with API server: {response.text}")
                return False

        elif operation == "create" and island_id:
            # Create a new island
            island = st.session_state.islands[island_id]
            response = requests.post(
                f"{api_base_url}/api/islands/create",
                json={"name": island["name"]}
            )

            if response.status_code == 200:
                # Update the local island_id with the one from the server
                new_id = response.json().get("id")
                if new_id and new_id != island_id:
                    st.session_state.islands[new_id] = st.session_state.islands.pop(island_id)
                    save_islands(st.session_state.islands)
                    st.experimental_rerun()

                st.success(f"Island '{island['name']}' created on API server.")
                return True
            else:
                st.error(f"Failed to create island on API server: {response.text}")
                return False

        elif operation == "delete" and island_id:
            # Delete an island
            response = requests.delete(
                f"{api_base_url}/api/islands/{island_id}/delete"
            )

            if response.status_code == 200:
                st.success("Island deleted from API server.")
                return True
            else:
                st.error(f"Failed to delete island from API server: {response.text}")
                return False

    except Exception as e:
        st.error(f"Error syncing with API server: {str(e)}")
        return False

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

    # Try to sync with API server
    api_base_url = st.session_state.get("api_base_url", "")
    if api_base_url:
        sync_with_api_server(api_base_url, island_id, "create")

    st.session_state.new_island_name = ""
    st.success(f"Island '{island_name}' created successfully!")

def update_island_content(island_id):
    """Update an island's content"""
    content = st.session_state.get(f"island_content_{island_id}", "")

    st.session_state.islands[island_id]["content"] = content
    st.session_state.islands[island_id]["updated_at"] = datetime.now().isoformat()
    save_islands(st.session_state.islands)

    # Try to sync with API server
    api_base_url = st.session_state.get("api_base_url", "")
    if api_base_url:
        sync_with_api_server(api_base_url, island_id, "update")

    st.success("Content updated successfully!")

def delete_island(island_id):
    """Delete an island"""
    island_name = st.session_state.islands[island_id]["name"]

    # Try to sync with API server first
    api_base_url = st.session_state.get("api_base_url", "")
    if api_base_url:
        if not sync_with_api_server(api_base_url, island_id, "delete"):
            if not st.checkbox("Force delete locally anyway?"):
                st.warning("Island was not deleted because sync with API server failed.")
                return

    # Delete locally
    del st.session_state.islands[island_id]
    save_islands(st.session_state.islands)
    st.success(f"Island '{island_name}' deleted successfully!")

def main():
    st.title("Island Content Manager")

    # Store API base URL in session state so it's available for sync operations
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = ""

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

                    # Two columns for the buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.button("Save Changes", key=f"save_btn_{island_id}",
                                on_click=update_island_content, args=(island_id,))

                    with col2:
                        # Manual sync button
                        api_base_url = st.session_state.api_base_url
                        if api_base_url:
                            st.button("Sync Now", key=f"sync_btn_{island_id}",
                                    on_click=sync_with_api_server,
                                    args=(api_base_url, island_id, "update"))

                    with col3:
                        # Delete button
                        st.button("Delete Island", key=f"delete_btn_{island_id}",
                                on_click=delete_island, args=(island_id,))

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

        **Important:** Enter your API URL below to enable automatic syncing with your API server
        """)

        # Get the API base URL - this needs to point to your Render deployment
        api_base_url = st.text_input(
            "Your API base URL (e.g., https://ai-airport.onrender.com)",
            value=st.session_state.api_base_url,
            placeholder="Enter your deployed API base URL (no trailing slash)",
            help="This should be your Render API URL, not your Streamlit URL",
            key="api_base_url_input",
            on_change=lambda: setattr(st.session_state, "api_base_url", st.session_state.api_base_url_input)
        )

        # Update the session state
        st.session_state.api_base_url = api_base_url

        if api_base_url:
            # Remove trailing slash if present
            if api_base_url.endswith('/'):
                api_base_url = api_base_url[:-1]
                st.session_state.api_base_url = api_base_url

            # Full sync button
            st.button("Sync All Islands with API Server",
                     on_click=sync_with_api_server,
                     args=(api_base_url, None, "full_sync"))

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
            st.warning("Please enter your API base URL (from Render) to see the API endpoints and enable syncing.")

        # Updated info about data sharing between platforms
        st.markdown("""
        ### Data Synchronization

        With the API sync feature enabled:

        - Changes made in this Streamlit app will be automatically synced to your API server
        - You can manually sync individual islands or all islands at once
        - Create, update, and delete operations are synced between platforms

        To use this feature:
        1. Enter your API base URL above
        2. Create and edit your islands in this Streamlit app
        3. The changes will automatically sync to your API server

        **Note:** For best results, always make changes in this Streamlit app and let it sync to the API server.
        """)

if __name__ == "__main__":
    main()
