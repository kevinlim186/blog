from dash import html, dcc, Input, Output, callback
from data.queries import fetch_telecom_interest_sensitive_stock
import plotly.graph_objects as go
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_telecom_interest_sensitive_stock()
    # Calculate y1 (interest rate) min/max
    min_rate = df['interest_rates'].min()
    max_rate = df['interest_rates'].max()
    center_rate = (min_rate + max_rate) / 2
    range_rate = max_rate - min_rate
    buffer_rate = range_rate * 0.1

    # Calculate y2 (cumulative gains) min/max
    min_gain = df['cumulative_gain'].min()
    max_gain = df['cumulative_gain'].max()
    center_gain = (min_gain + max_gain) / 2
    range_gain = max_gain - min_gain
    buffer_gain = range_gain * 0.1

    fig = go.Figure()

    tickers = df['ticker'].unique()
    color_map = {
        'T': THEME_COLORS.get("primary", "#005BBB"),
        'VZ': THEME_COLORS.get("secondary", "#2F80ED"),
        'CCOI': THEME_COLORS.get("accent", "#F2C94C"),
        'SP500': THEME_COLORS.get("benchmark", "#8B8B8B"),
    }

    # Add cumulative gain lines
    for ticker in tickers:
        fig.add_trace(go.Scatter(
            x=df[df['ticker'] == ticker]['date'],
            y=df[df['ticker'] == ticker]['cumulative_gain'],
            name=f'Cumulative Gain, {ticker}',
            yaxis='y2',
            line=dict(width=2.5, color=color_map.get(ticker, '#AAAAAA')),
            mode='lines'
        ))

    # Add interest rate line (one series only)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['interest_rates'],
        name='Interest Rate',
        yaxis='y1',
        mode='lines+markers',
        line=dict(width=2.5, color=THEME_COLORS["primary"]),
        fill='tozeroy',
        fillcolor='rgba(0, 91, 187, 0.10)',
        marker=dict(size=4, color=THEME_COLORS["primary"]),
        hovertemplate='Rate: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>',
        
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        xaxis=dict(
            title='Date',
            tickformat="%b %Y",
            hoverformat="%Y-%m-%d",
            gridcolor=THEME_COLORS["grid"]
        ),
        yaxis=dict(
            title='Interest Rate (%)',
            side='left',
            showgrid=True,
            gridcolor=THEME_COLORS["grid"],
            zeroline=False,
            range=[center_rate - range_rate/2 - buffer_rate, center_rate + range_rate/2 + buffer_rate]
        ),
        yaxis2=dict(
            title='Cumulative Gain (%)',
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=False,
            range=[center_gain - range_gain/2 - buffer_gain, center_gain + range_gain/2 + buffer_gain]
        ),
        hoverlabel=dict(namelength=-1)
    )

    return themed_card(
        title="Interest Rates vs Telecom Stock Performance",
        description="Comparison of U.S. interest rate movements and cumulative gains for interest-sensitive telecom stocks.",
        children=[
            dcc.Graph(
                id="interest-vs-stock-gain",
                figure=fig
            )
        ]
    )


def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "United States" },
        ]
    
    res['url'] = 'https://yellowplannet.com/interest-rate-sensitive-stocks/'

    return res 