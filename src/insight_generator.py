import json
from typing import Dict, Any

_INSIGHT_PROMPT = """You are a senior market research analyst. Based on social listening data, produce executive-grade insights.

Query: {query}
Request Type: {request_type}
Category: {category}
Topic: {topic}
Audience: {audience}

Analysis Summary:
- Total Mentions: {total_mentions}
- Avg Sentiment Score: {avg_sentiment} (scale: -1 negative to +1 positive)
- Positive: {pos_pct}% | Neutral: {neu_pct}% | Negative: {neg_pct}%
- Top Keywords: {keywords}
- Topic Clusters: {topics}
- Top Sources: {sources}

Sample Positive Voices: {positive_samples}
Sample Negative Voices: {negative_samples}

Return ONLY valid JSON with:
{{
  "summary": "2-3 sentence executive summary",
  "key_themes": [
    {{"theme": "Theme Name", "description": "One sentence explaining this theme"}},
    ...
  ],
  "opportunities": ["Opportunity 1", "Opportunity 2", "Opportunity 3", "Opportunity 4"],
  "risks": ["Risk 1", "Risk 2", "Risk 3"],
  "recommendations": ["Action 1", "Action 2", "Action 3", "Action 4"]
}}

Be specific, actionable, and grounded in the data provided."""


def _template_insights(classification: Dict, analysis: Dict) -> Dict:
    topic = classification.get("topic", "this category")
    category = classification.get("category", "the category")
    avg = analysis["avg_sentiment"]
    pct = analysis["sentiment_pct"]
    pos_pct = pct.get("positive", 0)
    neg_pct = pct.get("negative", 0)
    keywords = [kw for kw, _ in analysis["top_keywords"][:5]]
    topics = analysis.get("topics", [])

    sentiment_word = "positive" if avg > 0.1 else "mixed" if avg > -0.1 else "negative"

    themes = []
    for t in topics[:4]:
        themes.append({
            "theme": t["label"],
            "description": f"Consumers are actively discussing {', '.join(t['keywords'][:3])}, with {'positive' if t['sentiment'] > 0 else 'critical'} overall sentiment.",
        })
    if not themes:
        themes = [
            {"theme": "Ingredient Transparency", "description": f"Consumers demand clear, honest labelling of what goes into {topic} products."},
            {"theme": "Effectiveness Skepticism", "description": f"A significant segment questions whether {topic} claims are backed by clinical evidence."},
            {"theme": "Value for Money", "description": f"Price-to-performance ratio is a recurring concern across all consumer segments."},
        ]

    opportunities = [
        f"Develop clinically validated {topic} positioning to address consumer skepticism around effectiveness claims ({neg_pct:.0f}% negative sentiment).",
        f"Target the {pos_pct:.0f}% of positive advocates — they are potential brand ambassadors; build a community or loyalty program.",
        f"Address the unmet need for affordable, high-quality {topic} alternatives; premium pricing is a friction point.",
        f"Create educational content around key consumer interests: {', '.join(keywords[:3])}.",
    ]

    risks = [
        f"Negative sentiment at {neg_pct:.0f}% poses brand risk if misinformation or unmet expectations go unaddressed.",
        f"Credibility gap — bold product claims without clinical backing are drawing consumer backlash in the {category} space.",
        f"Competitive disruption risk from emerging brands better aligned with consumer values around {', '.join(keywords[:2])}.",
    ]

    recommendations = [
        f"Invest in third-party clinical validation for {topic} efficacy claims to build credibility and trust.",
        f"Launch a transparent ingredient communication campaign addressing the top concerns: {', '.join(keywords[:3])}.",
        f"Engage with online communities (Reddit, YouTube) where high-engagement conversations are happening — organic credibility is critical.",
        f"Explore product line extension targeting underserved sub-segments identified in consumer conversations.",
    ]

    summary = (
        f"Consumer conversations around {topic} reveal {sentiment_word} overall sentiment "
        f"({pos_pct:.0f}% positive, {neg_pct:.0f}% negative) across {analysis['total_mentions']} mentions. "
        f"Key drivers of discussion include {', '.join(keywords[:4])}, with significant debate around "
        f"ingredient efficacy and value. Opportunities exist for brands that lead with transparency, "
        f"clinical validation, and authentic consumer engagement."
    )

    return {
        "summary": summary,
        "key_themes": themes,
        "opportunities": opportunities,
        "risks": risks,
        "recommendations": recommendations,
    }


def generate_insights(query: str, classification: Dict, analysis: Dict, api_key: str = None) -> Dict[str, Any]:
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            pct = analysis["sentiment_pct"]
            prompt = _INSIGHT_PROMPT.format(
                query=query,
                request_type=classification.get("request_type", ""),
                category=classification.get("category", ""),
                topic=classification.get("topic", ""),
                audience=classification.get("audience", ""),
                total_mentions=analysis["total_mentions"],
                avg_sentiment=analysis["avg_sentiment"],
                pos_pct=pct.get("positive", 0),
                neu_pct=pct.get("neutral", 0),
                neg_pct=pct.get("negative", 0),
                keywords=[kw for kw, _ in analysis["top_keywords"][:10]],
                topics=[t["label"] for t in analysis.get("topics", [])],
                sources=list(analysis["source_distribution"].keys()),
                positive_samples=analysis["top_positive"][:2],
                negative_samples=analysis["top_negative"][:2],
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=900,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            pass

    return _template_insights(classification, analysis)
