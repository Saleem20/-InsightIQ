from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

_PALETTE = {
    "positive": "#22c55e",
    "neutral": "#94a3b8",
    "negative": "#ef4444",
    "primary": "#7c3aed",
    "secondary": "#a78bfa",
    "bg": "#0f172a",
    "surface": "#1e293b",
    "text": "#f1f5f9",
}

_PLOTLY_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=_PALETTE["text"], family="Inter, sans-serif"),
    xaxis=dict(gridcolor="rgba(148,163,184,0.1)", linecolor="rgba(148,163,184,0.2)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.1)", linecolor="rgba(148,163,184,0.2)"),
)


def sentiment_donut(distribution: Dict, pct: Dict) -> go.Figure:
    labels = ["Positive", "Neutral", "Negative"]
    values = [distribution.get("positive", 0), distribution.get("neutral", 0), distribution.get("negative", 0)]
    colors = [_PALETTE["positive"], _PALETTE["neutral"], _PALETTE["negative"]]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13, color=_PALETTE["text"]),
        hovertemplate="<b>%{label}</b><br>Mentions: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        annotations=[dict(
            text=f"<b>{pct.get('positive', 0)}%</b><br>Positive",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=_PALETTE["text"]),
        )],
    )
    return fig


def keywords_bar(top_keywords: List[tuple], n: int = 15) -> go.Figure:
    kws = top_keywords[:n]
    words = [w for w, _ in kws][::-1]
    counts = [c for _, c in kws][::-1]

    colors = [
        f"rgba(124,58,237,{0.5 + 0.5 * (i / len(words))})"
        for i in range(len(words))
    ]

    fig = go.Figure(go.Bar(
        x=counts,
        y=words,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b>: %{x} mentions<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        xaxis_title="Frequency",
        yaxis_title="",
        margin=dict(t=10, b=40, l=10, r=10),
    )
    return fig


def sentiment_trend(monthly_volume: List[Dict]) -> go.Figure:
    df = pd.DataFrame(monthly_volume)
    if df.empty:
        return go.Figure()

    fill_colors = {
        "positive": "rgba(34,197,94,0.12)",
        "neutral":  "rgba(148,163,184,0.12)",
        "negative": "rgba(239,68,68,0.12)",
    }
    fig = go.Figure()
    for label, color in [("positive", _PALETTE["positive"]),
                          ("neutral", _PALETTE["neutral"]),
                          ("negative", _PALETTE["negative"])]:
        fig.add_trace(go.Scatter(
            x=df["month"], y=df[label],
            name=label.title(),
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
            fill="tozeroy",
            fillcolor=fill_colors[label],
            hovertemplate=f"<b>{label.title()}</b><br>%{{x}}: %{{y}} mentions<extra></extra>",
        ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Month",
        yaxis_title="Mentions",
        margin=dict(t=30, b=40, l=10, r=10),
    )
    return fig


def volume_area(monthly_volume: List[Dict]) -> go.Figure:
    df = pd.DataFrame(monthly_volume)
    if df.empty:
        return go.Figure()

    fig = go.Figure(go.Scatter(
        x=df["month"], y=df["total"],
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color=_PALETTE["primary"], width=3),
        fillcolor="rgba(124,58,237,0.15)",
        marker=dict(size=8, color=_PALETTE["secondary"]),
        hovertemplate="<b>%{x}</b><br>Total Mentions: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        xaxis_title="Month",
        yaxis_title="Total Mentions",
        margin=dict(t=10, b=40, l=10, r=10),
    )
    return fig


def source_bar(source_distribution: Dict) -> go.Figure:
    sources = list(source_distribution.keys())
    counts = list(source_distribution.values())
    colors = [_PALETTE["primary"], _PALETTE["secondary"],
              "#6ee7b7", "#fcd34d", "#fb923c", "#f472b6"]

    fig = go.Figure(go.Bar(
        x=sources,
        y=counts,
        marker=dict(
            color=colors[:len(sources)],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b>: %{y} mentions<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        xaxis_title="Source",
        yaxis_title="Mentions",
        margin=dict(t=10, b=40, l=10, r=10),
    )
    return fig


def country_bar(country_distribution: Dict) -> go.Figure:
    if not country_distribution:
        return go.Figure()

    sorted_items = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
    countries = [c for c, _ in sorted_items][::-1]
    counts = [n for _, n in sorted_items][::-1]

    bar_colors = [
        f"rgba(124,58,237,{0.45 + 0.55 * (i / max(len(countries) - 1, 1))})"
        for i in range(len(countries))
    ]

    fig = go.Figure(go.Bar(
        x=counts,
        y=countries,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b>: %{x} mentions<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        xaxis_title="Mentions",
        yaxis_title="",
        margin=dict(t=10, b=40, l=10, r=10),
    )
    return fig


def topic_treemap(topics: List[Dict]) -> go.Figure:
    if not topics:
        return go.Figure()

    labels = [t["label"] for t in topics]
    values = [t["count"] for t in topics]
    parents = [""] * len(topics)
    colors = [t.get("sentiment", 0) for t in topics]

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            colorscale=[[0, _PALETTE["negative"]], [0.5, _PALETTE["neutral"]], [1, _PALETTE["positive"]]],
            cmid=0,
            showscale=True,
            colorbar=dict(title="Sentiment", thickness=12, len=0.7),
        ),
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Mentions: %{value}<br>Sentiment: %{color:.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_PLOTLY_TEMPLATE,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig
