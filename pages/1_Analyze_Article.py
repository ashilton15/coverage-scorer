"""Analyze Article page - Main scoring interface."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_clients, get_outlets, get_api_key, add_to_history
)
from utils.article_fetcher import fetch_article, count_words, extract_domain
from utils.analyzer import analyze_article
from utils.scoring import SCORING_MODEL, calculate_total_score

st.set_page_config(
    page_title="Analyze Article - Coverage Scorer",
    page_icon="",
    layout="wide"
)

# Import and inject custom styles
from utils.styles import (
    inject_custom_css, render_sidebar, render_score_circle,
    get_score_color, get_score_grade, render_grade_badge
)

inject_custom_css()
render_sidebar()


def render_tier_breakdown(tier_scores: dict, detailed_scores: dict):
    """Render tier-by-tier breakdown with expandable reasoning."""
    for tier_key, tier_info in tier_scores.items():
        score = tier_info.get("score", 0)
        max_pts = tier_info.get("max", 1)
        name = tier_info.get("name", tier_key.replace("_", " ").title())

        percentage = max(0, min(100, (score / max_pts) * 100)) if max_pts > 0 else 0
        color = get_score_color(percentage)

        with st.expander(f"{name}: {score:.1f} / {max_pts} pts", expanded=False):
            # Progress bar
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

            # Show individual factors
            if tier_key in detailed_scores:
                factors = detailed_scores[tier_key]
                tier_def = SCORING_MODEL.get(tier_key, {}).get("factors", {})

                for factor_key, factor_data in factors.items():
                    if isinstance(factor_data, dict):
                        factor_score = factor_data.get("score", 0)
                        reasoning = factor_data.get("reasoning", "")
                        factor_info = tier_def.get(factor_key, {})
                        factor_max = factor_info.get("max", 0)
                        factor_desc = factor_info.get("description", factor_key)

                        # Format score display
                        if factor_max < 0:
                            score_display = f"{factor_score:.1f}"
                        else:
                            score_display = f"{factor_score:.1f} / {factor_max}"

                        factor_pct = (factor_score / factor_max * 100) if factor_max > 0 else 0
                        factor_color = get_score_color(factor_pct)

                        st.markdown(f"""
                        <div style="padding: 1rem; background-color: #F9FAFB; border-radius: 8px; margin-bottom: 0.75rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <span style="font-weight: 500;">{factor_desc}</span>
                                <span style="font-weight: 600; color: {factor_color};">{score_display}</span>
                            </div>
                            {f'<div style="font-size: 0.875rem; color: #6B7280; border-left: 3px solid {factor_color}; padding-left: 0.75rem; margin-top: 0.5rem;">{reasoning}</div>' if reasoning else ''}
                        </div>
                        """, unsafe_allow_html=True)


def main():
    st.markdown("""
    <h1 style="font-size: 2.5rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important;">
        Analyze Article
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">
        Score media coverage against your client profile
    </p>
    """, unsafe_allow_html=True)

    # Check prerequisites
    api_key = get_api_key()
    clients = get_clients()
    outlets = get_outlets()

    if not api_key:
        st.error("Please configure your Anthropic API key in Settings before analyzing articles.")
        st.stop()

    if not clients:
        st.warning("No client profiles found. Please add a client profile first.")
        st.stop()

    # Initialize session state
    if "article_content" not in st.session_state:
        st.session_state.article_content = ""
    if "fetch_attempted" not in st.session_state:
        st.session_state.fetch_attempted = False
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    # Article Input Section
    st.markdown("## Article Input")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Client selection
        client_options = {c["name"]: c for c in clients}
        selected_client_name = st.selectbox(
            "Select Client Profile",
            options=list(client_options.keys()),
            help="Choose the client to score this article against"
        )
        selected_client = client_options[selected_client_name]

    with col2:
        # Outlet selection (optional)
        outlet_options = {"(Auto-detect or Unknown)": None}
        outlet_options.update({o["name"]: o for o in outlets})
        selected_outlet_name = st.selectbox(
            "Select Outlet (Optional)",
            options=list(outlet_options.keys()),
            help="Select from known outlets or leave as auto-detect"
        )
        selected_outlet = outlet_options[selected_outlet_name]

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    if "current_url" not in st.session_state:
        st.session_state.current_url = ""

    # Tabbed input interface
    input_tab1, input_tab2 = st.tabs(["URL", "Paste Text"])

    with input_tab1:
        # URL Input
        url_input = st.text_input(
            "Article URL",
            placeholder="https://example.com/article",
            help="Enter the URL of the article to analyze",
            key="url_input_field"
        )
        # Store in session state for later access
        st.session_state.current_url = url_input

        col1, col2 = st.columns([1, 4])
        with col1:
            fetch_btn = st.button("Fetch Article", type="primary")

        if fetch_btn and url_input:
            with st.spinner("Fetching article content..."):
                success, content, metadata = fetch_article(url_input)
                st.session_state.fetch_attempted = True

                if success:
                    st.session_state.article_content = content
                    st.session_state.fetched_metadata = metadata
                    st.success(f"Fetched {count_words(content)} words from {metadata['domain']}")
                else:
                    st.warning(content)  # content contains error message
                    st.session_state.fetched_metadata = metadata

    with input_tab2:
        st.markdown("Paste your article text directly below. You can edit the details in the Article Details section.")

    # Manual input fields
    st.markdown("### Article Details")

    col1, col2 = st.columns(2)
    with col1:
        headline = st.text_input(
            "Headline",
            value=st.session_state.get("fetched_metadata", {}).get("title", ""),
            help="The article headline"
        )
    with col2:
        outlet_name = st.text_input(
            "Outlet Name",
            value=selected_outlet["name"] if selected_outlet else st.session_state.get("fetched_metadata", {}).get("domain", ""),
            help="Name of the publication"
        )

    author_name = st.text_input(
        "Author Name",
        value=st.session_state.get("fetched_metadata", {}).get("author", ""),
        help="Article author (if known)"
    )

    article_text = st.text_area(
        "Article Text",
        value=st.session_state.article_content,
        height=300,
        help="Paste the full article text here",
        placeholder="Paste the article content here..."
    )

    word_count = count_words(article_text)
    if article_text:
        st.caption(f"Word count: {word_count}")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Analyze button
    analyze_btn = st.button("Analyze Article", type="primary", use_container_width=True)

    if analyze_btn:
        if not article_text or word_count < 50:
            st.error("Please provide article text (minimum 50 words)")
        elif not headline:
            st.error("Please provide a headline")
        elif not outlet_name:
            st.error("Please provide an outlet name")
        else:
            with st.spinner("Analyzing article with Claude AI..."):
                # Find outlet info if available
                outlet_info = selected_outlet
                if not outlet_info:
                    # Try to match by domain
                    current_url = st.session_state.get("current_url", "")
                    domain = extract_domain(current_url) if current_url else ""
                    for outlet in outlets:
                        if outlet.get("domain", "").lower() in domain.lower() or domain.lower() in outlet.get("domain", "").lower():
                            outlet_info = outlet
                            break

                result = analyze_article(
                    api_key=api_key,
                    article_text=article_text,
                    headline=headline,
                    outlet_name=outlet_name,
                    author=author_name,
                    client=selected_client,
                    outlet_info=outlet_info
                )

                if result["success"]:
                    st.session_state.analysis_result = result["analysis"]

                    # Extract scores for calculation
                    scores = {}
                    for tier_key in SCORING_MODEL.keys():
                        if tier_key in result["analysis"]:
                            scores[tier_key] = {}
                            for factor_key, factor_data in result["analysis"][tier_key].items():
                                if isinstance(factor_data, dict):
                                    scores[tier_key][factor_key] = factor_data.get("score", 0)

                    score_result = calculate_total_score(scores)
                    st.session_state.score_result = score_result

                    # Save to history
                    history_item = {
                        "headline": headline,
                        "outlet": outlet_name,
                        "author": author_name,
                        "client": selected_client["name"],
                        "url": st.session_state.get("current_url", ""),
                        "total_score": score_result["total_score"],
                        "tier_scores": score_result["tier_scores"],
                        "detailed_scores": result["analysis"],
                        "summary": result["analysis"].get("summary", {})
                    }
                    add_to_history(history_item)

                    st.success("Analysis complete!")
                else:
                    st.error(f"Analysis failed: {result['error']}")

    # Display Results
    if st.session_state.get("analysis_result") and st.session_state.get("score_result"):
        st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)
        st.markdown("## Analysis Results")

        result = st.session_state.analysis_result
        score_result = st.session_state.score_result

        # Score display
        col1, col2 = st.columns([1, 2])

        with col1:
            render_score_circle(score_result["total_score"], 116)

        with col2:
            # Summary
            summary = result.get("summary", {})
            if summary:
                st.markdown("### Overall Assessment")
                st.markdown(summary.get("overall_assessment", ""))

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    if summary.get("strengths"):
                        st.markdown("**Strengths:**")
                        for s in summary["strengths"]:
                            st.markdown(f"""
                            <div style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span style="color: #059669;">&#10003;</span>
                                <span>{s}</span>
                            </div>
                            """, unsafe_allow_html=True)

                with col_s2:
                    if summary.get("weaknesses"):
                        st.markdown("**Areas for Improvement:**")
                        for w in summary["weaknesses"]:
                            st.markdown(f"""
                            <div style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span style="color: #6B7280;">&#9675;</span>
                                <span>{w}</span>
                            </div>
                            """, unsafe_allow_html=True)

        st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

        # Detailed breakdown
        st.markdown("## Detailed Scoring Breakdown")
        st.markdown("Click each tier to see factor-by-factor analysis with AI reasoning")

        render_tier_breakdown(score_result["tier_scores"], result)

        # Recommendations
        if summary.get("recommendations"):
            st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)
            st.markdown("## Recommendations for Future Coverage")
            for i, rec in enumerate(summary["recommendations"], 1):
                st.markdown(f"""
                <div style="display: flex; gap: 1rem; margin-bottom: 1rem; padding: 1rem; background-color: #F9FAFB; border-radius: 8px;">
                    <div style="
                        width: 28px;
                        height: 28px;
                        background-color: #000000;
                        color: #FFFFFF;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: 600;
                        font-size: 0.875rem;
                        flex-shrink: 0;
                    ">{i}</div>
                    <div style="flex: 1;">{rec}</div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
