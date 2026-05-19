import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="InsightIQ",
    page_icon="IQ",
    layout="wide",
    initial_sidebar_state="expanded",
)


BRANDS = ["Brand X", "PureLeaf", "NutriGo", "FreshMint", "WellCore"]
REQUIRED_COLUMNS = ["date", "text", "source", "audience", "brand", "engagement", "category"]
CATEGORIES = ["Oral Care", "Home Care", "Personal Care", "Wellness", "OTC", "Beverage"]
SOURCE_OPTIONS = ["X", "Reddit", "YouTube", "Review", "Forum", "Blog", "News", "Facebook", "RSS", "Upload"]
AUDIENCE_OPTIONS = ["Gen Z", "Millennial", "Parent", "Analyst", "General"]
RSS_PRESETS = {
    "Google News": "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en",
}
CATEGORY_KEYWORDS = {
    "Oral Care": ["toothpaste", "fluoride", "enamel", "cavity", "gum", "mouthwash", "oral", "teeth"],
    "Home Care": ["detergent", "cleaner", "laundry", "floor", "dishwash", "home care", "surface"],
    "Personal Care": ["skin", "hair", "soap", "shampoo", "deodorant", "beauty", "collagen", "personal care"],
    "Wellness": ["protein", "probiotic", "gut", "fitness", "sleep", "vitamin", "supplement", "wellness"],
    "OTC": ["medicine", "pain", "cold", "cough", "tablet", "capsule", "relief", "otc"],
    "Beverage": ["drink", "soda", "juice", "tea", "coffee", "beverage", "sugar-free", "shake"],
}
CATEGORY_EXAMPLES = {
    "Oral Care": "Analyze consumer concerns around herbal and fluoride toothpaste",
    "Home Care": "Analyze what consumers expect from home cleaning products",
    "Personal Care": "Analyze trust signals in skin and hair care conversations",
    "Wellness": "Analyze consumer needs around protein and probiotic products",
    "OTC": "Analyze consumer concerns around OTC cold and pain relief products",
    "Beverage": "Analyze consumer concerns around sugar-free drinks",
}
TOPICS = {
    "Herbal": ["herbal", "natural", "turmeric", "ayurvedic", "plant-based"],
    "Fluoride": ["fluoride", "cavity", "enamel", "toothpaste"],
    "Sugar-Free": ["sugar-free", "sweetener", "aspartame", "stevia"],
    "Protein": ["protein", "shake", "drink", "gym", "recovery"],
    "Collagen": ["collagen", "skin", "beauty", "glow"],
    "Probiotics": ["probiotic", "gut", "digestion", "microbiome"],
}
POSITIVE_WORDS = {
    "love",
    "better",
    "healthy",
    "clean",
    "trusted",
    "effective",
    "fresh",
    "natural",
    "transparent",
    "recommend",
    "great",
    "good",
}
NEGATIVE_WORDS = {
    "worried",
    "bad",
    "fake",
    "causes",
    "cancer",
    "unsafe",
    "bitter",
    "expensive",
    "missing",
    "hard",
    "wish",
    "hate",
    "risk",
}
NEED_GAP_PATTERNS = [
    "i wish",
    "need better",
    "missing",
    "hard to find",
    "too expensive",
    "why is there no",
]
MISINFO_PATTERNS = [
    "causes cancer",
    "toxic",
    "secretly harmful",
    "fake science",
    "unsafe trend",
    "chemical fear",
]


