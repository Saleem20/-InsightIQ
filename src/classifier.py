import json
import os

CLASSIFICATION_PROMPT = """You are a market research AI that classifies social listening queries.

Given a user query, return ONLY valid JSON with these fields:
- request_type: one of [Brand Tracking, Campaign Analysis, Need Gap Analysis, Ingredient Intelligence, Competitor Analysis, Misinformation Detection, Ecommerce Review Mining, Sentiment Analysis, Trend Analysis]
- category: product/industry category (e.g., Oral Care, Skincare, Beverages, Wellness, Haircare)
- topic: the specific topic/product being researched
- audience: target audience (e.g., Gen Z, Health Enthusiasts, General Consumers)
- keywords: list of 6-8 relevant search keywords

Query: {query}"""

_FALLBACKS = {
    "toothpaste": {
        "request_type": "Need Gap Analysis", "category": "Oral Care",
        "topic": "Herbal Toothpaste", "audience": "General Consumers",
        "keywords": ["toothpaste", "herbal", "neem", "fluoride", "whitening", "natural", "gum care"],
    },
    "oral care": {
        "request_type": "Sentiment Analysis", "category": "Oral Care",
        "topic": "Oral Care Products", "audience": "General Consumers",
        "keywords": ["toothpaste", "mouthwash", "whitening", "gum", "dental", "fluoride"],
    },
    "skincare": {
        "request_type": "Need Gap Analysis", "category": "Skincare",
        "topic": "Skincare Products", "audience": "Millennial Women",
        "keywords": ["moisturizer", "serum", "sunscreen", "retinol", "hyaluronic acid", "SPF", "natural"],
    },
    "moisturizer": {
        "request_type": "Trend Analysis", "category": "Skincare",
        "topic": "Moisturizers", "audience": "General Consumers",
        "keywords": ["moisturizer", "hydration", "dry skin", "barrier", "niacinamide", "ceramide"],
    },
    "sugar": {
        "request_type": "Trend Analysis", "category": "Beverages",
        "topic": "Sugar-Free Drinks", "audience": "Health-Conscious Consumers",
        "keywords": ["sugar-free", "zero sugar", "stevia", "artificial sweetener", "diet", "low calorie"],
    },
    "beverage": {
        "request_type": "Sentiment Analysis", "category": "Beverages",
        "topic": "Health Beverages", "audience": "Health Enthusiasts",
        "keywords": ["sugar-free", "energy drink", "kombucha", "functional beverage", "electrolytes"],
    },
    "wellness": {
        "request_type": "Ingredient Intelligence", "category": "Wellness",
        "topic": "Wellness Supplements", "audience": "Health Enthusiasts",
        "keywords": ["supplements", "vitamins", "probiotics", "adaptogens", "immunity", "natural"],
    },
    "supplement": {
        "request_type": "Ingredient Intelligence", "category": "Wellness",
        "topic": "Dietary Supplements", "audience": "Health Enthusiasts",
        "keywords": ["vitamins", "minerals", "protein", "omega-3", "collagen", "biotin", "ashwagandha"],
    },
    "haircare": {
        "request_type": "Sentiment Analysis", "category": "Haircare",
        "topic": "Hair Care Products", "audience": "General Consumers",
        "keywords": ["shampoo", "conditioner", "hair loss", "scalp", "keratin", "natural hair", "damage"],
    },
    "shampoo": {
        "request_type": "Ecommerce Review Mining", "category": "Haircare",
        "topic": "Shampoo & Conditioner", "audience": "General Consumers",
        "keywords": ["shampoo", "conditioner", "sulphate-free", "scalp", "frizz", "volumizing"],
    },
}


def classify_query(query: str, api_key: str = None) -> dict:
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": CLASSIFICATION_PROMPT.format(query=query)}],
                temperature=0.1,
                max_tokens=400,
            )
            result = json.loads(resp.choices[0].message.content)
            if "keywords" not in result:
                result["keywords"] = [result.get("topic", "").lower()]
            return result
        except Exception:
            pass

    query_lower = query.lower()
    for key, classification in _FALLBACKS.items():
        if key in query_lower:
            return classification.copy()

    words = [w for w in query_lower.split() if len(w) > 3]
    return {
        "request_type": "Sentiment Analysis",
        "category": "Consumer Products",
        "topic": query.strip().title(),
        "audience": "General Consumers",
        "keywords": words[:7] or [query.lower()],
    }
