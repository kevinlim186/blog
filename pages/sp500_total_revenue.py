import plotly.graph_objects as go
from dash import dcc, html
from data.queries import fetch_coporate_america_revenue_to_sp500

def layout():
    df = fetch_coporate_america_revenue_to_sp500()  # Your DataFrame should have: year, total_revenue, avg_market_cap, price_to_earnings

    fig = go.Figure()

    # Total Revenue
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['total_revenue'],
        name="Total Revenue",
        yaxis="y1",
        line=dict(color="#00FF99", width=2.5),
        hovertemplate='Revenue: %{y:$.2s}<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Average Market Cap
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['avg_market_cap'],
        name="Avg Market Cap",
        yaxis="y1",
        line=dict(color="#3399FF", width=2.5, dash="dot"),
        hovertemplate='Market Cap: %{y:$.2s}<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Price-to-Revenue (called price_to_earnings in your SQL)
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['price_to_earnings'],
        name="Price-to-Revenue",
        yaxis="y2",
        line=dict(color="#FFCC00", width=2.5, dash="dash"),
        hovertemplate='P/R Ratio: %{y:.2f}<br>Year: %{x|%Y}<extra></extra>'
    ))

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        height=520,
        margin=dict(l=40, r=50, t=60, b=40),
        title=dict(
            text="S&P 500: Total Revenue, Avg Market Cap & Price-to-Revenue Ratio",
            x=0.01, xanchor='left', font=dict(size=22)
        ),
        hovermode='x unified',
        xaxis=dict(
            title="Year",
            gridcolor='#333',
            tickformat="%Y",
            showspikes=True,
            spikemode='across',
            spikesnap='cursor'
        ),
        yaxis=dict(
            title="Revenue / Market Cap (USD)",
            gridcolor='#333',
            tickformat="$.2s"
        ),
        yaxis2=dict(
            title="Price-to-Revenue Ratio",
            overlaying='y',
            side='right',
            showgrid=False,
            tickformat=".2f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(namelength=-1)
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="sp500-metrics", figure=fig),
        ], className="black-container")
    ])