import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="BrandTrack KPIs",
    page_icon="BT",
    layout="wide",
    initial_sidebar_state="expanded",
)


TOPIC_KEYWORDS = {
    "Price & Value": ["price", "expensive", "cheap", "value", "deal", "discount"],
    "Quality & Performance": ["quality", "works", "effective", "performance", "reliable", "lasting"],
    "Taste & Sensory": ["taste", "flavor", "smell", "texture", "fresh", "sweet"],
    "Ingredients & Claims": ["ingredient", "natural", "clean", "sugar", "fluoride", "protein", "organic"],
    "Service & Availability": ["delivery", "stock", "available", "store", "support", "shipping"],
    "Sustainability": ["recycle", "refill", "sustainable", "plastic", "eco", "waste"],
    "Campaign & Creators": ["campaign", "ad", "creator", "influencer", "sponsored", "collab"],
    "Risk & Complaints": ["boycott", "unsafe", "fake", "scam", "complaint", "recall", "bad"],
}
POSITIVE_WORDS = {
    "love", "great", "good", "best", "trusted", "effective", "fresh", "recommend", "reliable",
    "amazing", "happy", "works", "favorite", "clean", "quality", "better", "growth", "wins",
}
NEGATIVE_WORDS = {
    "bad", "hate", "expensive", "unsafe", "fake", "complaint", "angry", "broken", "worried",
    "disappointed", "poor", "issue", "risk", "recall", "boycott", "problem", "lawsuit", "fall",
}
EMOTION_KEYWORDS = {
    "Trust": ["trusted", "reliable", "safe", "proven", "quality"],
    "Joy": ["love", "happy", "favorite", "amazing", "great"],
    "Anger": ["angry", "hate", "complaint", "boycott", "bad"],
    "Fear": ["worried", "unsafe", "risk", "recall", "lawsuit"],
    "Disgust": ["gross", "disgusting", "fake", "dirty", "chemical"],
    "Anticipation": ["launch", "new", "try", "waiting", "excited", "growth"],
}


def clean_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def strip_html(value: str) -> str:
    return clean_text(re.sub(r"<[^>]+>", " ", value or ""))


def parse_date(value) -> object:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.date() if not pd.isna(parsed) else datetime.today().date()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_google_news_for_brand(brand: str, search_context: str, country_code: str, max_items: int) -> pd.DataFrame:
    query = f'"{brand}" {search_context}'.strip()
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=en-{country_code}&gl={country_code}&ceid={country_code}:en"
    )
    request = Request(url, headers={"User-Agent": "BrandTrack/1.0"})
    rows = []
    with urlopen(request, timeout=12) as response:
        root = ET.fromstring(response.read())

    for item in root.findall(".//item")[:max_items]:
        title = clean_text(item.findtext("title"))
        description = strip_html(item.findtext("description"))
        publisher = clean_text(item.findtext("source")) or "Google News"
        text = clean_text(f"{title}. {description}")
        if not text:
            continue
        rows.append(
            {
                "date": parse_date(item.findtext("pubDate")),
                "brand": brand,
                "platform": "Google Search",
                "publisher": publisher,
                "author": publisher,
                "text": text,
                "url": clean_text(item.findtext("link")),
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "reach": 0,
                "owned": False,
                "influencer": False,
            }
        )
    return pd.DataFrame(rows)


def fetch_google_mentions(brands: list[str], search_context: str, country_code: str, max_items: int) -> tuple[pd.DataFrame, list[str]]:
    frames = []
    errors = []
    for brand in brands:
        try:
            frame = fetch_google_news_for_brand(brand, search_context, country_code, max_items)
            if not frame.empty:
                frames.append(frame)
        except Exception as exc:
            errors.append(f"{brand}: {exc.__class__.__name__}")
    if not frames:
        return pd.DataFrame(), errors
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["brand", "url", "text"]), errors


