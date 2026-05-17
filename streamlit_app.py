import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="InsightIQ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .hero {
    background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 50%, #6d28d9 100%);
    padding: 2.2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.8rem;
    box-shadow: 0 4px 32px rgba(124,58,237,0.25);
  }
  .hero h1 { color: #fff; font-size: 2rem; font-weight: 700; margin: 0 0 0.3rem; }
  .hero p  { color: #ddd6fe; font-size: 1rem; margin: 0; }

  .badge {
    display: inline-block;
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0.2rem 0.15rem;
  }
  .badge-purple { background: rgba(124,58,237,0.18); color: #a78bfa; border: 1px solid rgba(124,58,237,0.35); }
  .badge-blue   { background: rgba(59,130,246,0.15); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
  .badge-green  { background: rgba(34,197,94,0.12);  color: #86efac; border: 1px solid rgba(34,197,94,0.3); }
  .badge-amber  { background: rgba(245,158,11,0.12); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }

  .kpi-card {
    background: #1e293b;
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    text-align: center;
  }
  .kpi-value { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
  .kpi-label { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

  .quote-card {
    background: #1e293b;
    border-left: 3px solid #7c3aed;
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.1rem;
    margin: 0.5rem 0;
    font-size: 0.88rem;
    color: #e2e8f0;
    font-style: italic;
  }
  .quote-pos { border-left-color: #22c55e; }
  .quote-neg { border-left-color: #ef4444; }

  .insight-block {
    background: #1e293b;
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
  }
  .insight-block h4 { color: #a78bfa; margin: 0 0 0.6rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }

  .opp-item  { background: rgba(34,197,94,0.08);  border-left: 3px solid #22c55e; border-radius: 0 8px 8px 0; padding: 0.65rem 1rem; margin: 0.4rem 0; color: #e2e8f0; font-size: 0.88rem; }
  .risk-item { background: rgba(239,68,68,0.08);  border-left: 3px solid #ef4444; border-radius: 0 8px 8px 0; padding: 0.65rem 1rem; margin: 0.4rem 0; color: #e2e8f0; font-size: 0.88rem; }
  .rec-item  { background: rgba(59,130,246,0.08); border-left: 3px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 0.65rem 1rem; margin: 0.4rem 0; color: #e2e8f0; font-size: 0.88rem; }

  .section-header { color: #e2e8f0; font-weight: 600; font-size: 1rem; margin: 1.2rem 0 0.6rem; border-bottom: 1px solid rgba(148,163,184,0.12); padding-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)


# ── Read API key from backend environment only ────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY") or None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown(
        f"**AI Model:** `gpt-4o-mini`  \n"
        f"**NLP Engine:** VADER Sentiment + sklearn NMF  \n"
        f"**Status:** {'🟢 AI mode active' if api_key else '🟡 Rule-based mode'}"
    )
    st.divider()

    st.markdown("### 💡 Example Queries")
    examples = [
        "What are consumers saying about herbal toothpaste?",
        "Identify unmet needs in skincare",
        "Track sentiment around sugar-free drinks",
        "What ingredient trends are emerging in wellness?",
        "Analyze consumer concerns around hair loss products",
    ]
    selected_example = None
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex[:20]}"):
            selected_example = ex

    st.divider()
    st.markdown("### 📊 About")
    st.caption(
        "InsightIQ converts social conversations into strategic business insights. "
        "Phase 1 MVP — powered by NLP + Generative AI."
    )


# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🔍 InsightIQ</h1>
  <p>AI-Powered Social Listening & Consumer Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)


# ── Query Input ───────────────────────────────────────────────────────────────
default_query = selected_example if selected_example else st.session_state.get("last_query", "")

query = st.text_area(
    "Ask a business question in plain English",
    value=default_query,
    height=90,
    placeholder='e.g. "What are consumers saying about herbal toothpaste?" or "Identify unmet needs in skincare"',
    label_visibility="collapsed",
)

col_btn, col_hint = st.columns([1, 5])
with col_btn:
    analyze = st.button("🔍 Analyze", type="primary", use_container_width=True)
with col_hint:
    st.caption("Analyzes social conversations across Reddit, Twitter, YouTube, Reviews & Blogs")


# ── Analysis Pipeline ─────────────────────────────────────────────────────────
if analyze and query.strip():
    st.session_state["last_query"] = query

    from src.classifier import classify_query
    from src.data_layer import get_conversations
    from src.nlp_engine import analyze_conversations
    from src.insight_generator import generate_insights
    import src.dashboard as dash

    progress = st.progress(0, text="Understanding your query…")
    time.sleep(0.3)

    classification = classify_query(query, api_key)
    progress.progress(20, text="Retrieving social conversations…")
    time.sleep(0.3)

    conversations = get_conversations(classification)
    progress.progress(45, text="Running NLP analysis…")
    time.sleep(0.4)

    analysis = analyze_conversations(conversations)
    progress.progress(70, text="Generating AI insights…")
    time.sleep(0.3)

    insights = generate_insights(query, classification, analysis, api_key)
    progress.progress(100, text="Done!")
    time.sleep(0.2)
    progress.empty()

    st.session_state["results"] = {
        "query": query,
        "classification": classification,
        "analysis": analysis,
        "insights": insights,
    }


# ── Results ───────────────────────────────────────────────────────────────────
if "results" in st.session_state:
    r = st.session_state["results"]
    classification = r["classification"]
    analysis = r["analysis"]
    insights = r["insights"]

    # Classification badges
    st.markdown(
        f'<div style="margin-bottom:1rem;">'
        f'<span class="badge badge-purple">🏷 {classification.get("request_type","")}</span>'
        f'<span class="badge badge-blue">📂 {classification.get("category","")}</span>'
        f'<span class="badge badge-green">🔎 {classification.get("topic","")}</span>'
        f'<span class="badge badge-amber">👥 {classification.get("audience","")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # KPI row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    sentiment_color = "#22c55e" if analysis["avg_sentiment"] > 0.05 else "#ef4444" if analysis["avg_sentiment"] < -0.05 else "#94a3b8"
    with kpi1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{analysis["total_mentions"]}</div><div class="kpi-label">Total Mentions</div></div>', unsafe_allow_html=True)
    with kpi2:
        score_str = f'{analysis["avg_sentiment"]:+.2f}'
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:{sentiment_color}">{score_str}</div><div class="kpi-label">Avg Sentiment</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{analysis["sentiment_pct"].get("positive",0)}%</div><div class="kpi-label">Positive</div></div>', unsafe_allow_html=True)
    with kpi4:
        country_count = len(analysis.get("country_distribution", {}))
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{country_count}</div><div class="kpi-label">Countries</div></div>', unsafe_allow_html=True)
    with kpi5:
        dr = analysis["date_range"]
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="font-size:1rem">{dr[0]}</div><div class="kpi-label">to {dr[1]}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_overview, tab_sentiment, tab_topics, tab_trends, tab_ai = st.tabs([
        "📊 Overview", "😊 Sentiment", "🗂️ Topics", "📈 Volume & Trends", "🤖 AI Insights"
    ])

    # ── Overview ──
    with tab_overview:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown('<p class="section-header">Sentiment Distribution</p>', unsafe_allow_html=True)
            st.plotly_chart(
                dash.sentiment_donut(analysis["sentiment_distribution"], analysis["sentiment_pct"]),
                use_container_width=True,
                key="chart_donut",
            )
        with col_right:
            st.markdown('<p class="section-header">Top Keywords</p>', unsafe_allow_html=True)
            st.plotly_chart(
                dash.keywords_bar(analysis["top_keywords"]),
                use_container_width=True,
                key="chart_keywords",
            )

        col_src, col_country = st.columns([1, 1])
        with col_src:
            st.markdown('<p class="section-header">Source Distribution</p>', unsafe_allow_html=True)
            st.plotly_chart(dash.source_bar(analysis["source_distribution"]), use_container_width=True, key="chart_source")
        with col_country:
            st.markdown('<p class="section-header">Geographic Distribution</p>', unsafe_allow_html=True)
            st.plotly_chart(dash.country_bar(analysis.get("country_distribution", {})), use_container_width=True, key="chart_country")

    # ── Sentiment ──
    with tab_sentiment:
        st.markdown('<p class="section-header">Sentiment Trend Over Time</p>', unsafe_allow_html=True)
        st.plotly_chart(dash.sentiment_trend(analysis["monthly_volume"]), use_container_width=True, key="chart_sentiment_trend")

        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.markdown('<p class="section-header">💚 Top Positive Voices</p>', unsafe_allow_html=True)
            for quote in analysis["top_positive"]:
                st.markdown(f'<div class="quote-card quote-pos">"{quote}"</div>', unsafe_allow_html=True)
        with col_neg:
            st.markdown('<p class="section-header">🔴 Top Negative Voices</p>', unsafe_allow_html=True)
            for quote in analysis["top_negative"]:
                st.markdown(f'<div class="quote-card quote-neg">"{quote}"</div>', unsafe_allow_html=True)

    # ── Topics ──
    with tab_topics:
        topics = analysis.get("topics", [])
        if topics:
            st.markdown('<p class="section-header">Topic Cluster Map</p>', unsafe_allow_html=True)
            st.plotly_chart(dash.topic_treemap(topics), use_container_width=True, key="chart_treemap")

            st.markdown('<p class="section-header">Topic Summary</p>', unsafe_allow_html=True)
            import pandas as pd
            topic_rows = []
            for t in topics:
                sentiment_icon = "🟢" if t.get("sentiment", 0) > 0.05 else "🔴" if t.get("sentiment", 0) < -0.05 else "🟡"
                topic_rows.append({
                    "Topic": t["label"],
                    "Top Keywords": ", ".join(t["keywords"][:4]),
                    "Mentions": t["count"],
                    "Sentiment": f'{sentiment_icon} {t.get("sentiment", 0):+.2f}',
                })
            st.dataframe(pd.DataFrame(topic_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Not enough data for topic clustering.")

    # ── Trends ──
    with tab_trends:
        st.markdown('<p class="section-header">Mention Volume Over Time</p>', unsafe_allow_html=True)
        st.plotly_chart(dash.volume_area(analysis["monthly_volume"]), use_container_width=True, key="chart_volume")

        st.markdown('<p class="section-header">Sentiment Breakdown by Month</p>', unsafe_allow_html=True)
        st.plotly_chart(dash.sentiment_trend(analysis["monthly_volume"]), use_container_width=True, key="chart_sentiment_trend_2")

        if analysis["monthly_volume"]:
            import pandas as pd
            st.markdown('<p class="section-header">Monthly Data Table</p>', unsafe_allow_html=True)
            df_monthly = pd.DataFrame(analysis["monthly_volume"])
            df_monthly.columns = ["Month", "Total", "Positive", "Neutral", "Negative"]
            st.dataframe(df_monthly, use_container_width=True, hide_index=True)

    # ── AI Insights ──
    with tab_ai:
        st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-block"><p style="color:#e2e8f0;font-size:0.95rem;line-height:1.65;margin:0">{insights.get("summary","")}</p></div>', unsafe_allow_html=True)

        # Key Themes
        themes = insights.get("key_themes", [])
        if themes:
            st.markdown('<p class="section-header">Key Themes</p>', unsafe_allow_html=True)
            cols = st.columns(min(len(themes), 2))
            for i, theme in enumerate(themes):
                with cols[i % 2]:
                    st.markdown(
                        f'<div class="insight-block"><h4>{theme.get("theme","")}</h4>'
                        f'<p style="color:#cbd5e1;font-size:0.87rem;margin:0">{theme.get("description","")}</p></div>',
                        unsafe_allow_html=True,
                    )

        col_opp, col_risk = st.columns(2)
        with col_opp:
            st.markdown('<p class="section-header">💡 Opportunities</p>', unsafe_allow_html=True)
            for opp in insights.get("opportunities", []):
                st.markdown(f'<div class="opp-item">✦ {opp}</div>', unsafe_allow_html=True)
        with col_risk:
            st.markdown('<p class="section-header">⚠️ Risk Alerts</p>', unsafe_allow_html=True)
            for risk in insights.get("risks", []):
                st.markdown(f'<div class="risk-item">▲ {risk}</div>', unsafe_allow_html=True)

        st.markdown('<p class="section-header">🎯 Strategic Recommendations</p>', unsafe_allow_html=True)
        for i, rec in enumerate(insights.get("recommendations", []), 1):
            st.markdown(f'<div class="rec-item"><b>#{i}</b> &nbsp; {rec}</div>', unsafe_allow_html=True)

elif not analyze:
    st.markdown("""
    <div style="text-align:center;padding:3rem 2rem;color:#64748b">
      <div style="font-size:3rem">🔍</div>
      <h3 style="color:#94a3b8;font-weight:500;margin:0.5rem 0">Start by entering a query above</h3>
      <p style="font-size:0.9rem">Try one of the example queries in the sidebar, or type your own business question.</p>
    </div>
    """, unsafe_allow_html=True)