@st.cache_data
def load_sample_data() -> pd.DataFrame:
    base_date = datetime.today() - timedelta(days=59)
    conversations = [
        ("Brand X herbal toothpaste feels natural and fresh, but I wish the ingredient label was clearer.", "Review", "Millennial", "Brand X", "Oral Care"),
        ("Fluoride causes cancer according to a viral video. I am worried about toothpaste now.", "X", "Gen Z", "FreshMint", "Oral Care"),
        ("Sugar-free drinks help me stay on track, but artificial sweeteners taste bitter.", "Reddit", "Gen Z", "NutriGo", "Beverage"),
        ("PureLeaf turmeric toothpaste feels clean and ayurvedic. I would recommend it.", "Review", "Millennial", "PureLeaf", "Oral Care"),
        ("Need better protein drinks without chalky texture after gym workouts.", "Reddit", "Gen Z", "WellCore", "Wellness"),
        ("Brand X has good cavity protection, but FreshMint is cheaper.", "Forum", "Parent", "Brand X", "Oral Care"),
        ("Collagen drinks are everywhere, but I do not trust beauty claims without proof.", "YouTube", "Millennial", "NutriGo", "Personal Care"),
        ("Probiotic soda sounds healthy, though sugar content still bothers me.", "Blog", "Millennial", "WellCore", "Wellness"),
        ("Hard to find sugar-free drinks using natural sweeteners like stevia.", "Review", "Gen Z", "NutriGo", "Beverage"),
        ("FreshMint fluoride toothpaste repaired sensitivity and feels effective.", "Review", "Parent", "FreshMint", "Oral Care"),
        ("A creator said aspartame is secretly harmful. Is sugar-free soda unsafe?", "X", "Gen Z", "NutriGo", "Beverage"),
        ("I love herbal toothpaste, but some brands feel like they skip real science.", "Forum", "Millennial", "PureLeaf", "Oral Care"),
        ("Protein drinks need better flavors for women who want light recovery drinks.", "Reddit", "Gen Z", "WellCore", "Wellness"),
        ("Brand X is trusted in my family, but social media makes fluoride confusing.", "Facebook", "Parent", "Brand X", "Oral Care"),
        ("Turmeric and herbal claims are growing, but people want clinical backing.", "News", "Analyst", "PureLeaf", "Oral Care"),
        ("Sugar-free positioning works when brands explain sweeteners transparently.", "Blog", "Millennial", "NutriGo", "Beverage"),
        ("I hate the metallic aftertaste in some protein shakes.", "Review", "Gen Z", "WellCore", "Wellness"),
        ("Fluoride fear content is spreading fast in parenting communities.", "Forum", "Parent", "FreshMint", "Oral Care"),
        ("Clean label collagen with proof would make me switch brands.", "Review", "Millennial", "NutriGo", "Personal Care"),
        ("Brand X should talk more about enamel benefits instead of generic freshness.", "X", "Parent", "Brand X", "Oral Care"),
    ]
    rows = []
    for idx in range(180):
        text, source, audience, brand, category = conversations[idx % len(conversations)]
        date = base_date + timedelta(days=idx % 60)
        engagement = 20 + ((idx * 17) % 240)
        if "viral" in text.lower() or "spreading fast" in text.lower():
            engagement += 260
        rows.append(
            {
                "date": date.date(),
                "text": text,
                "source": source,
                "audience": audience,
                "brand": brand,
                "engagement": engagement,
                "category": category,
            }
        )
    return pd.DataFrame(rows)


def score_sentiment(text: str) -> str:
    words = set(re.findall(r"[a-z-]+", text.lower()))
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    if negative > positive:
        return "Negative"
    if positive > negative:
        return "Positive"
    return "Neutral"


def detect_topic(text: str) -> str:
    lowered = text.lower()
    scores = {
        topic: sum(1 for keyword in keywords if keyword in lowered)
        for topic, keywords in TOPICS.items()
    }
    best_topic, best_score = max(scores.items(), key=lambda item: item[1])
    return best_topic if best_score else "General Wellness"


def detect_need_gap(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in NEED_GAP_PATTERNS)


