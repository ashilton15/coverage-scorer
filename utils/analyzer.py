"""Claude API integration for article analysis."""
import json
from typing import Dict, List, Any, Optional
from anthropic import Anthropic

def create_analysis_prompt(
    article_text: str,
    headline: str,
    outlet_name: str,
    author: str,
    client: Dict,
    outlet_info: Optional[Dict] = None
) -> str:
    """Create the analysis prompt for Claude."""

    # Format key messages with priorities
    key_messages_text = ""
    if client.get("key_messages"):
        for msg in client["key_messages"]:
            priority = msg.get("priority", "medium")
            key_messages_text += f"  - [{priority.upper()}] {msg['message']}\n"
    else:
        key_messages_text = "  (No key messages defined)\n"

    competitors_text = ", ".join(client.get("competitors", [])) if client.get("competitors") else "(No competitors defined)"

    outlet_tier = outlet_info.get("tier", "Unknown") if outlet_info else "Unknown"
    outlet_reach = outlet_info.get("reach_estimate", "Unknown") if outlet_info else "Unknown"

    prompt = f"""Analyze this news article and score it based on how well it covers the client. Evaluate each factor carefully and provide specific reasoning.

CLIENT PROFILE:
- Name: {client.get('name', 'Unknown')}
- Industry: {client.get('industry', 'Unknown')}
- Key Messages (with priority levels):
{key_messages_text}
- Competitors: {competitors_text}

ARTICLE METADATA:
- Headline: {headline}
- Outlet: {outlet_name}
- Outlet Tier: {outlet_tier}
- Outlet Reach: {outlet_reach}
- Author: {author}

ARTICLE TEXT:
{article_text}

---

Please analyze and score each factor below. For each factor, provide:
1. A score (within the specified range)
2. Brief reasoning for the score

Return your analysis as a JSON object with this exact structure:

{{
  "tier_1_foundational": {{
    "outlet_tier": {{"score": <0-20>, "reasoning": "..."}},
    "overall_sentiment": {{"score": <0-7>, "reasoning": "..."}},
    "article_exclusively_about_client": {{"score": <0-4>, "reasoning": "..."}},
    "article_type": {{"score": <0-2>, "reasoning": "..."}},
    "tone_toward_client": {{"score": <0-3>, "reasoning": "..."}}
  }},
  "tier_2_messaging": {{
    "key_messages_high": {{"score": <0-9>, "reasoning": "...", "messages_found": ["list of high-priority messages found"]}},
    "key_messages_medium": {{"score": <0-3>, "reasoning": "...", "messages_found": ["list of medium-priority messages found"]}},
    "key_messages_low": {{"score": <0-1>, "reasoning": "...", "messages_found": ["list of low-priority messages found"]}},
    "direct_quote_included": {{"score": <0-6>, "reasoning": "..."}},
    "number_of_quotes": {{"score": <0-3>, "reasoning": "...", "quote_count": <number>}},
    "preferred_framing_used": {{"score": <0-5>, "reasoning": "..."}},
    "data_stat_cited": {{"score": <0-3>, "reasoning": "..."}}
  }},
  "tier_3_prominence": {{
    "paragraph_first_mention": {{"score": <0.5-3>, "reasoning": "...", "paragraph_number": <number>}},
    "brand_in_opening": {{"score": <0-3>, "reasoning": "..."}},
    "percentage_focused_on_client": {{"score": <0-2>, "reasoning": "...", "percentage": <number>}},
    "brand_in_closing": {{"score": <0-1>, "reasoning": "..."}},
    "total_brand_mentions": {{"score": <0-1>, "reasoning": "...", "mention_count": <number>}}
  }},
  "tier_4_credibility": {{
    "spokesperson_named": {{"score": <0-2.5>, "reasoning": "...", "spokesperson": "name or null"}},
    "framed_as_expert": {{"score": <0-2>, "reasoning": "..."}},
    "framed_as_innovator": {{"score": <0-2>, "reasoning": "..."}},
    "spokesperson_title": {{"score": <0-1.5>, "reasoning": "...", "title": "title or null"}},
    "positive_trend_association": {{"score": <0-1>, "reasoning": "..."}},
    "problem_association": {{"score": <-1 to 0>, "reasoning": "..."}}
  }},
  "tier_5_competitive": {{
    "positioned_as_leader": {{"score": <0-2>, "reasoning": "..."}},
    "mentioned_before_competitors": {{"score": <0-1.5>, "reasoning": "..."}},
    "share_of_voice": {{"score": <0-1.5>, "reasoning": "...", "client_share": <percentage>}},
    "competitors_mentioned": {{"score": <-1.5 to 0>, "reasoning": "..."}},
    "more_quotes_than_competitors": {{"score": <0-1.5>, "reasoning": "..."}},
    "number_competitors_mentioned": {{"score": <-2.5 to 0>, "reasoning": "...", "competitor_count": <number>, "competitors_found": ["list"]}},
    "competitor_in_headline": {{"score": <-0.5 to 0>, "reasoning": "..."}}
  }},
  "tier_6_audience_fit": {{
    "outlet_industry_relevance": {{"score": <0-3.5>, "reasoning": "..."}},
    "outlet_audience_relevance": {{"score": <0-3>, "reasoning": "..."}}
  }},
  "tier_7_supporting": {{
    "cta_or_product_mention": {{"score": <0-0.5>, "reasoning": "..."}},
    "article_length": {{"score": <0-0.5>, "reasoning": "...", "word_count": <number>}},
    "brand_only_in_headline": {{"score": <0-0.5>, "reasoning": "..."}},
    "exclusive_story": {{"score": <0-0.5>, "reasoning": "..."}},
    "journalist_covered_before": {{"score": <0-0.5>, "reasoning": "..."}}
  }},
  "bonus": {{
    "op_ed_by_client": {{"score": <0 or 8>, "reasoning": "Award 8 pts if article is an opinion piece/op-ed AND has a byline from the client's spokesperson AND appears in a Tier 1 outlet. Look for opinion/op-ed indicators in the article type and check if the author is from the client organization."}},
    "brand_in_headline": {{"score": <0-3>, "reasoning": "Award 3 pts if client brand appears in headline, otherwise 0"}},
    "syndicated": {{"score": <0-1.5>, "reasoning": "..."}},
    "ranks_for_keywords": {{"score": <0-1.5>, "reasoning": "..."}},
    "appears_in_google_news": {{"score": <0-1>, "reasoning": "..."}},
    "open_access": {{"score": <0-0.5>, "reasoning": "..."}}
  }},
  "summary": {{
    "overall_assessment": "2-3 sentence summary of the coverage quality",
    "strengths": ["list of key strengths"],
    "weaknesses": ["list of key weaknesses"],
    "recommendations": ["list of recommendations for future coverage"]
  }}
}}

SCORING GUIDELINES:
- For outlet_tier: Tier 1 = 20pts, Tier 2 = 13pts, Tier 3 = 8pts, Tier 4 = 3pts
- For article_type: Feature article = 2pts, News article = 1pt, Brief/mention = 0pts
- For key_messages_high: 3 pts per message found, up to 9 pts max
- For key_messages_medium: 1.5 pts per message found, up to 3 pts max
- For key_messages_low: 0.5 pts per message found, up to 1 pt max
- For number_of_quotes: 1 quote = 1pt, 2 quotes = 2pts, 3+ quotes = 3pts
- For paragraph_first_mention: Paragraphs 1-3 = 3pts, Paragraphs 4-6 = 2pts, Paragraphs 7-10 = 1.5pts, Paragraphs 11-15 = 1pt, Paragraph 16+ = 0.5pts
- For number_competitors_mentioned: -0.5 pts per competitor mentioned
- Penalty scores should be negative (e.g., -1.5 for competitors_mentioned if competitors are present)

BONUS SCORING (up to +16 total):
- op_ed_by_client: +8 pts if article is an opinion/op-ed piece AND authored by client's spokesperson AND in a Tier 1 outlet
- brand_in_headline: +3 pts if client brand appears in headline
- syndicated: +1.5 pts if syndicated to other outlets
- ranks_for_keywords: +1.5 pts if ranks for target keywords
- appears_in_google_news: +1 pt if appears in Google News
- open_access: +0.5 pts if no paywall

Be thorough but fair. Only award points when clearly justified by the article content."""

    return prompt


