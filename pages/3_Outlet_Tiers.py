"""Outlet Tiers page - Manage media outlet classifications."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_outlets, save_outlets, add_outlet, update_outlet, delete_outlet,
    bulk_update_outlet_tiers
)

st.set_page_config(
    page_title="Outlet Tiers - Coverage Scorer",
    page_icon="",
    layout="wide"
)

# Import and inject custom styles
from utils.styles import inject_custom_css, render_sidebar

inject_custom_css()
render_sidebar()

TIER_DESCRIPTIONS = {
    1: "Tier 1 - Major National",
    2: "Tier 2 - Industry/Regional",
    3: "Tier 3 - Trade/Niche",
    4: "Tier 4 - Blogs/Minor"
}

TIER_COLORS = {
    1: ("#ECFDF5", "#059669"),
    2: ("#EFF6FF", "#2563EB"),
    3: ("#FFFBEB", "#D97706"),
    4: ("#F3F4F6", "#6B7280")
}

OUTLET_TYPES = [
    "National Newspaper",
    "Regional Newspaper",
    "Wire Service",
    "Broadcast TV",
    "Cable TV",
    "Radio",
    "Magazine",
    "Online News",
    "Tech News",
    "Trade Publication",
    "Industry Journal",
    "Blog",
    "Newsletter",
    "Podcast",
    "Other"
]


def get_tier_badge(tier: int) -> str:
    """Get HTML for tier badge."""
    bg_color, text_color = TIER_COLORS.get(tier, ("#F3F4F6", "#6B7280"))
    return f'''<span style="
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: {bg_color};
        color: {text_color};
    ">{TIER_DESCRIPTIONS.get(tier, f"Tier {tier}")}</span>'''


def render_outlet_list():
    """Render searchable/filterable outlet list."""
    outlets = get_outlets()

    if not outlets:
        st.info("No outlets configured yet. Add your first outlet below.")
        return

    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input("Search outlets", placeholder="Search by name or domain...")

    with col2:
        tier_filter = st.multiselect(
            "Filter by Tier",
            options=[1, 2, 3, 4],
            format_func=lambda x: f"Tier {x}",
            default=[]
        )

    with col3:
        type_filter = st.multiselect(
            "Filter by Type",
            options=list(set(o.get("type", "") for o in outlets if o.get("type"))),
            default=[]
        )

    # Filter outlets
    filtered_outlets = outlets
    if search:
        search_lower = search.lower()
        filtered_outlets = [
            o for o in filtered_outlets
            if search_lower in o.get("name", "").lower()
            or search_lower in o.get("domain", "").lower()
        ]
    if tier_filter:
        filtered_outlets = [o for o in filtered_outlets if o.get("tier") in tier_filter]
    if type_filter:
        filtered_outlets = [o for o in filtered_outlets if o.get("type") in type_filter]

    st.markdown(f"### Showing {len(filtered_outlets)} of {len(outlets)} outlets")

    # Bulk selection for tier change
    if "selected_outlets" not in st.session_state:
        st.session_state.selected_outlets = set()

    # Bulk actions
    if st.session_state.selected_outlets:
        st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 1rem 0;'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{len(st.session_state.selected_outlets)} outlet(s) selected**")

        with col2:
            new_tier = st.selectbox(
                "Change tier to",
                options=[1, 2, 3, 4],
                format_func=lambda x: f"Tier {x}",
                key="bulk_tier_select"
            )

        with col3:
            if st.button("Apply Tier Change"):
                count = bulk_update_outlet_tiers(
                    list(st.session_state.selected_outlets),
                    new_tier
                )
                st.success(f"Updated {count} outlet(s) to Tier {new_tier}")
                st.session_state.selected_outlets = set()
                st.rerun()

        if st.button("Clear Selection"):
            st.session_state.selected_outlets = set()
            st.rerun()

        st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 1rem 0;'>", unsafe_allow_html=True)

    # Select all / deselect all
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Select All Visible"):
            for o in filtered_outlets:
                st.session_state.selected_outlets.add(o["id"])
            st.rerun()

    # Display outlets
    for outlet in filtered_outlets:
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1, 1, 1])

        with col1:
            is_selected = outlet["id"] in st.session_state.selected_outlets
            if st.checkbox("", value=is_selected, key=f"select_{outlet['id']}", label_visibility="collapsed"):
                st.session_state.selected_outlets.add(outlet["id"])
            else:
                st.session_state.selected_outlets.discard(outlet["id"])

        with col2:
            tier = outlet.get("tier", 4)
            reach = outlet.get("reach_estimate", "N/A")
            if isinstance(reach, (int, float)):
                reach = f"{reach:,.0f}"

            st.markdown(f"""
            <div style="padding: 0.5rem 0;">
                <strong>{outlet['name']}</strong>
                {get_tier_badge(tier)}
                <br>
                <span style="color: #6B7280; font-size: 0.85rem;">
                    {outlet.get('domain', 'No domain')} &bull;
                    {outlet.get('type', 'No type')} &bull;
                    Reach: {reach}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            pass  # Spacer

        with col4:
            if st.button("Edit", key=f"edit_{outlet['id']}"):
                st.session_state.editing_outlet = outlet["id"]
                st.rerun()

        with col5:
            if st.button("Delete", key=f"delete_{outlet['id']}"):
                st.session_state.deleting_outlet = outlet["id"]
                st.rerun()


