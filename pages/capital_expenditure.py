from dash import html, dcc, Input, Output, callback
import plotly.express as px
from data.queries import fetch_capital_expenditure_by_industry
import dash
import pandas as pd
import numpy as np


def layout():
    df = fetch_capital_expenditure_by_industry()

    # Clean + filter
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]
    df['capital_expenditure_b'] = df['capital_expenditure'] / 1e9

    heatmap_data = df.pivot(index='category', columns='year', values='capital_expenditure_b')

    # Clip scale
    zmin = np.nanpercentile(heatmap_data.values, 5)
    zmax = np.nanpercentile(heatmap_data.values, 95)

    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Year", y="Industry", color="CapEx ($B)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='Viridis',
        aspect="auto",
        title="Total Capital Expenditures by Industry (in Billions)",
        zmin=zmin,
        zmax=zmax
    )

    fig.update_traces(
        hovertemplate="Industry: %{y}<br>Year: %{x}<br>CapEx: %{z:.1f}B<extra></extra>",
        showscale=True
    )
    fig.update_layout(
        template='plotly_dark',
        margin=dict(l=40, r=30, t=60, b=60),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(x=0.01, xanchor='left', font=dict(size=22))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="industry-capex-total-heatmap", figure=fig)
        ], className="black-container"),
    ])