def extract_key_messages_prompt(document_text: str, client_name: str, industry: str) -> str:
    """Create prompt for extracting key messages from a briefing document."""
    return f"""Analyze this briefing document for {client_name} (industry: {industry}) and extract all key messages that should be tracked in media coverage.

DOCUMENT:
{document_text}

---

Extract key messages that represent:
1. Core value propositions
2. Strategic positioning statements
3. Product/service differentiators
4. Company mission or vision statements
5. Key talking points for media
6. Important statistics or claims the company wants communicated

Return the key messages as a simple list, one per line, starting with a dash (-). Each message should be:
- Clear and concise (1-2 sentences max)
- Specific and measurable when possible
- Representative of what the company wants journalists to communicate

Example format:
- Company X is the leading provider of sustainable packaging solutions
- Our technology reduces carbon emissions by 40% compared to traditional methods
- We serve over 500 enterprise customers across 30 countries

Extract all relevant key messages from the document:"""


def analyze_article(
    api_key: str,
    article_text: str,
    headline: str,
    outlet_name: str,
    author: str,
    client: Dict,
    outlet_info: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Analyze an article using Claude API.

    Returns:
        Dict with scores, reasoning, and summary
    """
    try:
        client_api = Anthropic(api_key=api_key)

        prompt = create_analysis_prompt(
            article_text, headline, outlet_name, author, client, outlet_info
        )

        message = client_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            analysis = json.loads(json_str)
            return {"success": True, "analysis": analysis}
        else:
            return {"success": False, "error": "Could not parse analysis response"}

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Analysis error: {str(e)}"}


def extract_key_messages(
    api_key: str,
    document_text: str,
    client_name: str,
    industry: str
) -> Dict[str, Any]:
    """
    Extract key messages from a briefing document using Claude.

    Returns:
        Dict with success status and messages list or error
    """
    try:
        client_api = Anthropic(api_key=api_key)

        prompt = extract_key_messages_prompt(document_text, client_name, industry)

        message = client_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse the messages
        from utils.document_parser import parse_extracted_messages
        messages = parse_extracted_messages(response_text)

        return {"success": True, "messages": messages}

    except Exception as e:
        return {"success": False, "error": f"Extraction error: {str(e)}"}