def render_outlet_form(outlet=None):
    """Render outlet add/edit form."""
    is_edit = outlet is not None

    st.markdown(f"## {'Edit' if is_edit else 'Add New'} Outlet")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Outlet Name *",
            value=outlet.get("name", "") if outlet else "",
            key="outlet_name"
        )

        domain = st.text_input(
            "Domain",
            value=outlet.get("domain", "") if outlet else "",
            placeholder="example.com",
            key="outlet_domain"
        )

        tier = st.selectbox(
            "Tier *",
            options=[1, 2, 3, 4],
            index=(outlet.get("tier", 4) - 1) if outlet else 3,
            format_func=lambda x: TIER_DESCRIPTIONS.get(x, f"Tier {x}"),
            key="outlet_tier"
        )

    with col2:
        outlet_type = st.selectbox(
            "Type",
            options=OUTLET_TYPES,
            index=OUTLET_TYPES.index(outlet.get("type", "Other")) if outlet and outlet.get("type") in OUTLET_TYPES else len(OUTLET_TYPES) - 1,
            key="outlet_type"
        )

        reach = st.number_input(
            "Monthly Reach Estimate",
            min_value=0,
            value=int(outlet.get("reach_estimate", 0)) if outlet else 0,
            step=10000,
            key="outlet_reach"
        )

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Tier explanation
    st.markdown("""
    **Tier Guidelines:**
    - **Tier 1 (20 pts):** Major national outlets with broad reach (NYT, WSJ, CNN, BBC)
    - **Tier 2 (14 pts):** Industry-leading or major regional outlets (TechCrunch, Chicago Tribune)
    - **Tier 3 (8 pts):** Trade publications and niche outlets (Industry Week, sector-specific)
    - **Tier 4 (3 pts):** Blogs, minor publications, and emerging outlets
    """)

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Save Outlet", type="primary"):
            if not name:
                st.error("Outlet name is required")
            else:
                outlet_data = {
                    "name": name,
                    "domain": domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/"),
                    "tier": tier,
                    "type": outlet_type,
                    "reach_estimate": reach
                }

                if is_edit:
                    update_outlet(outlet["id"], outlet_data)
                    st.success("Outlet updated successfully!")
                else:
                    add_outlet(outlet_data)
                    st.success("Outlet added successfully!")

                if "editing_outlet" in st.session_state:
                    del st.session_state.editing_outlet

                st.rerun()

    with col2:
        if st.button("Cancel"):
            if "editing_outlet" in st.session_state:
                del st.session_state.editing_outlet
            st.rerun()


def render_csv_import():
    """Render CSV import section."""
    st.markdown("## Import Outlets from CSV")

    # Download template
    template_path = Path(__file__).parent.parent / "templates" / "outlets_template.csv"
    if template_path.exists():
        with open(template_path, "r") as f:
            template_content = f.read()
        st.download_button(
            "Download CSV Template",
            template_content,
            file_name="outlets_template.csv",
            mime="text/csv"
        )

    st.markdown("""
    **CSV Format:**
    - `name`: Outlet name (required)
    - `domain`: Website domain (e.g., "nytimes.com")
    - `tier`: 1, 2, 3, or 4
    - `type`: Type of outlet
    - `reach_estimate`: Monthly reach number
    """)

    uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"], key="outlet_csv_upload")

    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            st.dataframe(df)

            if st.button("Import Outlets"):
                imported = 0
                for _, row in df.iterrows():
                    outlet_data = {
                        "name": str(row["name"]),
                        "domain": str(row.get("domain", "")).replace("https://", "").replace("http://", "").replace("www.", "").strip("/"),
                        "tier": int(row.get("tier", 4)),
                        "type": str(row.get("type", "Other")),
                        "reach_estimate": int(row.get("reach_estimate", 0)) if pd.notna(row.get("reach_estimate")) else 0
                    }

                    add_outlet(outlet_data)
                    imported += 1

                st.success(f"Successfully imported {imported} outlet(s)!")
                st.rerun()

        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")


def render_tier_summary():
    """Render summary of outlets by tier."""
    outlets = get_outlets()

    if not outlets:
        return

    st.markdown("## Tier Summary")

    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for outlet in outlets:
        tier = outlet.get("tier", 4)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tier 1", tier_counts[1], help="Major National")
    with col2:
        st.metric("Tier 2", tier_counts[2], help="Industry/Regional")
    with col3:
        st.metric("Tier 3", tier_counts[3], help="Trade/Niche")
    with col4:
        st.metric("Tier 4", tier_counts[4], help="Blogs/Minor")


def main():
    st.markdown("""
    <h1 style="font-size: 2.5rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important;">
        Outlet Tiers
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">
        Manage and classify media outlets for accurate scoring
    </p>
    """, unsafe_allow_html=True)

    # Handle delete confirmation
    if "deleting_outlet" in st.session_state:
        outlet_id = st.session_state.deleting_outlet
        outlets = get_outlets()
        outlet = next((o for o in outlets if o["id"] == outlet_id), None)

        if outlet:
            st.warning(f"Are you sure you want to delete **{outlet['name']}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    delete_outlet(outlet_id)
                    del st.session_state.deleting_outlet
                    st.success("Outlet deleted!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    del st.session_state.deleting_outlet
                    st.rerun()
            st.stop()

    # Handle editing
    if "editing_outlet" in st.session_state:
        outlet_id = st.session_state.editing_outlet
        outlets = get_outlets()
        outlet = next((o for o in outlets if o["id"] == outlet_id), None)
        if outlet:
            render_outlet_form(outlet)
            st.stop()

    # Tier summary
    render_tier_summary()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["All Outlets", "Add New", "Import CSV"])

    with tab1:
        render_outlet_list()

    with tab2:
        render_outlet_form()

    with tab3:
        render_csv_import()


if __name__ == "__main__":
    main()
