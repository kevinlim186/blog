from dash import html, dcc, Input, Output, callback
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from data.queries import fetch_commitment_of_traders
from utils.utility import getBinsFromTrend
import numpy as np
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card


def layout():
    df = fetch_commitment_of_traders()

    _, t_values, slopes = getBinsFromTrend(close=df['close'].values, span=(4, 12), threshold=0, slope_threshold=0)

    df['t_values'] = t_values
    df_plot = df.dropna(subset=['t_values']).copy()

    # Classify for labels and color
    df_plot['signal_label'] = np.where(df_plot['t_values'] >= 0, 'Long', 'Short')
    df_plot['signal_color'] = df_plot['t_values']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_plot["df"],
        y=df_plot["close"],
        mode='markers',
        name="EUR/USD Close",
        marker=dict(
            color=df_plot["signal_color"],
            colorscale="RdBu_r",
            cmin=-10,
            cmax=10,
            colorbar=dict(title="t_value", tickvals=[-10, 0, 10], ticktext=["Short", "Neutral", "Long"]),
            size=6,
            line=dict(width=0)
        ),
        hovertemplate="%{x}<br>Close: %{y:.4f}<br>Position: %{text}<br>t_value: %{marker.color:.2f}",
        text=df_plot["signal_label"]
    ))

    fig.update_layout(
        title=dict(
            text="EUR/USD Close Colored by T-Value of Linear Trend",
            x=0.5,
            font=dict(size=20, family="Arial Black")
        ),
        template="plotly_dark",
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font=dict(color='white'),
        hovermode='x unified',
        xaxis_title="Date",
        yaxis_title="EUR/USD Close"
    )

    return html.Div([
        dcc.Graph(figure=fig)
    ])
