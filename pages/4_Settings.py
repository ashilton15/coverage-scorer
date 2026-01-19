"""Settings page - API key and logo configuration."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import get_config, save_config, save_logo, get_logo_path

st.set_page_config(
    page_title="Settings - Coverage Scorer",
    page_icon="",
    layout="wide"
)

# Import and inject custom styles
from utils.styles import inject_custom_css, render_sidebar

inject_custom_css()
render_sidebar()


def main():
    st.markdown("""
    <h1 style="font-size: 2.5rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important;">
        Settings
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">
        Configure your Coverage Scorer application
    </p>
    """, unsafe_allow_html=True)

    config = get_config()

    # API Key Section
    st.markdown("## Anthropic API Key")

    st.markdown("""
    <div style="
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    ">
        <strong>About the API Key</strong><br>
        The Coverage Scorer uses Claude AI to analyze articles. You need an Anthropic API key to use this feature.
        Get your API key from <a href="https://console.anthropic.com/" target="_blank" style="color: #2563EB;">console.anthropic.com</a>
    </div>
    """, unsafe_allow_html=True)

    current_key = config.get("api_key", "")
    masked_key = ""
    if current_key:
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "****"
        st.success(f"API Key configured: `{masked_key}`")

    new_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Your Anthropic API key starting with sk-ant-"
    )

    if st.button("Save API Key"):
        if new_key:
            if new_key.startswith("sk-ant-") or new_key.startswith("sk-"):
                config["api_key"] = new_key
                save_config(config)
                st.success("API Key saved successfully!")
                st.rerun()
            else:
                st.error("Invalid API key format. Should start with 'sk-ant-'")
        else:
            st.warning("Please enter an API key")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Logo Section
    st.markdown("## Logo Upload")

    st.markdown("""
    Upload your company logo to display in the sidebar. Recommended size: 150x50 pixels.
    Supported formats: PNG, JPG, SVG
    """)

    logo_path = get_logo_path()
    if logo_path and Path(logo_path).exists():
        st.markdown("**Current Logo:**")
        st.image(logo_path, width=150)

        if st.button("Remove Logo"):
            config["logo_path"] = ""
            save_config(config)
            st.success("Logo removed!")
            st.rerun()

    uploaded_logo = st.file_uploader(
        "Upload new logo",
        type=["png", "jpg", "jpeg", "svg"],
        key="logo_upload"
    )

    if uploaded_logo:
        st.image(uploaded_logo, width=150, caption="Preview")

        if st.button("Save Logo"):
            try:
                saved_path = save_logo(uploaded_logo)
                st.success("Logo saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving logo: {str(e)}")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Data Management Section
    st.markdown("## Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Export Data")
        st.markdown("Download your data for backup or transfer.")

        from utils.storage import get_clients, get_outlets, get_history
        import json

        export_data = {
            "clients": get_clients(),
            "outlets": get_outlets(),
            "history": get_history(),
            "config": {k: v for k, v in config.items() if k != "api_key"}  # Don't export API key
        }

        st.download_button(
            "Export All Data (JSON)",
            json.dumps(export_data, indent=2, default=str),
            file_name="coverage_scorer_backup.json",
            mime="application/json"
        )

    with col2:
        st.markdown("### Import Data")
        st.markdown("Restore data from a backup file.")

        uploaded_backup = st.file_uploader(
            "Upload backup file",
            type=["json"],
            key="backup_upload"
        )

        if uploaded_backup:
            try:
                import json
                backup_data = json.load(uploaded_backup)

                st.markdown("**Backup contents:**")
                st.markdown(f"- {len(backup_data.get('clients', []))} clients")
                st.markdown(f"- {len(backup_data.get('outlets', []))} outlets")
                st.markdown(f"- {len(backup_data.get('history', []))} history items")

                if st.button("Restore Backup"):
                    from utils.storage import save_clients, save_outlets, save_history

                    if "clients" in backup_data:
                        save_clients(backup_data["clients"])
                    if "outlets" in backup_data:
                        save_outlets(backup_data["outlets"])
                    if "history" in backup_data:
                        save_history(backup_data["history"])

                    st.success("Data restored successfully!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error reading backup file: {str(e)}")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Clear Data Section
    st.markdown("## Clear Data")
    st.warning("These actions cannot be undone!")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Clear History"):
            st.session_state.confirm_clear = "history"
            st.rerun()

    with col2:
        if st.button("Clear Clients"):
            st.session_state.confirm_clear = "clients"
            st.rerun()

    with col3:
        if st.button("Clear Outlets"):
            st.session_state.confirm_clear = "outlets"
            st.rerun()

    # Confirmation dialog
    if "confirm_clear" in st.session_state:
        data_type = st.session_state.confirm_clear
        st.error(f"Are you sure you want to clear all {data_type}?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Clear", type="primary"):
                from utils.storage import save_clients, save_outlets, save_history

                if data_type == "history":
                    save_history([])
                elif data_type == "clients":
                    save_clients([])
                elif data_type == "outlets":
                    save_outlets([])

                del st.session_state.confirm_clear
                st.success(f"{data_type.capitalize()} cleared!")
                st.rerun()

        with col2:
            if st.button("Cancel"):
                del st.session_state.confirm_clear
                st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # About Section
    st.markdown("## About")

    st.markdown("""
    <div style="
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
    ">
        <h3 style="margin-top: 0;">Coverage Scorer v1.0</h3>
        <p style="color: #6B7280; margin-bottom: 1rem;">
            A media coverage analysis tool that scores articles based on how well they cover your client.
        </p>

        <strong>Features:</strong>
        <ul style="color: #6B7280; margin-bottom: 1rem;">
            <li>AI-powered article analysis using Claude</li>
            <li>Multi-tier scoring system (40+ factors)</li>
            <li>Client profile management</li>
            <li>Media outlet classification</li>
            <li>Analysis history tracking</li>
        </ul>

        <strong>Scoring Model:</strong>
        <ul style="color: #6B7280; margin-bottom: 0;">
            <li>Base score: 100 points across 7 tiers</li>
            <li>Bonus points: Up to 16 additional points</li>
            <li>Maximum possible score: 116</li>
        </ul>
    </div>

    <p style="color: #9CA3AF; font-size: 0.875rem; margin-top: 1.5rem; text-align: center;">
        Built with Streamlit &bull; Powered by Anthropic Claude AI
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
