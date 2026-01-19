"""
Custom styling utilities for Coverage Scorer.
Provides modern SaaS-style CSS injection for all pages.
"""

import streamlit as st
from pathlib import Path
import base64


def inject_custom_css():
    """
    Inject minimal custom CSS into the Streamlit page.
    Only styles: sidebar (black bg), buttons (black), and basic layout.
    Form elements use Streamlit defaults for maximum compatibility.
    """
    st.markdown("""
    <style>
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar styling - black background with white text */
    [data-testid="stSidebar"] {
        background-color: #000000;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] a {
        text-decoration: none !important;
    }

    /* Buttons - black with white text */
    .stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
    }

    .stButton > button:hover {
        background-color: #333333 !important;
    }

    /* Main container - reasonable max width */
    .main .block-container {
        max-width: 1200px;
        padding: 2rem 3rem;
    }
    </style>
    """, unsafe_allow_html=True)


def _get_base64_image(image_path: Path) -> str:
    """Convert an image file to base64 string for embedding in HTML."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_sidebar():
    """
    Render the styled sidebar with branding and navigation.
    Call this after inject_custom_css().
    """
    with st.sidebar:
        # Logo at top (inverted to white for visibility on black background)
        logo_path = Path(__file__).parent.parent / "static" / "agnosticLogo@3x.png"
        if logo_path.exists():
            st.markdown("""
            <div style="padding: 1.5rem 1rem 0.5rem 1rem;">
                <img src="data:image/png;base64,{}" style="width: 140px; filter: brightness(0) invert(1);" alt="Agnostic Logo">
            </div>
            """.format(_get_base64_image(logo_path)), unsafe_allow_html=True)
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Tool name
        st.markdown("""
        <div style="padding: 0.5rem 1rem 1rem 1rem;">
            <h1 style="font-size: 1.5rem !important; font-weight: 700 !important; color: #FFFFFF !important; margin: 0 !important; letter-spacing: -0.02em;">
                Coverage Scorer
            </h1>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Navigation is handled automatically by Streamlit's page system

        # Spacer to push footer to bottom
        st.markdown("<div style='flex: 1; min-height: 300px;'></div>", unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div style="padding: 1rem; position: absolute; bottom: 1rem; left: 1rem;">
            <p style="font-size: 0.75rem !important; color: rgba(255,255,255,0.5) !important; margin: 0 !important;">
                Built by Agnostic
            </p>
        </div>
        """, unsafe_allow_html=True)


def get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= 80:
        return "#059669"  # Green
    elif score >= 60:
        return "#2563EB"  # Blue
    elif score >= 40:
        return "#D97706"  # Amber
    else:
        return "#DC2626"  # Red


def get_score_grade(score: float) -> str:
    """Get letter grade based on score."""
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C-"
    elif score >= 45:
        return "D+"
    elif score >= 40:
        return "D"
    else:
        return "F"


def get_grade_class(grade: str) -> str:
    """Get CSS class for grade badge."""
    if grade.startswith("A"):
        return "score-a"
    elif grade.startswith("B"):
        return "score-b"
    elif grade.startswith("C"):
        return "score-c"
    elif grade.startswith("D"):
        return "score-d"
    else:
        return "score-f"


def render_score_circle(score: float, max_score: float = 100):
    """
    Render a large circular score indicator.

    Args:
        score: The actual score
        max_score: Maximum possible score (default 100)
    """
    grade = get_score_grade(score)
    color = get_score_color(score)
    percentage = min((score / max_score) * 100, 100)

    # Calculate SVG circle parameters
    radius = 70
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference - (percentage / 100) * circumference

    grade_color_map = {
        "A": "#059669",
        "B": "#2563EB",
        "C": "#D97706",
        "D": "#DC2626",
        "F": "#6B7280"
    }
    grade_color = grade_color_map.get(grade[0], "#6B7280")

    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin: 2rem 0;">
        <svg width="180" height="180" viewBox="0 0 180 180">
            <!-- Background circle -->
            <circle
                cx="90"
                cy="90"
                r="{radius}"
                fill="none"
                stroke="#E5E7EB"
                stroke-width="12"
            />
            <!-- Progress circle -->
            <circle
                cx="90"
                cy="90"
                r="{radius}"
                fill="none"
                stroke="{color}"
                stroke-width="12"
                stroke-linecap="round"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{stroke_dashoffset}"
                transform="rotate(-90 90 90)"
                style="transition: stroke-dashoffset 0.5s ease;"
            />
            <!-- Score text -->
            <text x="90" y="80" text-anchor="middle" font-size="36" font-weight="700" fill="#000000" font-family="Inter, sans-serif">
                {score:.0f}
            </text>
            <!-- Max score text -->
            <text x="90" y="105" text-anchor="middle" font-size="14" fill="#6B7280" font-family="Inter, sans-serif">
                of {max_score:.0f}
            </text>
            <!-- Grade text -->
            <text x="90" y="130" text-anchor="middle" font-size="20" font-weight="600" fill="{grade_color}" font-family="Inter, sans-serif">
                {grade}
            </text>
        </svg>
    </div>
    """, unsafe_allow_html=True)