def sentiment_score(text: str) -> int:
    words = set(re.findall(r"[a-z]+", text.lower()))
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    if positive > negative:
        return 1
    if negative > positive:
        return -1
    return 0


def sentiment_label(score: int) -> str:
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"


def detect_topic(text: str) -> str:
    lowered = text.lower()
    scores = {
        topic: sum(1 for term in terms if term in lowered)
        for topic, terms in TOPIC_KEYWORDS.items()
    }
    topic, score = max(scores.items(), key=lambda item: item[1])
    return topic if score else "General Brand Talk"


def detect_emotion(text: str) -> str:
    lowered = text.lower()
    scores = {
        emotion: sum(1 for term in terms if term in lowered)
        for emotion, terms in EMOTION_KEYWORDS.items()
    }
    emotion, score = max(scores.items(), key=lambda item: item[1])
    return emotion if score else "Neutral"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["week"] = pd.to_datetime(result["date"]).dt.to_period("W").astype(str)
    result["sentiment_score"] = result["text"].apply(sentiment_score)
    result["sentiment"] = result["sentiment_score"].apply(sentiment_label)
    result["topic"] = result["text"].apply(detect_topic)
    result["emotion"] = result["text"].apply(detect_emotion)
    result["engagement"] = result["likes"] + result["shares"] + result["comments"]
    result["earned"] = ~result["owned"]
    return result


def safe_divide(num, den):
    return 0 if den == 0 else num / den


