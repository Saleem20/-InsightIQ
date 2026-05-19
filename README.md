# InsightIQ

AI-powered consumer and brand intelligence prototype for social listening workflows.

## What It Does

InsightIQ lets a business user ask a natural-language question and generates an insight dashboard with:

- Executive snapshot
- Sentiment tracking
- Theme and need-gap analysis
- Trend velocity
- Misinformation risk detection
- Competitor and ingredient intelligence
- Strategic recommendations

The app can now work with real digital-platform data in three ways:

- Live public RSS/web-search feeds for quick market scans
- CSV or Excel uploads from social listening tools, reviews, communities, CRM notes, or survey exports
- Demo fallback data so the dashboard still works when live sources are unavailable

## Run Locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Upload Format

CSV/XLSX uploads are normalized automatically. The app looks for common column names such as:

- `date`, `created_at`, `published_at`, `timestamp`
- `text`, `content`, `message`, `body`, `caption`, `review`, `comment`
- `source`, `platform`, `channel`, `network`
- `audience`, `persona`, `segment`
- `brand`, `company`, `product`, `keyword`
- `engagement`, `interactions`, `likes`, `shares`, `comments`, `score`

## Suggested Next Steps

- Add authenticated connectors for paid APIs such as YouTube Data API, Reddit API, Meta, X, Google Reviews, or your social listening provider.
- Replace rule-based classification with Hugging Face or OpenAI-powered NLP.
- Add PostgreSQL and ChromaDB for persistence and semantic search.
- Add automated PowerPoint export for executive reporting.
