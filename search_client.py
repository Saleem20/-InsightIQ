"""
Search client with two backends:
  - SerpAPI (preferred): organic + news + shopping results, country-targeted.
  - Google News RSS (fallback): news only, free, no key required.

Selection is automatic: if SERPAPI_KEY env var (or st.secrets) is set, SerpAPI is used.
Otherwise RSS is used and the UI warns the user that coverage is news-only.

Public surface:
    fetch_brand_mentions(brand, country_code, category_context, max_items) -> DataFrame
    fetch_many(brands, country_code, category_context, max_items)         -> (DataFrame, errors)
    active_backend() -> "serpapi" | "rss"
"""

from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import pandas as pd

try:
    import streamlit as st  # for st.secrets fallback when running inside Streamlit
except Exception:
    st = None  # type: ignore

# ----------------------------------------------------------------------------- helpers


def _clean(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _strip_html(value: str) -> str:
    return _clean(re.sub(r"<[^>]+>", " ", value or ""))


def _parse_date(value) -> object:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.date() if not pd.isna(parsed) else datetime.today().date()


def _get_serpapi_key() -> str | None:
    key = os.environ.get("SERPAPI_KEY")
    if key:
        return key
    if st is not None:
        try:
            return st.secrets.get("SERPAPI_KEY")  # type: ignore[attr-defined]
        except Exception:
            return None
    return None


def active_backend() -> str:
    return "serpapi" if _get_serpapi_key() else "rss"


# ----------------------------------------------------------------------------- RSS backend


def _fetch_rss(brand: str, context: str, country: str, max_items: int) -> pd.DataFrame:
    query = f'"{brand}" {context}'.strip()
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=en-{country}&gl={country}&ceid={country}:en"
    )
    request = Request(url, headers={"User-Agent": "BrandTrack/1.0"})
    with urlopen(request, timeout=15) as response:
        root = ET.fromstring(response.read())

    rows = []
    for item in root.findall(".//item")[:max_items]:
        title = _clean(item.findtext("title"))
        description = _strip_html(item.findtext("description"))
        publisher = _clean(item.findtext("source")) or "Google News"
        text = _clean(f"{title}. {description}")
        if not text:
            continue
        rows.append(
            {
                "date": _parse_date(item.findtext("pubDate")),
                "brand": brand,
                "platform": "Google News (RSS)",
                "result_type": "news",
                "publisher": publisher,
                "author": publisher,
                "text": text,
                "url": _clean(item.findtext("link")),
                "price": None,
                "rating": None,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "reach": 0,
                "owned": False,
                "influencer": False,
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- SerpAPI backend


def _serpapi_call(params: dict) -> dict:
    """Single SerpAPI HTTP call; isolated so it can be mocked in tests."""
    import json
    from urllib.parse import urlencode

    base = "https://serpapi.com/search.json"
    url = f"{base}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BrandTrack/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _fetch_serpapi(brand: str, context: str, country: str, max_items: int) -> pd.DataFrame:
    key = _get_serpapi_key()
    if not key:
        return pd.DataFrame()

    country_lower = country.lower()
    query = f'"{brand}" {context}'.strip()
    base = {
        "api_key": key,
        "q": query,
        "gl": country_lower,
        "hl": "en",
        "num": min(max_items, 20),
    }

    rows: List[dict] = []

    # 1. Organic web results
    try:
        organic_json = _serpapi_call({**base, "engine": "google"})
        for r in (organic_json.get("organic_results") or [])[:max_items]:
            rows.append(
                {
                    "date": datetime.today().date(),
                    "brand": brand,
                    "platform": "Google Organic",
                    "result_type": "organic",
                    "publisher": _clean(r.get("source") or r.get("displayed_link") or "Google"),
                    "author": _clean(r.get("source") or "Google"),
                    "text": _clean(f"{r.get('title','')}. {r.get('snippet','')}"),
                    "url": _clean(r.get("link")),
                    "price": None,
                    "rating": r.get("rating"),
                    "likes": 0,
                    "shares": 0,
                    "comments": 0,
                    "reach": 0,
                    "owned": False,
                    "influencer": False,
                }
            )
    except Exception:
        pass

    # 2. News results
    try:
        news_json = _serpapi_call({**base, "engine": "google_news"})
        news_items = news_json.get("news_results") or []
        for r in news_items[:max_items]:
            # Some entries have nested 'stories' (topic clusters); flatten one level.
            stories = r.get("stories") if isinstance(r, dict) else None
            iterable = stories if isinstance(stories, list) and stories else [r]
            for s in iterable[:max_items]:
                rows.append(
                    {
                        "date": _parse_date(s.get("date")),
                        "brand": brand,
                        "platform": "Google News",
                        "result_type": "news",
                        "publisher": _clean(s.get("source") or "Google News"),
                        "author": _clean(s.get("source") or "Google News"),
                        "text": _clean(f"{s.get('title','')}. {s.get('snippet','')}"),
                        "url": _clean(s.get("link")),
                        "price": None,
                        "rating": None,
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "reach": 0,
                        "owned": False,
                        "influencer": False,
                    }
                )
    except Exception:
        pass

    # 3. Shopping results
    try:
        shop_json = _serpapi_call({**base, "engine": "google_shopping"})
        for r in (shop_json.get("shopping_results") or [])[:max_items]:
            rows.append(
                {
                    "date": datetime.today().date(),
                    "brand": brand,
                    "platform": "Google Shopping",
                    "result_type": "shopping",
                    "publisher": _clean(r.get("source") or "Google Shopping"),
                    "author": _clean(r.get("source") or "Google Shopping"),
                    "text": _clean(r.get("title", "")),
                    "url": _clean(r.get("product_link") or r.get("link")),
                    "price": r.get("extracted_price"),
                    "rating": r.get("rating"),
                    "likes": int(r.get("reviews") or 0),
                    "shares": 0,
                    "comments": int(r.get("reviews") or 0),
                    "reach": 0,
                    "owned": False,
                    "influencer": False,
                }
            )
    except Exception:
        pass

    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- public API


def fetch_brand_mentions(
    brand: str,
    country_code: str,
    category_context: str,
    max_items: int = 20,
) -> pd.DataFrame:
    if _get_serpapi_key():
        df = _fetch_serpapi(brand, category_context, country_code, max_items)
        if not df.empty:
            return df
    # Fall back to free RSS (or use it as primary when no key)
    return _fetch_rss(brand, category_context, country_code, max_items)


def fetch_many(
    brands: List[str],
    country_code: str,
    category_context: str,
    max_items: int = 20,
    pause: float = 0.4,
) -> Tuple[pd.DataFrame, List[str]]:
    frames: List[pd.DataFrame] = []
    errors: List[str] = []
    for brand in brands:
        try:
            df = fetch_brand_mentions(brand, country_code, category_context, max_items)
            if not df.empty:
                frames.append(df)
        except Exception as exc:
            errors.append(f"{brand}: {exc.__class__.__name__} - {exc}")
        time.sleep(pause)  # gentle rate limit
    if not frames:
        return pd.DataFrame(), errors
    merged = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["brand", "url", "text"]
    )
    return merged, errors
