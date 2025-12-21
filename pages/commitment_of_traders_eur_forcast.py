from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data.queries import fetch_commitment_of_traders
from utils.utility import getBinsFromTrend
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card


def layout():
    df = fetch_commitment_of_traders().copy()
    df = df.sort_values(by="df")

    _, t_values, _ = getBinsFromTrend(
        close=df["close"].values,
        span=(4, 12),
        threshold=0,
        slope_threshold=0
    )

    df["t_value"] = t_values
    df = df.dropna(subset=["t_value"])

    df["signal_label"] = np.where(df["t_value"] >= 0, "Long", "Short")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["df"],
        y=df["close"],
        mode="markers",
        name="EUR/USD Close",
        marker=dict(
            color=df["t_value"],
            colorscale="RdBu_r",
            cmin=-10,
            cmax=10,
            size=6,
            colorbar=dict(
                title="Signal",
                tickvals=[-10, 0, 10],
                ticktext=["Short", "Neutral", "Long"]
            )
        ),
        hovertemplate=(
            "%{x}<br>"
            "Close: %{y:.4f}<br>"
            "Signal: %{text}<br>"
            "t-value: %{marker.color:.2f}"
            "<extra></extra>"
        ),
        text=df["signal_label"]
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="EUR/USD Close"),
        xaxis=dict(title="Date"),
        autosize=True
    )

    return themed_card(
        title="EUR/USD — COT Trend Signal",
        description="EUR/USD close prices colored by t-values from rolling linear trend detection.",
        children=[
            dcc.Graph(
                id="eur-usd-cot-trend",
                figure=fig,
                style={"height": "460px"}
            ),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-cot",
                    n_clicks=0,
                    style={
                        "backgroundColor": THEME_COLORS["primary"],
                        "color": "#FFF",
                        "padding": "10px 22px",
                        "border": "none",
                        "borderRadius": "6px",
                        "fontWeight": "600",
                        "cursor": "pointer",
                        "fontSize": "14px",
                        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
                    }
                ),
                dcc.Download(id="download-cot")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )


def get_data():
    df = fetch_commitment_of_traders().copy()
    _, t_values, _ = getBinsFromTrend(
        close=df["close"].values,
        span=(4, 12),
        threshold=0,
        slope_threshold=0
    )
    df["t_value"] = t_values
    df = df.dropna(subset=["t_value"])
    return df


def get_meta_data():
    res = {}
    res["spatial_coverage"] = [
        {"@type": "Place", "name": "Euro Area / United States"}
    ]
    res["url"] = "https://yellowplannet.com/can-cot-data-predict-the-eur-usd-a-data-driven-faq-on-positioning-reversals-and-trading-models/"
    return res
