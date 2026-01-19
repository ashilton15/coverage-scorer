"""Client Profiles page - Manage client profiles with key messages and competitors."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_clients, save_clients, add_client, update_client, delete_client, get_api_key
)
from utils.document_parser import extract_text_from_file
from utils.analyzer import extract_key_messages

st.set_page_config(
    page_title="Client Profiles - Coverage Scorer",
    page_icon="",
    layout="wide"
)

# Import and inject custom styles
from utils.styles import inject_custom_css, render_sidebar

inject_custom_css()
render_sidebar()


def render_client_list():
    """Render the list of all clients."""
    clients = get_clients()

    if not clients:
        st.info("No client profiles yet. Create your first client below.")
        return None

    st.markdown(f"### {len(clients)} Client Profile(s)")

    selected_client_id = None

    for client in clients:
        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            st.markdown(f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                transition: box-shadow 0.2s;
            ">
                <h4 style="margin: 0; color: #000000; font-weight: 600;">{client['name']}</h4>
                <p style="color: #6B7280; margin: 0.25rem 0 0 0; font-size: 0.875rem;">
                    {client.get('industry', 'No industry')} &bull;
                    {len(client.get('key_messages', []))} key messages &bull;
                    {len(client.get('competitors', []))} competitors
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("Edit", key=f"edit_{client['id']}"):
                # Clear temp state so it will be reloaded from the client being edited
                for key in ["temp_key_messages", "temp_competitors", "extracted_messages"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.editing_client = client['id']
                st.rerun()

        with col3:
            if st.button("Delete", key=f"delete_{client['id']}"):
                st.session_state.deleting_client = client['id']
                st.rerun()

    return selected_client_id


def render_client_form(client=None):
    """Render the client add/edit form."""
    is_edit = client is not None

    st.markdown(f"## {'Edit' if is_edit else 'Add New'} Client Profile")

    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Client Name *",
            value=client.get("name", "") if client else "",
            key="client_name"
        )
    with col2:
        industry = st.text_input(
            "Industry *",
            value=client.get("industry", "") if client else "",
            key="client_industry"
        )

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Key Messages Section
    st.markdown("### Key Messages")

    # Initialize key messages in session state
    if "temp_key_messages" not in st.session_state:
        if client and client.get("key_messages"):
            st.session_state.temp_key_messages = client["key_messages"].copy()
        else:
            st.session_state.temp_key_messages = []

    # Add key message methods
    tab1, tab2 = st.tabs(["Manual Entry", "Extract from Document"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            new_message = st.text_input("New Key Message", key="new_message_input")
        with col2:
            new_priority = st.selectbox(
                "Priority",
                options=["high", "medium", "low"],
                index=1,
                key="new_message_priority"
            )

        if st.button("Add Message"):
            if new_message:
                st.session_state.temp_key_messages.append({
                    "message": new_message,
                    "priority": new_priority
                })
                st.rerun()

    with tab2:
        api_key = get_api_key()
        if not api_key:
            st.warning("Configure your Anthropic API key in Settings to use AI extraction.")
        else:
            uploaded_file = st.file_uploader(
                "Upload briefing document",
                type=["pdf", "docx", "txt"],
                key="briefing_upload"
            )

            if uploaded_file and st.button("Extract Key Messages"):
                with st.spinner("Extracting key messages with AI..."):
                    success, text_or_error = extract_text_from_file(uploaded_file)

                    if success:
                        result = extract_key_messages(
                            api_key=api_key,
                            document_text=text_or_error,
                            client_name=name or "Unknown",
                            industry=industry or "Unknown"
                        )

                        if result["success"]:
                            st.session_state.extracted_messages = result["messages"]
                            st.success(f"Extracted {len(result['messages'])} key messages!")
                        else:
                            st.error(result["error"])
                    else:
                        st.error(text_or_error)

            # Review extracted messages
            if "extracted_messages" in st.session_state and st.session_state.extracted_messages:
                st.markdown("#### Review Extracted Messages")
                st.markdown("Edit messages and set priorities, then add to profile:")

                messages_to_add = []
                for i, msg in enumerate(st.session_state.extracted_messages):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        edited_msg = st.text_input(
                            f"Message {i+1}",
                            value=msg["message"],
                            key=f"extracted_msg_{i}"
                        )
                    with col2:
                        priority = st.selectbox(
                            "Priority",
                            options=["high", "medium", "low"],
                            index=1,
                            key=f"extracted_priority_{i}"
                        )
                    with col3:
                        include = st.checkbox("Include", value=True, key=f"include_msg_{i}")

                    if include:
                        messages_to_add.append({"message": edited_msg, "priority": priority})

                if st.button("Add Selected Messages"):
                    st.session_state.temp_key_messages.extend(messages_to_add)
                    st.session_state.extracted_messages = []
                    st.success(f"Added {len(messages_to_add)} messages!")
                    st.rerun()

    # Display current key messages
    if st.session_state.temp_key_messages:
        st.markdown("#### Current Key Messages")

        for i, msg in enumerate(st.session_state.temp_key_messages):
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                priority_colors = {
                    "high": "#DC2626",
                    "medium": "#D97706",
                    "low": "#059669"
                }
                color = priority_colors.get(msg['priority'], '#6B7280')
                st.markdown(f"""
                <div style="
                    background: #F9FAFB;
                    border-radius: 8px;
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    border-left: 3px solid {color};
                ">
                    <span style="color: {color}; font-weight: 600;">[{msg['priority'].upper()}]</span>
                    {msg['message']}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                new_pri = st.selectbox(
                    "Priority",
                    options=["high", "medium", "low"],
                    index=["high", "medium", "low"].index(msg["priority"]),
                    key=f"edit_priority_{i}",
                    label_visibility="collapsed"
                )
                if new_pri != msg["priority"]:
                    st.session_state.temp_key_messages[i]["priority"] = new_pri
                    st.rerun()

            with col3:
                if st.button("Remove", key=f"remove_msg_{i}"):
                    st.session_state.temp_key_messages.pop(i)
                    st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Competitors Section
    st.markdown("### Competitors")

    if "temp_competitors" not in st.session_state:
        if client and client.get("competitors"):
            st.session_state.temp_competitors = client["competitors"].copy()
        else:
            st.session_state.temp_competitors = []

    col1, col2 = st.columns([4, 1])
    with col1:
        new_competitor = st.text_input("Add Competitor", key="new_competitor_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="add_competitor_btn"):
            if new_competitor and new_competitor not in st.session_state.temp_competitors:
                st.session_state.temp_competitors.append(new_competitor)
                st.rerun()

    if st.session_state.temp_competitors:
        st.markdown("#### Current Competitors")
        for i, comp in enumerate(st.session_state.temp_competitors):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {comp}")
            with col2:
                if st.button("Remove", key=f"remove_comp_{i}"):
                    st.session_state.temp_competitors.pop(i)
                    st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Save/Cancel buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Save Client", type="primary"):
            if not name:
                st.error("Client name is required")
            elif not industry:
                st.error("Industry is required")
            else:
                client_data = {
                    "name": name,
                    "industry": industry,
                    "key_messages": st.session_state.temp_key_messages,
                    "competitors": st.session_state.temp_competitors
                }

                if is_edit:
                    update_client(client["id"], client_data)
                    st.success("Client updated successfully!")
                else:
                    add_client(client_data)
                    st.success("Client created successfully!")

                # Clear session state
                for key in ["temp_key_messages", "temp_competitors", "editing_client", "extracted_messages"]:
                    if key in st.session_state:
                        del st.session_state[key]

                st.rerun()

    with col2:
        if st.button("Cancel"):
            for key in ["temp_key_messages", "temp_competitors", "editing_client", "extracted_messages"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


def render_csv_import():
    """Render CSV import section."""
    st.markdown("## Import Clients from CSV")

    # Download template
    template_path = Path(__file__).parent.parent / "templates" / "clients_template.csv"
    if template_path.exists():
        with open(template_path, "r") as f:
            template_content = f.read()
        st.download_button(
            "Download CSV Template",
            template_content,
            file_name="clients_template.csv",
            mime="text/csv"
        )

    st.markdown("""
    **CSV Format:**
    - `name`: Client name (required)
    - `industry`: Industry (required)
    - `key_messages`: Pipe-separated messages (e.g., "Message 1|Message 2")
    - `competitors`: Comma-separated competitors (e.g., "Competitor A,Competitor B")
    """)

    uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"], key="csv_upload")

    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            st.dataframe(df)

            if st.button("Import Clients"):
                imported = 0
                for _, row in df.iterrows():
                    # Parse key messages
                    key_messages = []
                    if pd.notna(row.get("key_messages")):
                        for msg in str(row["key_messages"]).split("|"):
                            if msg.strip():
                                key_messages.append({
                                    "message": msg.strip(),
                                    "priority": "medium"
                                })

                    # Parse competitors
                    competitors = []
                    if pd.notna(row.get("competitors")):
                        competitors = [c.strip() for c in str(row["competitors"]).split(",") if c.strip()]

                    client_data = {
                        "name": str(row["name"]),
                        "industry": str(row.get("industry", "")),
                        "key_messages": key_messages,
                        "competitors": competitors
                    }

                    add_client(client_data)
                    imported += 1

                st.success(f"Successfully imported {imported} client(s)!")
                st.rerun()

        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")


def main():
    st.markdown("""
    <h1 style="font-size: 2.5rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important;">
        Client Profiles
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">
        Manage client profiles for coverage scoring
    </p>
    """, unsafe_allow_html=True)

    # Handle delete confirmation
    if "deleting_client" in st.session_state:
        client_id = st.session_state.deleting_client
        clients = get_clients()
        client = next((c for c in clients if c["id"] == client_id), None)

        if client:
            st.warning(f"Are you sure you want to delete **{client['name']}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    delete_client(client_id)
                    del st.session_state.deleting_client
                    st.success("Client deleted!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    del st.session_state.deleting_client
                    st.rerun()
            st.stop()

    # Handle editing
    if "editing_client" in st.session_state:
        client_id = st.session_state.editing_client
        clients = get_clients()
        client = next((c for c in clients if c["id"] == client_id), None)
        if client:
            render_client_form(client)
            st.stop()

    # Main view with tabs
    tab1, tab2, tab3 = st.tabs(["All Clients", "Add New", "Import CSV"])

    with tab1:
        render_client_list()

    with tab2:
        render_client_form()

    with tab3:
        render_csv_import()


if __name__ == "__main__":
    main()
