"""Scoring model definitions and calculations."""
from typing import Dict, List, Any

# Scoring model definition
SCORING_MODEL = {
    "tier_1_foundational": {
        "name": "Tier 1 - Foundational",
        "max_points": 36,  # Updated: outlet_tier now max 20, article_type now max 2, brand_in_headline moved to bonus
        "factors": {
            "outlet_tier": {"max": 20, "description": "Quality tier of the outlet"},
            "overall_sentiment": {"max": 7, "description": "Overall sentiment of the article"},
            "article_exclusively_about_client": {"max": 4, "description": "Article is exclusively about the client"},
            "article_type": {"max": 2, "description": "Type of article (feature/news/brief)"},
            "tone_toward_client": {"max": 3, "description": "Specific tone toward the client"}
        }
    },
    "tier_2_messaging": {
        "name": "Tier 2 - Messaging & Voice",
        "max_points": 30,
        "factors": {
            "key_messages_high": {"max": 9, "description": "High priority key messages present (3 pts each, up to 9)"},
            "key_messages_medium": {"max": 3, "description": "Medium priority key messages present (1.5 pts each, up to 3)"},
            "key_messages_low": {"max": 1, "description": "Low priority key messages present (0.5 pts each, up to 1)"},
            "direct_quote_included": {"max": 6, "description": "Direct quote from client included"},
            "number_of_quotes": {"max": 3, "description": "Number of quotes from client"},
            "preferred_framing_used": {"max": 5, "description": "Client's preferred framing used"},
            "data_stat_cited": {"max": 3, "description": "Data or statistic from client cited"}
        }
    },
    "tier_3_prominence": {
        "name": "Tier 3 - Prominence & Position",
        "max_points": 10,  # Updated: paragraph_first_mention max changed from 4 to 3
        "factors": {
            "paragraph_first_mention": {"max": 3, "description": "Paragraph of first mention (earlier = better)"},
            "brand_in_opening": {"max": 3, "description": "Brand in opening sentence"},
            "percentage_focused_on_client": {"max": 2, "description": "Percentage of article focused on client"},
            "brand_in_closing": {"max": 1, "description": "Brand in closing paragraph"},
            "total_brand_mentions": {"max": 1, "description": "Total number of brand mentions"}
        }
    },
    "tier_4_credibility": {
        "name": "Tier 4 - Credibility & Spokesperson",
        "max_points": 10,
        "factors": {
            "spokesperson_named": {"max": 2.5, "description": "Spokesperson is named"},
            "framed_as_expert": {"max": 2, "description": "Client framed as expert/authority"},
            "framed_as_innovator": {"max": 2, "description": "Client framed as innovator/leader"},
            "spokesperson_title": {"max": 1.5, "description": "Spokesperson title included"},
            "positive_trend_association": {"max": 1, "description": "Client associated with positive trend"},
            "problem_association": {"max": -1, "description": "Client associated with problem (penalty)", "is_penalty": True}
        }
    },
    "tier_5_competitive": {
        "name": "Tier 5 - Competitive Dynamics",
        "max_points": 9,
        "factors": {
            "positioned_as_leader": {"max": 2, "description": "Client positioned as leader vs follower"},
            "mentioned_before_competitors": {"max": 1.5, "description": "Client mentioned before competitors"},
            "share_of_voice": {"max": 1.5, "description": "Share of voice vs competitors"},
            "competitors_mentioned": {"max": -1.5, "description": "Competitors mentioned (penalty)", "is_penalty": True},
            "more_quotes_than_competitors": {"max": 1.5, "description": "Client has more quotes than competitors"},
            "number_competitors_mentioned": {"max": -2.5, "description": "Number of competitors mentioned (-0.5 each)", "is_penalty": True},
            "competitor_in_headline": {"max": -0.5, "description": "Competitor in headline (penalty)", "is_penalty": True}
        }
    },
    "tier_6_audience_fit": {
        "name": "Tier 6 - Outlet & Audience Fit",
        "max_points": 6.5,
        "factors": {
            "outlet_industry_relevance": {"max": 3.5, "description": "Outlet relevance to client's industry"},
            "outlet_audience_relevance": {"max": 3, "description": "Outlet relevance to target audience"}
        }
    },
    "tier_7_supporting": {
        "name": "Tier 7 - Supporting Details",
        "max_points": 2.5,
        "factors": {
            "cta_or_product_mention": {"max": 0.5, "description": "CTA or product mention"},
            "article_length": {"max": 0.5, "description": "Article length (longer = better)"},
            "brand_only_in_headline": {"max": 0.5, "description": "Brand is the only company in headline"},
            "exclusive_story": {"max": 0.5, "description": "Exclusive story"},
            "journalist_covered_before": {"max": 0.5, "description": "Journalist covered client before"}
        }
    },
    "bonus": {
        "name": "Bonus Points",
        "max_points": 16,  # Updated: new bonus structure with +16 cap
        "factors": {
            "op_ed_by_client": {"max": 8, "description": "Op-ed by client spokesperson in Tier 1 outlet"},
            "brand_in_headline": {"max": 3, "description": "Client brand appears in headline"},
            "syndicated": {"max": 1.5, "description": "Syndicated to other outlets"},
            "ranks_for_keywords": {"max": 1.5, "description": "Ranks for target keywords"},
            "appears_in_google_news": {"max": 1, "description": "Appears in Google News"},
            "open_access": {"max": 0.5, "description": "Open access (no paywall)"}
        }
    }
}

def get_outlet_tier_points(tier: int) -> float:
    """Calculate points based on outlet tier."""
    # Updated: Tier 1 increased from 15 to 20 points
    tier_points = {1: 20, 2: 13, 3: 8, 4: 3}
    return tier_points.get(tier, 0)

def calculate_total_score(scores: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Calculate total score from individual factor scores.

    Args:
        scores: Dict with tier keys containing factor scores

    Returns:
        Dict with total_score, tier_scores, and breakdown
    """
    tier_scores = {}
    total = 0

    for tier_key, tier_info in SCORING_MODEL.items():
        tier_total = 0
        if tier_key in scores:
            for factor_key, score in scores[tier_key].items():
                tier_total += score
        tier_scores[tier_key] = {
            "name": tier_info["name"],
            "score": tier_total,
            "max": tier_info["max_points"]
        }
        if tier_key != "bonus":
            total += max(0, tier_total)  # Don't let individual tiers go negative
        else:
            total += tier_total  # Bonus can only be positive

    # Cap at 116 (100 base + 16 bonus)
    total = min(116, max(0, total))

    return {
        "total_score": round(total, 1),
        "tier_scores": tier_scores,
        "detailed_scores": scores
    }

def get_score_grade(score: float) -> str:
    """Get letter grade for score."""
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

def get_score_color(score: float) -> str:
    """Get color for score display."""
    if score >= 80:
        return "#10B981"  # Green
    elif score >= 60:
        return "#3B82F6"  # Blue
    elif score >= 40:
        return "#F59E0B"  # Amber
    else:
        return "#EF4444"  # Red
