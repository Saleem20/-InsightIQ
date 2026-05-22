"""
BrandTrack KPIs — rebuilt.

Changes vs previous version:
  * Brands now come from a structured catalog (brands_catalog.py) — pick category + country,
    top brands auto-fill. No more hand-typing.
  * Search switched from news-only RSS to a dual-mode client (search_client.py):
    SerpAPI when SERPAPI_KEY is set (organic + news + shopping), RSS fallback when not.
  * KPI layer preserved (Share of Voice, Net Sentiment, Topic Ownership, Brand Health Index,
    Spike Risk, Whitespace topics, Negative Velocity).
"""

import re
from typing import Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from brands_catalog import CATALOG, COUNTRIES, brands_for, categories, context_for
from search_client import active_backend, fetch_many


# ----------------------------------------------------------------------------- page config

st.set_page_config(
    page_title="BrandTrack KPIs",
    page_icon="BT",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------------------- enrichment

TOPIC_KEYWORDS = {
    "Price & Value": ["price", "expensive", "cheap", "value", "deal", "discount", "offer"],
    "Quality & Performance": ["quality", "works", "effective", "performance", "reliable", "lasting", "durable"],
    "Taste & Sensory": ["taste", "flavor", "smell", "texture", "fresh", "sweet", "minty"],
    "Ingredients & Claims": ["ingredient", "natural", "clean", "sugar", "fluoride", "protein", "organic", "vegan", "gluten"],
    "Service & Availability": ["delivery", "stock", "available", "store", "support", "shipping", "online"],
    "Sustainability": ["recycle", "refill", "sustainable", "plastic", "eco", "waste", "carbon"],
    "Campaign & Creators": ["campaign", "ad", "creator", "influencer", "sponsored", "collab", "launch"],
    "Risk & Complaints": ["boycott", "unsafe", "fake", "scam", "complaint", "recall", "lawsuit", "ban"],
}
POSITIVE_WORDS = {
    "love", "great", "good", "best", "trusted", "effective", "fresh", "recommend", "reliable",
    "amazing", "happy", "works", "favorite", "clean", "quality", "better", "growth", "wins",
    "praised", "win", "leading", "premium", "loved",
}
NEGATIVE_WORDS = {
    "bad", "hate", "expensive", "unsafe", "fake", "complaint", "angry", "broken", "worried",
    "disappointed", "poor", "issue", "risk", "recall", "boycott", "problem", "lawsuit", "fall",
    "decline", "drop", "criticism", "harmful", "banned",
}
EMOTION_KEYWORDS = {
    "Trust": ["trusted", "reliable", "safe", "proven", "quality"],
    "Joy": ["love", "happy", "favorite", "amazing", "great"],
    "Anger": ["angry", "hate", "complaint", "boycott", "bad"],
    "Fear": ["worried", "unsafe", "risk", "recall", "lawsuit"],
    "Disgust": ["gross", "disgusting", "fake", "dirty", "chemical"],
    "Anticipation": ["launch", "new", "try", "waiting", "excited", "growth"],
}


def sentiment_score(text: str) -> int:
    words = set(re.findall(r"[a-z]+", text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return 1
    if neg > pos:
        return -1
    return 0


def sentiment_label(score: int) -> str:
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"


def detect_topic(text: str) -> str:
    lowered = text.lower()
    scores = {t: sum(1 for w in words if w in lowered) for t, words in TOPIC_KEYWORDS.items()}
    topic, score = max(scores.items(), key=lambda x: x[1])
    return topic if score else "General Brand Talk"


def detect_emotion(text: str) -> str:
    lowered = text.lower()
    scores = {e: sum(1 for w in words if w in lowered) for e, words in EMOTION_KEYWORDS.items()}
    emotion, score = max(scores.items(), key=lambda x: x[1])
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


# ----------------------------------------------------------------------------- KPI engine


def _safe_div(num, den):
    return 0 if den == 0 else num / den


def brand_kpis(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    cat_topic_share = df["topic"].value_counts(normalize=True)
    rows = []
    for brand, group in df.groupby("brand"):
        mentions = len(group)
        positive = (group["sentiment"] == "Positive").mean()
        negative = (group["sentiment"] == "Negative").mean()
        net_sent = (positive - negative) * 100
        unique_pubs = group["publisher"].nunique()
        advocacy = ((group["earned"]) & (group["sentiment"] == "Positive")).mean() * 100
        vol = group.groupby("week")["sentiment_score"].mean().std()
        vol = 0 if pd.isna(vol) else vol
        topic_strength = []
        for topic, tg in group.groupby("topic"):
            brand_share = len(tg) / mentions
            cat_share = cat_topic_share.get(topic, 0)
            topic_strength.append(_safe_div(brand_share, cat_share))
        topic_own = max(topic_strength) if topic_strength else 0
        neg_velocity = (
            group.sort_values("date").tail(max(3, mentions // 4))["sentiment_score"].lt(0).mean() * 100
        )
        weekly = group.groupby("week").size()
        spike = bool(len(weekly) >= 4 and weekly.iloc[-1] > weekly.mean() + 2 * weekly.std())
        health = (
            _safe_div(mentions, total) * 30
            + ((net_sent + 100) / 200) * 30
            + min(topic_own, 2) / 2 * 25
            + max(0, 1 - vol) * 15
        )
        rows.append(
            {
                "Brand": brand,
                "Mentions": mentions,
                "Share of Voice": _safe_div(mentions, total) * 100,
                "Net Sentiment": net_sent,
                "Top Emotion": group["emotion"].mode().iat[0],
                "Top Topic": group["topic"].mode().iat[0],
                "Topic Ownership": topic_own,
                "Unique Publishers": unique_pubs,
                "Advocacy Proxy": advocacy,
                "Sentiment Volatility": vol,
                "Negative Velocity": neg_velocity,
                "Spike Risk": "High" if spike or neg_velocity > 45 else "Watch" if neg_velocity > 25 else "Low",
                "Brand Health Index": health,
            }
        )
    return pd.DataFrame(rows).sort_values("Brand Health Index", ascending=False)


def topic_ownership_table(df: pd.DataFrame) -> pd.DataFrame:
    cat_share = df["topic"].value_counts(normalize=True)
    rows = []
    for brand, bdf in df.groupby("brand"):
        total_b = len(bdf)
        for topic, tdf in bdf.groupby("topic"):
            brand_share = len(tdf) / total_b
            rows.append(
                {
                    "Brand": brand,
                    "Topic": topic,
                    "Mentions": len(tdf),
                    "Topic Ownership Index": _safe_div(brand_share, cat_share.get(topic, 0)),
                    "Net Sentiment": tdf["sentiment_score"].mean() * 100,
                }
            )
    return pd.DataFrame(rows).sort_values("Topic Ownership Index", ascending=False)


def whitespace_topics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for topic, tdf in df.groupby("topic"):
        total = len(tdf)
        max_share = tdf["brand"].value_counts(normalize=True).max()
        if total >= 3 and max_share < 0.55:
            rows.append(
                {
                    "Topic": topic,
                    "Category Mentions": total,
                    "Max Brand Ownership": max_share * 100,
                    "Avg Sentiment": tdf["sentiment_score"].mean() * 100,
                }
            )
    return pd.DataFrame(rows).sort_values("Category Mentions", ascending=False)


# ----------------------------------------------------------------------------- caching wrappers


@st.cache_data(ttl=900, show_spinner=False)
def cached_fetch(brands_tuple: Tuple[str, ...], country: str, context: str, max_items: int):
    return fetch_many(list(brands_tuple), country, context, max_items)


# ----------------------------------------------------------------------------- UI

st.markdown(
    """
    <style>
    .main .block-container { max-width: 1280px; padding-top: 1.2rem; }
    .hero { border: 1px solid #d9e2ec; border-radius: 8px; padding: 20px 22px; background: #f7fafc; margin-bottom: 16px; }
    .hero h1 { margin: 0 0 4px 0; letter-spacing: 0; font-size: 2rem; }
    .hero p { margin: 0; color: #52606d; }
    div[data-testid="stMetric"] { border: 1px solid #d9e2ec; border-radius: 8px; padding: 12px; background: #fff; }
    .callout { border-left: 4px solid #0f766e; background: #f0fdfa; padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; margin-right: 6px; }
    .pill-ok { background: #ecfdf5; color: #047857; }
    .pill-warn { background: #fff7ed; color: #b45309; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Social Listening KPIs for Brand Tracking</h1>
      <p>Pick a category and country. Top brands auto-load. The app pulls Google search results
      and computes share-of-voice, sentiment, topic ownership, risk, and brand health.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

backend = active_backend()
if backend == "serpapi":
    st.markdown(
        '<span class="pill pill-ok">Mode: SerpAPI</span> Full coverage — organic + news + shopping results.',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<span class="pill pill-warn">Mode: News RSS (fallback)</span> '
        "No SERPAPI_KEY found — running on free Google News RSS only. "
        "Add a key to env or st.secrets to unlock organic + shopping results.",
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.title("Brand Tracking")

    category = st.selectbox("Category", categories(), index=0)
    available_countries = [c for c in COUNTRIES.keys() if brands_for(category, c)]
    country = st.selectbox(
        "Country / Google market",
        available_countries,
        format_func=lambda c: f"{c} — {COUNTRIES[c]}",
    )

    default_brands = brands_for(category, country)
    brands_selected = st.multiselect(
        "Brands to track (from catalog — edit as needed)",
        options=default_brands,
        default=default_brands,
    )

    custom_brand = st.text_input("Add custom brand (optional)", value="")
    if custom_brand.strip():
        brands_selected = brands_selected + [custom_brand.strip()]

    context_override = st.text_input(
        "Search context (auto-filled from category)",
        value=context_for(category, country),
    )
    max_items = st.slider("Results per brand", 5, 50, 20)
    fetch = st.button("Fetch Google Data", type="primary", use_container_width=True)

    st.caption(
        "Catalog: brands_catalog.py · Search backend: search_client.py · "
        "Edit either without touching the dashboard."
    )

if not fetch:
    st.info("Pick category, country, and brands in the sidebar, then click Fetch Google Data.")
    st.stop()

if len(brands_selected) < 2:
    st.warning("Select at least two brands so we can compare share-of-voice and topic ownership.")
    st.stop()

with st.spinner(f"Fetching Google data for {len(brands_selected)} brand(s)..."):
    raw, errors = cached_fetch(tuple(brands_selected), country, context_override, max_items)

if errors:
    st.warning("Some fetches failed: " + "; ".join(errors))

if raw.empty:
    st.warning(
        "No results found. Try a broader search context, increase results per brand, "
        "or verify the brand names match how Google indexes them."
    )
    st.stop()

data = enrich(raw)
kpis = brand_kpis(data)
leader = kpis.iloc[0]
laggard = kpis.iloc[-1]

st.markdown(
    f"""
    <div class="callout">
    <strong>Readout — {category}, {COUNTRIES[country]}:</strong>
    {leader['Brand']} leads on Brand Health Index. {laggard['Brand']} is weakest.
    Use topic ownership and risk signals before acting on raw volume.
    </div>
    """,
    unsafe_allow_html=True,
)

# KPI strip
metric_cols = st.columns(5)
metric_cols[0].metric("Total Results", f"{len(data):,}")
metric_cols[1].metric("Brands", data["brand"].nunique())
metric_cols[2].metric("Net Sentiment", f"{data['sentiment_score'].mean() * 100:+.0f}")
metric_cols[3].metric("Publishers", f"{data['publisher'].nunique():,}")
metric_cols[4].metric("Risk Mentions", f"{(data['topic'] == 'Risk & Complaints').sum():,}")

# Result-type breakdown (visible only when SerpAPI returns multiple types)
if data["result_type"].nunique() > 1:
    rt_mix = data.groupby(["brand", "result_type"], as_index=False).size().rename(
        columns={"brand": "Brand", "result_type": "Source", "size": "Results"}
    )
    st.plotly_chart(
        px.bar(rt_mix, x="Brand", y="Results", color="Source", title="Result Mix (Organic / News / Shopping)"),
        use_container_width=True,
    )

tab_position, tab_sentiment, tab_topics, tab_risk, tab_health, tab_data = st.tabs(
    ["Position", "Sentiment", "Topics", "Risk", "Health Index", "Raw Data"]
)

with tab_position:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(kpis, x="Brand", y="Share of Voice", color="Brand", title="Share of Voice"),
        use_container_width=True,
    )
    pub_mix = (
        data.groupby(["brand", "publisher"], as_index=False)
        .size()
        .rename(columns={"brand": "Brand", "publisher": "Publisher", "size": "Mentions"})
    )
    c2.plotly_chart(
        px.bar(pub_mix, x="Brand", y="Mentions", color="Publisher", title="Publisher Mix"),
        use_container_width=True,
    )
    st.dataframe(
        kpis[["Brand", "Mentions", "Share of Voice", "Unique Publishers"]],
        hide_index=True,
        use_container_width=True,
    )

with tab_sentiment:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(
            kpis, x="Brand", y="Net Sentiment", color="Net Sentiment",
            color_continuous_scale="RdYlGn", title="Net Sentiment",
        ),
        use_container_width=True,
    )
    emo = (
        data.groupby(["brand", "emotion"], as_index=False)
        .size()
        .rename(columns={"brand": "Brand", "emotion": "Emotion", "size": "Mentions"})
    )
    c2.plotly_chart(
        px.bar(emo, x="Brand", y="Mentions", color="Emotion", title="Emotional Texture"),
        use_container_width=True,
    )
    drivers = (
        data.groupby(["brand", "topic", "sentiment"], as_index=False)
        .size()
        .rename(columns={"brand": "Brand", "topic": "Topic", "sentiment": "Sentiment", "size": "Mentions"})
    )
    st.dataframe(drivers.sort_values("Mentions", ascending=False), hide_index=True, use_container_width=True)

with tab_topics:
    ownership = topic_ownership_table(data)
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(
            ownership.head(15), x="Topic Ownership Index", y="Topic",
            color="Brand", orientation="h", title="Topic Ownership Index",
        ),
        use_container_width=True,
    )
    topic_counts = (
        data.groupby(["brand", "topic"], as_index=False)
        .size()
        .rename(columns={"brand": "Brand", "topic": "Topic", "size": "Mentions"})
    )
    c2.plotly_chart(
        px.bar(topic_counts, x="Brand", y="Mentions", color="Topic", title="Topic Share per Brand"),
        use_container_width=True,
    )
    st.write("Whitespace topics")
    ws = whitespace_topics(data)
    st.dataframe(
        ws if not ws.empty else pd.DataFrame({"Message": ["No whitespace topic met the current threshold."]}),
        hide_index=True,
        use_container_width=True,
    )

with tab_risk:
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(kpis, x="Brand", y="Negative Velocity", color="Spike Risk", title="Negative Velocity"),
        use_container_width=True,
    )
    risk_mentions = data[(data["sentiment"] == "Negative") | (data["topic"] == "Risk & Complaints")]
    if not risk_mentions.empty:
        risk_counts = (
            risk_mentions.groupby(["brand", "topic"], as_index=False)
            .size()
            .rename(columns={"brand": "Brand", "topic": "Topic", "size": "Mentions"})
        )
        c2.plotly_chart(
            px.bar(risk_counts, x="Brand", y="Mentions", color="Topic", title="Risk Topic Clusters"),
            use_container_width=True,
        )
        st.dataframe(
            risk_mentions[["date", "brand", "publisher", "topic", "emotion", "text", "url"]].head(50),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No risk-flagged mentions in this dataset.")

with tab_health:
    st.plotly_chart(
        px.bar(
            kpis, x="Brand", y="Brand Health Index", color="Brand Health Index",
            color_continuous_scale="Teal", title="Brand Health Index",
        ),
        use_container_width=True,
    )
    st.dataframe(
        kpis[[
            "Brand", "Brand Health Index", "Share of Voice", "Net Sentiment",
            "Topic Ownership", "Sentiment Volatility", "Spike Risk",
        ]],
        hide_index=True,
        use_container_width=True,
    )

with tab_data:
    st.dataframe(data.sort_values("date", ascending=False), hide_index=True, use_container_width=True)
    st.download_button(
        "Download as CSV",
        data.to_csv(index=False).encode("utf-8"),
        file_name=f"brandtrack_{category}_{country}.csv",
        mime="text/csv",
    )
