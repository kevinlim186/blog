from dash import html, dcc
from data.queries import fetch_inflation_data
import plotly.graph_objects as go
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_inflation_data()

    fig = go.Figure()

    # Breakeven Inflation Spread
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['breakeven_inflation_spread'],
        name='Breakeven Inflation Spread (DE - US)',
        yaxis='y1',
        line=dict(color=THEME_COLORS["primary"], width=2.5),
        hovertemplate='Breakeven Spread: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    # Real Return Spread
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['real_return_spread'],
        name='Real Return Spread (DE - US)',
        yaxis='y1',
        line=dict(color=THEME_COLORS["secondary"], width=2.5, dash='dash'),
        hovertemplate='Real Return Spread: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    # EUR/USD Exchange Rate
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['eur_usd_fx'],
        name='EUR/USD Exchange Rate',
        yaxis='y2',
        line=dict(color=THEME_COLORS["accent"], width=2.5, dash='dot'),
        hovertemplate='EUR/USD: %{y:.4f}<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        height=500,
        xaxis=dict(
            title='Date',
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor=THEME_COLORS["grid"]
        ),
        yaxis=dict(
            title='Bond Spread (%)',
            gridcolor=THEME_COLORS["grid"]
        ),
        yaxis2=dict(
            title='EUR/USD Exchange Rate',
            overlaying='y',
            side='right',
            showgrid=False,
            tickformat=".2f"
        ),
        hoverlabel=dict(namelength=-1),

    )

    return themed_card(
        title="Eurozone–US Yield Spreads & EUR/USD",
        description="Breakeven and real yield spreads alongside EUR/USD.",
        children=[
            dcc.Graph(
                id="interpolated-yield-bond",
                figure=fig
            )
        ]
    )