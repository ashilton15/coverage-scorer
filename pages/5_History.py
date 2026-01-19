"""History page - View past article analyses."""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_history, delete_history_item, get_history_item,
    get_batches, get_batch_by_id, delete_batch
)
from utils.scoring import SCORING_MODEL

st.set_page_config(
    page_title="History - Coverage Scorer",
    page_icon="",
    layout="wide"
)

# Import and inject custom styles
from utils.styles import (
    inject_custom_css, render_sidebar, render_score_circle,
    get_score_color, get_score_grade
)

inject_custom_css()
render_sidebar()


def format_date(date_str: str) -> str:
    """Format ISO date string for display."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except:
        return date_str


def render_batch_list():
    """Render the list of batch analyses."""
    batches = get_batches()
    history = get_history()  # For single article analyses

    if not batches and not history:
        st.info("No analyses yet. Go to Analyze Article or Batch Analysis to score articles.")
        return

    # Filter controls
    col1, col2 = st.columns([2, 1])

    with col1:
        search = st.text_input("Search", placeholder="Search by batch name, headline, or outlet...")

    with col2:
        # Get unique clients from both batches and history
        clients = set()
        for b in batches:
            if b.get("client"):
                clients.add(b["client"])
        for h in history:
            if h.get("client"):
                clients.add(h["client"])
        client_filter = st.multiselect(
            "Filter by Client",
            options=sorted(list(clients)),
            default=[]
        )

    # Filter batches
    filtered_batches = batches
    if search:
        search_lower = search.lower()
        filtered_batches = [
            b for b in filtered_batches
            if search_lower in b.get("batch_name", "").lower()
            or search_lower in b.get("client", "").lower()
            or any(search_lower in a.get("headline", "").lower() or search_lower in a.get("outlet", "").lower()
                   for a in b.get("articles", []))
        ]
    if client_filter:
        filtered_batches = [b for b in filtered_batches if b.get("client") in client_filter]

    # Filter single article history (non-batch)
    filtered_history = [h for h in history if not h.get("batch_id")]
    if search:
        search_lower = search.lower()
        filtered_history = [
            h for h in filtered_history
            if search_lower in h.get("headline", "").lower()
            or search_lower in h.get("outlet", "").lower()
        ]
    if client_filter:
        filtered_history = [h for h in filtered_history if h.get("client") in client_filter]

    total_count = len(filtered_batches) + len(filtered_history)
    st.markdown(f"### {total_count} Analysis Record(s)")

    # Render batches
    for batch in filtered_batches:
        render_batch_card(batch)

    # Render single article analyses (non-batch)
    for item in filtered_history:
        render_single_article_card(item)


def render_batch_card(batch):
    """Render a single batch as an expandable card."""
    batch_id = batch.get("batch_id", "")
    batch_name = batch.get("batch_name", "Unknown Batch")
    client = batch.get("client", "Unknown")
    article_count = batch.get("article_count", 0)
    successful = batch.get("successful_count", 0)
    failed = batch.get("failed_count", 0)
    avg_score = batch.get("avg_score", 0)
    created_at = batch.get("created_at", "")

    color = get_score_color(avg_score)
    grade = get_score_grade(avg_score)

    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4 style="margin: 0; color: #000000; font-weight: 600;">
                        {batch_name}
                        <span style="background: #EEF2FF; color: #4F46E5; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;">Batch</span>
                    </h4>
                    <p style="color: #6B7280; margin: 0.25rem 0 0 0; font-size: 0.875rem;">
                        {client} &bull; {format_date(created_at)} &bull; {successful}/{article_count} successful
                        {f' &bull; {failed} failed' if failed > 0 else ''}
                    </p>
                </div>
                <div style="
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 700;
                    background: {color}20;
                    color: {color};
                ">
                    Avg: {avg_score:.1f} ({grade})
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("View", key=f"view_batch_{batch_id}"):
            st.session_state.viewing_batch = batch_id
            st.rerun()

    with col3:
        if st.button("Delete", key=f"delete_batch_{batch_id}"):
            st.session_state.deleting_batch = batch_id
            st.rerun()


def render_single_article_card(item):
    """Render a single article analysis card."""
    score = item.get("total_score", 0)
    color = get_score_color(score)
    grade = get_score_grade(score)

    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4 style="margin: 0; color: #000000; font-weight: 600;">{item.get('headline', 'Untitled')}</h4>
                    <p style="color: #6B7280; margin: 0.25rem 0 0 0; font-size: 0.875rem;">
                        {item.get('outlet', 'Unknown outlet')} &bull;
                        {item.get('client', 'Unknown client')} &bull;
                        {format_date(item.get('analyzed_at', ''))}
                    </p>
                </div>
                <div style="
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 700;
                    background: {color}20;
                    color: {color};
                ">
                    {score:.1f} ({grade})
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("View", key=f"view_{item['id']}"):
            st.session_state.viewing_item = item["id"]
            st.rerun()

    with col3:
        if st.button("Delete", key=f"delete_{item['id']}"):
            st.session_state.deleting_item = item["id"]
            st.rerun()


def render_tier_breakdown(tier_scores: dict, detailed_scores: dict):
    """Render tier breakdown with expandable reasoning."""
    for tier_key, tier_info in tier_scores.items():
        score = tier_info.get("score", 0)
        max_pts = tier_info.get("max", 1)
        name = tier_info.get("name", tier_key.replace("_", " ").title())

        percentage = max(0, min(100, (score / max_pts) * 100)) if max_pts > 0 else 0
        color = get_score_color(percentage)

        with st.expander(f"{name}: {score:.1f} / {max_pts} pts", expanded=False):
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


def render_detail_view(item_id: str):
    """Render detailed view of a history item."""
    item = get_history_item(item_id)

    if not item:
        st.error("Analysis not found")
        return

    # Back button
    if st.button("Back to History"):
        del st.session_state.viewing_item
        st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Header
    st.markdown(f"# {item.get('headline', 'Untitled')}")

    # Check if this is from a batch
    batch_name = item.get('batch_name', '')

    if batch_name:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"**Outlet:** {item.get('outlet', 'Unknown')}")
        with col2:
            st.markdown(f"**Client:** {item.get('client', 'Unknown')}")
        with col3:
            st.markdown(f"**Author:** {item.get('author', 'Unknown')}")
        with col4:
            st.markdown(f"**Date:** {format_date(item.get('analyzed_at', ''))}")
        with col5:
            st.markdown(f"**Batch:** {batch_name}")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"**Outlet:** {item.get('outlet', 'Unknown')}")
        with col2:
            st.markdown(f"**Client:** {item.get('client', 'Unknown')}")
        with col3:
            st.markdown(f"**Author:** {item.get('author', 'Unknown')}")
        with col4:
            st.markdown(f"**Date:** {format_date(item.get('analyzed_at', ''))}")

    if item.get("url"):
        st.markdown(f"**URL:** [{item['url']}]({item['url']})")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Score display
    col1, col2 = st.columns([1, 2])

    with col1:
        render_score_circle(item.get("total_score", 0), 116)

    with col2:
        summary = item.get("summary", {})
        if summary:
            st.markdown("### Overall Assessment")
            st.markdown(summary.get("overall_assessment", "No assessment available"))

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

    tier_scores = item.get("tier_scores", {})
    detailed_scores = item.get("detailed_scores", {})

    render_tier_breakdown(tier_scores, detailed_scores)

    # Recommendations
    if summary.get("recommendations"):
        st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)
        st.markdown("## Recommendations")
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


def render_batch_detail_view(batch_id: str):
    """Render detailed view of a batch with all its articles."""
    batch = get_batch_by_id(batch_id)

    if not batch:
        st.error("Batch not found")
        return

    # Back button
    if st.button("Back to History"):
        del st.session_state.viewing_batch
        st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Header
    batch_name = batch.get("batch_name", "Unknown Batch")
    client = batch.get("client", "Unknown")
    article_count = batch.get("article_count", 0)
    successful = batch.get("successful_count", 0)
    failed = batch.get("failed_count", 0)
    avg_score = batch.get("avg_score", 0)
    created_at = batch.get("created_at", "")
    articles = batch.get("articles", [])

    st.markdown(f"# {batch_name}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"**Client:** {client}")
    with col2:
        st.markdown(f"**Date:** {format_date(created_at)}")
    with col3:
        st.markdown(f"**Articles:** {successful}/{article_count} successful")
    with col4:
        color = get_score_color(avg_score)
        grade = get_score_grade(avg_score)
        st.markdown(f"**Avg Score:** <span style='color: {color}; font-weight: bold;'>{avg_score:.1f} ({grade})</span>", unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", article_count)
    with col2:
        st.metric("Successful", successful)
    with col3:
        st.metric("Failed", failed)
    with col4:
        st.metric("Average Score", f"{avg_score:.1f}")

    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("## Articles in this Batch")

    # Render each article
    for i, article in enumerate(articles):
        # Get article data - articles is a list of dicts
        status = article.get("status", "unknown")
        headline = article.get("headline", "") or "Untitled"
        outlet = article.get("outlet", "") or "Unknown"
        url = article.get("url", "")
        score = article.get("total_score")

        # Clean up headline - remove extra whitespace/newlines
        headline = " ".join(str(headline).split()).strip()
        if not headline:
            headline = "Untitled"

        # Clean up outlet
        outlet = " ".join(str(outlet).split()).strip()
        if not outlet:
            outlet = "Unknown"

        # Determine score display
        if status == "success" and score is not None:
            color = get_score_color(score)
            grade = get_score_grade(score)
            score_display = f"{score:.1f} ({grade})"
        elif status == "failed":
            color = "#EF4444"
            score_display = "Failed"
        else:
            color = "#6B7280"
            score_display = "N/A"

        # Truncate headline for display
        display_headline = headline[:80] + "..." if len(headline) > 80 else headline

        # Create expander label with article info
        expander_label = f"{display_headline} - {outlet} - Score: {score_display}"

        with st.expander(expander_label):
            col1, col2 = st.columns([1, 3])

            with col1:
                if status == "success" and score is not None:
                    render_score_circle(score, 116)
                else:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 2rem;">
                        <div style="font-size: 2rem; color: {color};">{'X' if status == 'failed' else '-'}</div>
                        <div style="color: #6B7280; margin-top: 0.5rem;">
                            {'Fetch Failed' if status == 'failed' else 'No Score'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"**Headline:** {headline or '(Not provided)'}")
                st.markdown(f"**Outlet:** {outlet}")
                if article.get("author"):
                    st.markdown(f"**Author:** {article['author']}")
                if url:
                    st.markdown(f"**URL:** [{url}]({url})")

                if status == "failed":
                    error = article.get("error", "Unknown error")
                    http_status = article.get("http_status")
                    st.error(f"Error: {error}" + (f" (HTTP {http_status})" if http_status else ""))
                elif status == "success":
                    key_messages = article.get("key_messages_found", [])
                    if key_messages:
                        st.markdown(f"**Key Messages Found:** {', '.join(key_messages)}")
                    notes = article.get("analysis_notes", "")
                    if notes:
                        st.markdown(f"**Notes:** {notes}")

            # Show detailed breakdown for successful articles
            if status == "success":
                st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 1rem 0;'>", unsafe_allow_html=True)
                st.markdown("#### Scoring Breakdown")

                tier_scores = article.get("tier_scores", {})
                detailed_scores = article.get("detailed_scores", {})

                if tier_scores:
                    render_tier_breakdown(tier_scores, detailed_scores)

                # Summary
                summary = article.get("summary", {})
                if summary:
                    if summary.get("overall_assessment"):
                        st.markdown("**Overall Assessment:**")
                        st.markdown(summary["overall_assessment"])

                    col1, col2 = st.columns(2)
                    with col1:
                        if summary.get("strengths"):
                            st.markdown("**Strengths:**")
                            for s in summary["strengths"]:
                                st.markdown(f"- {s}")
                    with col2:
                        if summary.get("weaknesses"):
                            st.markdown("**Areas for Improvement:**")
                            for w in summary["weaknesses"]:
                                st.markdown(f"- {w}")


def main():
    st.markdown("""
    <h1 style="font-size: 2.5rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important;">
        Analysis History
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">
        View past article analyses and their scores
    </p>
    """, unsafe_allow_html=True)

    # Handle batch delete confirmation
    if "deleting_batch" in st.session_state:
        batch_id = st.session_state.deleting_batch
        batch = get_batch_by_id(batch_id)

        if batch:
            st.warning(f"Are you sure you want to delete the batch **{batch.get('batch_name', 'Unknown')}** and all {batch.get('article_count', 0)} articles in it?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete Batch", type="primary"):
                    delete_batch(batch_id)
                    del st.session_state.deleting_batch
                    st.success("Batch deleted!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    del st.session_state.deleting_batch
                    st.rerun()
            st.stop()

    # Handle single article delete confirmation
    if "deleting_item" in st.session_state:
        item_id = st.session_state.deleting_item
        item = get_history_item(item_id)

        if item:
            st.warning(f"Are you sure you want to delete the analysis for **{item.get('headline', 'Untitled')}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    delete_history_item(item_id)
                    del st.session_state.deleting_item
                    st.success("Analysis deleted!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    del st.session_state.deleting_item
                    st.rerun()
            st.stop()

    # Handle viewing batch
    if "viewing_batch" in st.session_state:
        render_batch_detail_view(st.session_state.viewing_batch)
        st.stop()

    # Handle viewing single article
    if "viewing_item" in st.session_state:
        render_detail_view(st.session_state.viewing_item)
        st.stop()

    # Main list view
    render_batch_list()


if __name__ == "__main__":
    main()