def detect_misinformation(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in MISINFO_PATTERNS)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["sentiment"] = result["text"].apply(score_sentiment)
    result["topic"] = result["text"].apply(detect_topic)
    result["need_gap"] = result["text"].apply(detect_need_gap)
    result["misinformation"] = result["text"].apply(detect_misinformation)
    result["risk_score"] = np.where(
        result["misinformation"],
        np.minimum(100, 55 + result["engagement"] // 8),
        np.where(result["sentiment"].eq("Negative"), 35 + result["engagement"] // 20, 15),
    )
    return result


def clean_text(value) -> str:
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"\s+", " ", text).strip()


def infer_audience(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["gen z", "college", "student", "tiktok"]):
        return "Gen Z"
    if any(term in lowered for term in ["parent", "kids", "family", "child"]):
        return "Parent"
    if any(term in lowered for term in ["millennial", "workout", "skincare", "career"]):
        return "Millennial"
    if any(term in lowered for term in ["market", "industry", "analyst", "report"]):
        return "Analyst"
    return "General"


def infer_category(text: str) -> str:
    lowered = text.lower()
    scores = {
        category: sum(1 for keyword in keywords if keyword in lowered)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score else "Wellness"


def normalize_category(value: str, fallback_text: str = "") -> str:
    cleaned = clean_text(value)
    for category in CATEGORIES:
        if cleaned.lower() == category.lower():
            return category
    return infer_category(f"{cleaned} {fallback_text}")


def normalize_columns(df: pd.DataFrame, default_source: str = "Upload") -> pd.DataFrame:
    """Accept common platform export schemas and convert them into the app contract."""
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    normalized_names = {
        column: re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in df.columns
    }
    working = df.rename(columns=normalized_names).copy()

    column_aliases = {
        "date": ["date", "created_at", "published_at", "posted_at", "time", "timestamp"],
        "text": ["text", "content", "message", "body", "caption", "title", "review", "comment", "post"],
        "source": ["source", "platform", "channel", "site", "network"],
        "audience": ["audience", "persona", "segment", "demographic"],
        "brand": ["brand", "company", "product", "keyword", "query"],
        "engagement": ["engagement", "interactions", "likes", "shares", "comments", "score", "upvotes"],
        "category": ["category", "vertical", "sector", "business_unit"],
    }

    selected = {}
    for target, aliases in column_aliases.items():
        for alias in aliases:
            if alias in working.columns:
                selected[target] = working[alias]
                break

    result = pd.DataFrame()
    result["text"] = selected.get("text", pd.Series(dtype=str)).apply(clean_text)
    result = result[result["text"].str.len() > 0]
    if result.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    if "date" in selected:
        result["date"] = pd.to_datetime(selected["date"], errors="coerce").dt.date
        result["date"] = result["date"].fillna(datetime.today().date())
    else:
        result["date"] = datetime.today().date()

    result["source"] = selected.get("source", default_source)
    result["source"] = result["source"].apply(lambda value: clean_text(value) or default_source)
    result["audience"] = selected.get("audience", result["text"].apply(infer_audience))
    result["audience"] = result["audience"].apply(lambda value: clean_text(value) or "General")
    result["brand"] = selected.get("brand", "Unassigned")
    result["brand"] = result["brand"].apply(lambda value: clean_text(value) or "Unassigned")

    if "engagement" in selected:
        result["engagement"] = pd.to_numeric(selected["engagement"], errors="coerce").fillna(1).clip(lower=1)
    else:
        result["engagement"] = 1

    if "category" in selected:
        category_values = selected["category"].reindex(result.index)
        result["category"] = [
            normalize_category(value, text)
            for value, text in zip(category_values, result["text"], strict=False)
        ]
    else:
        result["category"] = result["text"].apply(infer_category)

    return result[REQUIRED_COLUMNS].reset_index(drop=True)


def read_uploaded_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return normalize_columns(pd.read_csv(uploaded_file), default_source="Upload")
    if filename.endswith((".xlsx", ".xls")):
        return normalize_columns(pd.read_excel(uploaded_file), default_source="Upload")
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def rss_entry_text(item: ET.Element) -> str:
    title = clean_text(item.findtext("title"))
    description = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
    description = clean_text(description)
    return clean_text(f"{title}. {description}")


@st.cache_data(ttl=900, show_spinner="Fetching public web mentions...")
def fetch_rss_feeds(feed_urls: tuple[str, ...]) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    errors = []
    for feed_url in feed_urls[:3]:
        if not feed_url.strip():
            continue
        try:
            request = Request(
                feed_url.strip(),
                headers={"User-Agent": "InsightIQ/1.0 social-listening dashboard"},
            )
            with urlopen(request, timeout=3) as response:
                xml_payload = response.read()
            root = ET.fromstring(xml_payload)
            for item in root.findall(".//item"):
                text = rss_entry_text(item)
                if not text:
                    continue
                published = item.findtext("pubDate") or item.findtext("published")
                parsed_date = pd.to_datetime(published, errors="coerce")
                rows.append(
                    {
                        "date": parsed_date.date() if not pd.isna(parsed_date) else datetime.today().date(),
                        "text": text,
                        "source": "RSS",
                        "audience": infer_audience(text),
                        "brand": "Digital conversation",
                        "engagement": 1,
                        "category": infer_category(text),
                    }
                )
        except (ET.ParseError, TimeoutError, URLError, ValueError, OSError) as exc:
            errors.append(f"{feed_url.strip()} ({exc.__class__.__name__})")
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS), errors


def build_data_source(mode: str, uploaded_file, query: str, custom_feeds: str) -> tuple[pd.DataFrame, list[str], str]:
    warnings = []
    if mode == "Upload platform export":
        uploaded_df = read_uploaded_data(uploaded_file)
        return uploaded_df, warnings, "Uploaded platform export"

    if mode == "RSS link":
        feed_urls = [
            url.strip()
            for url in re.split(r"[\n,]+", custom_feeds or "")
            if url.strip()
        ]
        rss_df, warnings = fetch_rss_feeds(tuple(feed_urls)) if feed_urls else (
            pd.DataFrame(columns=REQUIRED_COLUMNS),
            ["No RSS links provided"],
        )
        return rss_df, warnings, "RSS link data"

    if mode == "Automatic web + upload":
        frames = [load_sample_data()]
        if uploaded_file is not None:
            frames.insert(0, read_uploaded_data(uploaded_file))
        feed_urls = [
            template.format(query=quote_plus(query))
            for template in RSS_PRESETS.values()
            if query.strip()
        ]
        feed_urls.extend(
            url.strip()
            for url in re.split(r"[\n,]+", custom_feeds or "")
            if url.strip()
        )
        if feed_urls:
            rss_df, warnings = fetch_rss_feeds(tuple(feed_urls))
            if not rss_df.empty:
                frames.insert(0, rss_df)
        blended = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
        return blended, warnings, "Automatic web, upload, and fallback data"

    if mode == "Live RSS / web search":
        feed_urls = [
            template.format(query=quote_plus(query))
            for template in RSS_PRESETS.values()
            if query.strip()
        ]
        feed_urls.extend(
            url.strip()
            for url in re.split(r"[\n,]+", custom_feeds or "")
            if url.strip()
        )
        rss_df, warnings = fetch_rss_feeds(tuple(feed_urls))
        return rss_df, warnings, "Live RSS and public web signals"

    if mode == "Blend live/upload with demo fallback":
        frames = []
        if uploaded_file is not None:
            frames.append(read_uploaded_data(uploaded_file))
        if query.strip() or custom_feeds.strip():
            feed_urls = [
                template.format(query=quote_plus(query))
                for template in RSS_PRESETS.values()
                if query.strip()
            ]
            feed_urls.extend(
                url.strip()
                for url in re.split(r"[\n,]+", custom_feeds or "")
                if url.strip()
            )
            rss_df, warnings = fetch_rss_feeds(tuple(feed_urls))
            frames.append(rss_df)
        frames.append(load_sample_data())
        blended = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
        return blended, warnings, "Blended live/upload/demo data"

    return load_sample_data(), warnings, "Demo data"


def filter_by_query(df: pd.DataFrame, query: str) -> pd.DataFrame:
    tokens = [
        token
        for token in re.findall(r"[a-zA-Z0-9-]+", query.lower())
        if len(token) > 2 and token not in {"what", "are", "the", "about", "around", "track", "identify", "compare"}
    ]
    if not tokens:
        return df
    mask = df["text"].str.lower().apply(lambda text: any(token in text for token in tokens))
    matched = df[mask]
    return matched if len(matched) >= 8 else df


def top_keywords(texts: pd.Series) -> list[tuple[str, int]]:
    stopwords = {
        "and",
        "the",
        "but",
        "with",
        "that",
        "this",
        "are",
        "for",
        "about",
        "from",
        "some",
        "like",
        "without",
        "brands",
        "brand",
    }
    words = []
    for text in texts:
        words.extend(
            word
            for word in re.findall(r"[a-z-]+", text.lower())
            if len(word) > 3 and word not in stopwords
        )
    return Counter(words).most_common(12)


def build_recommendations(df: pd.DataFrame, query: str) -> list[str]:
    leading_topic = df["topic"].mode().iat[0]
    negative_share = (df["sentiment"] == "Negative").mean()
    has_misinfo = df["misinformation"].any()
    need_gap_share = df["need_gap"].mean()

    recommendations = [
        f"Prioritize messaging around {leading_topic.lower()} because it is the strongest conversation cluster in this query.",
    ]
    if negative_share > 0.35:
        recommendations.append(
            "Address negative drivers directly with clearer claims, proof points, and product experience fixes."
        )
    if need_gap_share > 0.2:
        recommendations.append(
            "Convert repeated unmet needs into innovation briefs, especially around taste, transparency, availability, and proof."
        )
    if has_misinfo:
        recommendations.append(
            "Launch a rapid-response misinformation playbook with source tracking, expert-backed content, and community-specific rebuttals."
        )
    if "competitor" in query.lower() or "compare" in query.lower():
        recommendations.append(
            "Benchmark competitor associations by sentiment and claim territory before adjusting positioning."
        )
    return recommendations[:4]


def sentiment_chart(df: pd.DataFrame):
    trend = (
        df.groupby(["date", "sentiment"], as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
    )
    fig = px.area(
        trend,
        x="date",
        y="mentions",
        color="sentiment",
        color_discrete_map={
            "Positive": "#2e7d32",
            "Neutral": "#607d8b",
            "Negative": "#c62828",
        },
    )
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=310)
    return fig


def sentiment_summary(df: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    total = max(len(df), 1)
    counts = df["sentiment"].value_counts()
    positive = int(counts.get("Positive", 0))
    negative = int(counts.get("Negative", 0))
    neutral = int(counts.get("Neutral", 0))
    net_score = ((positive - negative) / total) * 100
    summary = pd.DataFrame(
        [
            {"Sentiment": "Positive", "Mentions": positive, "Share": positive / total},
            {"Sentiment": "Negative", "Mentions": negative, "Share": negative / total},
            {"Sentiment": "Neutral", "Mentions": neutral, "Share": neutral / total},
        ]
    )
    summary["Share"] = summary["Share"].map(lambda value: f"{value:.0%}")
    return net_score, summary


def topic_chart(df: pd.DataFrame):
    topic_counts = df["topic"].value_counts().reset_index()
    topic_counts.columns = ["topic", "mentions"]
    fig = px.bar(topic_counts, x="mentions", y="topic", orientation="h", color="mentions", color_continuous_scale="Teal")
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=310, yaxis={"categoryorder": "total ascending"})
    return fig


def risk_chart(df: pd.DataFrame):
    risk = df.groupby("source", as_index=False)["risk_score"].mean().sort_values("risk_score", ascending=False)
    fig = px.bar(risk, x="source", y="risk_score", color="risk_score", color_continuous_scale="Reds")
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=310, yaxis_title="Avg. risk")
    return fig


