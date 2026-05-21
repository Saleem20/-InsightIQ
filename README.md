# BrandTrack KPIs

Simple Google Search-based brand tracking dashboard for the top 5 brands.

## What It Does

The app fetches Google News Search RSS results for each brand and builds a KPI dashboard covering:

- Share of Voice
- Publisher mix
- Net Sentiment
- Emotional texture
- Sentiment drivers
- Topic ownership
- Whitespace topics
- Risk clusters
- Negative velocity
- Brand Health Index

## Run Locally

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deployment

Use this as the Streamlit Cloud main file:

```text
streamlit_app.py
```

No upload, demo data, database, or API keys are required.
