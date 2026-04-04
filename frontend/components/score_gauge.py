"""Circular score gauge display using Plotly."""

import plotly.graph_objects as go
import streamlit as st


def _score_color(score: float) -> str:
    """Return a color based on the score value."""
    if score >= 80:
        return "#22c55e"  # green
    elif score >= 60:
        return "#84cc16"  # lime
    elif score >= 40:
        return "#eab308"  # yellow
    elif score >= 25:
        return "#f97316"  # orange
    else:
        return "#ef4444"  # red


def render_score_gauge(overall_result: dict):
    """Render the main score gauge and breakdown metrics."""
    score = overall_result["overall_score"]
    grade = overall_result["grade"]
    summary = overall_result["summary"]
    breakdown = overall_result["breakdown"]
    color = _score_color(score)

    # -- Gauge chart --
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 48}},
        title={"text": f"Match Score  |  Grade: {grade}", "font": {"size": 20}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color, "thickness": 0.75},
            "bgcolor": "#1e1e2e",
            "steps": [
                {"range": [0, 25], "color": "rgba(239,68,68,0.15)"},
                {"range": [25, 50], "color": "rgba(234,179,8,0.15)"},
                {"range": [50, 75], "color": "rgba(132,204,22,0.15)"},
                {"range": [75, 100], "color": "rgba(34,197,94,0.15)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e0e0e0"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # -- Summary --
    st.markdown(f"**{summary}**")

    # -- Score breakdown columns --
    cols = st.columns(3)
    for col, (key, data) in zip(cols, breakdown.items()):
        label = key.title()
        weight_pct = int(data["weight"] * 100)
        col.metric(
            label=f"{label} ({weight_pct}%)",
            value=f"{data['score']:.0f}",
            delta=f"{data['contribution']:.1f} pts",
        )