def render_grade_badge(grade: str):
    """Render a colored grade badge."""
    color_map = {
        "A": ("#ECFDF5", "#059669"),
        "B": ("#EFF6FF", "#2563EB"),
        "C": ("#FFFBEB", "#D97706"),
        "D": ("#FEF2F2", "#DC2626"),
        "F": ("#F3F4F6", "#6B7280")
    }
    bg_color, text_color = color_map.get(grade[0], ("#F3F4F6", "#6B7280"))

    st.markdown(f"""
    <span style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        background-color: {bg_color};
        color: {text_color};
    ">{grade}</span>
    """, unsafe_allow_html=True)


def render_progress_bar(value: float, max_value: float, label: str = ""):
    """
    Render a styled progress bar.

    Args:
        value: Current value
        max_value: Maximum value
        label: Optional label to display
    """
    if max_value <= 0:
        percentage = 0
    else:
        percentage = min((value / max_value) * 100, 100)

    color = get_score_color(percentage)

    st.markdown(f"""
    <div style="margin: 0.5rem 0;">
        {f'<div style="font-size: 0.875rem; font-weight: 500; margin-bottom: 0.25rem;">{label}</div>' if label else ''}
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="flex: 1; height: 8px; background-color: #E5E7EB; border-radius: 4px; overflow: hidden;">
                <div style="width: {percentage}%; height: 100%; background-color: {color}; border-radius: 4px; transition: width 0.3s ease;"></div>
            </div>
            <span style="font-size: 0.875rem; font-weight: 500; color: #6B7280; min-width: 4rem; text-align: right;">
                {value:.1f} / {max_value:.1f}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_tier_breakdown(tier_name: str, tier_score: float, tier_max: float, factors: list):
    """
    Render a tier breakdown section with expandable factors.

    Args:
        tier_name: Name of the tier
        tier_score: Score achieved in this tier
        tier_max: Maximum possible score for this tier
        factors: List of factor dicts with 'name', 'score', 'max', 'reasoning'
    """
    percentage = (tier_score / tier_max * 100) if tier_max > 0 else 0
    color = get_score_color(percentage)

    with st.expander(f"{tier_name} — {tier_score:.1f} / {tier_max:.1f} pts", expanded=False):
        # Progress bar for tier
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="flex: 1; height: 10px; background-color: #E5E7EB; border-radius: 5px; overflow: hidden;">
                    <div style="width: {percentage}%; height: 100%; background-color: {color}; border-radius: 5px;"></div>
                </div>
                <span style="font-weight: 600; color: {color};">{percentage:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Individual factors
        for factor in factors:
            factor_pct = (factor['score'] / factor['max'] * 100) if factor['max'] > 0 else 0
            factor_color = get_score_color(factor_pct)

            st.markdown(f"""
            <div style="padding: 1rem; background-color: #F9FAFB; border-radius: 8px; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 500;">{factor['name']}</span>
                    <span style="font-weight: 600; color: {factor_color};">{factor['score']:.1f} / {factor['max']:.1f}</span>
                </div>
                {f'<div style="font-size: 0.875rem; color: #6B7280; border-left: 3px solid {factor_color}; padding-left: 0.75rem; margin-top: 0.5rem;">{factor.get("reasoning", "")}</div>' if factor.get('reasoning') else ''}
            </div>
            """, unsafe_allow_html=True)


def render_card(title: str, description: str, icon: str = "", button_text: str = "", button_key: str = ""):
    """
    Render a modern card component.

    Args:
        title: Card title
        description: Card description
        icon: Optional emoji icon
        button_text: Optional button text
        button_key: Unique key for button

    Returns:
        True if button was clicked, False otherwise
    """
    st.markdown(f"""
    <div style="
        padding: 1.5rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        transition: all 0.2s ease;
        cursor: pointer;
    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.1)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
        <div style="font-size: 2rem; margin-bottom: 0.75rem;">{icon}</div>
        <h3 style="font-size: 1.25rem !important; font-weight: 600 !important; margin-bottom: 0.5rem !important;">{title}</h3>
        <p style="color: #6B7280; font-size: 0.95rem; margin-bottom: 1rem; line-height: 1.5;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

    if button_text and button_key:
        return st.button(button_text, key=button_key, use_container_width=True)
    return False
