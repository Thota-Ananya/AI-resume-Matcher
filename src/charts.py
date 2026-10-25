"""Plotly figures for the dashboard."""

from __future__ import annotations

import plotly.graph_objects as go

from src.skill_extractor import group_by_category

PRIMARY = "#4F46E5"
GOOD = "#16A34A"
BAD = "#DC2626"


def gauge_chart(score: float) -> go.Figure:
    """Gauge showing the match percentage."""
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%"},
            title={"text": "Resume-job text similarity"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": PRIMARY},
                "steps": [
                    {"range": [0, 7], "color": "rgba(220,38,38,0.25)"},
                    {"range": [7, 15], "color": "rgba(245,158,11,0.25)"},
                    {"range": [15, 30], "color": "rgba(132,204,22,0.25)"},
                    {"range": [30, 100], "color": "rgba(22,163,74,0.25)"},
                ],
            },
        )
    )
    figure.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=10))
    return figure


def category_chart(analysis: dict, skills_db: dict) -> go.Figure | None:
    """Stacked bar chart of matched vs missing skills per category."""
    matched = group_by_category(analysis["matched"], skills_db)
    missing = group_by_category(analysis["missing"], skills_db)
    categories = sorted(set(matched) | set(missing))
    if not categories:
        return None
    figure = go.Figure()
    figure.add_bar(name="Matched", y=categories, x=[len(matched.get(c, [])) for c in categories],
                   orientation="h", marker_color=GOOD)
    figure.add_bar(name="Missing", y=categories, x=[len(missing.get(c, [])) for c in categories],
                   orientation="h", marker_color=BAD)
    figure.update_layout(
        barmode="stack", height=300, title="Job skills by category",
        xaxis_title="Number of skills", margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.25),
    )
    return figure


def keyword_chart(keywords: list[tuple[str, float]], title: str, color: str) -> go.Figure | None:
    """Horizontal bar chart of weighted keywords."""
    if not keywords:
        return None
    ordered = list(reversed(keywords))
    figure = go.Figure(
        go.Bar(x=[w for _, w in ordered], y=[t for t, _ in ordered], orientation="h", marker_color=color)
    )
    figure.update_layout(
        height=360, title=title, xaxis_title="TF-IDF weight in job description",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return figure
