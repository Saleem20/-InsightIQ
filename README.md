# BrandTrack KPIs

Social-listening dashboard that pulls Google search results for a chosen category
and country, then computes share-of-voice, sentiment, topic ownership, risk, and
a composite Brand Health Index.

## What's new in this rebuild

- **Brand catalog**: pick a category (Toothpaste, Mouthwash, VMS, Beverages,
  Digestive, Shoes, SUV) and a country (US / India / China / UK). The top brands
  load automatically from `brands_catalog.py`. No more hand-typing.
- **Complete Google search**: when a `SERPAPI_KEY` is configured, the app pulls
  organic + news + shopping results in one go. Without a key, it falls back to
  the free Google News RSS feed so the app still runs.
- **Result-type breakdown**: when SerpAPI is active, a chart shows the mix of
  organic / news / shopping per brand.

## Files

| File | Purpose |
|---|---|
| `streamlit_app.py` | Dashboard UI and KPI engine |
| `brands_catalog.py` | Brand list per category and country |
| `search_client.py`  | SerpAPI + RSS search backend (auto-selects) |
| `requirements.txt`  | Python dependencies |
| `.env.example`      | Template for SerpAPI key |

## Run locally

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app works out of the box with no key (RSS mode). To enable full Google
coverage, get a free key at https://serpapi.com, then either:

- Set the env var: `setx SERPAPI_KEY your_key_here` (Windows)
- Or add it to `.streamlit/secrets.toml`:
  ```toml
  SERPAPI_KEY = "your_key_here"
  ```

## Deployment

Use this as the Streamlit Cloud main file:

```text
streamlit_app.py
```

Add `SERPAPI_KEY` to Streamlit Cloud's secrets to enable full search mode.

## Editing the brand catalog

Open `brands_catalog.py` and edit the `CATALOG` dict. Add a country, swap a
brand, change rank order — no changes to the app are needed.

## KPIs explained

- **Share of Voice** — brand mentions / total mentions in the dataset.
- **Net Sentiment** — `% positive − % negative`, scaled to ±100.
- **Topic Ownership Index** — how dominant a brand is in its top topic relative
  to the category average. Above 1 means above-average ownership.
- **Negative Velocity** — `% negative` in the most recent slice of mentions.
- **Spike Risk** — flags when the latest week's volume is unusually high or
  negative velocity is elevated.
- **Brand Health Index** — weighted blend of the above (volume 30%, sentiment
  30%, ownership 25%, stability 15%).

## Known limitations

- Sentiment is keyword-based today — fast and zero-dependency but coarse. A
  Hugging Face upgrade is a one-function swap (`sentiment_score` in
  `streamlit_app.py`).
- No persistence yet — each fetch is live. Adding SQLite to track history over
  time and surface real trends is the next planned step.
- SerpAPI free tier is 100 searches/month. Each brand uses up to 3 calls
  (organic + news + shopping), so 5 brands × 1 run = 15 calls. Plan accordingly.
