from dash import html, dcc
from data.queries import fetch_inflation_data
import plotly.graph_objects as go

def layout():
    df = fetch_inflation_data()

    fig = go.Figure()

    # Breakeven Inflation Spread
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['breakeven_inflation_spread'],
        name='Breakeven Inflation Spread (DE - US)',
        yaxis='y1',
        line=dict(color='#00FF99', width=2.5),
        hovertemplate='Breakeven Spread: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    # Real Return Spread
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['real_return_spread'],
        name='Real Return Spread (DE - US)',
        yaxis='y1',
        line=dict(color='#3399FF', width=2.5, dash='dash'),
        hovertemplate='Real Return Spread: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    # EUR/USD Exchange Rate
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['eur_usd_fx'],
        name='EUR/USD Exchange Rate',
        yaxis='y2',
        line=dict(color='#FFCC00', width=2.5, dash='dot'),
        hovertemplate='EUR/USD: %{y:.4f}<br>Date: %{x|%Y-%m-%d}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text="Eurozone vs US: Bond Spreads and EUR/USD Exchange Rate",
            x=0.01,
            xanchor='left',
            font=dict(size=22)
        ),
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        height=500,
        margin=dict(l=30, r=30, t=60, b=40),
        hovermode='x unified',
        xaxis=dict(
            title='Date',
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor='#333'
        ),
        yaxis=dict(
            title='Bond Spread (%)',
            gridcolor='#333'
        ),
        yaxis2=dict(
            title='EUR/USD Exchange Rate',
            overlaying='y',
            side='right',
            showgrid=False,
            tickformat=".2f"
        ),
        hoverlabel=dict(namelength=-1),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,  # Push further down below x-axis labels
            xanchor='center',
            x=0.5,
            font=dict(size=12)
        ),
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="interpolated-yield-bond", figure=fig)
        ], className="black-container")
    ])