def brand_kpis(df: pd.DataFrame) -> pd.DataFrame:
    total_mentions = len(df)
    category_topic_share = df["topic"].value_counts(normalize=True)
    rows = []
    for brand, group in df.groupby("brand"):
        mentions = len(group)
        positive = (group["sentiment"] == "Positive").mean()
        negative = (group["sentiment"] == "Negative").mean()
        net_sentiment = (positive - negative) * 100
        unique_publishers = group["publisher"].nunique()
        advocacy = ((group["earned"]) & (group["sentiment"] == "Positive")).mean() * 100
        volatility = group.groupby("week")["sentiment_score"].mean().std()
        volatility = 0 if pd.isna(volatility) else volatility
        topic_strength = []
        for topic, topic_group in group.groupby("topic"):
            brand_topic_share = len(topic_group) / mentions
            category_share = category_topic_share.get(topic, 0)
            topic_strength.append(safe_divide(brand_topic_share, category_share))
        topic_ownership = max(topic_strength) if topic_strength else 0
        negative_velocity = group.sort_values("date").tail(max(3, mentions // 4))["sentiment_score"].lt(0).mean() * 100
        weekly_mentions = group.groupby("week").size()
        spike_flag = bool(len(weekly_mentions) >= 4 and weekly_mentions.iloc[-1] > weekly_mentions.mean() + 2 * weekly_mentions.std())
        health = (
            safe_divide(mentions, total_mentions) * 30
            + ((net_sentiment + 100) / 200) * 30
            + min(topic_ownership, 2) / 2 * 25
            + max(0, 1 - volatility) * 15
        )
        rows.append(
            {
                "Brand": brand,
                "Mentions": mentions,
                "Share of Voice": safe_divide(mentions, total_mentions) * 100,
                "Net Sentiment": net_sentiment,
                "Top Emotion": group["emotion"].mode().iat[0],
                "Top Topic": group["topic"].mode().iat[0],
                "Topic Ownership": topic_ownership,
                "Unique Publishers": unique_publishers,
                "Advocacy Proxy": advocacy,
                "Sentiment Volatility": volatility,
                "Negative Velocity": negative_velocity,
                "Spike Risk": "High" if spike_flag or negative_velocity > 45 else "Watch" if negative_velocity > 25 else "Low",
                "Brand Health Index": health,
            }
        )
    return pd.DataFrame(rows).sort_values("Brand Health Index", ascending=False)


def topic_ownership_table(df: pd.DataFrame) -> pd.DataFrame:
    category_share = df["topic"].value_counts(normalize=True)
    rows = []
    for brand, brand_df in df.groupby("brand"):
        brand_total = len(brand_df)
        for topic, topic_df in brand_df.groupby("topic"):
            brand_topic_share = len(topic_df) / brand_total
            rows.append(
                {
                    "Brand": brand,
                    "Topic": topic,
                    "Mentions": len(topic_df),
                    "Topic Ownership Index": safe_divide(brand_topic_share, category_share.get(topic, 0)),
                    "Net Sentiment": topic_df["sentiment_score"].mean() * 100,
                }
            )
    return pd.DataFrame(rows).sort_values("Topic Ownership Index", ascending=False)


def whitespace_topics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for topic, topic_df in df.groupby("topic"):
        total = len(topic_df)
        max_brand_share = topic_df["brand"].value_counts(normalize=True).max()
        if total >= 3 and max_brand_share < 0.55:
            rows.append(
                {
                    "Topic": topic,
                    "Category Mentions": total,
                    "Max Brand Ownership": max_brand_share * 100,
                    "Avg Sentiment": topic_df["sentiment_score"].mean() * 100,
                }
            )
    return pd.DataFrame(rows).sort_values("Category Mentions", ascending=False)


st.markdown(
    """
    <style>
    .main .block-container { max-width: 1280px; padding-top: 1.2rem; }
    .hero { border: 1px solid #d9e2ec; border-radius: 8px; padding: 20px 22px; background: #f7fafc; margin-bottom: 16px; }
    .hero h1 { margin: 0 0 4px 0; letter-spacing: 0; font-size: 2rem; }
    .hero p { margin: 0; color: #52606d; }
    div[data-testid="stMetric"] { border: 1px solid #d9e2ec; border-radius: 8px; padding: 12px; background: #fff; }
    .callout { border-left: 4px solid #0f766e; background: #f0fdfa; padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Social Listening KPIs for Brand Tracking</h1>
      <p>Google Search data for the top 5 brands: share of voice, sentiment, topics, risk, and brand health.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Google Brand Tracking")
    brand_input = st.text_area(
        "Top 5 brands",
        value="Colgate\nSensodyne\nCloseup\nPepsodent\nDabur Red",
        height=116,
    )
    search_context = st.text_input("Category / search context", value="toothpaste oral care India")
    country_code = st.selectbox("Google market", ["IN", "US", "GB", "AU", "CA"], index=0)
    max_items = st.slider("Results per brand", 5, 50, 20)
    fetch = st.button("Fetch Google Data", type="primary", use_container_width=True)
    st.caption("Uses Google News Search RSS. It is a public web signal, not full social-platform firehose data.")

brands = [brand.strip() for brand in brand_input.splitlines() if brand.strip()][:5]

if not fetch:
    st.info("Enter five brands and click Fetch Google Data to build the KPI dashboard.")
    st.stop()

if len(brands) < 2:
    st.warning("Enter at least two brands.")
    st.stop()

with st.spinner("Fetching Google Search results for each brand..."):
    raw, errors = fetch_google_mentions(brands, search_context, country_code, max_items)

if errors:
    st.warning("Some Google searches failed: " + "; ".join(errors))
if raw.empty:
    st.warning("No Google results found. Try broader brand names or a broader category/search context.")
    st.stop()

data = enrich(raw)
kpis = brand_kpis(data)
leader = kpis.iloc[0]
laggard = kpis.iloc[-1]

st.markdown(
    f"""
    <div class="callout">
    <strong>Readout:</strong> {leader['Brand']} currently leads on Brand Health Index from Google Search results.
    {laggard['Brand']} is weakest among the selected brands. Use topic ownership and risk signals before acting on raw volume.
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(5)
metric_cols[0].metric("Google Mentions", f"{len(data):,}")
metric_cols[1].metric("Brands", data["brand"].nunique())
metric_cols[2].metric("Net Sentiment", f"{data['sentiment_score'].mean() * 100:+.0f}")
metric_cols[3].metric("Publishers", f"{data['publisher'].nunique():,}")
metric_cols[4].metric("Risk Mentions", f"{(data['topic'] == 'Risk & Complaints').sum():,}")

tab_position, tab_sentiment, tab_topics, tab_risk, tab_health, tab_data = st.tabs(
    ["Position", "Sentiment", "Topics", "Risk", "Health Index", "Google Data"]
)

with tab_position:
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(kpis, x="Brand", y="Share of Voice", color="Brand", title="Share of Voice"), use_container_width=True)
    publisher_mix = data.groupby(["brand", "publisher"], as_index=False).size().rename(columns={"brand": "Brand", "publisher": "Publisher", "size": "Mentions"})
    col2.plotly_chart(px.bar(publisher_mix, x="Brand", y="Mentions", color="Publisher", title="Publisher Mix"), use_container_width=True)
    st.dataframe(kpis[["Brand", "Mentions", "Share of Voice", "Unique Publishers"]], hide_index=True, use_container_width=True)

with tab_sentiment:
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(kpis, x="Brand", y="Net Sentiment", color="Net Sentiment", color_continuous_scale="RdYlGn", title="Net Sentiment"), use_container_width=True)
    emotion = data.groupby(["brand", "emotion"], as_index=False).size().rename(columns={"brand": "Brand", "emotion": "Emotion", "size": "Mentions"})
    col2.plotly_chart(px.bar(emotion, x="Brand", y="Mentions", color="Emotion", title="Emotional Texture"), use_container_width=True)
    drivers = data.groupby(["brand", "topic", "sentiment"], as_index=False).size().rename(columns={"brand": "Brand", "topic": "Topic", "sentiment": "Sentiment", "size": "Mentions"})
    st.dataframe(drivers.sort_values("Mentions", ascending=False), hide_index=True, use_container_width=True)

with tab_topics:
    ownership = topic_ownership_table(data)
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(ownership.head(15), x="Topic Ownership Index", y="Topic", color="Brand", orientation="h", title="Topic Ownership Index"), use_container_width=True)
    topic_counts = data.groupby(["brand", "topic"], as_index=False).size().rename(columns={"brand": "Brand", "topic": "Topic", "size": "Mentions"})
    col2.plotly_chart(px.bar(topic_counts, x="Brand", y="Mentions", color="Topic", title="Topic Share per Brand"), use_container_width=True)
    st.write("Whitespace topics")
    ws = whitespace_topics(data)
    st.dataframe(ws if not ws.empty else pd.DataFrame({"Message": ["No whitespace topic met the current threshold."]}), hide_index=True, use_container_width=True)

with tab_risk:
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(kpis, x="Brand", y="Negative Velocity", color="Spike Risk", title="Negative Velocity"), use_container_width=True)
    risk_mentions = data[(data["sentiment"] == "Negative") | (data["topic"] == "Risk & Complaints")]
    risk_counts = risk_mentions.groupby(["brand", "topic"], as_index=False).size().rename(columns={"brand": "Brand", "topic": "Topic", "size": "Mentions"})
    col2.plotly_chart(px.bar(risk_counts, x="Brand", y="Mentions", color="Topic", title="Risk Topic Clusters"), use_container_width=True)
    st.dataframe(risk_mentions[["date", "brand", "publisher", "topic", "emotion", "text", "url"]].head(50), hide_index=True, use_container_width=True)

with tab_health:
    st.plotly_chart(px.bar(kpis, x="Brand", y="Brand Health Index", color="Brand Health Index", color_continuous_scale="Teal", title="Brand Health Index"), use_container_width=True)
    st.dataframe(
        kpis[["Brand", "Brand Health Index", "Share of Voice", "Net Sentiment", "Topic Ownership", "Sentiment Volatility", "Spike Risk"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_data:
    st.dataframe(data.sort_values("date", ascending=False), hide_index=True, use_container_width=True)
