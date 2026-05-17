# InsightIQ — AI-Powered Social Listening Platform

Ask a business question in plain English. Get sentiment analysis, topic clusters, trend charts, and AI-generated strategic insights — instantly.

## Quick Start

### 1. Install dependencies

```bash
cd insightiq
pip install -r requirements.txt
```

### 2. Set your OpenAI key (optional)

```bash
cp .env.example .env
# Edit .env and add your key
```

Without an API key the app runs in **rule-based mode** — classification uses keyword matching and insights are template-generated. All charts and NLP analysis work without a key.

### 3. Run the app

```bash
streamlit run streamlit_app.py
```

---

## Example Queries

| Query | Type |
|---|---|
| What are consumers saying about herbal toothpaste? | Need Gap Analysis |
| Identify unmet needs in skincare | Need Gap Analysis |
| Track sentiment around sugar-free drinks | Sentiment Analysis |
| What ingredient trends are emerging in wellness? | Ingredient Intelligence |
| Analyze consumer concerns around haircare | Sentiment Analysis |

---

## Architecture

```
streamlit_app.py          ← Full UI (Streamlit)
src/
  classifier.py           ← NLU + query classification (OpenAI / keyword fallback)
  data_layer.py           ← Social listening data (mock, 25–30 posts × 5 topics)
  nlp_engine.py           ← VADER sentiment + TF-IDF/NMF topic modeling
  insight_generator.py    ← Executive insights (OpenAI / template fallback)
  dashboard.py            ← All Plotly chart builders
```

### Topics covered in mock data

- **Oral Care** — herbal toothpaste, neem, fluoride, whitening
- **Skincare** — moisturizer, serum, retinol, barrier care
- **Beverages** — sugar-free drinks, functional beverages, kombucha
- **Wellness** — supplements, adaptogens, vitamins, probiotics
- **Haircare** — shampoo, scalp health, hair loss, natural hair

---

## Dashboard Tabs

| Tab | Contents |
|---|---|
| 📊 Overview | Sentiment donut · Top keywords · Source breakdown |
| 😊 Sentiment | Trend over time · Best/worst quotes |
| 🗂️ Topics | NMF topic treemap · Topic summary table |
| 📈 Volume & Trends | Mention volume area chart · Monthly table |
| 🤖 AI Insights | Executive summary · Themes · Opportunities · Risks · Recommendations |

---

## Phase 2 Roadmap

- Real-time data ingestion (Reddit API, Twitter API)
- Semantic search with ChromaDB
- Competitor benchmarking dashboards
- Automated PDF/email report generation
- Misinformation detection module

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Streamlit |
| NLP | VADER Sentiment + sklearn NMF |
| LLM | OpenAI gpt-4o-mini |
| Visualization | Plotly |
| Data | Mock social dataset (Phase 1) |