def competitor_chart(df: pd.DataFrame):
    brand_sentiment = (
        df.groupby(["brand", "sentiment"], as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
    )
    fig = px.bar(
        brand_sentiment,
        x="brand",
        y="mentions",
        color="sentiment",
        barmode="stack",
        color_discrete_map={
            "Positive": "#2e7d32",
            "Neutral": "#607d8b",
            "Negative": "#c62828",
        },
    )
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=310)
    return fig


st.markdown(
    """
    <style>
    :root {
        --ink: #17202a;
        --muted: #5c6670;
        --line: #dce3ea;
        --panel: #ffffff;
        --wash: #f5f7fa;
        --accent: #0f766e;
        --accent-2: #1d4ed8;
    }
    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }
    h1, h2, h3 { letter-spacing: 0; color: var(--ink); }
    section[data-testid="stSidebar"] {
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] > div {
        background: #fbfcfe;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 15px 16px;
        background: var(--panel);
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: var(--muted);
        font-weight: 650;
    }
    .hero-panel {
        border: 1px solid var(--line);
        background: linear-gradient(135deg, #ffffff 0%, #eef7f6 55%, #f7fafc 100%);
        border-radius: 8px;
        padding: 22px 24px;
        margin-bottom: 18px;
    }
    .hero-panel h1 {
        margin: 0 0 6px 0;
        font-size: 2.15rem;
        line-height: 1.1;
    }
    .hero-panel p {
        margin: 0;
        color: var(--muted);
        font-size: 1rem;
    }
    .insight-box {
        border: 1px solid #cfe4e1;
        border-left: 4px solid var(--accent);
        background: #f4fbf9;
        padding: 14px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .risk-alert {
        border: 1px solid #ffd7d7;
        border-left: 4px solid #c62828;
        background: #fff5f5;
        padding: 14px 16px;
        border-radius: 8px;
    }
    .data-badge {
        display: inline-flex;
        gap: 8px;
        align-items: center;
        border: 1px solid var(--line);
        background: var(--wash);
        border-radius: 999px;
        padding: 7px 11px;
        color: var(--muted);
        font-size: 0.86rem;
        margin: 0 8px 12px 0;
    }
    .section-label {
        color: var(--muted);
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-panel">
        <h1>InsightIQ</h1>
        <p>Consumer intelligence from digital conversations, platform exports, and live public feeds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index("Beverage"))

query = st.text_input(
    "Business question",
    value=CATEGORY_EXAMPLES[category],
    placeholder="What are consumers saying about herbal toothpaste?",
)

with st.sidebar:
    st.title("InsightIQ")
    st.caption("AI-powered consumer and brand intelligence")
    analysis_source = st.selectbox(
        "How do you want to analyze?",
        [
            "Live web search from digital/social platforms",
            "Upload files",
            "RSS link",
            "Upload + live web search",
            "Demo data",
        ],
        index=0,
    )
    uploaded_file = None
    custom_feeds = ""
    if analysis_source in {"Upload files", "Upload + live web search"}:
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel export",
            type=["csv", "xlsx", "xls"],
            help="Use exports from reviews, social listening tools, CRM notes, survey comments, or community platforms.",
        )
    if analysis_source == "RSS link":
        custom_feeds = st.text_area(
            "RSS feed URLs",
            placeholder="Paste RSS URLs, one per line",
            height=100,
        )
    elif analysis_source == "Upload + live web search":
        custom_feeds = st.text_area(
            "Optional RSS feed URLs",
            placeholder="Paste extra RSS URLs, one per line",
            height=86,
        )
    business_mode = st.selectbox(
        "Analysis mode",
        ["Insight dashboard", "Brand tracking", "Need gap analysis", "Ingredient intelligence", "Misinformation detection", "Competitor intelligence"],
    )
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

DATA_MODE_BY_SOURCE = {
    "Live web search from digital/social platforms": "Live RSS / web search",
    "Upload files": "Upload platform export",
    "RSS link": "RSS link",
    "Upload + live web search": "Automatic web + upload",
    "Demo data": "Demo data",
}
data_mode = DATA_MODE_BY_SOURCE[analysis_source]

if "has_analyzed" not in st.session_state:
    st.session_state.has_analyzed = False
if analyze_clicked:
    st.session_state.has_analyzed = True

requires_live_fetch = data_mode in {
    "Live RSS / web search",
    "RSS link",
    "Automatic web + upload",
    "Blend live/upload with demo fallback",
}
should_fetch_live = st.session_state.has_analyzed or not requires_live_fetch

if requires_live_fetch and not st.session_state.has_analyzed:
    st.info("Choose a category and business question, then click Analyze to fetch live web mentions.")

effective_mode = data_mode if should_fetch_live else "Demo data"
raw_df, source_warnings, source_label = build_data_source(effective_mode, uploaded_file, query, custom_feeds)
if raw_df.empty and data_mode != "Demo data":
    st.warning("No usable live or uploaded records were found. Showing demo data so the dashboard still renders.")
    raw_df = load_sample_data()
    source_label = "Demo fallback"
elif requires_live_fetch and st.session_state.has_analyzed:
    st.success(f"Analysis complete using {source_label}.")

df = enrich(raw_df)
if "category" not in df.columns:
    df["category"] = df["text"].apply(infer_category)
category_df = df[df["category"].eq(category)]
if not category_df.empty:
    df = category_df

available_sources = sorted(df["source"].dropna().astype(str).unique())
available_audiences = sorted(df["audience"].dropna().astype(str).unique())
with st.sidebar:
    st.divider()
    source_filter = st.multiselect("Sources", available_sources, default=available_sources)
    audience_filter = st.multiselect("Audience", available_audiences, default=available_audiences)

df = df[df["source"].isin(source_filter) & df["audience"].isin(audience_filter)]
analysis_df = filter_by_query(df, query)

if business_mode == "Need gap analysis":
    analysis_df = analysis_df[analysis_df["need_gap"]]
elif business_mode == "Misinformation detection":
    analysis_df = analysis_df[analysis_df["misinformation"] | analysis_df["risk_score"].gt(50)]
elif business_mode == "Competitor intelligence":
    analysis_df = analysis_df[analysis_df["brand"].ne("Unassigned")]
elif business_mode == "Ingredient intelligence":
    analysis_df = analysis_df[analysis_df["topic"].ne("General Wellness")]

if analysis_df.empty:
    st.warning("No matching conversations found. Widen the filters or adjust the business question.")
    st.stop()

date_range = f"{analysis_df['date'].min()} to {analysis_df['date'].max()}"
st.markdown(
    f"""
    <span class="data-badge">Data: {source_label}</span>
    <span class="data-badge">Category: {category}</span>
    <span class="data-badge">Records analyzed: {len(analysis_df):,}</span>
    <span class="data-badge">Date range: {date_range}</span>
    """,
    unsafe_allow_html=True,
)
if source_warnings:
    st.info("Some live feeds could not be reached. The dashboard used the available records and fallback data where selected.")
if "RSS" in analysis_df["source"].astype(str).unique():
    st.success("Live web mentions are included in this analysis.")
elif data_mode in {"Live RSS / web search", "RSS link"} and st.session_state.has_analyzed:
    st.warning("No live web mentions were returned for this query. Try a broader question or add RSS feed URLs.")

mentions = len(analysis_df)
positive_share = (analysis_df["sentiment"] == "Positive").mean()
negative_share = (analysis_df["sentiment"] == "Negative").mean()
risk_count = int(analysis_df["misinformation"].sum())
top_topic = analysis_df["topic"].mode().iat[0]

metric_cols = st.columns(5)
metric_cols[0].metric("Mentions", f"{mentions:,}")
metric_cols[1].metric("Positive", f"{positive_share:.0%}")
metric_cols[2].metric("Negative", f"{negative_share:.0%}")
metric_cols[3].metric("Risk alerts", risk_count)
metric_cols[4].metric("Top theme", top_topic)

st.markdown("### Executive Snapshot")
snapshot_cols = st.columns([1.4, 1])
with snapshot_cols[0]:
    st.markdown(
        f"""
        <div class="insight-box">
        <strong>AI insight</strong><br>
        Consumers are primarily discussing <strong>{top_topic.lower()}</strong>, with sentiment shaped by trust,
        proof, taste, transparency, and perceived health risk. The strongest strategic signal is to pair benefit-led
        positioning with clearer evidence and faster response to anxiety-led narratives.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if risk_count:
        st.markdown(
            f"""
            <div class="risk-alert">
            <strong>Misinformation watch</strong><br>
            {risk_count} conversation clusters include potentially misleading or fear-based claims. Prioritize source
            analysis and expert-backed clarification before these narratives spread further.
            </div>
            """,
            unsafe_allow_html=True,
        )
with snapshot_cols[1]:
    keywords = top_keywords(analysis_df["text"])
    st.write("Top conversation keywords")
    st.dataframe(pd.DataFrame(keywords, columns=["Keyword", "Mentions"]), hide_index=True, use_container_width=True)

tab_overview, tab_themes, tab_risk, tab_recs, tab_data = st.tabs(
    ["Trends", "Themes", "Risk", "Recommendations", "Conversation Data"]
)

with tab_overview:
    col1, col2 = st.columns(2)
    net_sentiment, sentiment_table = sentiment_summary(analysis_df)
    with col1:
        st.metric("Net sentiment score", f"{net_sentiment:+.0f}")
        st.caption("Calculated as positive share minus negative share, on a -100 to +100 scale.")
        st.dataframe(sentiment_table, hide_index=True, use_container_width=True)
    col2.plotly_chart(competitor_chart(analysis_df), use_container_width=True)

with tab_themes:
    col1, col2 = st.columns(2)
    col1.plotly_chart(topic_chart(analysis_df), use_container_width=True)
    audience = analysis_df.groupby(["audience", "topic"], as_index=False).size().rename(columns={"size": "mentions"})
    fig = px.density_heatmap(audience, x="topic", y="audience", z="mentions", color_continuous_scale="Viridis")
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=310)
    col2.plotly_chart(fig, use_container_width=True)
    st.write("Need-gap signals")
    st.dataframe(
        analysis_df.loc[analysis_df["need_gap"], ["date", "source", "audience", "category", "brand", "topic", "text"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_risk:
    col1, col2 = st.columns(2)
    col1.plotly_chart(risk_chart(analysis_df), use_container_width=True)
    risky = analysis_df.sort_values("risk_score", ascending=False).head(10)
    col2.dataframe(
        risky[["date", "source", "audience", "brand", "risk_score", "text"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_recs:
    recommendations = build_recommendations(analysis_df, query)
    for index, recommendation in enumerate(recommendations, start=1):
        st.markdown(
            f"""
            <div class="insight-box">
            <strong>Recommendation {index}</strong><br>{recommendation}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.write("Action planner")
    action_df = pd.DataFrame(
        {
            "Workstream": ["Claims", "Innovation", "Risk", "Media"],
            "Action": [
                "Translate top concerns into proof-backed messaging.",
                "Create concept briefs from repeated need-gap phrases.",
                "Monitor high-risk sources and misinformation triggers.",
                "Tune creator and community content to leading themes.",
            ],
            "Priority": ["High", "High", "Medium", "Medium"],
        }
    )
    st.dataframe(action_df, hide_index=True, use_container_width=True)

with tab_data:
    st.dataframe(
        analysis_df[["date", "source", "audience", "category", "brand", "topic", "sentiment", "risk_score", "text"]],
        hide_index=True,
        use_container_width=True,
    )
