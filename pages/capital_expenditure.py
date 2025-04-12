from dash import html, dcc, Input, Output, callback
import plotly.express as px
from data.queries import fetch_capital_expenditure_by_industry
import dash
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def layout():
    df = fetch_capital_expenditure_by_industry()

    # Filter and reshape
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]
    df['capital_expenditure_b'] = df['capital_expenditure'] / 1e9

    rename_map = {
        'Industrial Applications and Services': 'Industrial',
        'Energy & Transportation': 'Energy/Transport',
        'Real Estate & Construction': 'Real Estate',
        'Trade & Services': 'Trade',
        'Life Sciences': 'LifeSci',
        'Technology': 'Tech',
        'Manufacturing': 'Mfg',
        'Finance': 'Finance'
    }
    df['category'] = df['category'].map(rename_map).fillna(df['category'])

    heatmap_data = df.pivot(index='category', columns='year', values='capital_expenditure_b')
    zmin = np.nanpercentile(heatmap_data.values, 5)
    zmax = np.nanpercentile(heatmap_data.values, 95)

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        zmin=zmin,
        zmax=zmax,
        colorbar=dict(
            title="CapEx ($B)",
            orientation="h",     # Horizontal
            x=0.5,               # Center horizontally
            xanchor="center",
            y=-0.3,              # Push below the x-axis
            len=1.0,             # Full width
            thickness=12         # Slim for aesthetic
        ),
        hovertemplate="Industry: %{y}<br>Year: %{x}<br>CapEx: %{z:.1f}B<extra></extra>"
    ))

    fig.update_layout(
        template='plotly_dark',
        title="Total Capital Expenditures by Industry (in Billions)",
        title_x=0.01,
        margin=dict(l=40, r=30, t=60, b=100),
        font=dict(color='white', family='Arial'),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111'
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="industry-capex-total-heatmap", figure=fig, config={"responsive": True})
        ], className="black-container", style={"overflowX": "auto", "padding": "1rem"})
    ])