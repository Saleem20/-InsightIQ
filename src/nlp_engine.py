import re
import math
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

_analyzer = SentimentIntensityAnalyzer()

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "this", "that", "was",
    "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "my", "your", "his", "her", "our", "their", "we", "you", "i", "me",
    "he", "she", "they", "them", "us", "just", "so", "if", "not", "no",
    "more", "also", "as", "than", "too", "very", "still", "even", "after",
    "how", "what", "why", "when", "where", "who", "which", "all", "any",
    "now", "up", "out", "about", "there", "then", "some", "much", "many",
    "most", "other", "into", "over", "get", "like", "use", "know", "one",
    "time", "work", "well", "first", "good", "new", "think", "people",
    "never", "don", "didn", "doesn", "won", "isn", "aren", "wasn", "ve",
    "re", "ll", "m", "s", "t", "d", "actually", "really", "years",
}


def _label(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _extract_keywords(texts: List[str], top_n: int = 20) -> List[tuple]:
    words = []
    for text in texts:
        tokens = re.findall(r"[a-z]{4,}", text.lower())
        words.extend(t for t in tokens if t not in _STOPWORDS)
    return Counter(words).most_common(top_n)


def _extract_topics(texts: List[str], n_topics: int = 5) -> List[Dict]:
    if len(texts) < n_topics:
        n_topics = max(2, len(texts) - 1)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=500,
        ngram_range=(1, 2),
        min_df=1,
    )
    try:
        tfidf = vectorizer.fit_transform(texts)
    except Exception:
        return []

    nmf = NMF(n_components=n_topics, random_state=42, max_iter=200)
    nmf.fit(tfidf)

    feature_names = vectorizer.get_feature_names_out()
    doc_topics = nmf.transform(tfidf)

    topics = []
    for topic_idx, topic_vec in enumerate(nmf.components_):
        top_indices = topic_vec.argsort()[-6:][::-1]
        keywords = [feature_names[i] for i in top_indices]
        doc_mask = doc_topics.argmax(axis=1) == topic_idx
        count = int(doc_mask.sum())
        label = " & ".join(kw.title() for kw in keywords[:2])
        topics.append({
            "id": topic_idx,
            "label": label,
            "keywords": keywords,
            "count": count,
        })

    return [t for t in topics if t["count"] > 0]


def analyze_conversations(conversations: List[Dict]) -> Dict[str, Any]:
    enriched = []
    for conv in conversations:
        score = _analyzer.polarity_scores(conv["text"])["compound"]
        enriched.append({**conv, "sentiment_score": score, "sentiment_label": _label(score)})

    df = pd.DataFrame(enriched)
    df["month"] = df["timestamp"].apply(lambda d: d.strftime("%b %Y"))

    dist = df["sentiment_label"].value_counts().to_dict()
    dist.setdefault("positive", 0)
    dist.setdefault("neutral", 0)
    dist.setdefault("negative", 0)

    total = len(df)
    pct = {k: round(v / total * 100, 1) for k, v in dist.items()}

    keywords = _extract_keywords(df["text"].tolist())

    topics = _extract_topics(df["text"].tolist())
    for t in topics:
        doc_mask = [i for i, row in df.iterrows()
                    if any(kw in row["text"].lower() for kw in t["keywords"])]
        if doc_mask:
            t["sentiment"] = round(float(df.loc[doc_mask, "sentiment_score"].mean()), 3)
        else:
            t["sentiment"] = 0.0

    month_order = sorted(df["month"].unique(),
                         key=lambda m: datetime.strptime(m, "%b %Y"))
    monthly = []
    for month in month_order:
        mdf = df[df["month"] == month]
        monthly.append({
            "month": month,
            "total": len(mdf),
            "positive": int((mdf["sentiment_label"] == "positive").sum()),
            "neutral": int((mdf["sentiment_label"] == "neutral").sum()),
            "negative": int((mdf["sentiment_label"] == "negative").sum()),
        })

    source_dist = df["source"].value_counts().to_dict()
    country_dist = df["country"].value_counts().to_dict() if "country" in df.columns else {}

    pos_df = df[df["sentiment_label"] == "positive"].nlargest(3, "engagement")
    neg_df = df[df["sentiment_label"] == "negative"].nlargest(3, "engagement")

    return {
        "conversations": enriched,
        "total_mentions": total,
        "avg_sentiment": round(float(df["sentiment_score"].mean()), 3),
        "sentiment_distribution": dist,
        "sentiment_pct": pct,
        "top_keywords": keywords,
        "topics": topics,
        "monthly_volume": monthly,
        "source_distribution": source_dist,
        "country_distribution": country_dist,
        "top_positive": pos_df["text"].tolist(),
        "top_negative": neg_df["text"].tolist(),
        "date_range": (
            df["timestamp"].min().strftime("%d %b %Y"),
            df["timestamp"].max().strftime("%d %b %Y"),
        ),
    }
