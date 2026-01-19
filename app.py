"""
Coverage Scorer - Media Coverage Analysis Tool
A Streamlit application for scoring news article coverage.
"""
import streamlit as st
from pathlib import Path
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.storage import get_config, get_clients, get_outlets

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Coverage Scorer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import and inject custom styles
from utils.styles import inject_custom_css, render_sidebar

inject_custom_css()
render_sidebar()


def main():
    # Hero section
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0 2rem 0;">
        <h1 style="font-size: 3.5rem !important; font-weight: 700 !important; margin-bottom: 1rem !important; letter-spacing: -0.03em;">
            Coverage Scorer
        </h1>
        <p style="font-size: 1.25rem; color: #6B7280; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            Analyze and score media coverage with AI precision
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Three action cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="
            padding: 2rem;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            height: 100%;
            transition: all 0.2s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.12)';"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
            </div>
            <h3 style="font-size: 1.35rem !important; font-weight: 600 !important; margin-bottom: 0.75rem !important; color: #000000;">
                Analyze Article
            </h3>
            <p style="color: #6B7280; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                Score individual articles based on 40+ factors across 7 tiers. Get detailed AI-powered insights and recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze Article", key="nav_analyze", use_container_width=True):
            st.switch_page("pages/1_Analyze_Article.py")

    with col2:
        st.markdown("""
        <div style="
            padding: 2rem;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            height: 100%;
            transition: all 0.2s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.12)';"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
            </div>
            <h3 style="font-size: 1.35rem !important; font-weight: 600 !important; margin-bottom: 0.75rem !important; color: #000000;">
                Batch Analysis
            </h3>
            <p style="color: #6B7280; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                Process multiple articles at once. Import from Excel or paste URLs for efficient bulk scoring and reporting.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Batch Analysis", key="nav_batch", use_container_width=True):
            st.switch_page("pages/6_Batch_Analysis.py")

    with col3:
        st.markdown("""
        <div style="
            padding: 2rem;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            height: 100%;
            transition: all 0.2s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.12)';"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
            </div>
            <h3 style="font-size: 1.35rem !important; font-weight: 600 !important; margin-bottom: 0.75rem !important; color: #000000;">
                History
            </h3>
            <p style="color: #6B7280; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                View and search past analyses. Track coverage trends over time and export reports for your records.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View History", key="nav_history", use_container_width=True):
            st.switch_page("pages/5_History.py")

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    # Configuration status
    st.markdown("""
    <h2 style="font-size: 1.5rem !important; font-weight: 600 !important; margin-bottom: 1.5rem !important;">
        Configuration Status
    </h2>
    """, unsafe_allow_html=True)

    config = get_config()
    clients = get_clients()
    outlets = get_outlets()

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        if config.get("api_key"):
            st.markdown("""
            <div style="
                padding: 1.25rem;
                background-color: #ECFDF5;
                border-radius: 12px;
                border-left: 4px solid #059669;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span style="font-weight: 600; color: #059669;">API Key Configured</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                padding: 1.25rem;
                background-color: #FFFBEB;
                border-radius: 12px;
                border-left: 4px solid #D97706;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <span style="font-weight: 600; color: #D97706;">API Key Required</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with status_col2:
        if clients:
            st.markdown(f"""
            <div style="
                padding: 1.25rem;
                background-color: #ECFDF5;
                border-radius: 12px;
                border-left: 4px solid #059669;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span style="font-weight: 600; color: #059669;">{len(clients)} Client(s) Added</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                padding: 1.25rem;
                background-color: #F3F4F6;
                border-radius: 12px;
                border-left: 4px solid #9CA3AF;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                    <span style="font-weight: 600; color: #6B7280;">No Clients Yet</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with status_col3:
        if outlets:
            st.markdown(f"""
            <div style="
                padding: 1.25rem;
                background-color: #ECFDF5;
                border-radius: 12px;
                border-left: 4px solid #059669;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span style="font-weight: 600; color: #059669;">{len(outlets)} Outlet(s) Added</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                padding: 1.25rem;
                background-color: #F3F4F6;
                border-radius: 12px;
                border-left: 4px solid #9CA3AF;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                    <span style="font-weight: 600; color: #6B7280;">No Outlets Yet</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
